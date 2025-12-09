"""
Pydantic schemas for Vectorization router.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EmbeddingModelInfo(BaseModel):
    """Information about an embedding model."""

    id: str = Field(..., description="Model identifier")
    provider: str = Field(..., description="Provider (openai, google, etc.)")
    dimensions: int = Field(..., description="Embedding dimensions")
    max_tokens: int = Field(..., description="Maximum input tokens")
    description: str | None = Field(None, description="Model description")


class EmbeddingModelsResponse(BaseModel):
    """Response listing available embedding models."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "models": [
                    {
                        "id": "text-embedding-3-small",
                        "provider": "openai",
                        "dimensions": 1536,
                        "max_tokens": 8191,
                        "description": "OpenAI's small embedding model",
                    },
                    {
                        "id": "text-embedding-3-large",
                        "provider": "openai",
                        "dimensions": 3072,
                        "max_tokens": 8191,
                        "description": "OpenAI's large embedding model",
                    },
                ],
                "default_model": "text-embedding-3-small",
            }
        }
    )

    models: list[dict[str, Any]] = Field(
        ...,
        description="List of available embedding models",
    )
    default_model: str = Field(
        ...,
        description="Default model ID",
    )


class VectorizeChunksRequest(BaseModel):
    """Request to vectorize chunks."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_ids": ["chunk_001", "chunk_002", "chunk_003"],
                "model": "text-embedding-3-small",
                "store": True,
            }
        }
    )

    chunk_ids: list[str] = Field(
        ...,
        description="List of chunk IDs to vectorize",
    )
    model: str | None = Field(
        default=None,
        description="Embedding model to use (defaults to configured model)",
    )
    store: bool = Field(
        default=True,
        description="Whether to store embeddings in database",
    )


class VectorizeChunksResponse(BaseModel):
    """Response for chunk vectorization job."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "vec_12345",
                "status": "queued",
                "chunks_queued": 3,
                "model": "text-embedding-3-small",
            }
        }
    )

    job_id: str = Field(
        ...,
        description="Unique job identifier",
    )
    status: str = Field(
        ...,
        description="Job status",
    )
    chunks_queued: int = Field(
        ...,
        description="Number of chunks queued",
    )
    model: str = Field(
        ...,
        description="Embedding model being used",
    )
    message: str | None = Field(default=None)


class VectorizeQueryRequest(BaseModel):
    """Request to vectorize a query string."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What is cognitive load theory?",
                "model": "text-embedding-3-small",
            }
        }
    )

    query: str = Field(
        ...,
        description="Query text to vectorize",
    )
    model: str | None = Field(
        default=None,
        description="Embedding model to use",
    )


class VectorizeQueryResponse(BaseModel):
    """Response containing query embedding."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What is cognitive load theory?",
                "model": "text-embedding-3-small",
                "dimensions": 1536,
                "embedding": [0.01, -0.02, 0.03],  # Truncated
                "message": "Note: embedding truncated in example",
            }
        }
    )

    query: str = Field(
        ...,
        description="Original query text",
    )
    model: str = Field(
        ...,
        description="Model used for embedding",
    )
    dimensions: int = Field(
        ...,
        description="Embedding dimensions",
    )
    embedding: list[float] = Field(
        ...,
        description="Embedding vector (truncated in examples)",
    )
    message: str | None = Field(default=None)


class VectorizationStatusResponse(BaseModel):
    """Response for vectorization job status."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "vec_12345",
                "status": "completed",
                "progress": 100,
                "chunks_processed": 10,
                "chunks_total": 10,
                "message": "Vectorization complete",
            }
        }
    )

    job_id: str = Field(
        ...,
        description="Job identifier",
    )
    status: str = Field(
        ...,
        description="Current status: queued, processing, completed, failed",
    )
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Progress percentage",
    )
    chunks_processed: int = Field(
        default=0,
        description="Chunks processed so far",
    )
    chunks_total: int = Field(
        default=0,
        description="Total chunks to process",
    )
    message: str | None = Field(default=None)


class EligibleChunksResponse(BaseModel):
    """Response for eligible chunks count."""
    
    count: int = Field(..., description="Number of eligible chunks")


class VectorizeAllRequest(BaseModel):
    """Request to vectorize chunks with optional limit."""
    
    limit: int | None = Field(None, description="Maximum number of chunks to vectorize (None for all)")
    work_id: int | None = Field(None, description="Work ID to filter by (None for all works)")


class VectorizeAllResponse(BaseModel):
    """Response for vectorization operation."""
    
    total_eligible: int = Field(..., description="Total number of eligible chunks")
    processed: int = Field(..., description="Number of chunks processed")
    success: int = Field(..., description="Number of chunks successfully vectorized")
    failed: int = Field(..., description="Number of chunks that failed")
    errors: list[dict] | None = Field(None, description="List of errors (chunk_id and error message)")


