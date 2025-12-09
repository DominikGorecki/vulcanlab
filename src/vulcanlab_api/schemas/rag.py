"""
Pydantic schemas for RAG (Retrieval-Augmented Generation) router.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RAGQueryRequest(BaseModel):
    """Request for a RAG query."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What is cognitive load theory and how does it affect learning?",
                "top_k": 5,
                "rerank": True,
                "expand_query": True,
                "model": "gpt-4o",
            }
        }
    )

    query: str = Field(
        ...,
        description="User's question or query",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of chunks to retrieve",
    )
    rerank: bool = Field(
        default=True,
        description="Whether to rerank retrieved results",
    )
    expand_query: bool = Field(
        default=True,
        description="Whether to expand the query with variations",
    )
    model: str | None = Field(
        default=None,
        description="LLM model for generation",
    )
    work_ids: list[str] | None = Field(
        default=None,
        description="Filter to specific works (optional)",
    )


class SourceChunk(BaseModel):
    """A source chunk used in the response."""

    chunk_id: str = Field(..., description="Chunk identifier")
    title: str | None = Field(None, description="Section title")
    content: str = Field(..., description="Chunk content")
    score: float = Field(..., description="Relevance score")
    work_id: str | None = Field(None, description="Work identifier")


class TokenUsage(BaseModel):
    """Token usage statistics."""

    prompt: int = Field(..., description="Prompt tokens")
    completion: int = Field(..., description="Completion tokens")
    total: int = Field(..., description="Total tokens")


class RAGQueryResponse(BaseModel):
    """Response for a RAG query."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What is cognitive load theory?",
                "answer": "Cognitive load theory, developed by John Sweller, suggests that...",
                "sources": [
                    {
                        "chunk_id": "chunk_001",
                        "title": "Cognitive Load Theory",
                        "content": "Cognitive load theory is...",
                        "score": 0.92,
                        "work_id": "work_001",
                    }
                ],
                "model": "gpt-4o",
                "tokens_used": {"prompt": 1500, "completion": 250, "total": 1750},
                "confidence": 0.85,
            }
        }
    )

    query: str = Field(
        ...,
        description="Original query",
    )
    answer: str = Field(
        ...,
        description="Generated answer",
    )
    sources: list[dict[str, Any]] = Field(
        ...,
        description="Source chunks used",
    )
    model: str = Field(
        ...,
        description="Model used for generation",
    )
    tokens_used: dict[str, int] = Field(
        default_factory=dict,
        description="Token usage statistics",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score",
    )


class RetrieveRequest(BaseModel):
    """Request to retrieve relevant chunks."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What is working memory?",
                "top_k": 10,
                "rerank": True,
            }
        }
    )

    query: str = Field(
        ...,
        description="Query text",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of chunks to retrieve",
    )
    rerank: bool = Field(
        default=True,
        description="Whether to rerank results",
    )
    work_ids: list[str] | None = Field(
        default=None,
        description="Filter to specific works",
    )


class RetrievedChunk(BaseModel):
    """A retrieved chunk with metadata."""

    chunk_id: str = Field(..., description="Chunk identifier")
    content: str = Field(..., description="Chunk content")
    score: float = Field(..., description="Relevance score")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Chunk metadata",
    )


class RetrieveResponse(BaseModel):
    """Response containing retrieved chunks."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What is working memory?",
                "chunks": [
                    {
                        "chunk_id": "chunk_001",
                        "content": "Working memory is a cognitive system...",
                        "score": 0.95,
                        "metadata": {"work_id": "work_001", "heading": "Working Memory"},
                    }
                ],
                "total_retrieved": 1,
                "reranked": True,
            }
        }
    )

    query: str = Field(
        ...,
        description="Original query",
    )
    chunks: list[dict[str, Any]] = Field(
        ...,
        description="Retrieved chunks",
    )
    total_retrieved: int = Field(
        ...,
        description="Number of chunks retrieved",
    )
    reranked: bool = Field(
        ...,
        description="Whether results were reranked",
    )


class ExpandQueryRequest(BaseModel):
    """Request to expand a query."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "cognitive load",
                "num_variations": 4,
            }
        }
    )

    query: str = Field(
        ...,
        description="Original query to expand",
    )
    num_variations: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Number of variations to generate",
    )


class ExpandQueryResponse(BaseModel):
    """Response containing expanded queries."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "original_query": "cognitive load",
                "expanded_queries": [
                    "cognitive load",
                    "What is cognitive load theory?",
                    "How does cognitive load affect learning?",
                    "Types of cognitive load in education",
                ],
                "total_variations": 4,
            }
        }
    )

    original_query: str = Field(
        ...,
        description="Original query",
    )
    expanded_queries: list[str] = Field(
        ...,
        description="List of query variations",
    )
    total_variations: int = Field(
        ...,
        description="Number of variations generated",
    )


class AugmentRequest(BaseModel):
    """Request to augment content."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Cognitive load refers to...",
                "context_type": "related",
            }
        }
    )

    content: str = Field(
        ...,
        description="Content to augment",
    )
    context_type: str = Field(
        default="related",
        description="Type of context to add: related, citations, definitions",
    )


class ContextItem(BaseModel):
    """An item of context added during augmentation."""

    source: str = Field(..., description="Source chunk ID")
    relevance: float = Field(..., description="Relevance score")
    snippet: str = Field(..., description="Content snippet")


class AugmentResponse(BaseModel):
    """Response containing augmented content."""

    original_content: str = Field(
        ...,
        description="Original content",
    )
    augmented_content: str = Field(
        ...,
        description="Content with added context",
    )
    context_added: list[dict[str, Any]] = Field(
        ...,
        description="Context items that were added",
    )


class GenerateRequest(BaseModel):
    """Request to generate a response from context."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Summarize the key points about memory",
                "context_chunks": ["chunk_001", "chunk_002", "chunk_003"],
                "model": "gpt-4o",
                "temperature": 0.7,
            }
        }
    )

    query: str = Field(
        ...,
        description="User query",
    )
    context_chunks: list[str] = Field(
        ...,
        description="Pre-retrieved context chunk IDs",
    )
    model: str | None = Field(
        default=None,
        description="LLM model to use",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Generation temperature",
    )


class GenerateResponse(BaseModel):
    """Response containing generated text."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Summarize the key points about memory",
                "response": "Based on the provided context, the key points about memory are...",
                "model": "gpt-4o",
                "tokens_used": {"prompt": 1000, "completion": 200, "total": 1200},
                "context_chunks_used": 3,
            }
        }
    )

    query: str = Field(
        ...,
        description="Original query",
    )
    response: str = Field(
        ...,
        description="Generated response",
    )
    model: str = Field(
        ...,
        description="Model used",
    )
    tokens_used: dict[str, int] = Field(
        default_factory=dict,
        description="Token usage statistics",
    )
    context_chunks_used: int = Field(
        ...,
        description="Number of context chunks used",
    )


