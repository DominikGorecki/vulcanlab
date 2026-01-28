"""
Pydantic schemas for expansion API endpoints.

These schemas define request/response models for the answer expansion feature
which breaks down RAG answers into multiple sections for deeper analysis.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Request Schemas
# =============================================================================


class CreateExpansionRequest(BaseModel):
    """Request to create a new expansion from a result."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "result_id": 123,
                "mode": "automatic"
            }
        }
    )

    result_id: int = Field(
        ...,
        description="ID of the Result to expand"
    )
    mode: str = Field(
        default="automatic",
        pattern="^(automatic|manual)$",
        description="Expansion mode: 'automatic' (LLM-driven) or 'manual' (user-driven)"
    )


class ManualResponseRequest(BaseModel):
    """Request to save a manual response for a section."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "response_text": "This is my manually written response for this section..."
            }
        }
    )

    response_text: str = Field(
        ...,
        min_length=1,
        description="The manual response text to save"
    )


class ManualBreakdownRequest(BaseModel):
    """Request to save a manual breakdown result (sections JSON from user)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "breakdown_json": '{"sections": [{"heading": "Introduction", "summary": "Overview", "expansion_prompt": "Explain..."}]}'
            }
        }
    )

    breakdown_json: str = Field(
        ...,
        min_length=1,
        description="JSON string containing the breakdown sections from external LLM"
    )


# =============================================================================
# Response Schemas
# =============================================================================


class CreateExpansionResponse(BaseModel):
    """Response from creating an expansion."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "expansion_id": 456,
                "status": "created",
                "message": "Expansion created successfully"
            }
        }
    )

    expansion_id: int = Field(
        ...,
        description="ID of the created expansion"
    )
    status: str = Field(
        ...,
        description="Current status of the expansion"
    )
    message: str = Field(
        default="Expansion created successfully",
        description="Status message"
    )


class SectionSummary(BaseModel):
    """Summary of an expansion section for list views."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "order": 1,
                "heading": "Introduction to Working Memory",
                "summary": "Overview of working memory concepts",
                "status": "completed",
                "error_message": None
            }
        }
    )

    id: int = Field(..., description="Section ID")
    order: int = Field(..., description="Section order (1-based)")
    heading: str = Field(..., description="Section heading")
    summary: str = Field(..., description="Brief summary of the section")
    status: str = Field(..., description="Current section status")
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if section failed"
    )


class SectionDetailResponse(BaseModel):
    """Full detail of an expansion section including RAG data."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "expansion_id": 456,
                "order": 1,
                "heading": "Introduction to Working Memory",
                "summary": "Overview of working memory concepts",
                "expansion_prompt": "Explain the key components of working memory...",
                "expanded_queries": {"queries": ["What is working memory?", "Define working memory"]},
                "hyde_answer": "Working memory is a cognitive system...",
                "intent": "DEFINITION",
                "entities": {"entities": ["working memory", "cognitive system"]},
                "clean_retrieval_context": {"chunks": []},
                "augmented_prompt": "Based on the following context...",
                "response_text": "Working memory is a fundamental cognitive process...",
                "status": "completed",
                "error_message": None,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:35:00Z"
            }
        }
    )

    id: int = Field(..., description="Section ID")
    expansion_id: int = Field(..., description="Parent expansion ID")
    order: int = Field(..., description="Section order (1-based)")
    heading: str = Field(..., description="Section heading")
    summary: str = Field(..., description="Brief summary of the section")
    expansion_prompt: str = Field(..., description="Prompt used for RAG expansion")
    expanded_queries: Optional[dict] = Field(
        default=None,
        description="Expanded queries from MQE"
    )
    hyde_answer: Optional[str] = Field(
        default=None,
        description="HyDE-generated hypothetical answer"
    )
    intent: Optional[str] = Field(
        default=None,
        description="Detected query intent"
    )
    entities: Optional[dict] = Field(
        default=None,
        description="Extracted entities"
    )
    clean_retrieval_context: Optional[dict] = Field(
        default=None,
        description="Consolidated retrieval context"
    )
    augmented_prompt: Optional[str] = Field(
        default=None,
        description="Final augmented prompt with context"
    )
    response_text: Optional[str] = Field(
        default=None,
        description="LLM-generated or manual response"
    )
    status: str = Field(..., description="Current section status")
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if section failed"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ExpansionListItem(BaseModel):
    """Expansion summary for list views."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 456,
                "result_id": 123,
                "query_id": 100,
                "original_query": "What is working memory?",
                "mode": "automatic",
                "status": "completed",
                "section_count": 5,
                "completed_count": 5,
                "failed_count": 0,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    )

    id: int = Field(..., description="Expansion ID")
    result_id: int = Field(..., description="Associated result ID")
    query_id: int = Field(..., description="Associated query ID")
    original_query: Optional[str] = Field(
        default=None,
        description="Original query text"
    )
    mode: str = Field(..., description="Expansion mode (automatic/manual)")
    status: str = Field(..., description="Current expansion status")
    section_count: int = Field(..., description="Total number of sections")
    completed_count: int = Field(
        default=0,
        description="Number of completed sections"
    )
    failed_count: int = Field(
        default=0,
        description="Number of failed sections"
    )
    created_at: datetime = Field(..., description="Creation timestamp")


class ExpansionDetailResponse(BaseModel):
    """Full detail of an expansion including sections."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 456,
                "result_id": 123,
                "query_id": 100,
                "original_query": "What is working memory?",
                "mode": "automatic",
                "status": "completed",
                "combined_report": "## Introduction\n\nWorking memory is...",
                "expansion_metadata": {"source_token_estimate": 5000, "section_count": 5},
                "sections": [],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:40:00Z"
            }
        }
    )

    id: int = Field(..., description="Expansion ID")
    result_id: int = Field(..., description="Associated result ID")
    query_id: int = Field(..., description="Associated query ID")
    original_query: Optional[str] = Field(
        default=None,
        description="Original query text"
    )
    mode: str = Field(..., description="Expansion mode (automatic/manual)")
    status: str = Field(..., description="Current expansion status")
    combined_report: Optional[str] = Field(
        default=None,
        description="Final combined report markdown"
    )
    expansion_metadata: Optional[dict] = Field(
        default=None,
        description="Additional expansion metadata"
    )
    sections: list[SectionSummary] = Field(
        default_factory=list,
        description="List of expansion sections"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ExpansionListResponse(BaseModel):
    """Response for listing expansions."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "expansions": [],
                "total": 0
            }
        }
    )

    expansions: list[ExpansionListItem] = Field(
        ...,
        description="List of expansions"
    )
    total: int = Field(..., description="Total count")


class BreakdownResponse(BaseModel):
    """Response from running breakdown."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "expansion_id": 456,
                "status": "breakdown_complete",
                "section_count": 5,
                "sections": [],
                "message": "Breakdown complete, 5 sections created"
            }
        }
    )

    expansion_id: int = Field(..., description="Expansion ID")
    status: str = Field(..., description="Updated expansion status")
    section_count: int = Field(..., description="Number of sections created")
    sections: list[SectionSummary] = Field(
        default_factory=list,
        description="Created sections"
    )
    message: str = Field(..., description="Status message")


class SectionOperationResponse(BaseModel):
    """Response from section operations (expand/generate/manual)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "section_id": 1,
                "expansion_id": 456,
                "status": "completed",
                "message": "Section expanded successfully"
            }
        }
    )

    section_id: int = Field(..., description="Section ID")
    expansion_id: int = Field(..., description="Parent expansion ID")
    status: str = Field(..., description="Updated section status")
    message: str = Field(..., description="Status message")


class CombineResponse(BaseModel):
    """Response from combining sections."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "expansion_id": 456,
                "status": "completed",
                "report_length": 15000,
                "message": "Sections combined successfully"
            }
        }
    )

    expansion_id: int = Field(..., description="Expansion ID")
    status: str = Field(..., description="Updated expansion status")
    report_length: int = Field(..., description="Length of combined report in characters")
    message: str = Field(..., description="Status message")


class RunAutomaticResponse(BaseModel):
    """Response from running automatic mode pipeline."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "expansion_id": 456,
                "status": "completed",
                "sections_processed": 5,
                "sections_completed": 5,
                "sections_failed": 0,
                "message": "Automatic expansion completed successfully"
            }
        }
    )

    expansion_id: int = Field(..., description="Expansion ID")
    status: str = Field(..., description="Final expansion status")
    sections_processed: int = Field(
        ...,
        description="Number of sections processed"
    )
    sections_completed: int = Field(
        ...,
        description="Number of sections completed successfully"
    )
    sections_failed: int = Field(
        ...,
        description="Number of sections that failed"
    )
    message: str = Field(..., description="Status message")


class ResultExpansionResponse(BaseModel):
    """Response for checking if a result has an expansion."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "result_id": 123,
                "has_expansion": True,
                "expansion_id": 456,
                "expansion_status": "completed"
            }
        }
    )

    result_id: int = Field(..., description="Result ID")
    has_expansion: bool = Field(
        ...,
        description="Whether an expansion exists for this result"
    )
    expansion_id: Optional[int] = Field(
        default=None,
        description="Expansion ID if exists"
    )
    expansion_status: Optional[str] = Field(
        default=None,
        description="Expansion status if exists"
    )


class BreakdownPromptResponse(BaseModel):
    """Response containing the breakdown prompt for manual mode."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "expansion_id": 456,
                "prompt": "Break down the following answer into 3-7 sections...",
                "answer_token_estimate": 5000
            }
        }
    )

    expansion_id: int = Field(..., description="Expansion ID")
    prompt: str = Field(..., description="The breakdown prompt to copy and paste into an LLM")
    answer_token_estimate: int = Field(
        ...,
        description="Estimated token count of the original answer"
    )
