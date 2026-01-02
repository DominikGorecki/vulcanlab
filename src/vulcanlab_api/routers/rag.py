"""
RAG Router - Retrieval, Augmentation and Generation operations.

Endpoints for query management:
    GET  /rag/queries                      - List all queries with status info
    GET  /rag/queries/{id}                 - Get single query details
    PATCH /rag/queries/{id}                - Update query fields
    POST /rag/queries/{id}/embed           - Run vectorization
    POST /rag/queries/{id}/retrieve        - Run retrieval
    POST /rag/queries/{id}/consolidate     - Run consolidation
    GET  /rag/queries/{id}/augment/prompt  - Get augmented prompt
    POST /rag/queries/{id}/augment/run     - Run augmented prompt with LLM
    POST /rag/queries/{id}/augment/manual  - Save manually-run LLM response
    GET  /rag/queries/{id}/results         - List query results
    GET  /rag/queries/{id}/results/{id}    - Get specific result

Endpoints for query expansion:
    POST /rag/expansion/prompt             - Generate expansion prompt (no LLM)
    POST /rag/expansion/run                - Run full expansion with LLM
    POST /rag/expansion/manual             - Parse & save manual expansion response

Endpoints for automated RAG:
    POST /rag/auto                         - Run full automated RAG pipeline
"""

import logging
from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)

from vulcanlab.data.database import get_session
from vulcanlab.data.models import Query, Result
from vulcanlab.retrieval import (
    vectorize_query,
    generate_expansion_prompt,
    parse_expansion_response,
    save_expansion_to_db,
    expand_query,
    retrieve,
)
from vulcanlab.augmentation import consolidate_context, generate_augmented_prompt
from vulcanlab.ai.config import ModelTier
from vulcanlab.ai.llm_factory import create_langchain_chat

from vulcanlab_api.schemas.rag_queries import (
    QueryListItem,
    QueryListResponse,
    QueryDetailResponse,
    QueryUpdateRequest,
    ExpansionPromptRequest,
    ExpansionPromptResponse,
    ExpansionRunRequest,
    ExpansionRunResponse,
    ExpansionManualRequest,
    ExpansionManualResponse,
    EmbedResponse,
    RetrieveOperationResponse,
    ConsolidateResponse,
    AugmentPromptResponse,
    AugmentRunRequest,
    AugmentRunResponse,
    AugmentManualRequest,
    AugmentManualResponse,
    ResultListResponse,
    ResultItem,
    AutoRAGRequest,
    AutoRAGResponse,
)

router = APIRouter()


def _get_query_status(query: Query) -> str:
    """Determine the current status of a query."""
    if query.vector_status == "to_vec":
        return "needs_embeddings"
    if not query.retrieved_context:
        return "needs_retrieval"
    if not query.clean_retrieval_context:
        return "needs_consolidation"
    return "ready"


# ============================================================================
# Query Listing Endpoints
# ============================================================================

@router.get(
    "/queries",
    response_model=QueryListResponse,
    summary="List all queries",
    description="List all queries with their current status.",
)
async def list_queries() -> QueryListResponse:
    """List all queries with status information."""
    with get_session() as session:
        queries = session.query(Query).order_by(Query.created_at.desc()).all()

        items = []
        for q in queries:
            items.append(QueryListItem(
                id=q.id,
                original_query=q.original_query,
                created_at=q.created_at,
                updated_at=q.updated_at,
                status=_get_query_status(q),
                intent=q.intent,
                entities_count=len(q.entities) if q.entities else 0
            ))

        return QueryListResponse(queries=items, total=len(items))


@router.get(
    "/queries/{query_id}",
    response_model=QueryDetailResponse,
    summary="Get query details",
    description="Get detailed information about a specific query.",
)
async def get_query(query_id: int) -> QueryDetailResponse:
    """Get detailed query information."""
    with get_session() as session:
        query = session.query(Query).filter(Query.id == query_id).first()

        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with ID {query_id} not found"
            )

        return QueryDetailResponse(
            id=query.id,
            original_query=query.original_query,
            expanded_queries=query.expanded_queries,
            hyde_answer=query.hyde_answer,
            intent=query.intent,
            entities=query.entities,
            vector_status=query.vector_status,
            has_retrieved_context=bool(query.retrieved_context),
            has_clean_context=bool(query.clean_retrieval_context),
            clean_retrieval_context=query.clean_retrieval_context,
            created_at=query.created_at,
            updated_at=query.updated_at
        )


@router.patch(
    "/queries/{query_id}",
    response_model=QueryDetailResponse,
    summary="Update query fields",
    description="Update editable fields of a query.",
)
async def update_query(query_id: int, request: QueryUpdateRequest) -> QueryDetailResponse:
    """Update query fields."""
    with get_session() as session:
        query = session.query(Query).filter(Query.id == query_id).first()

        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with ID {query_id} not found"
            )

        if request.expanded_queries is not None:
            query.expanded_queries = request.expanded_queries
        
        if request.hyde_answer is not None:
            query.hyde_answer = request.hyde_answer
        
        if request.intent is not None:
            query.intent = request.intent
        
        if request.entities is not None:
            query.entities = request.entities
        
        if request.clean_retrieval_context is not None:
            query.clean_retrieval_context = request.clean_retrieval_context

        session.commit()
        session.refresh(query)

        return QueryDetailResponse(
            id=query.id,
            original_query=query.original_query,
            expanded_queries=query.expanded_queries,
            hyde_answer=query.hyde_answer,
            intent=query.intent,
            entities=query.entities,
            vector_status=query.vector_status,
            has_retrieved_context=bool(query.retrieved_context),
            has_clean_context=bool(query.clean_retrieval_context),
            clean_retrieval_context=query.clean_retrieval_context,
            created_at=query.created_at,
            updated_at=query.updated_at
        )


# ============================================================================
# Query Operations Endpoints
# ============================================================================

@router.post(
    "/queries/{query_id}/embed",
    response_model=EmbedResponse,
    summary="Embed query vectors",
    description="Generate embeddings for a query.",
)
async def embed_query(query_id: int) -> EmbedResponse:
    """Generate embeddings for a query."""
    try:
        result = vectorize_query(query_id=query_id, verbose=False)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Vectorization failed"
            )

        return EmbedResponse(
            query_id=result.query_id,
            total_embeddings=result.total_embeddings,
            original_count=result.original_count,
            mqe_count=result.mqe_count,
            hyde_count=result.hyde_count,
            success=True,
            message="Embeddings generated successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/queries/{query_id}/retrieve",
    response_model=RetrieveOperationResponse,
    summary="Run retrieval",
    description="Run dense + lexical retrieval with RRF fusion and reranking.",
)
async def retrieve_query(query_id: int, config_preset: str | None = None) -> RetrieveOperationResponse:
    """Run retrieval for a query."""
    try:
        result = retrieve(query_id=query_id, config_preset=config_preset, verbose=False)

        return RetrieveOperationResponse(
            query_id=result.query_id,
            total_dense_candidates=result.total_dense_candidates,
            total_lexical_candidates=result.total_lexical_candidates,
            rrf_candidates=result.rrf_candidates,
            final_count=result.final_count,
            message=f"Retrieved {result.final_count} chunks"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/queries/{query_id}/consolidate",
    response_model=ConsolidateResponse,
    summary="Run consolidation",
    description="Consolidate retrieved context by grouping and merging chunks.",
)
async def consolidate_query(query_id: int, config_preset: str | None = None) -> ConsolidateResponse:
    """Run consolidation for a query."""
    try:
        result = consolidate_context(query_id=query_id, config_preset=config_preset, verbose=False)

        return ConsolidateResponse(
            query_id=result.query_id,
            original_count=result.original_count,
            consolidated_count=result.consolidated_count,
            message=f"Consolidated {result.original_count} items into {result.consolidated_count} groups"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


# ============================================================================
# Augmentation Endpoints
# ============================================================================

@router.get(
    "/queries/{query_id}/augment/prompt",
    response_model=AugmentPromptResponse,
    summary="Get augmented prompt",
    description="Get the full augmented RAG prompt for a query.",
)
async def get_augment_prompt(
    query_id: int,
    top_n: int | None = None,
    config_preset: str | None = None
) -> AugmentPromptResponse:
    """Get the augmented prompt for a query."""
    try:
        prompt = generate_augmented_prompt(query_id=query_id, top_n=top_n, config_preset=config_preset)

        with get_session() as session:
            query = session.query(Query).filter(Query.id == query_id).first()
            context_count = len(query.clean_retrieval_context or [])

            # If top_n was not specified, get it from the config that was used
            if top_n is None:
                if config_preset:
                    from vulcanlab.utils.rag_config_loader import get_config_by_name
                    config = get_config_by_name(config_preset)
                else:
                    from vulcanlab.utils.rag_config_loader import get_default_config
                    config = get_default_config()
                actual_top_n = config["augmentation"]["top_n_contexts"]
            else:
                actual_top_n = top_n

            return AugmentPromptResponse(
                query_id=query_id,
                original_query=query.original_query,
                prompt=prompt,
                context_count=min(context_count, actual_top_n)
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/queries/{query_id}/augment/run",
    response_model=AugmentRunResponse,
    summary="Run augmented prompt",
    description="Run the augmented prompt with LLM and save result.",
)
async def run_augment(
    query_id: int,
    request: AugmentRunRequest = AugmentRunRequest(),
    top_n: int | None = None,
    config_preset: str | None = None
) -> AugmentRunResponse:
    """Run augmented prompt with LLM and save result."""
    from vulcanlab.ai.config import LLMSettings
    from vulcanlab_api.routers.result_models import get_or_create_result_model

    try:
        # Generate the prompt
        prompt = generate_augmented_prompt(query_id=query_id, top_n=top_n, config_preset=config_preset)

        # Create LangChain chat with FULL model and search
        stack = create_langchain_chat(tier=ModelTier.FULL, search=True, temperature=0.2)

        # Get the model name from config
        llm_settings = LLMSettings()
        model_name = llm_settings.get_model(ModelTier.FULL)
        logger.info(f"Running augmented prompt with model: {model_name}")

        # Call LLM
        response = stack.chat.invoke(prompt)

        # Handle both string and list responses (some models return list of content blocks)
        if isinstance(response.content, list):
            response_text = response.content[0].get('text', '') if response.content else ''
        else:
            response_text = response.content

        # Save result to database with model tracking
        with get_session() as session:
            # Get or create model
            model = get_or_create_result_model(model_name, session)
            logger.info(f"Automatic result using model '{model.name}' (id={model.id})")

            result = Result(
                query_id=query_id,
                response_text=response_text,
                model_id=model.id
            )
            session.add(result)
            session.commit()
            result_id = result.id

        return AugmentRunResponse(
            query_id=query_id,
            result_id=result_id,
            response_text=response_text,
            model_name=model_name,
            message="Augmented prompt executed and result saved"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/queries/{query_id}/augment/manual",
    response_model=AugmentManualResponse,
    summary="Save manual augmented response",
    description="Save a manually-run LLM response for an augmented prompt.",
)
async def save_manual_augment(
    query_id: int,
    request: AugmentManualRequest
) -> AugmentManualResponse:
    """Save manually-run augmented response."""
    from vulcanlab_api.routers.result_models import get_or_create_result_model

    with get_session() as session:
        # Verify query exists
        query = session.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with ID {query_id} not found"
            )

        # Determine model_id
        model_id = None
        model_name = None

        if request.new_model_name:
            # Create or get model by name
            model = get_or_create_result_model(request.new_model_name, session)
            model_id = model.id
            model_name = model.name
            logger.info(f"Manual result using new model '{model_name}' (id={model_id})")
        elif request.model_id:
            # Verify model exists
            from vulcanlab.data.models.result_model import ResultModel
            model = session.query(ResultModel).filter(ResultModel.id == request.model_id).first()
            if not model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Model with ID {request.model_id} not found"
                )
            model_id = model.id
            model_name = model.name
            logger.info(f"Manual result using existing model '{model_name}' (id={model_id})")
        else:
            logger.info("Manual result saved without model association")

        # Save result
        result = Result(
            query_id=query_id,
            response_text=request.response_text,
            model_id=model_id
        )
        session.add(result)
        session.commit()

        return AugmentManualResponse(
            query_id=query_id,
            result_id=result.id,
            model_name=model_name or "Unspecified",
            message="Manual response saved successfully"
        )


# ============================================================================
# Query Expansion Endpoints
# ============================================================================

@router.post(
    "/expansion/prompt",
    response_model=ExpansionPromptResponse,
    summary="Generate expansion prompt",
    description="Generate the expansion prompt without calling LLM.",
)
async def get_expansion_prompt(request: ExpansionPromptRequest) -> ExpansionPromptResponse:
    """Generate expansion prompt for manual LLM execution."""
    prompt = generate_expansion_prompt(query=request.query, n=request.n)

    return ExpansionPromptResponse(
        prompt=prompt,
        query=request.query,
        n=request.n
    )


@router.post(
    "/expansion/run",
    response_model=ExpansionRunResponse,
    summary="Run query expansion",
    description="Run full query expansion with LLM.",
)
async def run_expansion(request: ExpansionRunRequest) -> ExpansionRunResponse:
    """Run full query expansion pipeline."""
    try:
        result = expand_query(query=request.query, n=request.n, verbose=False)

        return ExpansionRunResponse(
            query_id=result.query_id,
            original_query=result.original_query,
            expanded_queries=result.expanded_queries,
            hyde_answer=result.hyde_answer,
            intent=result.intent,
            entities=result.entities,
            message="Query expanded and saved successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/expansion/manual",
    response_model=ExpansionManualResponse,
    summary="Save manual expansion",
    description="Parse and save manually-run expansion response.",
)
async def save_manual_expansion(request: ExpansionManualRequest) -> ExpansionManualResponse:
    """Parse and save manually-run expansion response."""
    try:
        # Parse the response
        parsed = parse_expansion_response(request.response_text)

        # Save to database
        query_id = save_expansion_to_db(request.query, parsed)

        return ExpansionManualResponse(
            query_id=query_id,
            message="Expansion parsed and saved successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Auto RAG Endpoint
# ============================================================================

@router.post(
    "/auto",
    response_model=AutoRAGResponse,
    summary="Run automated RAG pipeline",
    description="Automatically run the complete RAG preparation pipeline: expansion, embedding, retrieval, and consolidation.",
)
async def run_auto_rag(request: AutoRAGRequest) -> AutoRAGResponse:
    """Run the full automated RAG pipeline.

    This endpoint orchestrates the complete RAG preparation process:
    1. Expand query using LLM (creates Query record)
    2. Generate embeddings for the query
    3. Retrieve relevant chunks
    4. Consolidate context

    On success, returns the query_id with status "ready".
    On failure, raises HTTPException with detail and failed_step.
    """
    logger.info(f"Starting automated RAG pipeline for query: {request.query[:100]}...")

    query_id = None

    # Step 1: Expand query (creates Query record)
    try:
        logger.info("Step 1/4: Expanding query...")
        result = expand_query(query=request.query, n=3, verbose=False)
        query_id = result.query_id
        logger.info(f"Query expanded successfully. Query ID: {query_id}")
    except ValueError as e:
        logger.error(f"Query expansion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query expansion failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during query expansion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query expansion failed: {str(e)}"
        )

    # Step 2: Generate embeddings
    try:
        logger.info(f"Step 2/4: Generating embeddings for query {query_id}...")
        vectorize_query(query_id=query_id, verbose=False)
        logger.info(f"Embeddings generated successfully for query {query_id}")
    except Exception as e:
        logger.error(f"Embedding generation failed for query {query_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {str(e)}"
        )

    # Step 3: Retrieve chunks
    try:
        logger.info(f"Step 3/4: Retrieving chunks for query {query_id}...")
        retrieve(query_id=query_id, config_preset=None, verbose=False)
        logger.info(f"Retrieval completed successfully for query {query_id}")
    except Exception as e:
        logger.error(f"Retrieval failed for query {query_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval failed: {str(e)}"
        )

    # Step 4: Consolidate context
    try:
        logger.info(f"Step 4/4: Consolidating context for query {query_id}...")
        consolidate_context(query_id=query_id, config_preset=None, verbose=False)
        logger.info(f"Context consolidated successfully for query {query_id}")
    except Exception as e:
        logger.error(f"Consolidation failed for query {query_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Consolidation failed: {str(e)}"
        )

    logger.info(f"Automated RAG pipeline completed successfully for query {query_id}")

    return AutoRAGResponse(
        query_id=query_id,
        status="ready",
        message="Query processed successfully through all pipeline steps"
    )


# ============================================================================
# Result Endpoints
# ============================================================================

@router.get(
    "/queries/{query_id}/results",
    response_model=ResultListResponse,
    summary="List query results",
    description="List all generated results for a query.",
)
async def list_results(query_id: int) -> ResultListResponse:
    """List all results for a query."""
    from vulcanlab.data.models.result_model import ResultModel

    with get_session() as session:
        # Verify query exists
        query = session.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with ID {query_id} not found"
            )

        # Get results with LEFT JOIN to result_models for denormalization
        results = session.query(Result, ResultModel.name)\
            .outerjoin(ResultModel, Result.model_id == ResultModel.id)\
            .filter(Result.query_id == query_id)\
            .order_by(Result.created_at.desc())\
            .all()

        items = [
            ResultItem(
                id=r.id,
                query_id=r.query_id,
                response_text=r.response_text,
                model_name=model_name or "Unspecified",
                created_at=r.created_at
            )
            for r, model_name in results
        ]

        return ResultListResponse(
            query_id=query_id,
            results=items,
            total=len(items)
        )


@router.get(
    "/queries/{query_id}/results/{result_id}",
    response_model=ResultItem,
    summary="Get result details",
    description="Get a specific result.",
)
async def get_result(query_id: int, result_id: int) -> ResultItem:
    """Get a specific result."""
    from vulcanlab.data.models.result_model import ResultModel

    with get_session() as session:
        # Get result with LEFT JOIN to result_models
        result_data = session.query(Result, ResultModel.name)\
            .outerjoin(ResultModel, Result.model_id == ResultModel.id)\
            .filter(Result.id == result_id, Result.query_id == query_id)\
            .first()

        if not result_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Result with ID {result_id} not found for query {query_id}"
            )

        result, model_name = result_data

        return ResultItem(
            id=result.id,
            query_id=result.query_id,
            response_text=result.response_text,
            model_name=model_name or "Unspecified",
            created_at=result.created_at
        )
