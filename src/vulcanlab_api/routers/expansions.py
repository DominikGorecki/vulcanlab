"""
Expansion Router - Answer expansion CRUD and operation endpoints.

Endpoints for expansion management:
    POST /                                    - Create expansion from result_id
    GET  /                                    - List all expansions with status summary
    GET  /{expansion_id}                      - Get expansion detail with sections
    POST /{expansion_id}/breakdown            - Run initial breakdown
    POST /{expansion_id}/sections/{id}/expand - Run RAG pipeline for section
    POST /{expansion_id}/sections/{id}/generate - Run LLM generation for section
    POST /{expansion_id}/sections/{id}/manual - Save manual response for section
    POST /{expansion_id}/combine              - Combine sections into final report
    POST /{expansion_id}/run                  - Run automatic mode end-to-end
"""

import asyncio
import logging
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import joinedload

from vulcanlab.data.database import get_session
from vulcanlab.data.models import Result
from vulcanlab.data.models.expansion import (
    AnswerExpansion,
    ExpansionSection,
    ExpansionMode,
    ExpansionStatus,
    SectionStatus,
)
from vulcanlab.expansion import (
    expand_section,
    generate_section,
    save_manual_response,
    combine_sections,
)
from vulcanlab.expansion.breakdown import (
    generate_breakdown_prompt,
    parse_breakdown_response,
    BreakdownResponseSchema,
    estimate_answer_tokens,
    validate_answer_length,
)
from vulcanlab.ai.config import ModelTier
from vulcanlab.ai.llm_factory import create_langchain_chat

from vulcanlab_api.schemas.expansions import (
    CreateExpansionRequest,
    CreateExpansionResponse,
    ManualResponseRequest,
    ManualBreakdownRequest,
    ExpansionListItem,
    ExpansionListResponse,
    ExpansionDetailResponse,
    SectionSummary,
    SectionDetailResponse,
    BreakdownResponse,
    BreakdownPromptResponse,
    SectionOperationResponse,
    CombineResponse,
    RunAutomaticResponse,
    ResultExpansionResponse,
)


logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


def _section_to_summary(section: ExpansionSection) -> SectionSummary:
    """Convert an ExpansionSection to a SectionSummary."""
    return SectionSummary(
        id=section.id,
        order=section.order,
        heading=section.heading,
        summary=section.summary,
        status=section.status.value,
        error_message=section.error_message
    )


def _section_to_detail(section: ExpansionSection) -> SectionDetailResponse:
    """Convert an ExpansionSection to a SectionDetailResponse."""
    return SectionDetailResponse(
        id=section.id,
        expansion_id=section.expansion_id,
        order=section.order,
        heading=section.heading,
        summary=section.summary,
        expansion_prompt=section.expansion_prompt,
        expanded_queries=section.expanded_queries,
        hyde_answer=section.hyde_answer,
        intent=section.intent,
        entities=section.entities,
        clean_retrieval_context=section.clean_retrieval_context,
        augmented_prompt=section.augmented_prompt,
        response_text=section.response_text,
        status=section.status.value,
        error_message=section.error_message,
        created_at=section.created_at,
        updated_at=section.updated_at
    )


def _expansion_to_list_item(
    expansion: AnswerExpansion,
    sections: list[ExpansionSection]
) -> ExpansionListItem:
    """Convert an AnswerExpansion to an ExpansionListItem."""
    completed_count = sum(1 for s in sections if s.status == SectionStatus.COMPLETED)
    failed_count = sum(1 for s in sections if s.status == SectionStatus.FAILED)

    return ExpansionListItem(
        id=expansion.id,
        result_id=expansion.result_id,
        query_id=expansion.query_id,
        original_query=expansion.query.original_query if expansion.query else None,
        mode=expansion.mode.value,
        status=expansion.status.value,
        section_count=len(sections),
        completed_count=completed_count,
        failed_count=failed_count,
        created_at=expansion.created_at
    )


def _expansion_to_detail(
    expansion: AnswerExpansion,
    sections: list[ExpansionSection]
) -> ExpansionDetailResponse:
    """Convert an AnswerExpansion to an ExpansionDetailResponse."""
    return ExpansionDetailResponse(
        id=expansion.id,
        result_id=expansion.result_id,
        query_id=expansion.query_id,
        original_query=expansion.query.original_query if expansion.query else None,
        mode=expansion.mode.value,
        status=expansion.status.value,
        combined_report=expansion.combined_report,
        expansion_metadata=expansion.expansion_metadata,
        sections=[_section_to_summary(s) for s in sections],
        created_at=expansion.created_at,
        updated_at=expansion.updated_at
    )


# =============================================================================
# CRUD Endpoints
# =============================================================================


@router.post(
    "/",
    response_model=CreateExpansionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create expansion",
    description="Create a new expansion from a result ID. One expansion per result.",
)
async def create_expansion(request: CreateExpansionRequest) -> CreateExpansionResponse:
    """Create a new expansion from a result."""
    with get_session() as session:
        # Verify result exists
        result = session.query(Result).filter(Result.id == request.result_id).first()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Result with ID {request.result_id} not found"
            )

        # Check if expansion already exists for this result
        existing = session.query(AnswerExpansion).filter(
            AnswerExpansion.result_id == request.result_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Expansion already exists for result {request.result_id} (expansion_id={existing.id})"
            )

        # Convert mode string to enum
        mode = ExpansionMode.AUTOMATIC if request.mode == "automatic" else ExpansionMode.MANUAL

        # Create expansion record
        expansion = AnswerExpansion(
            result_id=request.result_id,
            query_id=result.query_id,
            mode=mode,
            status=ExpansionStatus.CREATED
        )
        session.add(expansion)
        session.commit()

        logger.info(f"Created expansion {expansion.id} for result {request.result_id}")

        return CreateExpansionResponse(
            expansion_id=expansion.id,
            status=expansion.status.value,
            message="Expansion created successfully"
        )


@router.get(
    "/",
    response_model=ExpansionListResponse,
    summary="List expansions",
    description="List all expansions with status summary and section counts.",
)
async def list_expansions(
    offset: int = 0,
    limit: int = 50
) -> ExpansionListResponse:
    """List all expansions with pagination."""
    with get_session() as session:
        # Get total count
        total = session.query(AnswerExpansion).count()

        # Get expansions with pagination
        expansions = session.query(AnswerExpansion)\
            .options(joinedload(AnswerExpansion.query))\
            .order_by(AnswerExpansion.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()

        items = []
        for expansion in expansions:
            sections = session.query(ExpansionSection)\
                .filter(ExpansionSection.expansion_id == expansion.id)\
                .all()
            items.append(_expansion_to_list_item(expansion, sections))

        return ExpansionListResponse(
            expansions=items,
            total=total
        )


@router.get(
    "/{expansion_id}",
    response_model=ExpansionDetailResponse,
    summary="Get expansion detail",
    description="Get full detail of an expansion including all sections.",
)
async def get_expansion(expansion_id: int) -> ExpansionDetailResponse:
    """Get detailed expansion information."""
    with get_session() as session:
        expansion = session.query(AnswerExpansion)\
            .options(joinedload(AnswerExpansion.query))\
            .filter(
                AnswerExpansion.id == expansion_id
            ).first()

        if not expansion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expansion with ID {expansion_id} not found"
            )

        sections = session.query(ExpansionSection)\
            .filter(ExpansionSection.expansion_id == expansion_id)\
            .order_by(ExpansionSection.order)\
            .all()

        return _expansion_to_detail(expansion, sections)


@router.get(
    "/{expansion_id}/sections/{section_id}",
    response_model=SectionDetailResponse,
    summary="Get section detail",
    description="Get full detail of a section including RAG data.",
)
async def get_section(expansion_id: int, section_id: int) -> SectionDetailResponse:
    """Get detailed section information."""
    with get_session() as session:
        section = session.query(ExpansionSection).filter(
            ExpansionSection.id == section_id,
            ExpansionSection.expansion_id == expansion_id
        ).first()

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section with ID {section_id} not found in expansion {expansion_id}"
            )

        return _section_to_detail(section)


# =============================================================================
# Operation Endpoints
# =============================================================================


@router.get(
    "/{expansion_id}/breakdown/prompt",
    response_model=BreakdownPromptResponse,
    summary="Get breakdown prompt",
    description="Get the breakdown prompt for manual mode (no LLM call).",
)
async def get_breakdown_prompt(expansion_id: int) -> BreakdownPromptResponse:
    """Get the breakdown prompt without executing LLM.

    Used in manual mode to allow users to copy the prompt to an external LLM.
    """
    with get_session() as session:
        # Get expansion
        expansion = session.query(AnswerExpansion).filter(
            AnswerExpansion.id == expansion_id
        ).first()

        if not expansion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expansion with ID {expansion_id} not found"
            )

        # Get result to access answer text
        result = session.query(Result).filter(Result.id == expansion.result_id).first()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Result with ID {expansion.result_id} not found"
            )

        # Generate breakdown prompt (no LLM call)
        answer_text = result.response_text
        prompt = generate_breakdown_prompt(answer_text, session)
        token_estimate = estimate_answer_tokens(answer_text)

        return BreakdownPromptResponse(
            expansion_id=expansion_id,
            prompt=prompt,
            answer_token_estimate=token_estimate
        )


@router.post(
    "/{expansion_id}/breakdown/manual",
    response_model=BreakdownResponse,
    summary="Save manual breakdown",
    description="Save a manual breakdown result (parsed from user-pasted JSON).",
)
async def save_manual_breakdown(
    expansion_id: int,
    request: ManualBreakdownRequest,
    overwrite: bool = False
) -> BreakdownResponse:
    """Save a manual breakdown from user-pasted JSON.

    Used in manual mode where user copies prompt to external LLM and pastes back result.
    """
    with get_session() as session:
        # Get expansion
        expansion = session.query(AnswerExpansion).filter(
            AnswerExpansion.id == expansion_id
        ).first()

        if not expansion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expansion with ID {expansion_id} not found"
            )

        # Check if breakdown already done
        existing_sections = session.query(ExpansionSection).filter(
            ExpansionSection.expansion_id == expansion_id
        ).count()

        if existing_sections > 0:
            if not overwrite:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Breakdown already completed for expansion {expansion_id} ({existing_sections} sections exist). Use overwrite=True to re-run."
                )

            # Delete existing sections
            session.query(ExpansionSection).filter(
                ExpansionSection.expansion_id == expansion_id
            ).delete()
            session.commit()
            logger.info(f"Deleted {existing_sections} existing sections for expansion {expansion_id}")

        # Get result for token estimate
        result = session.query(Result).filter(Result.id == expansion.result_id).first()
        answer_text = result.response_text if result else ""

        try:
            # Parse the user-provided JSON
            sections_data = parse_breakdown_response(request.breakdown_json)

            logger.info(f"Manual breakdown parsed {len(sections_data)} sections for expansion {expansion_id}")

            # Create section records
            for section_data in sections_data:
                section = ExpansionSection(
                    expansion_id=expansion.id,
                    order=section_data.order,
                    heading=section_data.heading,
                    summary=section_data.summary,
                    expansion_prompt=section_data.expansion_prompt,
                    status=SectionStatus.PENDING
                )
                session.add(section)

            # Update expansion metadata and status
            expansion.expansion_metadata = {
                "source_token_estimate": estimate_answer_tokens(answer_text),
                "section_count": len(sections_data),
                "breakdown_mode": "manual"
            }
            expansion.status = ExpansionStatus.BREAKDOWN_COMPLETE
            session.commit()

            # Get created sections
            sections = session.query(ExpansionSection).filter(
                ExpansionSection.expansion_id == expansion_id
            ).order_by(ExpansionSection.order).all()

            logger.info(
                f"Manual breakdown complete for expansion {expansion_id}: "
                f"{len(sections)} sections created"
            )

            return BreakdownResponse(
                expansion_id=expansion_id,
                status=expansion.status.value,
                section_count=len(sections),
                sections=[_section_to_summary(s) for s in sections],
                message=f"Manual breakdown complete, {len(sections)} sections created"
            )

        except ValueError as e:
            logger.error(f"Manual breakdown parsing failed for expansion {expansion_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse breakdown JSON: {str(e)}"
            )


@router.post(
    "/{expansion_id}/breakdown",
    response_model=BreakdownResponse,
    summary="Run breakdown",
    description="Run initial breakdown to split answer into sections.",
)
async def run_breakdown(expansion_id: int, overwrite: bool = False) -> BreakdownResponse:
    """Run breakdown to create sections from the answer.

    This endpoint uses the lower-level breakdown functions to create sections
    for an existing expansion record, rather than creating a new expansion.
    """
    with get_session() as session:
        # Get expansion
        expansion = session.query(AnswerExpansion).filter(
            AnswerExpansion.id == expansion_id
        ).first()

        if not expansion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expansion with ID {expansion_id} not found"
            )

        # Check if breakdown already done
        existing_sections = session.query(ExpansionSection).filter(
            ExpansionSection.expansion_id == expansion_id
        ).count()

        if existing_sections > 0:
            if not overwrite:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Breakdown already completed for expansion {expansion_id} ({existing_sections} sections exist). Use overwrite=True to re-run."
                )
            
            # Delete existing sections
            session.query(ExpansionSection).filter(
                ExpansionSection.expansion_id == expansion_id
            ).delete()
            session.commit()
            logger.info(f"Deleted {existing_sections} existing sections for expansion {expansion_id} to re-run breakdown")

        # Get result to access answer text
        result = session.query(Result).filter(Result.id == expansion.result_id).first()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Result with ID {expansion.result_id} not found"
            )

        # Update status to indicate breakdown is in progress
        expansion.status = ExpansionStatus.BREAKDOWN_PENDING
        session.commit()

        try:
            # Validate answer length
            answer_text = result.response_text
            validate_answer_length(answer_text)

            logger.info(
                f"Starting breakdown for expansion {expansion_id} "
                f"(~{estimate_answer_tokens(answer_text):,} tokens)"
            )

            # Generate breakdown prompt
            prompt = generate_breakdown_prompt(answer_text, session)

            # Create LLM client
            langchain_stack = create_langchain_chat(tier=ModelTier.FULL)
            llm_client = langchain_stack.chat

            # Call LLM with structured output
            try:
                structured_client = llm_client.with_structured_output(BreakdownResponseSchema)
                response = structured_client.invoke(prompt)
            except AttributeError:
                logger.warning("Structured output not supported, using raw invocation")
                response = llm_client.invoke(prompt)

            # Parse response
            sections_data = parse_breakdown_response(response)

            logger.info(f"LLM returned {len(sections_data)} sections for expansion {expansion_id}")

            # Create section records
            for section_data in sections_data:
                section = ExpansionSection(
                    expansion_id=expansion.id,
                    order=section_data.order,
                    heading=section_data.heading,
                    summary=section_data.summary,
                    expansion_prompt=section_data.expansion_prompt,
                    status=SectionStatus.PENDING
                )
                session.add(section)

            # Update expansion metadata and status
            expansion.expansion_metadata = {
                "source_token_estimate": estimate_answer_tokens(answer_text),
                "section_count": len(sections_data)
            }
            expansion.status = ExpansionStatus.BREAKDOWN_COMPLETE
            session.commit()

            # Get created sections
            sections = session.query(ExpansionSection).filter(
                ExpansionSection.expansion_id == expansion_id
            ).order_by(ExpansionSection.order).all()

            logger.info(
                f"Breakdown complete for expansion {expansion_id}: "
                f"{len(sections)} sections created"
            )

            return BreakdownResponse(
                expansion_id=expansion_id,
                status=expansion.status.value,
                section_count=len(sections),
                sections=[_section_to_summary(s) for s in sections],
                message=f"Breakdown complete, {len(sections)} sections created"
            )

        except ValueError as e:
            logger.error(f"Breakdown failed for expansion {expansion_id}: {e}")
            expansion.status = ExpansionStatus.FAILED
            expansion.expansion_metadata = {"error": str(e)}
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Breakdown failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Breakdown failed for expansion {expansion_id}: {e}")
            expansion.status = ExpansionStatus.FAILED
            expansion.expansion_metadata = {"error": str(e)}
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Breakdown failed: {str(e)}"
            )


@router.get(
    "/{expansion_id}/sections/{section_id}/expand/prompt",
    response_model=dict,
    summary="Get query expansion prompt",
    description="Get the query expansion prompt for manual mode (no LLM call).",
)
async def get_section_expand_prompt(
    expansion_id: int,
    section_id: int
) -> dict:
    """Get the query expansion prompt without executing LLM.

    Used in manual mode to allow users to copy the prompt to an external LLM.
    """
    with get_session() as session:
        # Verify section exists and belongs to expansion
        section = session.query(ExpansionSection).filter(
            ExpansionSection.id == section_id,
            ExpansionSection.expansion_id == expansion_id
        ).first()

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section with ID {section_id} not found in expansion {expansion_id}"
            )

        # Generate query expansion prompt (no LLM call)
        from vulcanlab.retrieval.query_expansion import generate_expansion_prompt

        prompt = generate_expansion_prompt(section.expansion_prompt, n=3)

        return {
            "expansion_id": expansion_id,
            "section_id": section_id,
            "prompt": prompt,
            "expansion_prompt": section.expansion_prompt
        }


@router.post(
    "/{expansion_id}/sections/{section_id}/expand/manual",
    response_model=SectionOperationResponse,
    summary="Save manual query expansion",
    description="Save a manual query expansion result (parsed from user-pasted JSON).",
)
async def save_manual_expand(
    expansion_id: int,
    section_id: int,
    request: dict
) -> SectionOperationResponse:
    """Save a manual query expansion from user-pasted JSON.

    Used in manual mode where user copies prompt to external LLM and pastes back result.
    After saving, automatically runs embeddings and retrieval.
    """
    with get_session() as session:
        # Verify section exists and belongs to expansion
        section = session.query(ExpansionSection).filter(
            ExpansionSection.id == section_id,
            ExpansionSection.expansion_id == expansion_id
        ).first()

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section with ID {section_id} not found in expansion {expansion_id}"
            )

        # Update expansion status if needed
        expansion = session.query(AnswerExpansion).filter(
            AnswerExpansion.id == expansion_id
        ).first()

        if expansion.status == ExpansionStatus.BREAKDOWN_COMPLETE:
            expansion.status = ExpansionStatus.SECTIONS_IN_PROGRESS
            session.commit()

        try:
            # Parse the user-provided expansion JSON
            from vulcanlab.retrieval.query_expansion import parse_expansion_response

            expansion_json = request.get("expansion_json", "")
            parsed = parse_expansion_response(expansion_json)

            logger.info(f"Manual query expansion parsed for section {section_id}")

            # Update section status
            section.status = SectionStatus.EXPANDING
            session.commit()

            # Store expansion results
            section.expanded_queries = {"queries": parsed.expanded_queries}
            section.hyde_answer = parsed.hyde_answer
            section.intent = parsed.intent
            section.entities = {"entities": parsed.entities}

            # Generate embeddings automatically (this is OK per spec)
            from vulcanlab.expansion.section_processing import (
                _generate_embeddings_for_section,
                _retrieve_for_section,
                _consolidate_section_context
            )

            embeddings_data = _generate_embeddings_for_section(
                section.expansion_prompt,
                parsed.expanded_queries,
                parsed.hyde_answer
            )

            # Retrieve chunks
            retrieved_context = _retrieve_for_section(
                session,
                embeddings_data["embedding_original"],
                embeddings_data.get("embeddings_mqe"),
                embeddings_data.get("embedding_hyde"),
                parsed.entities,
                parsed.intent,
                section.expansion_prompt,
                parsed.expanded_queries
            )

            # Store retrieved context
            section.retrieved_context = {"chunks": retrieved_context}

            # Consolidate context
            clean_context = _consolidate_section_context(session, retrieved_context)
            section.clean_retrieval_context = {"chunks": clean_context}

            # Update status to ready
            section.status = SectionStatus.READY
            session.commit()

            logger.info(
                f"Manual expansion complete for section {section_id}: "
                f"{len(retrieved_context)} chunks retrieved, "
                f"{len(clean_context)} after consolidation"
            )

            return SectionOperationResponse(
                section_id=section_id,
                expansion_id=expansion_id,
                status=section.status.value,
                message="Manual query expansion saved and RAG pipeline completed"
            )

        except ValueError as e:
            logger.error(f"Manual expansion parsing failed for section {section_id}: {e}")
            section.status = SectionStatus.FAILED
            section.error_message = str(e)
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse expansion JSON: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Manual expansion failed for section {section_id}: {e}")
            section.status = SectionStatus.FAILED
            section.error_message = str(e)
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Manual expansion failed: {str(e)}"
            )


@router.post(
    "/{expansion_id}/sections/{section_id}/expand",
    response_model=SectionOperationResponse,
    summary="Expand section",
    description="Run RAG pipeline (query expansion, retrieval, consolidation) for a section.",
)
async def expand_section_endpoint(
    expansion_id: int,
    section_id: int
) -> SectionOperationResponse:
    """Run RAG expansion pipeline for a section."""
    with get_session() as session:
        # Verify section exists and belongs to expansion
        section = session.query(ExpansionSection).filter(
            ExpansionSection.id == section_id,
            ExpansionSection.expansion_id == expansion_id
        ).first()

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section with ID {section_id} not found in expansion {expansion_id}"
            )

        # Update expansion status if needed
        expansion = session.query(AnswerExpansion).filter(
            AnswerExpansion.id == expansion_id
        ).first()

        if expansion.status == ExpansionStatus.BREAKDOWN_COMPLETE:
            expansion.status = ExpansionStatus.SECTIONS_IN_PROGRESS
            session.commit()

        try:
            # Create LLM client
            langchain_stack = create_langchain_chat(tier=ModelTier.FULL)
            llm_client = langchain_stack.chat

            # Run expansion
            expand_section(section_id, session, llm_client)

            # Refresh to get updated status
            session.refresh(section)

            return SectionOperationResponse(
                section_id=section_id,
                expansion_id=expansion_id,
                status=section.status.value,
                message="Section expanded successfully"
            )

        except Exception as e:
            logger.error(f"Section expansion failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Section expansion failed: {str(e)}"
            )


@router.get(
    "/{expansion_id}/sections/{section_id}/generate/prompt",
    response_model=dict,
    summary="Get augmented prompt",
    description="Get the augmented prompt (with sources) for manual mode (no LLM call).",
)
async def get_section_generate_prompt(
    expansion_id: int,
    section_id: int,
    top_n: int | None = Query(default=None, description="Number of sources to include (defaults to all)")
) -> dict:
    """Get the augmented prompt without executing LLM.

    Used in manual mode to allow users to copy the prompt to an external LLM.
    Requires that expand has already been run (section must be in READY status).
    """
    with get_session() as session:
        # Verify section exists and belongs to expansion
        section = session.query(ExpansionSection).filter(
            ExpansionSection.id == section_id,
            ExpansionSection.expansion_id == expansion_id
        ).first()

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section with ID {section_id} not found in expansion {expansion_id}"
            )

        # Check section status - must be READY
        if section.status != SectionStatus.READY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Section {section_id} is not ready for generation (status: {section.status.value}). "
                       f"Run expand first."
            )

        # Build augmented prompt (no LLM call)
        from vulcanlab.expansion.section_processing import _format_section_context
        from vulcanlab.data.template_loader import get_active_template

        all_chunks = section.clean_retrieval_context.get("chunks", []) if section.clean_retrieval_context else []
        # Apply top_n limit if specified
        clean_context = all_chunks[:top_n] if top_n and top_n < len(all_chunks) else all_chunks
        context_blocks = _format_section_context(clean_context)

        # Extract entities from stored data
        entities_data = section.entities or {}
        entities_list = entities_data.get("entities", [])
        entities_str = ", ".join(str(e) for e in entities_list) if entities_list else "None specified"

        template_content = get_active_template("expansion_section_generation", session)
        augmented_prompt = template_content.format(
            section_heading=section.heading,
            section_summary=section.summary or "",
            intent=section.intent or "GENERAL",
            entities_str=entities_str,
            context_blocks=context_blocks,
            user_question=section.expansion_prompt
        )

        return {
            "expansion_id": expansion_id,
            "section_id": section_id,
            "prompt": augmented_prompt,
            "source_count": len(clean_context),
            "available_source_count": len(all_chunks)
        }


@router.post(
    "/{expansion_id}/sections/{section_id}/generate",
    response_model=SectionOperationResponse,
    summary="Generate section response",
    description="Run LLM generation for a section (requires expand first).",
)
async def generate_section_endpoint(
    expansion_id: int,
    section_id: int
) -> SectionOperationResponse:
    """Run LLM generation for a section."""
    with get_session() as session:
        # Verify section exists and belongs to expansion
        section = session.query(ExpansionSection).filter(
            ExpansionSection.id == section_id,
            ExpansionSection.expansion_id == expansion_id
        ).first()

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section with ID {section_id} not found in expansion {expansion_id}"
            )

        # Check section status - must be READY or FAILED (for retry)
        if section.status not in [SectionStatus.READY, SectionStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Section {section_id} is not ready for generation (status: {section.status.value}). "
                       f"Run expand first or wait for current operation to complete."
            )

        try:
            # Create LLM client
            langchain_stack = create_langchain_chat(tier=ModelTier.FULL)
            llm_client = langchain_stack.chat

            # Run generation
            generate_section(section_id, session, llm_client)

            # Refresh to get updated status
            session.refresh(section)

            return SectionOperationResponse(
                section_id=section_id,
                expansion_id=expansion_id,
                status=section.status.value,
                message="Section generated successfully"
            )

        except Exception as e:
            logger.error(f"Section generation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Section generation failed: {str(e)}"
            )


@router.post(
    "/{expansion_id}/sections/{section_id}/manual",
    response_model=SectionOperationResponse,
    summary="Save manual response",
    description="Save a user-provided manual response for a section.",
)
async def save_manual_response_endpoint(
    expansion_id: int,
    section_id: int,
    request: ManualResponseRequest
) -> SectionOperationResponse:
    """Save a manual response for a section."""
    with get_session() as session:
        # Verify section exists and belongs to expansion
        section = session.query(ExpansionSection).filter(
            ExpansionSection.id == section_id,
            ExpansionSection.expansion_id == expansion_id
        ).first()

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section with ID {section_id} not found in expansion {expansion_id}"
            )

        try:
            # Save manual response
            save_manual_response(section_id, request.response_text, session)

            # Refresh to get updated status
            session.refresh(section)

            return SectionOperationResponse(
                section_id=section_id,
                expansion_id=expansion_id,
                status=section.status.value,
                message="Manual response saved successfully"
            )

        except Exception as e:
            logger.error(f"Saving manual response failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save manual response: {str(e)}"
            )


@router.post(
    "/{expansion_id}/combine",
    response_model=CombineResponse,
    summary="Combine sections",
    description="Combine all completed sections into a final report.",
)
async def combine_sections_endpoint(expansion_id: int) -> CombineResponse:
    """Combine all sections into a final report."""
    with get_session() as session:
        # Verify expansion exists
        expansion = session.query(AnswerExpansion).filter(
            AnswerExpansion.id == expansion_id
        ).first()

        if not expansion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expansion with ID {expansion_id} not found"
            )

        # Get all sections
        sections = session.query(ExpansionSection).filter(
            ExpansionSection.expansion_id == expansion_id
        ).all()

        if not sections:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Expansion {expansion_id} has no sections. Run breakdown first."
            )

        # Check if all sections are completed
        incomplete = [s for s in sections if s.status != SectionStatus.COMPLETED]
        if incomplete:
            incomplete_info = ", ".join(
                f"#{s.order} ({s.status.value})" for s in incomplete
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot combine: {len(incomplete)} sections not completed: {incomplete_info}"
            )

        try:
            # Run combine
            combined_report = combine_sections(expansion_id, session)

            return CombineResponse(
                expansion_id=expansion_id,
                status=ExpansionStatus.COMPLETED.value,
                report_length=len(combined_report),
                message="Sections combined successfully"
            )

        except Exception as e:
            logger.error(f"Combining sections failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to combine sections: {str(e)}"
            )


@router.post(
    "/{expansion_id}/run",
    response_model=RunAutomaticResponse,
    summary="Run automatic mode",
    description="Run full automatic pipeline: breakdown -> expand all sections -> generate all -> combine.",
)
async def run_automatic(expansion_id: int) -> RunAutomaticResponse:
    """Run full automatic expansion pipeline with 2-concurrent parallelism."""
    with get_session() as session:
        # Verify expansion exists
        expansion = session.query(AnswerExpansion).filter(
            AnswerExpansion.id == expansion_id
        ).first()

        if not expansion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expansion with ID {expansion_id} not found"
            )

        # Check if already completed
        if expansion.status == ExpansionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Expansion {expansion_id} is already completed"
            )

    # Run breakdown if not done
    sections = None
    with get_session() as session:
        sections = session.query(ExpansionSection).filter(
            ExpansionSection.expansion_id == expansion_id
        ).all()

    if not sections:
        # Run breakdown first
        try:
            breakdown_response = await run_breakdown(expansion_id)
            sections_count = breakdown_response.section_count
        except HTTPException:
            # Breakdown might have already been done, check again
            with get_session() as session:
                sections = session.query(ExpansionSection).filter(
                    ExpansionSection.expansion_id == expansion_id
                ).all()
                if not sections:
                    raise
                sections_count = len(sections)
    else:
        sections_count = len(sections)

    # Process sections with 2-concurrent limit
    semaphore = asyncio.Semaphore(2)
    completed_count = 0
    failed_count = 0

    async def process_section(section_id: int):
        nonlocal completed_count, failed_count

        async with semaphore:
            try:
                # Expand
                await expand_section_endpoint(expansion_id, section_id)

                # Generate
                await generate_section_endpoint(expansion_id, section_id)

                completed_count += 1
            except HTTPException as e:
                logger.error(f"Section {section_id} failed: {e.detail}")
                failed_count += 1
            except Exception as e:
                logger.error(f"Section {section_id} failed: {e}")
                failed_count += 1

    # Get section IDs
    with get_session() as session:
        section_ids = [s.id for s in session.query(ExpansionSection).filter(
            ExpansionSection.expansion_id == expansion_id,
            ExpansionSection.status.in_([SectionStatus.PENDING, SectionStatus.FAILED])
        ).all()]

    # Process sections in parallel (with 2-concurrent limit)
    if section_ids:
        await asyncio.gather(*[process_section(sid) for sid in section_ids])

    # Combine if all sections completed
    final_status = ExpansionStatus.SECTIONS_IN_PROGRESS.value
    if completed_count == sections_count and failed_count == 0:
        try:
            await combine_sections_endpoint(expansion_id)
            final_status = ExpansionStatus.COMPLETED.value
        except HTTPException as e:
            logger.error(f"Combine failed: {e.detail}")
            final_status = ExpansionStatus.FAILED.value
    elif failed_count > 0:
        final_status = ExpansionStatus.FAILED.value

    return RunAutomaticResponse(
        expansion_id=expansion_id,
        status=final_status,
        sections_processed=sections_count,
        sections_completed=completed_count,
        sections_failed=failed_count,
        message=f"Automatic expansion {'completed' if final_status == ExpansionStatus.COMPLETED.value else 'finished with failures'}"
    )


# =============================================================================
# Result-Expansion Link Endpoint
# =============================================================================


@router.get(
    "/by-result/{result_id}",
    response_model=ResultExpansionResponse,
    summary="Get expansion for result",
    description="Check if a result has an expansion and get its details.",
)
async def get_expansion_for_result(result_id: int) -> ResultExpansionResponse:
    """Get expansion for a result if it exists."""
    with get_session() as session:
        # Verify result exists
        result = session.query(Result).filter(Result.id == result_id).first()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Result with ID {result_id} not found"
            )

        # Check for expansion
        expansion = session.query(AnswerExpansion).filter(
            AnswerExpansion.result_id == result_id
        ).first()

        if expansion:
            return ResultExpansionResponse(
                result_id=result_id,
                has_expansion=True,
                expansion_id=expansion.id,
                expansion_status=expansion.status.value
            )
        else:
            return ResultExpansionResponse(
                result_id=result_id,
                has_expansion=False,
                expansion_id=None,
                expansion_status=None
            )
