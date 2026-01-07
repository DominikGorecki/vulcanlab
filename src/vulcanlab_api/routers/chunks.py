"""
Chunks Router - API endpoints for chunk search and deletion.

This router provides endpoints for:
- Lexical search of chunks with title/content ranking
- Retrieve full chunk details with complete content
- Preview of chunk descendants before deletion
- Cascading deletion of chunks with all descendants

Endpoints:
    GET     /search                     - Search chunks with lexical matching
    GET     /{chunk_id}                 - Get full chunk details with complete content
    GET     /{chunk_id}/descendants     - Get all descendants of a chunk
    DELETE  /{chunk_id}                 - Delete chunk and all descendants
"""

from fastapi import APIRouter, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from vulcanlab.data.database import get_session
from vulcanlab.data.chunk_operations import (
    search_chunks_lexical,
    get_all_descendants,
    delete_chunk_cascade,
)
from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.work import Work
from vulcanlab.utils.file_utils import get_path_resolver
from vulcanlab_api.schemas.chunks import (
    ChunkSearchResponse,
    ChunkSearchResult,
    PaginationInfo,
    DescendantsResponse,
    DescendantInfo,
    ChunkDetailResponse,
    ChunkDeleteResponse,
)

router = APIRouter()


@router.get(
    "/search",
    response_model=ChunkSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search chunks",
    description="Search chunks using lexical matching with custom title/content ranking. "
                "Exact title matches are ranked first, followed by partial title matches, "
                "then content matches. Results are paginated with 25 items per page.",
    responses={
        200: {
            "description": "Search results with pagination",
            "model": ChunkSearchResponse,
        },
        400: {
            "description": "Invalid query parameter (empty query or invalid page number)",
        },
        500: {
            "description": "Internal server error during search",
        },
    }
)
async def search_chunks(
    q: str = Query(
        ...,
        min_length=1,
        description="Search query to match against chunk titles and content",
        example="introduction",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number (1-indexed)",
        example=1,
    ),
    headings_only: bool = Query(
        default=False,
        description="If true, only return heading chunks (H1-H5), excluding sentence and chunk levels",
        example=False,
    ),
) -> ChunkSearchResponse:
    """
    Search chunks using lexical matching.

    Ranking priority:
    1. Exact title match (extracted last heading equals query, case-insensitive)
    2. Partial title match (extracted last heading contains query, case-insensitive)
    3. Content match (content contains query, case-insensitive)

    Args:
        q: Search query (minimum 1 character)
        page: Page number (default: 1, minimum: 1)
        headings_only: Only return heading chunks (H1-H5), default: False

    Returns:
        ChunkSearchResponse with results and pagination info

    Raises:
        400: Invalid query parameter (empty or invalid page)
        500: Database error during search
    """
    # Additional validation for empty query (FastAPI Query validates min_length,
    # but we add explicit check for clarity)
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'q' cannot be empty"
        )

    try:
        with get_session() as session:
            # Call core search function
            results, total_count = search_chunks_lexical(
                query=q.strip(),
                page=page,
                page_size=25,
                headings_only=headings_only,
                session=session
            )

            # Map results to response model with content truncation
            search_results = [
                ChunkSearchResult(
                    id=chunk.id,
                    content_preview=chunk.content[:100],  # Truncate to 100 chars
                    heading_breadcrumbs=chunk.heading_breadcrumbs,
                    level=chunk.level,
                    work_id=chunk.work_id,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                )
                for chunk in results
            ]

            # Calculate pagination info
            has_next = (page * 25) < total_count
            has_prev = page > 1

            pagination = PaginationInfo(
                page=page,
                page_size=25,
                total_results=total_count,
                has_next=has_next,
                has_prev=has_prev,
            )

            return ChunkSearchResponse(
                results=search_results,
                pagination=pagination,
            )

    except ValueError as e:
        # Invalid parameters (page < 1, etc.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except SQLAlchemyError as e:
        # Database error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during search: {str(e)}"
        )
    except Exception as e:
        # Generic error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during search: {str(e)}"
        )


@router.get(
    "/{chunk_id}",
    response_model=ChunkDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chunk detail",
    description="Retrieve full details of a specific chunk including complete content. "
                "Used for viewing the entire chunk content in a modal.",
    responses={
        200: {
            "description": "Chunk details with full content",
            "model": ChunkDetailResponse,
        },
        404: {
            "description": "Chunk not found",
        },
        500: {
            "description": "Internal server error",
        },
    }
)
async def get_chunk_detail(
    chunk_id: int = Path(
        ...,
        gt=0,
        description="ID of the chunk to retrieve",
        example=123,
    ),
) -> ChunkDetailResponse:
    """
    Get full details of a chunk.

    Retrieves complete information about a specific chunk including the full
    content (not truncated like in search results).

    Args:
        chunk_id: ID of the chunk to retrieve

    Returns:
        ChunkDetailResponse with full chunk details

    Raises:
        404: Chunk not found
        500: Database error
    """
    try:
        with get_session() as session:
            # Query chunk
            chunk = session.query(Chunk).filter(Chunk.id == chunk_id).first()
            if chunk is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Chunk with id {chunk_id} not found"
                )

            # Return full chunk details
            return ChunkDetailResponse(
                id=chunk.id,
                content=chunk.content,  # Full content, not truncated
                heading_breadcrumbs=chunk.heading_breadcrumbs,
                level=chunk.level,
                work_id=chunk.work_id,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except SQLAlchemyError as e:
        # Database error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        # Generic error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get(
    "/{chunk_id}/descendants",
    response_model=DescendantsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chunk descendants",
    description="Retrieve all descendants of a chunk for preview before deletion. "
                "Returns all children, grandchildren, and deeper descendants in a flat list.",
    responses={
        200: {
            "description": "List of descendants with count",
            "model": DescendantsResponse,
        },
        404: {
            "description": "Chunk not found",
        },
        500: {
            "description": "Internal server error",
        },
    }
)
async def get_chunk_descendants(
    chunk_id: int = Path(
        ...,
        gt=0,
        description="ID of the chunk to get descendants for",
        example=123,
    ),
) -> DescendantsResponse:
    """
    Get all descendants of a chunk.

    Retrieves all children, grandchildren, and deeper descendants of the specified
    chunk. Used for preview before deletion to show what will be removed.

    Args:
        chunk_id: ID of the parent chunk

    Returns:
        DescendantsResponse with list of descendants and total count

    Raises:
        404: Chunk not found
        500: Database error
    """
    try:
        with get_session() as session:
            # Verify chunk exists
            chunk = session.query(Chunk).filter(Chunk.id == chunk_id).first()
            if chunk is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Chunk with id {chunk_id} not found"
                )

            # Get all descendants
            descendants = get_all_descendants(chunk_id, session)

            # Map to response model
            descendant_info = [
                DescendantInfo(
                    id=desc.id,
                    level=desc.level,
                    heading_breadcrumbs=desc.heading_breadcrumbs,
                )
                for desc in descendants
            ]

            return DescendantsResponse(
                descendants=descendant_info,
                total_count=len(descendant_info),
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except SQLAlchemyError as e:
        # Database error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        # Generic error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.delete(
    "/{chunk_id}",
    response_model=ChunkDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete chunk",
    description="Delete a chunk and all its descendants using database CASCADE. "
                "This operation cannot be undone. Returns IDs of all deleted chunks.",
    responses={
        200: {
            "description": "Chunk and descendants successfully deleted",
            "model": ChunkDeleteResponse,
        },
        404: {
            "description": "Chunk not found",
        },
        500: {
            "description": "Internal server error during deletion",
        },
    }
)
async def delete_chunk(
    chunk_id: int = Path(
        ...,
        gt=0,
        description="ID of the chunk to delete",
        example=123,
    ),
) -> ChunkDeleteResponse:
    """
    Delete a chunk and all its descendants.

    Deletes the specified chunk and all children, grandchildren, and deeper
    descendants using database CASCADE. The deletion is committed immediately
    and cannot be undone.

    Args:
        chunk_id: ID of the chunk to delete

    Returns:
        ChunkDeleteResponse with deleted chunk ID, descendant IDs, and total count

    Raises:
        404: Chunk not found
        500: Database error during deletion
    """
    try:
        with get_session() as session:
            # Get descendants BEFORE deletion (for response)
            descendants = get_all_descendants(chunk_id, session)
            descendant_ids = [desc.id for desc in descendants]

            # Delete chunk and descendants
            total_deleted = delete_chunk_cascade(chunk_id, session)

            # Commit transaction
            session.commit()

            return ChunkDeleteResponse(
                deleted_chunk_id=chunk_id,
                descendants_deleted=descendant_ids,
                total_deleted=total_deleted,
            )

    except ValueError as e:
        # Chunk not found (raised by delete_chunk_cascade)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except SQLAlchemyError as e:
        # Database error - rollback is handled by context manager
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during deletion: {str(e)}"
        )
    except Exception as e:
        # Generic error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during deletion: {str(e)}"
            )
