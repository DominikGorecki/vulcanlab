"""
Summarize Router - API endpoints for document summarization preparation and prompt generation.
"""

from fastapi import APIRouter, HTTPException, Path, status, Body
from sqlalchemy import select, delete, func
from sqlalchemy.orm import Session

from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.summarize_settings import SummarizeSettings
from vulcanlab.data.models.summary_chunk import SummaryChunk
from vulcanlab.data.models.summary_result import SummaryResult
from vulcanlab.data.models.chunk import Chunk
from vulcanlab.summarization.heading_selector import select_headings_for_summarization, HeadingInfo
from vulcanlab.summarization.chunk_ranker import rank_content_chunks, RankedChunk
from vulcanlab.summarization.prompt_generator import (
    HeadingWithChunks,
    calculate_total_budget,
    prune_to_budget,
    assemble_prompts,
    calculate_heading_with_chunks_tokens,
    batch_headings
)
from vulcanlab.summarization.summary_storage import (
    delete_existing_summaries,
    process_llm_response
)
from vulcanlab_api.schemas.summarize import (
    HeadingPreview,
    PrepareResponse,
    GeneratePromptsRequest,
    GeneratePromptsResponse,
    PromptResponse,
    SubmitResponseRequest,
    SubmitResponseResponse,
    SummarySection,
    WorkSummaryResponse,
    WorkSummaryListItem,
    WorkSummaryListResponse,
    SummarizeSettingsSchema
)

router = APIRouter()


@router.post(
    "/works/{work_id}/prepare",
    response_model=PrepareResponse,
    status_code=status.HTTP_200_OK,
    summary="Prepare work for summarization",
    description="Selects headings and ranks chunks for summarization. Stores results in summary_chunks table."
)
async def prepare_summarization(
    work_id: int = Path(..., gt=0)
) -> PrepareResponse:
    """
    Prepare a work for summarization.
    
    1. Load settings.
    2. Select headings.
    3. Rank content chunks for each heading.
    4. Store results in summary_chunks.
    5. Calculate estimates.
    """
    with get_session() as session:
        # 1. Check if work exists
        work = session.get(Work, work_id)
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with id {work_id} not found"
            )

        # Check if work has any chunks
        chunk_count = session.execute(
            select(Chunk).where(Chunk.work_id == work_id).limit(1)
        ).scalar()
        if not chunk_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Work with id {work_id} has no chunks"
            )

        try:
            # 2. Load settings
            settings = session.execute(select(SummarizeSettings)).scalar_one_or_none()
            if not settings:
                # Create default settings if not exists
                settings = SummarizeSettings()
                session.add(settings)
                session.flush()

            # 3. Select headings
            headings = select_headings_for_summarization(work_id, session, settings)
            if not headings:
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No headings found that qualify for summarization based on current settings."
                )

            # 4. Check if summary_chunks already exist for this work
            existing_chunks = session.execute(
                select(SummaryChunk).where(SummaryChunk.work_id == work_id).limit(1)
            ).scalar() is not None

            headings_with_chunks = []
            heading_previews = []

            for h in headings:
                ranked_chunks = rank_content_chunks(h, session, settings)
                hc_container = HeadingWithChunks(heading=h, ranked_chunks=ranked_chunks)
                hc_container.total_tokens = calculate_heading_with_chunks_tokens(hc_container, settings.tokens_per_word)
                headings_with_chunks.append(hc_container)

                heading_previews.append(HeadingPreview(
                    chunk_id=h.chunk_id,
                    level=h.level,
                    title=h.heading_title,
                    start_line=h.start_line,
                    content_word_count=h.content_word_count
                ))

                # Only save to summary_chunks if none exist yet
                # (preserves prompt_index from previous generate-prompts calls)
                if not existing_chunks:
                    for rc in ranked_chunks:
                        sc = SummaryChunk(
                            work_id=work_id,
                            heading_chunk_id=h.chunk_id,
                            content_chunk_id=rc.chunk_id,
                            word_count=rc.word_count,
                            dense_score=rc.dense_score,
                            lexical_score=rc.lexical_score,
                            rrf_score=rc.rrf_score,
                            mmr_score=rc.mmr_score,
                            rank_position=rc.rank_position
                        )
                        session.add(sc)
            
            # 5. Check for existing summaries
            has_existing = session.execute(
                select(SummaryResult).where(SummaryResult.work_id == work_id).limit(1)
            ).scalar() is not None
            
            # 6. Calculate estimates (after pruning)
            _, max_budget = calculate_total_budget(headings_with_chunks, settings)
            pruned_hc = prune_to_budget(headings_with_chunks, max_budget, settings)
            
            # Re-calculate total tokens and prompts after pruning
            total_tokens = sum(hc.total_tokens for hc in pruned_hc)
            # Note: assemble_prompts uses batch_headings which we should use for prompt count
            batches = batch_headings(pruned_hc, settings.max_tokens_per_call, settings.tokens_per_word)
            total_prompts = len(batches)

            session.commit()

            return PrepareResponse(
                headings=heading_previews,
                total_prompts=total_prompts,
                estimated_tokens=total_tokens,
                has_existing_summaries=has_existing
            )

        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred during preparation: {str(e)}"
            )


@router.post(
    "/works/{work_id}/generate-prompts",
    response_model=GeneratePromptsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate summarization prompts",
    description="Assembles prompts from ranked chunks. Uses results stored in summary_chunks."
)
async def generate_summarization_prompts(
    request: GeneratePromptsRequest,
    work_id: int = Path(..., gt=0)
) -> GeneratePromptsResponse:
    """
    Generate prompts for summarization.
    
    1. Handle regeneration if requested.
    2. Load ranked chunks from summary_chunks.
    3. Reconstruct HeadingWithChunks.
    4. Prune to budget.
    5. Assemble prompts.
    """
    with get_session() as session:
        work = session.get(Work, work_id)
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with id {work_id} not found"
            )

        try:
            # 1. Handle regeneration
            if request.regenerate_all:
                delete_existing_summaries(work_id, session)
                
                # Re-load settings
                settings = session.execute(select(SummarizeSettings)).scalar_one_or_none()
                if not settings:
                    settings = SummarizeSettings()
                    session.add(settings)
                    session.flush()
                    
                # Re-run selection and ranking
                headings = select_headings_for_summarization(work_id, session, settings)
                if not headings:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No headings found for summarization."
                    )
                    
                headings_with_chunks = []
                for h in headings:
                    ranked_chunks = rank_content_chunks(h, session, settings)
                    hc_container = HeadingWithChunks(heading=h, ranked_chunks=ranked_chunks)
                    hc_container.total_tokens = calculate_heading_with_chunks_tokens(hc_container, settings.tokens_per_word)
                    headings_with_chunks.append(hc_container)
                    
                    # Re-save to summary_chunks
                    for rc in ranked_chunks:
                        sc = SummaryChunk(
                            work_id=work_id,
                            heading_chunk_id=h.chunk_id,
                            content_chunk_id=rc.chunk_id,
                            word_count=rc.word_count,
                            dense_score=rc.dense_score,
                            lexical_score=rc.lexical_score,
                            rrf_score=rc.rrf_score,
                            mmr_score=rc.mmr_score,
                            rank_position=rc.rank_position
                        )
                        session.add(sc)
                all_headings = headings
            else:
                # Load from storage
                settings = session.execute(select(SummarizeSettings)).scalar_one_or_none()
                if not settings:
                    settings = SummarizeSettings()

                # Load SummaryChunks joined with Chunks
                stmt = (
                    select(SummaryChunk, Chunk)
                    .join(Chunk, SummaryChunk.content_chunk_id == Chunk.id)
                    .where(SummaryChunk.work_id == work_id)
                    .order_by(SummaryChunk.heading_chunk_id, SummaryChunk.rank_position)
                )
                rows = session.execute(stmt).all()
                
                if not rows:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Work has not been prepared for summarization. Call /prepare first."
                    )

                # Reconstruct HeadingWithChunks
                heading_ids = sorted(list(set(row[0].heading_chunk_id for row in rows)))
                
                # Get all headings for context
                all_headings = select_headings_for_summarization(work_id, session, settings)
                heading_map = {h.chunk_id: h for h in all_headings}
                
                hc_map = {}
                for sc, chunk in rows:
                    if sc.heading_chunk_id not in hc_map:
                        h_info = heading_map.get(sc.heading_chunk_id)
                        if not h_info:
                            continue
                        hc_map[sc.heading_chunk_id] = HeadingWithChunks(
                            heading=h_info,
                            ranked_chunks=[]
                        )
                    
                    rc = RankedChunk(
                        chunk_id=chunk.id,
                        content=chunk.content,
                        word_count=sc.word_count,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                        dense_score=sc.dense_score,
                        lexical_score=sc.lexical_score,
                        rrf_score=sc.rrf_score,
                        mmr_score=sc.mmr_score,
                        rank_position=sc.rank_position
                    )
                    hc_map[sc.heading_chunk_id].ranked_chunks.append(rc)
                
                headings_with_chunks = [hc_map[hid] for hid in heading_ids if hid in hc_map]

            # 2. Prune and assemble
            _, max_budget = calculate_total_budget(headings_with_chunks, settings)
            pruned_hc = prune_to_budget(headings_with_chunks, max_budget, settings)
            
            prompt_batches = assemble_prompts(pruned_hc, all_headings, session, settings)
            
            # Update summary_chunks with prompt_index for tracking
            for pb in prompt_batches:
                for hid in pb.heading_ids:
                    session.execute(
                        SummaryChunk.__table__.update()
                        .where(SummaryChunk.work_id == work_id)
                        .where(SummaryChunk.heading_chunk_id == hid)
                        .values(prompt_index=pb.prompt_index)
                    )

            session.commit()
            
            return GeneratePromptsResponse(
                prompts=[
                    PromptResponse(
                        prompt_index=pb.prompt_index,
                        content=pb.content,
                        heading_ids=pb.heading_ids
                    )
                    for pb in prompt_batches
                ]
            )

        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred during prompt generation: {str(e)}"
            )


@router.post(
    "/works/{work_id}/submit-response",
    response_model=SubmitResponseResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit LLM response and store summaries",
    description="Parses LLM response, validates against expected heading IDs, and stores in summary_results."
)
async def submit_summarization_response(
    request: SubmitResponseRequest,
    work_id: int = Path(..., gt=0)
) -> SubmitResponseResponse:
    """
    Submit LLM response for a specific prompt batch.
    """
    with get_session() as session:
        work = session.get(Work, work_id)
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with id {work_id} not found"
            )

        # Look up expected heading_ids for this prompt_index
        expected_ids = session.execute(
            select(SummaryChunk.heading_chunk_id)
            .where(SummaryChunk.work_id == work_id)
            .where(SummaryChunk.prompt_index == request.prompt_index)
            .distinct()
        ).scalars().all()

        if not expected_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No expected headings found for work {work_id} and prompt index {request.prompt_index}. "
                       f"Has prompt generation been run?"
            )

        result = process_llm_response(
            work_id=work_id,
            prompt_index=request.prompt_index,
            response_json=request.response_json,
            expected_heading_ids=list(expected_ids),
            session=session
        )

        return SubmitResponseResponse(
            success=result.success,
            summaries_saved=result.summaries_saved,
            errors=result.errors
        )


@router.get(
    "/works/{work_id}/summary",
    response_model=WorkSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full summary for a work",
    description="Returns all generated summary sections for a work, ordered by document position."
)
async def get_work_summary(
    work_id: int = Path(..., gt=0)
) -> WorkSummaryResponse:
    """
    Retrieve all summary sections for a work.
    """
    with get_session() as session:
        work = session.get(Work, work_id)
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with id {work_id} not found"
            )

        # Query summary_results joined with chunks for heading info
        stmt = (
            select(SummaryResult, Chunk)
            .join(Chunk, SummaryResult.chunk_id == Chunk.id)
            .where(SummaryResult.work_id == work_id)
            .order_by(Chunk.start_line.asc())
        )
        rows = session.execute(stmt).all()

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No summaries found for work with id {work_id}"
            )

        sections = []
        for res, chunk in rows:
            # For heading chunks (level without "-chunk"), the title is the first line of content
            # The first line should be a markdown heading like "# Title" or "## Subtitle"
            heading = "Untitled Section"
            if chunk.content:
                first_line = chunk.content.split('\n')[0].strip()
                # Verify it looks like a markdown heading (starts with #)
                if first_line.startswith('#'):
                    heading = first_line
                elif chunk.heading_breadcrumbs:
                    # Fallback to last part of breadcrumbs with markdown heading
                    last_breadcrumb = chunk.heading_breadcrumbs.split(' > ')[-1]
                    heading = f"## {last_breadcrumb}"
            elif chunk.heading_breadcrumbs:
                last_breadcrumb = chunk.heading_breadcrumbs.split(' > ')[-1]
                heading = f"## {last_breadcrumb}"

            sections.append(SummarySection(
                chunk_id=res.chunk_id,
                heading=heading,
                summary_content=res.summary_content,
                start_line=chunk.start_line,
                end_line=chunk.end_line
            ))

        return WorkSummaryResponse(
            work_id=work_id,
            work_title=work.title,
            sections=sections
        )


@router.get(
    "/works",
    response_model=WorkSummaryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List works with summaries",
    description="Returns a list of all works that have at least one generated summary."
)
async def list_works_with_summaries() -> WorkSummaryListResponse:
    """
    List all works that have generated summaries.
    """
    with get_session() as session:
        # Group summary_results by work_id
        stmt = (
            select(
                Work.id,
                Work.title,
                func.count(SummaryResult.id).label("summary_count"),
                func.max(SummaryResult.updated_at).label("last_updated")
            )
            .join(SummaryResult, Work.id == SummaryResult.work_id)
            .group_by(Work.id, Work.title)
            .order_by(func.max(SummaryResult.updated_at).desc())
        )
        rows = session.execute(stmt).all()

        works = [
            WorkSummaryListItem(
                work_id=row.id,
                title=row.title,
                summary_count=row.summary_count,
                last_updated=row.last_updated
            )
            for row in rows
        ]

        return WorkSummaryListResponse(works=works)


@router.get(
    "/settings",
    response_model=SummarizeSettingsSchema,
    status_code=status.HTTP_200_OK,
    summary="Get summarization settings",
    description="Returns the current global summarization configuration."
)
async def get_summarization_settings() -> SummarizeSettingsSchema:
    """
    Retrieve current summarization settings.
    """
    with get_session() as session:
        settings = session.execute(select(SummarizeSettings)).scalar_one_or_none()
        if not settings:
            # Create default settings if not exists
            settings = SummarizeSettings()
            session.add(settings)
            session.commit()
            session.refresh(settings)

        return SummarizeSettingsSchema(
            min_heading_word_count=settings.min_heading_word_count,
            max_total_heading_words=settings.max_total_heading_words,
            dense_top_k=settings.dense_top_k,
            lexical_top_k=settings.lexical_top_k,
            rrf_k=settings.rrf_k,
            rrf_top_k=settings.rrf_top_k,
            mmr_lambda=settings.mmr_lambda,
            mmr_top_n=settings.mmr_top_n,
            max_llm_calls=settings.max_llm_calls,
            max_tokens_per_call=settings.max_tokens_per_call,
            tokens_per_word=settings.tokens_per_word,
            h1_h2_min_chunks=settings.h1_h2_min_chunks,
            h3_min_chunks=settings.h3_min_chunks
        )


@router.put(
    "/settings",
    response_model=SummarizeSettingsSchema,
    status_code=status.HTTP_200_OK,
    summary="Update summarization settings",
    description="Updates the global summarization configuration."
)
async def update_summarization_settings(
    settings_update: SummarizeSettingsSchema = Body(...)
) -> SummarizeSettingsSchema:
    """
    Update summarization settings.
    """
    with get_session() as session:
        settings = session.execute(select(SummarizeSettings)).scalar_one_or_none()
        if not settings:
            settings = SummarizeSettings()
            session.add(settings)

        # Update fields
        settings.min_heading_word_count = settings_update.min_heading_word_count
        settings.max_total_heading_words = settings_update.max_total_heading_words
        settings.dense_top_k = settings_update.dense_top_k
        settings.lexical_top_k = settings_update.lexical_top_k
        settings.rrf_k = settings_update.rrf_k
        settings.rrf_top_k = settings_update.rrf_top_k
        settings.mmr_lambda = settings_update.mmr_lambda
        settings.mmr_top_n = settings_update.mmr_top_n
        settings.max_llm_calls = settings_update.max_llm_calls
        settings.max_tokens_per_call = settings_update.max_tokens_per_call
        settings.tokens_per_word = settings_update.tokens_per_word
        settings.h1_h2_min_chunks = settings_update.h1_h2_min_chunks
        settings.h3_min_chunks = settings_update.h3_min_chunks

        session.commit()
        session.refresh(settings)

        return SummarizeSettingsSchema(
            min_heading_word_count=settings.min_heading_word_count,
            max_total_heading_words=settings.max_total_heading_words,
            dense_top_k=settings.dense_top_k,
            lexical_top_k=settings.lexical_top_k,
            rrf_k=settings.rrf_k,
            rrf_top_k=settings.rrf_top_k,
            mmr_lambda=settings.mmr_lambda,
            mmr_top_n=settings.mmr_top_n,
            max_llm_calls=settings.max_llm_calls,
            max_tokens_per_call=settings.max_tokens_per_call,
            tokens_per_word=settings.tokens_per_word,
            h1_h2_min_chunks=settings.h1_h2_min_chunks,
            h3_min_chunks=settings.h3_min_chunks
        )
