"""
API endpoints for simple conversion pipeline.

Provides REST API for the streamlined conversion workflow including
both automatic and manual execution modes.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging
from datetime import datetime, UTC

from vulcanlab_api.schemas.simple_conversion import (
    StartConversionRequest,
    StartConversionResponse,
    ConversionStatus,
    ExecuteAutoResponse,
    ManualPromptResponse,
    ManualSubmitRequest,
    ManualSubmitResponse,
    ConversionResults,
    ChunkResult
)
from vulcanlab_api.dependencies import get_db_session
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.parsed_markdown import ParsedMarkdown
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.data.models.chunk import Chunk
from vulcanlab.simple_conversion.parse_classify import parse_and_classify, count_tokens
from vulcanlab.simple_conversion.sanitize_small import (
    sanitize_small_document,
    get_hardcoded_template_small,
    parse_llm_response
)
from vulcanlab.simple_conversion.sanitize_large import (
    sanitize_large_document,
    get_hardcoded_template_large,
    parse_llm_response_large,
    apply_modifications_to_markdown,
    create_heading_modifications_large,
    extract_headings_with_context,
    create_condensed_markdown
)
from vulcanlab.simple_conversion.chunk_simple import (
    create_heading_chunks_simple,
    create_content_chunks_simple,
    create_chunks_from_sanitized  # Keep for backward compatibility
)
from vulcanlab.data.template_loader import load_template

logger = logging.getLogger(__name__)
router = APIRouter()


from pathlib import Path
from vulcanlab.config import load_config

# ... existing imports ...

@router.post("/api/simple-conversion/start", response_model=StartConversionResponse, tags=["Simple Conversion"])
async def start_conversion(
    request: StartConversionRequest,
    session: Session = Depends(get_db_session)
):
    """
    Start simple conversion process.

    Creates a new Work record with provided metadata and initiates
    the PDF/EPUB conversion step.

    Args:
        request: Conversion start parameters
        session: Database session

    Returns:
        Work ID and initial status
    """
    try:
        # Resolve file path
        config = load_config()
        input_dir = Path(config.paths.input_dir)
        full_path = input_dir / request.file_path

        if not full_path.exists():
            # Try as absolute path just in case
            full_path = Path(request.file_path)
            if not full_path.exists():
                raise HTTPException(
                    status_code=400, 
                    detail=f"File not found: {request.file_path}"
                )

        # Create Work record
        work = Work(
            title=request.title,
            authors=request.author,
            year=request.year
        )

        session.add(work)
        session.flush()

        # Initialize processing_status
        work.processing_status = {
            'simple_conversion_step': 'converting',
            'simple_conversion_mode': request.mode,
            'file_path': str(full_path)
        }

        # TODO: Trigger actual PDF/EPUB conversion
        # For MVP, assume conversion happens externally or via existing module

        session.commit()
        session.refresh(work)

        logger.info(f"Started simple conversion for work {work.id} in {request.mode} mode")

        return StartConversionResponse(
            work_id=work.id,
            status='converting',
            mode=request.mode,
            message=f'Conversion started in {request.mode} mode'
        )

    except Exception as e:
        logger.error(f"Failed to start conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/simple-conversion/status/{work_id}", response_model=ConversionStatus, tags=["Simple Conversion"])
async def get_status(
    work_id: int,
    session: Session = Depends(get_db_session)
):
    """
    Get current conversion pipeline status.

    Args:
        work_id: Work ID
        session: Database session

    Returns:
        Current pipeline status including step, classification, counts
    """
    try:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise HTTPException(status_code=404, detail=f"Work {work_id} not found")

        ps = work.processing_status or {}

        return ConversionStatus(
            work_id=work_id,
            step=ps.get('simple_conversion_step', 'unknown'),
            classification=ps.get('simple_conversion_classification'),
            token_count=ps.get('simple_conversion_token_count'),
            chunk_count=ps.get('chunk_count'),
            mode=ps.get('simple_conversion_mode'),
            error_message=ps.get('error_message')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for work {work_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/simple-conversion/execute-auto/{work_id}", response_model=ExecuteAutoResponse, tags=["Simple Conversion"])
async def execute_automatic(
    work_id: int,
    session: Session = Depends(get_db_session)
):
    """
    Execute full automatic pipeline.

    Runs parse → classify → sanitize → chunk steps automatically
    without user intervention.

    Args:
        work_id: Work ID (must have completed conversion)
        session: Database session

    Returns:
        Final status with chunk count
    """
    try:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise HTTPException(status_code=404, detail=f"Work {work_id} not found")

        # Step 1: Parse and classify (if needed)
        parsed = session.query(ParsedMarkdown).filter(
            ParsedMarkdown.work_id == work_id
        ).first()

        if not parsed:
            logger.info(f"Automatic: Parse & classify work {work_id}")
            parsed = parse_and_classify(work_id, session)
        else:
            logger.info(f"Automatic: Using existing ParsedMarkdown for work {work_id}")

        # Step 2: Sanitize (small or large based on classification)
        logger.info(f"Automatic: Sanitize {parsed.classification.value} document")

        if parsed.classification.value == 'small':
            sanitized = sanitize_small_document(work_id, session)
        else:
            sanitized = sanitize_large_document(work_id, session)

        # Step 3a: Create heading chunks
        logger.info(f"Automatic: Create heading chunks for work {work_id}")
        heading_chunks = create_heading_chunks_simple(work_id, session)
        logger.info(f"Created {len(heading_chunks)} heading chunks")

        # Step 3b: Create content chunks
        logger.info(f"Automatic: Create content chunks for work {work_id}")
        content_chunks = create_content_chunks_simple(work_id, session)
        logger.info(f"Created {len(content_chunks)} content chunks")

        chunks = heading_chunks + content_chunks

        # Update final status
        work.processing_status['simple_conversion_step'] = 'complete'
        session.commit()

        logger.info(f"Automatic pipeline complete for work {work_id}: {len(chunks)} total chunks ({len(heading_chunks)} heading, {len(content_chunks)} content)")

        return ExecuteAutoResponse(
            work_id=work_id,
            status='complete',
            chunks_created=len(chunks),
            message=f'Automatic pipeline completed successfully'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Automatic pipeline failed for work {work_id}: {e}")

        # Update error status
        try:
            work = session.query(Work).filter(Work.id == work_id).first()
            if work:
                if not work.processing_status:
                    work.processing_status = {}
                work.processing_status['simple_conversion_step'] = 'error'
                work.processing_status['error_message'] = str(e)
                session.commit()
        except:
            pass

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/simple-conversion/manual-prompt/{work_id}", response_model=ManualPromptResponse, tags=["Simple Conversion"])
async def get_manual_prompt(
    work_id: int,
    session: Session = Depends(get_db_session)
):
    """
    Get prompt text for manual LLM execution.

    Returns the formatted prompt that the user should copy and paste
    into their LLM interface.

    Args:
        work_id: Work ID (must be parsed and classified)
        session: Database session

    Returns:
        Prompt text and instructions
    """
    try:
        # Parse and classify first if not already done
        parsed = session.query(ParsedMarkdown).filter(
            ParsedMarkdown.work_id == work_id
        ).first()

        if not parsed:
            # Need to parse first
            parsed = parse_and_classify(work_id, session)

        classification = parsed.classification.value

        # Load appropriate template
        if classification == 'small':
            template = load_template('simple_sanitize_small', get_hardcoded_template_small)
            prompt = template.format(markdown=parsed.content)
            instructions = (
                "Copy the prompt below and paste it into your LLM interface (ChatGPT, Claude, etc.). "
                "The LLM will return sanitized markdown (NOT JSON). Copy the entire markdown response and paste it in the text area below."
            )
        else:  # large
            # Need to create condensed version
            headings = extract_headings_with_context(parsed.content)
            condensed = create_condensed_markdown(headings)

            template = load_template('simple_sanitize_large', get_hardcoded_template_large)
            prompt = template.format(condensed_document=condensed)
            instructions = (
                "This is a LARGE document, so you're seeing a condensed version with headings and context. "
                "Copy the prompt below and paste it into your LLM interface. "
                "Then copy the JSON response and submit it using the Manual Submit endpoint."
            )

        logger.info(f"Generated manual prompt for work {work_id} ({classification})")

        return ManualPromptResponse(
            work_id=work_id,
            classification=classification,
            prompt=prompt,
            instructions=instructions
        )

    except Exception as e:
        logger.error(f"Failed to generate manual prompt for work {work_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/simple-conversion/manual-submit/{work_id}", response_model=ManualSubmitResponse, tags=["Simple Conversion"])
async def submit_manual_result(
    work_id: int,
    request: ManualSubmitRequest,
    session: Session = Depends(get_db_session)
):
    """
    Submit manual LLM result.

    Processes the LLM response submitted by the user, creates sanitized
    markdown, and proceeds to chunking.

    Args:
        work_id: Work ID
        request: LLM response text
        session: Database session

    Returns:
        Status after processing manual result
    """
    try:
        parsed = session.query(ParsedMarkdown).filter(
            ParsedMarkdown.work_id == work_id
        ).first()

        if not parsed:
            raise HTTPException(
                status_code=400,
                detail="Work must be parsed before submitting manual result"
            )

        classification = parsed.classification.value

        # Process based on classification
        if classification == 'small':
            # Parse LLM response (now returns literal markdown)
            sanitized_content = parse_llm_response(request.llm_response)

            # Count tokens in sanitized content
            token_count = count_tokens(sanitized_content)

            sanitized = SanitizedMarkdown(
                work_id=work_id,
                content=sanitized_content,
                token_count=token_count,
                created_at=datetime.now(UTC)
            )

            session.add(sanitized)
            session.flush()

        else:  # large
            modifications = parse_llm_response_large(request.llm_response)
            sanitized_content = apply_modifications_to_markdown(
                parsed.content,
                modifications
            )

            # Count tokens in sanitized content
            token_count = count_tokens(sanitized_content)

            sanitized = SanitizedMarkdown(
                work_id=work_id,
                content=sanitized_content,
                token_count=token_count,
                created_at=datetime.now(UTC)
            )

            session.add(sanitized)
            session.flush()

            # Extract headings for line numbers
            headings = extract_headings_with_context(parsed.content)

            create_heading_modifications_large(
                modifications,
                work_id,
                headings,
                session
            )

        # Update work status
        work = session.query(Work).filter(Work.id == work_id).first()
        if not work.processing_status:
            work.processing_status = {}
        work.processing_status['simple_conversion_step'] = 'sanitized'

        # Now proceed to chunking
        logger.info(f"Manual result processed, creating chunks for work {work_id}")

        # Step 1: Create heading chunks
        heading_chunks = create_heading_chunks_simple(work_id, session)
        logger.info(f"Created {len(heading_chunks)} heading chunks")

        # Step 2: Create content chunks
        content_chunks = create_content_chunks_simple(work_id, session)
        logger.info(f"Created {len(content_chunks)} content chunks")

        chunks = heading_chunks + content_chunks

        work.processing_status['simple_conversion_step'] = 'complete'
        session.commit()

        logger.info(f"Manual pipeline complete for work {work_id}: {len(chunks)} total chunks ({len(heading_chunks)} heading, {len(content_chunks)} content)")

        return ManualSubmitResponse(
            work_id=work_id,
            status='complete',
            message=f'Manual result processed successfully. Created {len(chunks)} chunks.'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process manual result for work {work_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/simple-conversion/results/{work_id}", response_model=ConversionResults, tags=["Simple Conversion"])
async def get_results(
    work_id: int,
    session: Session = Depends(get_db_session)
):
    """
    Get final conversion results.

    Returns work metadata and all created chunks.

    Args:
        work_id: Work ID
        session: Database session

    Returns:
        Complete conversion results with chunks
    """
    try:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise HTTPException(status_code=404, detail=f"Work {work_id} not found")

        parsed = session.query(ParsedMarkdown).filter(
            ParsedMarkdown.work_id == work_id
        ).first()

        if not parsed:
            raise HTTPException(
                status_code=400,
                detail="Work has not been processed yet"
            )

        chunks = session.query(Chunk).filter(Chunk.work_id == work_id).all()

        chunk_results = [
            ChunkResult(
                id=chunk.id,
                heading_level=chunk.level,  # "H1", "H2", etc.
                heading_text=chunk.heading_breadcrumbs or "",  # Use breadcrumbs as heading text
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                content_preview=chunk.content[:200] + '...' if len(chunk.content) > 200 else chunk.content
            )
            for chunk in chunks
        ]

        return ConversionResults(
            work_id=work_id,
            title=work.title,
            author=work.authors,
            classification=parsed.classification.value,
            token_count=parsed.token_count,
            chunk_count=len(chunks),
            chunks=chunk_results
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results for work {work_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
