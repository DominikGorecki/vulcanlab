"""
Pydantic schemas for RAG query management endpoints.

These schemas support the query listing, expansion, retrieval,
consolidation, and augmentation workflows.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Query Listing Schemas
# ============================================================================

class QueryListItem(BaseModel):
    """A query item in the list view."""

    id: int = Field(..., description="Query ID")
    original_query: str = Field(..., description="Original query text")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    status: str = Field(
        ...,
        description="Current status: needs_embeddings, needs_retrieval, needs_consolidation, ready"
    )
    intent: Optional[str] = Field(None, description="Query intent")
    entities_count: int = Field(0, description="Number of extracted entities")


class QueryListResponse(BaseModel):
    """Response containing list of queries."""

    queries: list[QueryListItem] = Field(..., description="List of queries")
    total: int = Field(..., description="Total number of queries")


class QueryDetailResponse(BaseModel):
    """Detailed query information."""

    id: int = Field(..., description="Query ID")
    original_query: str = Field(..., description="Original query text")
    expanded_queries: Optional[list[str]] = Field(None, description="Expanded query variations")
    hyde_answer: Optional[str] = Field(None, description="Hypothetical answer")
    intent: Optional[str] = Field(None, description="Query intent")
    entities: Optional[list[str]] = Field(None, description="Extracted entities")
    vector_status: str = Field(..., description="Vectorization status")
    has_retrieved_context: bool = Field(..., description="Whether retrieval has been run")
    has_clean_context: bool = Field(..., description="Whether consolidation has been run")
    clean_retrieval_context: Optional[list[dict[str, Any]]] = Field(None, description="Clean retrieval context")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class QueryUpdateRequest(BaseModel):
    """Request to update query fields."""

    expanded_queries: Optional[list[str]] = Field(None, description="Expanded query variations")
    hyde_answer: Optional[str] = Field(None, description="Hypothetical answer")
    intent: Optional[str] = Field(None, description="Query intent")
    entities: Optional[list[str]] = Field(None, description="Extracted entities")
    clean_retrieval_context: Optional[list[dict[str, Any]]] = Field(None, description="Clean retrieval context")


# ============================================================================
# Query Expansion Schemas
# ============================================================================

class ExpansionPromptRequest(BaseModel):
    """Request for generating expansion prompt."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What is working memory?",
                "n": 3,
            }
        }
    )

    query: str = Field(
        ...,
        description="The query to expand",
        min_length=1,
        max_length=2000,
    )
    n: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of alternative queries to generate"
    )


class ExpansionPromptResponse(BaseModel):
    """Response containing the expansion prompt."""

    prompt: str = Field(..., description="The generated prompt for LLM")
    query: str = Field(..., description="The original query")
    n: int = Field(..., description="Number of alternatives requested")


class ExpansionRunRequest(BaseModel):
    """Request to run full expansion with LLM."""

    query: str = Field(
        ...,
        description="The query to expand",
        min_length=1,
        max_length=2000
    )
    n: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of alternative queries to generate"
    )


class ExpansionRunResponse(BaseModel):
    """Response after running expansion."""

    query_id: int = Field(..., description="ID of the created query record")
    original_query: str = Field(..., description="The original query")
    expanded_queries: list[str] = Field(..., description="Generated alternative queries")
    hyde_answer: str = Field(..., description="Hypothetical answer")
    intent: str = Field(..., description="Query intent")
    entities: list[str] = Field(..., description="Extracted entities")
    message: str = Field(..., description="Success message")


class ExpansionManualRequest(BaseModel):
    """Request to save manually-run expansion response."""

    query: str = Field(
        ...,
        description="The original query",
        min_length=1,
        max_length=2000
    )
    response_text: str = Field(
        ...,
        description="The LLM response text to parse",
        min_length=1
    )


class ExpansionManualResponse(BaseModel):
    """Response after saving manual expansion."""

    query_id: int = Field(..., description="ID of the created query record")
    message: str = Field(..., description="Success message")


# ============================================================================
# Query Operation Schemas (Embed, Retrieve, Consolidate)
# ============================================================================

class EmbedResponse(BaseModel):
    """Response after embedding a query."""

    query_id: int = Field(..., description="Query ID")
    total_embeddings: int = Field(..., description="Number of embeddings generated")
    original_count: int = Field(..., description="Original query embedding count")
    mqe_count: int = Field(..., description="MQE queries embedding count")
    hyde_count: int = Field(..., description="HyDE answer embedding count")
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Status message")


class RetrieveOperationResponse(BaseModel):
    """Response after running retrieval."""

    query_id: int = Field(..., description="Query ID")
    total_dense_candidates: int = Field(..., description="Dense search candidates")
    total_lexical_candidates: int = Field(..., description="Lexical search candidates")
    rrf_candidates: int = Field(..., description="RRF fusion candidates")
    final_count: int = Field(..., description="Final result count")
    message: str = Field(..., description="Status message")


class ConsolidateResponse(BaseModel):
    """Response after running consolidation."""

    query_id: int = Field(..., description="Query ID")
    original_count: int = Field(..., description="Original context count")
    consolidated_count: int = Field(..., description="Consolidated group count")
    message: str = Field(..., description="Status message")


# ============================================================================
# Augmentation Schemas
# ============================================================================

class AugmentPromptResponse(BaseModel):
    """Response containing the augmented prompt."""

    query_id: int = Field(..., description="Query ID")
    original_query: str = Field(..., description="The original query")
    prompt: str = Field(..., description="The generated augmented prompt")
    context_count: int = Field(..., description="Number of context items included")


class AugmentRunRequest(BaseModel):
    """Request to run augmented prompt with LLM."""

    force: bool = Field(
        default=False,
        description="Force regeneration even if result exists"
    )


class AugmentRunResponse(BaseModel):
    """Response after running augmented prompt."""

    query_id: int = Field(..., description="Query ID")
    result_id: int = Field(..., description="ID of the saved result")
    response_text: str = Field(..., description="The LLM response")
    message: str = Field(..., description="Status message")


class AugmentManualRequest(BaseModel):
    """Request to save manually-run augmented response."""

    response_text: str = Field(
        ...,
        description="The LLM response text",
        min_length=1
    )


class AugmentManualResponse(BaseModel):
    """Response after saving manual augmented response."""

    query_id: int = Field(..., description="Query ID")
    result_id: int = Field(..., description="ID of the saved result")
    message: str = Field(..., description="Success message")


# ============================================================================
# Result Schemas
# ============================================================================

class ResultItem(BaseModel):
    """A result item."""

    id: int = Field(..., description="Result ID")
    query_id: int = Field(..., description="Associated query ID")
    response_text: str = Field(..., description="The LLM response")
    created_at: datetime = Field(..., description="Creation timestamp")


class ResultListResponse(BaseModel):
    """Response containing list of results for a query."""

    query_id: int = Field(..., description="Query ID")
    results: list[ResultItem] = Field(..., description="List of results")
    total: int = Field(..., description="Total number of results")
