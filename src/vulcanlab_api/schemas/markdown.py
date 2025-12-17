"""
Pydantic schemas for markdown import/export API endpoints.
"""

from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


class MetadataSchema(BaseModel):
    """Metadata extracted from markdown file frontmatter."""

    model_config = {"json_schema_extra": {
        "example": {
            "title": "The Psychology of Learning",
            "author": "John Doe",
            "year": 2023
        }
    }}

    title: str = Field(
        ...,
        description="Work title from frontmatter"
    )
    author: Optional[str] = Field(
        None,
        description="Author name(s) from frontmatter"
    )
    year: Optional[int] = Field(
        None,
        description="Publication year from frontmatter"
    )


class MarkdownFileSchema(BaseModel):
    """Information about a markdown file available for import."""

    model_config = {"json_schema_extra": {
        "example": {
            "filename": "cognitive-psychology.md",
            "file_path": "/input/cognitive-psychology.md",
            "has_metadata": True,
            "metadata": {
                "title": "Cognitive Psychology",
                "author": "Jane Smith",
                "year": 2020
            }
        }
    }}

    filename: str = Field(
        ...,
        description="Name of the markdown file"
    )
    file_path: str = Field(
        ...,
        description="Full path to the markdown file"
    )
    has_metadata: bool = Field(
        ...,
        description="Whether YAML frontmatter was found in the file"
    )
    metadata: Optional[MetadataSchema] = Field(
        None,
        description="Extracted metadata if frontmatter was found"
    )


class MarkdownFilesResponse(BaseModel):
    """Response for GET /files endpoint."""

    model_config = {"json_schema_extra": {
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
    }}

    files: List[MarkdownFileSchema] = Field(
        ...,
        description="List of markdown files available for import"
    )


class ImportRequest(BaseModel):
    """Request body for POST /import endpoint."""

    model_config = {"json_schema_extra": {
        "example": {
            "filename": "cognitive-psychology.md",
            "title": "Cognitive Psychology",
            "author": "Jane Smith",
            "year": 2020,
            "is_sanitized": True
        }
    }}

    filename: str = Field(
        ...,
        description="Name of the markdown file to import",
        min_length=1
    )
    title: str = Field(
        ...,
        description="Work title (required)",
        min_length=1
    )
    author: str = Field(
        ...,
        description="Author name (required)",
        min_length=1
    )
    year: Optional[int] = Field(
        None,
        description="Publication year (optional)"
    )
    is_sanitized: bool = Field(
        ...,
        description="Whether the markdown is already sanitized (true) or needs sanitization (false)"
    )

    @field_validator('title', 'author')
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that string fields are not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace-only")
        return v.strip()

    @field_validator('year')
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        """Validate year is in reasonable range."""
        if v is not None:
            if v < 1000 or v > 2100:
                raise ValueError("Year must be between 1000 and 2100")
        return v


class ImportResponse(BaseModel):
    """Response for POST /import endpoint."""

    model_config = {"json_schema_extra": {
        "example": {
            "work_id": 123,
            "status": "completed",
            "duplicate_warning": None
        }
    }}

    work_id: int = Field(
        ...,
        description="ID of the created work"
    )
    status: str = Field(
        ...,
        description="Import status (e.g., 'completed', 'failed')"
    )
    duplicate_warning: Optional[str] = Field(
        None,
        description="Warning message if duplicate work detected"
    )


class ErrorResponse(BaseModel):
    """Structured error response for API errors."""

    model_config = {"json_schema_extra": {
        "example": {
            "error": "validation_error",
            "message": "File is empty (0 bytes)",
            "detail": None
        }
    }}

    error: str = Field(
        ...,
        description="Error type/code (e.g., 'validation_error', 'file_not_found', 'permission_denied')"
    )
    message: str = Field(
        ...,
        description="User-friendly error message"
    )
    detail: Optional[str] = Field(
        None,
        description="Optional technical details for debugging (not shown to end users)"
    )
