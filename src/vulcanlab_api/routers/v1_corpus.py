"""
V1 Corpus Router - Versioned API endpoints for corpus management.

This router contains versioned write operations for corpus management.
Read operations remain in the legacy corpus router for backwards compatibility.

Endpoints:
    DELETE  /api/v1/corpus/works/{work_id}     - Delete a work and all associated data
"""

from fastapi import APIRouter, HTTPException, Response, status

from vulcanlab.data.database import get_session
from vulcanlab.data.work_operations import delete_work

router = APIRouter()


@router.delete(
    "/works/{work_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a work",
    description="Delete a work and all associated data including files, chunks, "
                "parsed markdown, and sanitized markdown. This operation cannot be undone.",
    responses={
        204: {"description": "Work successfully deleted"},
        400: {"description": "Invalid work_id (must be positive integer)"},
        404: {"description": "Work not found"},
        500: {"description": "Internal server error during deletion"},
    }
)
async def delete_corpus_work(work_id: int) -> Response:
    """
    Delete a work and all associated data.

    Deletes:
    - Work record
    - All chunks (via CASCADE)
    - ParsedMarkdown records
    - SanitizedMarkdown records
    - Physical files tracked in work.files

    Args:
        work_id: ID of the work to delete

    Returns:
        204 No Content on success

    Raises:
        400: Invalid work_id (must be positive)
        404: Work not found
        500: Error during deletion (e.g., file permission issues)
    """
    # Validate work_id
    if work_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid work_id: must be a positive integer"
        )

    try:
        with get_session() as session:
            # Call core deletion function
            delete_work(work_id, session)
            # Commit is handled by session context manager
            session.commit()

        # Return 204 No Content
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except ValueError as e:
        # Work not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except IOError as e:
        # File deletion error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete work files: {str(e)}"
        )
    except Exception as e:
        # Generic error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting work: {str(e)}"
        )
