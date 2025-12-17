"""
Markdown export/import router - markdown file operations.

Endpoints:
    POST /api/v1/markdown/export/{work_id} - Export work markdown to file
    GET /api/v1/markdown/check-duplicate - Check for duplicate work by title/author
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from vulcanlab_api.dependencies import get_db_session
from vulcanlab.markdown_export import export_work
from vulcanlab.markdown_import.duplicate_check import check_duplicate_work

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/export/{work_id}",
    response_model=Dict[str, Any],
    summary="Export work markdown to file",
    description="Export a work's markdown content with YAML frontmatter to the exports folder.",
    responses={
        200: {
            "description": "Export successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "export_path": "/path/to/output/exports/the-psychology-of-learning.md"
                    }
                }
            }
        },
        400: {
            "description": "Markdown not available for this work"
        },
        404: {
            "description": "Work not found"
        },
        500: {
            "description": "Failed to write export file"
        }
    },
    tags=["Markdown"],
)
async def export_work_endpoint(
    work_id: int,
    session: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Export work markdown to exports folder.

    Retrieves markdown from database (simple conversion) or output folder
    (advanced conversion), adds YAML frontmatter, and writes to exports directory.

    Args:
        work_id: ID of work to export
        session: Database session

    Returns:
        Success status and export file path

    Raises:
        HTTPException: 404 if work not found, 400 if markdown unavailable,
                      500 if write operation fails
    """
    try:
        export_path = export_work(work_id, session)
        return {
            "success": True,
            "export_path": export_path
        }
    except HTTPException:
        # Re-raise HTTPExceptions from export_work
        raise
    except Exception as e:
        logger.error(f"Unexpected error exporting work {work_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during export: {str(e)}"
        )


@router.get(
    "/check-duplicate",
    response_model=Dict[str, Any],
    summary="Check for duplicate work",
    description="Check if a work with the given title and author already exists in the database.",
    responses={
        200: {
            "description": "Duplicate check completed",
            "content": {
                "application/json": {
                    "examples": {
                        "duplicate_found": {
                            "summary": "Duplicate found",
                            "value": {
                                "exists": True,
                                "work_id": 123,
                                "work_title": "The Psychology of Learning"
                            }
                        },
                        "no_duplicate": {
                            "summary": "No duplicate",
                            "value": {
                                "exists": False
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Missing or invalid parameters"
        },
        500: {
            "description": "Database error"
        }
    },
    tags=["Markdown"],
)
async def check_duplicate_endpoint(
    title: str = Query(..., description="Work title to check for duplicates"),
    author: str = Query(..., description="Author name to check for duplicates"),
    session: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Check if a work with matching title and author already exists.

    Performs case-insensitive matching on both title and author fields.
    Returns work details if a duplicate is found.

    Args:
        title: Work title to search for (required)
        author: Author name to search for (required)
        session: Database session

    Returns:
        Dictionary with 'exists' boolean and optional work details

    Raises:
        HTTPException: 400 if parameters are invalid, 500 if database error occurs
    """
    # Validate parameters
    if not title or not title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title parameter is required and cannot be empty"
        )

    if not author or not author.strip():
        raise HTTPException(
            status_code=400,
            detail="Author parameter is required and cannot be empty"
        )

    try:
        # Check for duplicate work
        duplicate_work = check_duplicate_work(
            title.strip(),
            author.strip(),
            session
        )

        if duplicate_work:
            return {
                "exists": True,
                "work_id": duplicate_work.id,
                "work_title": duplicate_work.title
            }
        else:
            return {
                "exists": False
            }

    except Exception as e:
        logger.error(f"Error checking for duplicate work: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error while checking for duplicates: {str(e)}"
        )
