"""
Pydantic schemas for result model management endpoints.

These schemas support the model listing and creation workflows.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ResultModelItem(BaseModel):
    """A result model item in the list view."""

    id: int = Field(..., description="Model ID")
    name: str = Field(..., description="Model name (e.g., 'gpt-4', 'claude-sonnet-3.5')")
    created_at: datetime = Field(..., description="Creation timestamp")


class ResultModelListResponse(BaseModel):
    """Response containing list of result models."""

    models: list[ResultModelItem] = Field(..., description="List of result models")
    total: int = Field(..., description="Total number of models")


class ResultModelCreateRequest(BaseModel):
    """Request to create a new result model."""

    name: str = Field(
        ...,
        description="Model name (e.g., 'gpt-4', 'claude-sonnet-3.5')",
        min_length=1,
        max_length=200
    )


class ResultModelCreateResponse(BaseModel):
    """Response after creating a result model."""

    id: int = Field(..., description="Model ID")
    name: str = Field(..., description="Model name")
    created_at: datetime = Field(..., description="Creation timestamp")
    message: str = Field(..., description="Success message")
