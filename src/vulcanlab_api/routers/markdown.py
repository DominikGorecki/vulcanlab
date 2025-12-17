"""
Markdown export/import router - markdown file operations.

Endpoints:
    POST /api/v1/markdown/export/{work_id} - Export work markdown to file
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from vulcanlab_api.dependencies import get_db_session
from vulcanlab.markdown_export import export_work

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
