"""
Pydantic schemas for summarization API.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class HeadingPreview(BaseModel):
    """Preview of a heading selected for summarization."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_id": 123,
                "level": "H2",
                "title": "Introduction to Neural Networks",
                "start_line": 45,
                "content_word_count": 750,
            }
        }
    )

    chunk_id: int = Field(..., description="ID of the heading chunk")
    level: str = Field(..., description="Heading level (H1, H2, etc.)")
    title: str = Field(..., description="Heading title text")
    start_line: int = Field(..., description="Starting line number in the original work")
    content_word_count: int = Field(..., description="Number of words in this heading's section")


class PrepareResponse(BaseModel):
    """Response for the summarization preparation endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "headings": [
                    {
                        "chunk_id": 123,
                        "level": "H2",
                        "title": "Introduction",
                        "start_line": 45,
                        "content_word_count": 750,
                    }
                ],
                "total_prompts": 3,
                "estimated_tokens": 12500,
                "has_existing_summaries": False,
            }
        }
    )

    headings: list[HeadingPreview] = Field(..., description="List of headings selected for summarization")
    total_prompts: int = Field(..., description="Estimated number of LLM calls/prompts required")
    estimated_tokens: int = Field(..., description="Estimated total tokens for all prompts")
    has_existing_summaries: bool = Field(..., description="Whether summaries already exist for this work")


class GeneratePromptsRequest(BaseModel):
    """Request for the prompt generation endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "regenerate_all": False,
            }
        }
    )

    regenerate_all: bool = Field(
        default=False, 
        description="If true, deletes existing summaries before generating new prompts"
    )


class PromptResponse(BaseModel):
    """A single generated prompt and its metadata."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt_index": 0,
                "content": "Summarize the following sections...",
                "heading_ids": [123, 124, 125],
            }
        }
    )

    prompt_index: int = Field(..., description="Zero-based index of the prompt")
    content: str = Field(..., description="The full assembled prompt text")
    heading_ids: list[int] = Field(..., description="IDs of headings included in this prompt")


class GeneratePromptsResponse(BaseModel):
    """Response for the prompt generation endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompts": [
                    {
                        "prompt_index": 0,
                        "content": "Summarize the following sections...",
                        "heading_ids": [123, 124, 125],
                    }
                ]
            }
        }
    )

    prompts: list[PromptResponse] = Field(..., description="List of assembled prompt batches")


class SubmitResponseRequest(BaseModel):
    """Request for submitting LLM response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt_index": 0,
                "response_json": '[{"id": 123, "summary": "..."}]',
            }
        }
    )

    prompt_index: int = Field(..., description="Index of the prompt this response is for")
    response_json: str = Field(..., description="Raw JSON response from the LLM")


class SubmitResponseResponse(BaseModel):
    """Response for submitting LLM response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "summaries_saved": 3,
                "errors": [],
            }
        }
    )

    success: bool = Field(..., description="Whether processing was successful")
    summaries_saved: int = Field(..., description="Number of summaries successfully parsed and saved")
    errors: list[str] = Field(default_factory=list, description="List of errors or warnings encountered")


class SummarySection(BaseModel):
    """A single summary section for a work."""

    chunk_id: int = Field(..., description="ID of the heading chunk")
    heading: str = Field(..., description="Heading title")
    summary_content: str = Field(..., description="The generated summary text")
    start_line: int = Field(..., description="Starting line in original work")
    end_line: int = Field(..., description="Ending line in original work")


class WorkSummaryResponse(BaseModel):
    """Response for full work summary."""

    work_id: int = Field(..., description="ID of the work")
    work_title: str = Field(..., description="Title of the work")
    sections: list[SummarySection] = Field(..., description="List of summary sections")


class WorkSummaryListItem(BaseModel):
    """Item for work summary list."""

    work_id: int = Field(..., description="ID of the work")
    title: str = Field(..., description="Title of the work")
    summary_count: int = Field(..., description="Number of summaries generated for this work")
    last_updated: datetime = Field(..., description="Timestamp of most recent summary update")


class WorkSummaryListResponse(BaseModel):
    """Response for work summary list."""

    works: list[WorkSummaryListItem] = Field(..., description="List of works with summaries")


class SummarizeSettingsSchema(BaseModel):
    """Schema for summarization settings."""

    min_heading_word_count: int = Field(..., description="Min words in heading to summarize")
    max_total_heading_words: int = Field(..., description="Max total words in combined headings")
    dense_top_k: int = Field(..., description="Top K for dense retrieval")
    lexical_top_k: int = Field(..., description="Top K for lexical retrieval")
    rrf_k: int = Field(..., description="RRF k constant")
    rrf_top_k: int = Field(..., description="Top K after RRF")
    mmr_lambda: float = Field(..., description="MMR lambda diversity parameter")
    mmr_top_n: int = Field(..., description="Final number of chunks to select via MMR")
    max_llm_calls: int = Field(..., description="Max LLM calls per work")
    max_tokens_per_call: int = Field(..., description="Max tokens per call")
    tokens_per_word: float = Field(..., description="Tokens per word conversion factor")
    h1_h2_min_chunks: int = Field(..., description="Min chunks for H1/H2")
    h3_min_chunks: int = Field(..., description="Min chunks for H3")
