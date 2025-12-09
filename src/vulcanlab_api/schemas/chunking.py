"""
Pydantic schemas for chunking API endpoints.

This module defines request and response models for the chunking router.
"""

from pydantic import BaseModel, ConfigDict, Field


# Work List Schemas
class WorkListItem(BaseModel):
    """Individual work item in the list."""
    id: int = Field(..., description="Work ID")
    title: str = Field(..., description="Work title")
    authors: str | None = Field(None, description="Work authors")
    year: int | None = Field(None, description="Publication year")
    work_type: str | None = Field(None, description="Type of work (book, article, etc.)")
    has_sanitized: bool = Field(..., description="Whether sanitized file exists")
    heading_chunks_status: str | None = Field(None, description="Status of heading chunks (completed, pending, failed)")
    content_chunks_status: str | None = Field(None, description="Status of content chunks (completed, pending, failed)")


class WorkListResponse(BaseModel):
    """Response for work listing."""
    works: list[WorkListItem] = Field(..., description="List of works with sanitized files")
    total: int = Field(..., description="Total number of works")


# File Status Schema
class FileStatusInfo(BaseModel):
    """File status information."""
    exists: bool = Field(..., description="Whether the file exists")
    path: str | None = Field(None, description="File path if exists")
    hash: str | None = Field(None, description="File hash from database")
    hash_match: bool | None = Field(None, description="Whether file hash matches database (None if file doesn't exist)")


# Work Detail Schema
class WorkDetailResponse(BaseModel):
    """Detailed work information with file statuses."""
    id: int = Field(..., description="Work ID")
    title: str = Field(..., description="Work title")
    authors: str | None = Field(None, description="Work authors")
    year: int | None = Field(None, description="Publication year")
    work_type: str | None = Field(None, description="Type of work")
    files: dict[str, FileStatusInfo] = Field(..., description="File status information")
    processing_status: dict[str, str] | None = Field(None, description="Processing status (heading_chunks, content_chunks)")


# Sanitized Content Schemas
class SanitizedContentResponse(BaseModel):
    """Response for sanitized file content."""
    content: str = Field(..., description="Content of the sanitized file")
    filename: str = Field(..., description="Filename of the sanitized file")
    current_hash: str = Field(..., description="Current SHA-256 hash of the file")


class UpdateSanitizedContentRequest(BaseModel):
    """Request to update sanitized file content."""
    content: str = Field(..., description="New content for the sanitized file")


# Sanitized Titles Schemas
class SanTitlesContentResponse(BaseModel):
    """Response for sanitized titles file content."""
    content: str = Field(..., description="Content of the sanitized_titles file")
    filename: str = Field(..., description="Filename of the sanitized_titles file")
    current_hash: str = Field(..., description="Current SHA-256 hash of the file")


class UpdateSanTitlesContentRequest(BaseModel):
    """Request to update sanitized titles file content."""
    content: str = Field(..., description="New content for the sanitized_titles file")


class ExtractSanitizedTitlesRequest(BaseModel):
    """Request to extract sanitized titles."""
    force: bool = Field(False, description="Force extraction even if hash doesn't match")


class ExtractSanitizedTitlesResponse(BaseModel):
    """Response after extracting sanitized titles."""
    success: bool = Field(..., description="Whether extraction was successful")
    message: str = Field(..., description="Status message")
    output_path: str = Field(..., description="Path to the created titles file")


# Apply Chunking Schemas
class ApplyHeadingChunksResponse(BaseModel):
    """Response after applying heading chunks."""
    success: bool = Field(..., description="Whether chunking was successful")
    message: str = Field(..., description="Status message")
    chunks_created: int = Field(..., description="Number of chunks created")


class ApplyContentChunksResponse(BaseModel):
    """Response after applying content chunks."""
    success: bool = Field(..., description="Whether chunking was successful")
    message: str = Field(..., description="Status message")
    chunks_created: int = Field(..., description="Number of chunks created")


# Vec Suggestions Schemas
class VecSuggestionsPromptResponse(BaseModel):
    """Response for vec suggestions prompt."""
    prompt: str = Field(..., description="The LLM prompt for generating vec suggestions")
    work_title: str | None = Field(None, description="Work title")
    work_authors: str | None = Field(None, description="Work authors")


class ManualVecSuggestionsRequest(BaseModel):
    """Request to save manual vec suggestions response."""
    response_text: str = Field(..., description="The LLM response text")
    force: bool = Field(False, description="Force save even if hash doesn't match")


class ManualVecSuggestionsResponse(BaseModel):
    """Response after saving manual vec suggestions."""
    success: bool = Field(..., description="Whether save was successful")
    message: str = Field(..., description="Status message")
    output_path: str = Field(..., description="Path to the created vec_suggestions file")


class RunVecSuggestionsRequest(BaseModel):
    """Request to run vec suggestions with LLM."""
    force: bool = Field(False, description="Force run even if hash doesn't match")


class RunVecSuggestionsResponse(BaseModel):
    """Response after running vec suggestions."""
    success: bool = Field(..., description="Whether generation was successful")
    message: str = Field(..., description="Status message")
    output_path: str = Field(..., description="Path to the created vec_suggestions file")


# Interactive Vec Suggestions Table Schemas

class VecSuggestionRow(BaseModel):
    """A single row in the vec suggestions table."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "line_num": 155,
                "heading": "# 1 Cognitive Psychology and the Brain",
                "decision": "VECTORIZE"
            }
        }
    )

    line_num: int = Field(..., description="Line number in sanitized markdown file")
    heading: str = Field(..., description="Full heading text with markdown symbols")
    decision: str = Field(..., description="Vectorization decision (VECTORIZE or SKIP)")


class VecSuggestionsTableResponse(BaseModel):
    """Response containing table data for vec suggestions."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "work_id": 3,
                "rows": [
                    {
                        "line_num": 155,
                        "heading": "# 1 Cognitive Psychology and the Brain",
                        "decision": "VECTORIZE"
                    },
                    {
                        "line_num": 649,
                        "heading": "## 2.9 References",
                        "decision": "SKIP"
                    }
                ],
                "filename": "test3.sanitized.vec_sugg.md",
                "hash": "abc123def456..."
            }
        }
    )

    work_id: int = Field(..., description="Work ID")
    rows: list[VecSuggestionRow] = Field(..., description="All heading rows merged with decisions")
    filename: str = Field(..., description="Vec suggestions filename")
    hash: str = Field(..., description="Current hash of vec_suggestions file")


class UpdateVecSuggestionsTableRequest(BaseModel):
    """Request to update vec suggestions from table data."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rows": [
                    {
                        "line_num": 155,
                        "heading": "# 1 Cognitive Psychology and the Brain",
                        "decision": "VECTORIZE"
                    },
                    {
                        "line_num": 649,
                        "heading": "## 2.9 References",
                        "decision": "SKIP"
                    }
                ]
            }
        }
    )

    rows: list[VecSuggestionRow] = Field(..., description="Updated vec suggestion rows")
