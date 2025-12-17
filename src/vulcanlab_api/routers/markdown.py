"""
Markdown export/import router - markdown file operations.

Endpoints:
    POST /api/v1/markdown/export/{work_id} - Export work markdown to file
    GET /api/v1/markdown/check-duplicate - Check for duplicate work by title/author
    GET /api/v1/markdown/files - List available markdown files for import
    POST /api/v1/markdown/import - Import a markdown file as a work
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from vulcanlab_api.dependencies import get_db_session
from vulcanlab_api.schemas.markdown import (
    MarkdownFilesResponse,
    MarkdownFileSchema,
    MetadataSchema,
    ImportRequest,
    ImportResponse,
    ErrorResponse
)
from vulcanlab.markdown_export import export_work
from vulcanlab.markdown_import.duplicate_check import check_duplicate_work
from vulcanlab.markdown_import.scanner import list_markdown_files
from vulcanlab.markdown_import.metadata import Metadata
from vulcanlab.markdown_import.import_flow import (
    import_sanitized_markdown,
    import_unsanitized_markdown
)
from vulcanlab.config import load_config

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
            "description": "Markdown not available for this work",
            "model": ErrorResponse
        },
        404: {
            "description": "Work not found",
            "model": ErrorResponse
        },
        500: {
            "description": "Failed to write export file",
            "model": ErrorResponse
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
        # Re-raise HTTPExceptions from export_work (already have good error messages)
        raise
    except Exception as e:
        logger.error(f"Unexpected error exporting work {work_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "unexpected_error",
                "message": "An unexpected error occurred during export",
                "detail": str(e) if logger.level <= logging.DEBUG else None
            }
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


@router.get(
    "/files",
    response_model=MarkdownFilesResponse,
    summary="List available markdown files",
    description="List all markdown files in the input directory with their metadata.",
    responses={
        200: {
            "description": "List of markdown files",
            "content": {
                "application/json": {
                    "example": {
                        "files": [
                            {
                                "filename": "cognitive-psychology.md",
                                "file_path": "/input/cognitive-psychology.md",
                                "has_metadata": True,
                                "metadata": {
                                    "title": "Cognitive Psychology",
                                    "author": "Jane Smith",
                                    "year": 2020
                                }
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Filesystem error"
        }
    },
    tags=["Markdown"],
)
async def list_files_endpoint() -> MarkdownFilesResponse:
    """
    List all markdown files available for import.

    Scans the input directory for .md files and extracts metadata from
    YAML frontmatter if present.

    Returns:
        List of markdown files with metadata

    Raises:
        HTTPException: 500 if filesystem error occurs
    """
    try:
        markdown_files = list_markdown_files()

        # Convert MarkdownFile dataclasses to Pydantic schemas
        file_schemas = []
        for md_file in markdown_files:
            metadata_schema = None
            if md_file.metadata:
                metadata_schema = MetadataSchema(
                    title=md_file.metadata.title,
                    author=md_file.metadata.author,
                    year=md_file.metadata.year
                )

            file_schema = MarkdownFileSchema(
                filename=md_file.filename,
                file_path=md_file.file_path,
                has_metadata=md_file.has_metadata,
                metadata=metadata_schema
            )
            file_schemas.append(file_schema)

        return MarkdownFilesResponse(files=file_schemas)

    except ValueError as e:
        logger.error(f"Configuration error listing markdown files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error listing markdown files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Filesystem error: {str(e)}"
        )


@router.post(
    "/import",
    response_model=ImportResponse,
    summary="Import markdown file as work",
    description="Import a markdown file from the input directory and create a work record.",
    responses={
        200: {
            "description": "Import successful",
            "content": {
                "application/json": {
                    "example": {
                        "work_id": 123,
                        "status": "completed",
                        "duplicate_warning": None
                    }
                }
            }
        },
        400: {
            "description": "Invalid request or validation error",
            "model": ErrorResponse
        },
        404: {
            "description": "File not found",
            "model": ErrorResponse
        },
        500: {
            "description": "Import failed",
            "model": ErrorResponse
        }
    },
    tags=["Markdown"],
)
async def import_markdown_endpoint(
    request: ImportRequest,
    session: Session = Depends(get_db_session)
) -> ImportResponse:
    """
    Import a markdown file as a work.

    Creates a Work record from the markdown file, runs sanitization if needed,
    creates chunks, and prepares for vectorization.

    Args:
        request: Import request with filename and metadata
        session: Database session

    Returns:
        Import response with work ID and status

    Raises:
        HTTPException: 400 for validation errors, 404 if file not found,
                      500 if import fails
    """
    try:
        # Load config to get input directory
        config = load_config()
        if not config.paths.input_dir:
            raise HTTPException(
                status_code=500,
                detail="input_dir not configured"
            )

        input_dir = Path(config.paths.input_dir)
        file_path = input_dir / request.filename

        # Validate file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.filename}"
            )

        if not file_path.is_file():
            raise HTTPException(
                status_code=400,
                detail=f"Not a file: {request.filename}"
            )

        # Create Metadata object from request
        metadata = Metadata(
            title=request.title,
            author=request.author,
            year=request.year
        )

        # Check for duplicate (warning only, doesn't block import)
        duplicate_warning = None
        try:
            duplicate_work = check_duplicate_work(
                request.title,
                request.author,
                session
            )
            if duplicate_work:
                duplicate_warning = (
                    f"A work with similar title/author already exists "
                    f"(ID: {duplicate_work.id}, Title: '{duplicate_work.title}')"
                )
                logger.warning(f"Duplicate detected but proceeding: {duplicate_warning}")
        except Exception as e:
            # Log error but don't fail import
            logger.error(f"Error checking for duplicates: {e}")

        # Import based on sanitization flag
        try:
            if request.is_sanitized:
                logger.info(f"Importing sanitized markdown: {request.filename}")
                work = import_sanitized_markdown(
                    str(file_path),
                    metadata,
                    session
                )
            else:
                logger.info(f"Importing unsanitized markdown: {request.filename}")
                work = import_unsanitized_markdown(
                    str(file_path),
                    metadata,
                    session
                )

            return ImportResponse(
                work_id=work.id,
                status="completed",
                duplicate_warning=duplicate_warning
            )

        except FileNotFoundError as e:
            error_msg = str(e)
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "file_not_found",
                    "message": "The specified file could not be found",
                    "detail": error_msg
                }
            )
        except ValueError as e:
            error_msg = str(e)
            # Determine error type based on message
            if "empty" in error_msg.lower():
                error_type = "empty_file"
                user_message = "The file is empty or contains no content"
            elif "encoding" in error_msg.lower():
                error_type = "encoding_error"
                user_message = "The file encoding is not supported"
            elif "permission" in error_msg.lower():
                error_type = "permission_denied"
                user_message = "Permission denied reading the file"
            elif "frontmatter" in error_msg.lower() or "whitespace" in error_msg.lower():
                error_type = "no_content"
                user_message = "File contains only metadata or whitespace, no actual content"
            elif "chunking" in error_msg.lower():
                error_type = "chunking_failed"
                user_message = "Failed to process markdown structure"
            elif "sanitization" in error_msg.lower():
                error_type = "sanitization_failed"
                user_message = "Failed to sanitize markdown content"
            else:
                error_type = "validation_error"
                user_message = error_msg

            raise HTTPException(
                status_code=400,
                detail={
                    "error": error_type,
                    "message": user_message,
                    "detail": error_msg if error_msg != user_message else None
                }
            )

    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error importing markdown: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "unexpected_error",
                "message": "An unexpected error occurred during import",
                "detail": str(e) if logger.level <= logging.DEBUG else None
            }
        )
