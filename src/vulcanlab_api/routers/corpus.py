"""
Corpus Router - Read-only access to works ready for vectorization.

The corpus represents works that have completed both content and heading chunking
(processing_status has both content_chunks="completed" AND heading_chunks="completed")
and have a sanitized file. These works are ready for vectorization and RAG operations.

Endpoints:
    GET  /corpus/stats                      - Get corpus statistics
    GET  /corpus/works                      - List all corpus works
    GET  /corpus/work/{work_id}             - Get specific work details
    GET  /corpus/work/{work_id}/content     - Get sanitized markdown content
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func

from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.chunk import Chunk
from vulcanlab.utils.file_utils import get_path_resolver


# Initialize path resolver
resolver = get_path_resolver()
from vulcanlab_api.schemas.corpus import (
    ChunkVectorStats,
    CorpusStatsResponse,
    CorpusWorkListItem,
    CorpusWorksResponse,
    CorpusWorkDetailResponse,
    SanitizedContentResponse,
)

router = APIRouter()


def _is_corpus_work(work: Work) -> bool:
    """
    Check if a work is part of the corpus.

    A work is in the corpus if it meets ONE of these criteria:

    Regular conversion:
    1. It has processing_status
    2. processing_status["content_chunks"] == "completed"
    3. processing_status["heading_chunks"] == "completed"
    4. It has a sanitized file in work.files

    Simple conversion:
    1. It has processing_status
    2. processing_status["simple_conversion_step"] == "complete"

    Args:
        work: Work object to check

    Returns:
        True if work is in corpus, False otherwise
    """
    if not work.processing_status:
        return False

    # Check for simple conversion completion
    simple_conversion_step = work.processing_status.get("simple_conversion_step")
    if simple_conversion_step == "complete":
        return True

    # Check for regular conversion completion
    content_status = work.processing_status.get("content_chunks")
    heading_status = work.processing_status.get("heading_chunks")

    if content_status != "completed" or heading_status != "completed":
        return False

    if not work.files or "sanitized" not in work.files:
        return False

    return True


def _get_corpus_works(session) -> list[Work]:
    """
    Get all works in the corpus.

    Filters works to only include those with completed chunking and sanitized files.

    Args:
        session: Database session

    Returns:
        List of Work objects that are in the corpus
    """
    # Get all works (we need to filter in Python due to JSON field complexity)
    all_works = session.query(Work).all()

    # Filter to corpus works
    corpus_works = [work for work in all_works if _is_corpus_work(work)]

    return corpus_works


def _get_chunk_vector_stats(session, corpus_work_ids: list[int]) -> dict[str, int]:
    """
    Get chunk statistics by vector_status for corpus works.

    Args:
        session: Database session
        corpus_work_ids: List of work IDs to include in statistics

    Returns:
        Dict with counts for each vector_status: {no_vec, to_vec, vec, vec_err}
    """
    if not corpus_work_ids:
        return {"no_vec": 0, "to_vec": 0, "vec": 0, "vec_err": 0}

    # Query chunks grouped by vector_status
    stats_query = (
        session.query(
            Chunk.vector_status,
            func.count(Chunk.id)
        )
        .filter(Chunk.work_id.in_(corpus_work_ids))
        .group_by(Chunk.vector_status)
        .all()
    )

    # Initialize all statuses to 0
    result = {"no_vec": 0, "to_vec": 0, "vec": 0, "vec_err": 0}

    # Populate with actual counts
    for vector_status, count in stats_query:
        if vector_status in result:
            result[vector_status] = count

    return result


@router.get(
    "/stats",
    response_model=CorpusStatsResponse,
    summary="Get corpus statistics",
    description="Get count of corpus works and chunk vectorization statistics. "
                "Corpus works are those with completed chunking (both content and heading).",
)
async def get_corpus_stats() -> CorpusStatsResponse:
    """
    Get corpus statistics.

    Returns:
        - Total number of works in corpus
        - Chunk counts broken down by vector_status (no_vec, to_vec, vec, vec_err)

    Only includes works where both content_chunks and heading_chunks are "completed"
    and that have a sanitized file.
    """
    with get_session() as session:
        # Get corpus works
        corpus_works = _get_corpus_works(session)
        corpus_work_ids = [work.id for work in corpus_works]

        # Get chunk statistics
        chunk_stats = _get_chunk_vector_stats(session, corpus_work_ids)

        return CorpusStatsResponse(
            total_works=len(corpus_works),
            chunk_stats=ChunkVectorStats(**chunk_stats)
        )


@router.get(
    "/works",
    response_model=CorpusWorksResponse,
    summary="List corpus works",
    description="Get all works that have completed chunking (both content and heading) "
                "and are ready for vectorization. Returns works sorted by ID descending.",
)
async def list_corpus_works() -> CorpusWorksResponse:
    """
    List all corpus works.

    Returns works where:
    - Regular conversion: processing_status["content_chunks"] == "completed" AND
      processing_status["heading_chunks"] == "completed" AND work.files["sanitized"] exists
    - Simple conversion: processing_status["simple_conversion_step"] == "complete"

    Works are sorted by ID descending (newest first).
    """
    with get_session() as session:
        corpus_works = _get_corpus_works(session)

        # Build work list items
        work_items = []
        for work in corpus_works:
            work_items.append(
                CorpusWorkListItem(
                    id=work.id,
                    title=work.title,
                    authors=work.authors
                )
            )

        # Sort by ID descending (newest first)
        work_items.sort(key=lambda x: x.id, reverse=True)

        return CorpusWorksResponse(
            works=work_items,
            total=len(work_items)
        )


@router.get(
    "/work/{work_id}",
    response_model=CorpusWorkDetailResponse,
    summary="Get corpus work details",
    description="Get detailed information about a specific corpus work. "
                "Returns 404 if work doesn't exist or isn't in the corpus.",
)
async def get_corpus_work_detail(work_id: int) -> CorpusWorkDetailResponse:
    """
    Get detailed information about a corpus work.

    Args:
        work_id: ID of the work

    Returns:
        Detailed work information including sanitized file info

    Raises:
        404: Work not found or not in corpus
        400: Work doesn't have completed chunking
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )

        # Verify work is in corpus
        if not _is_corpus_work(work):
            # Provide specific error message about what's missing
            if not work.processing_status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Work {work_id} has no processing status"
                )

            content_status = work.processing_status.get("content_chunks")
            heading_status = work.processing_status.get("heading_chunks")

            if content_status != "completed" or heading_status != "completed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Work {work_id} has not completed chunking "
                           f"(content_chunks: {content_status}, heading_chunks: {heading_status})"
                )

            if not work.files or "sanitized" not in work.files:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Work {work_id} does not have a sanitized file"
                )

        sanitized_info = work.files["sanitized"]

        return CorpusWorkDetailResponse(
            id=work.id,
            title=work.title,
            authors=work.authors,
            year=work.year,
            publisher=work.publisher,
            sanitized_path=sanitized_info["path"],
            sanitized_hash=sanitized_info["hash"]
        )


@router.get(
    "/work/{work_id}/content",
    response_model=SanitizedContentResponse,
    summary="Get sanitized markdown content",
    description="Retrieve the sanitized markdown file content for a corpus work.",
)
async def get_sanitized_content(work_id: int) -> SanitizedContentResponse:
    """
    Get the sanitized markdown content for a work.

    Args:
        work_id: ID of the work

    Returns:
        Sanitized markdown content and metadata

    Raises:
        404: Work not found or sanitized file missing
        500: Error reading file from disk
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )

        if not work.files or "sanitized" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have a sanitized file"
            )

        sanitized_path = resolver.resolve_work_path(work, "sanitized")

        if not sanitized_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sanitized file not found on disk: {sanitized_path.name}"
            )

        # Read file content
        try:
            content = sanitized_path.read_text(encoding="utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read sanitized file: {str(e)}"
            )

        return SanitizedContentResponse(
            content=content,
            filename=sanitized_path.name,
            work_id=work.id,
            work_title=work.title
        )
