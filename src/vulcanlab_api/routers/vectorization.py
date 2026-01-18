"""
Vectorization Router - Embedding generation operations.

Endpoints:
    POST /vec/chunks        - Vectorize document chunks
    POST /vec/query         - Vectorize a query string
    GET  /vec/models        - List available embedding models
    GET  /vec/status/{id}   - Get vectorization job status
"""

from fastapi import APIRouter, HTTPException, status

from vulcanlab_api.schemas.vectorization import (
    EmbeddingModelsResponse,
    VectorizeChunksRequest,
    VectorizeChunksResponse,
    VectorizeQueryRequest,
    VectorizeQueryResponse,
    VectorizationStatusResponse,
    EligibleChunksResponse,
    VectorizeAllRequest,
    VectorizeAllResponse,
)

router = APIRouter()


@router.get(
    "/models",
    response_model=EmbeddingModelsResponse,
    summary="List embedding models",
    description="Get a list of available embedding models and their specifications.",
    responses={
        200: {
            "description": "Models listed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "models": [
                            {
                                "id": "text-embedding-3-small",
                                "provider": "openai",
                                "dimensions": 1536,
                                "max_tokens": 8191,
                            }
                        ],
                        "default_model": "text-embedding-3-small",
                    }
                }
            },
        }
    },
)
async def list_embedding_models() -> EmbeddingModelsResponse:
    """
    List available embedding models.
    
    Returns model specifications including:
    - Dimensions
    - Max input tokens
    - Provider information
    """
    return EmbeddingModelsResponse(
        models=[
            {
                "id": "text-embedding-3-small",
                "provider": "openai",
                "dimensions": 1536,
                "max_tokens": 8191,
                "description": "OpenAI's small embedding model - good balance of speed and quality",
            },
            {
                "id": "text-embedding-3-large",
                "provider": "openai",
                "dimensions": 3072,
                "max_tokens": 8191,
                "description": "OpenAI's large embedding model - highest quality",
            },
            {
                "id": "text-embedding-004",
                "provider": "google",
                "dimensions": 768,
                "max_tokens": 2048,
                "description": "Google's text embedding model",
            },
        ],
        default_model="text-embedding-3-small",
    )


@router.post(
    "/chunks",
    response_model=VectorizeChunksResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Vectorize chunks",
    description="Generate embeddings for document chunks and store them.",
    responses={
        202: {"description": "Vectorization job started"},
        400: {"description": "Invalid chunk IDs"},
        503: {"description": "Embedding service unavailable"},
    },
)
async def vectorize_chunks(request: VectorizeChunksRequest) -> VectorizeChunksResponse:
    """
    Generate embeddings for chunks.
    
    Processes chunks through the embedding model and stores
    the resulting vectors in the database.
    """
    # TODO: Implement using vulcanlab.vectorization.vect_chunks
    return VectorizeChunksResponse(
        job_id="vec_12345",
        status="queued",
        chunks_queued=len(request.chunk_ids),
        model=request.model or "text-embedding-3-small",
        message=f"Stub: Would vectorize {len(request.chunk_ids)} chunks",
    )


@router.post(
    "/query",
    response_model=VectorizeQueryResponse,
    summary="Vectorize query",
    description="Generate an embedding vector for a query string.",
    responses={
        200: {"description": "Query vectorized successfully"},
        503: {"description": "Embedding service unavailable"},
    },
)
async def vectorize_query(request: VectorizeQueryRequest) -> VectorizeQueryResponse:
    """
    Generate embedding for a query.
    
    Returns the embedding vector for use in similarity search.
    """
    # TODO: Implement using vulcanlab.vectorization or langchain embeddings
    return VectorizeQueryResponse(
        query=request.query,
        model=request.model or "text-embedding-3-small",
        dimensions=1536,
        embedding=[0.0] * 10,  # Stub - would be actual embedding
        message="Stub: Query embedding (truncated)",
    )


@router.get(
    "/status/{job_id}",
    response_model=VectorizationStatusResponse,
    summary="Get vectorization status",
    description="Check the status of a vectorization job.",
    responses={
        200: {"description": "Status retrieved successfully"},
        404: {"description": "Job not found"},
    },
)
async def get_vectorization_status(job_id: str) -> VectorizationStatusResponse:
    """
    Get vectorization job status.
    
    Returns progress and results for async vectorization jobs.
    """
    # TODO: Implement job status tracking
    return VectorizationStatusResponse(
        job_id=job_id,
        status="completed",
        progress=100,
        chunks_processed=10,
        chunks_total=10,
        message="Stub: Vectorization complete",
    )


@router.get(
    "/eligible",
    response_model=EligibleChunksResponse,
    summary="Get eligible chunks count",
    description="Returns the count of chunks eligible for vectorization across all works.",
)
async def get_eligible_count() -> EligibleChunksResponse:
    """Get count of chunks eligible for vectorization (across all works)."""
    from vulcanlab.vectorization.vect_chunks import get_eligible_chunks_count
    
    try:
        count = get_eligible_chunks_count(work_id=None)
        return EligibleChunksResponse(count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get eligible chunks count: {e}"
        )


@router.post(
    "/vectorize",
    response_model=VectorizeAllResponse,
    summary="Vectorize chunks",
    description="Vectorize eligible chunks with optional limit. Runs synchronously.",
)
async def vectorize_all_chunks(request: VectorizeAllRequest) -> VectorizeAllResponse:
    """Vectorize chunks (all or limited number)."""
    from vulcanlab.vectorization import vectorize_chunks, DEFAULT_BATCH_SIZE
    
    try:
        # Use batch_size from request if provided, otherwise use default
        batch_size = request.batch_size or DEFAULT_BATCH_SIZE
        
        result = vectorize_chunks(
            work_id=request.work_id,  # None for all works
            limit=request.limit,
            batch_size=batch_size,
            verbose=True
        )
        
        # Format errors for response
        errors = None
        if result.errors:
            errors = [{"chunk_id": chunk_id, "error": error} for chunk_id, error in result.errors]
        
        return VectorizeAllResponse(
            total_eligible=result.total_eligible,
            processed=result.processed,
            success=result.success,
            failed=result.failed,
            errors=errors
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to vectorize chunks: {e}"
        )


