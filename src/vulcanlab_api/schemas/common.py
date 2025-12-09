"""
Common/shared Pydantic schemas used across multiple routers.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base response with common fields."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully",
            }
        }
    )

    message: str | None = Field(
        default=None,
        description="Optional message providing additional context",
    )


class ErrorResponse(BaseModel):
    """Standard error response format."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "detail": "Invalid file format. Expected PDF.",
                "timestamp": "2024-01-15T10:30:00Z",
                "path": "/conv/pdf",
            }
        }
    )

    error: str = Field(
        ...,
        description="Error type/code",
    )
    detail: str = Field(
        ...,
        description="Human-readable error description",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the error occurred",
    )
    path: str | None = Field(
        default=None,
        description="API path where error occurred",
    )


class JobStatusResponse(BaseModel):
    """Response for async job status queries."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "job_abc123",
                "status": "processing",
                "progress": 45,
            }
        }
    )

    job_id: str = Field(
        ...,
        description="Unique job identifier",
    )
    status: str = Field(
        ...,
        description="Current job status",
    )
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Progress percentage (0-100)",
    )
    created_at: datetime | None = Field(
        default=None,
        description="When the job was created",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="When the job was last updated",
    )
    message: str | None = Field(
        default=None,
        description="Status message",
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
            }
        }
    )

    items: list[T] = Field(
        ...,
        description="List of items in current page",
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of items",
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number",
    )
    page_size: int = Field(
        ...,
        ge=1,
        description="Items per page",
    )
    total_pages: int = Field(
        ...,
        ge=0,
        description="Total number of pages",
    )


class FilePathRequest(BaseModel):
    """Request containing a file path."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_path": "/output/document.md",
            }
        }
    )

    file_path: str = Field(
        ...,
        description="Path to the file",
    )


class WorkIdentifier(BaseModel):
    """Identifier for a work/document."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "work_id": "work_123",
                "file_path": "/output/cognitive_psych.md",
            }
        }
    )

    work_id: str | None = Field(
        default=None,
        description="Work ID in the database",
    )
    file_path: str | None = Field(
        default=None,
        description="Path to the work file",
    )


