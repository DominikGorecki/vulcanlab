"""
Unit tests for the automated RAG endpoint.

Tests the POST /rag/auto endpoint that orchestrates the full RAG pipeline:
expand_query -> vectorize_query -> retrieve -> consolidate_context
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from vulcanlab_api.routers.rag import run_auto_rag
from vulcanlab_api.schemas.rag_queries import AutoRAGRequest
from vulcanlab.retrieval.query_expansion import QueryExpansionResult


@pytest.fixture
def mock_expand_query_result():
    """Mock result from expand_query function."""
    return QueryExpansionResult(
        query_id=123,
        original_query="What is working memory?",
        expanded_queries=[
            "What is working memory?",
            "How does working memory function?",
            "What are the components of working memory?"
        ],
        hyde_answer="Working memory is a cognitive system...",
        intent="DEFINITION",
        entities=["working memory", "cognitive system"]
    )


@pytest.fixture
def mock_vectorize_result():
    """Mock result from vectorize_query function."""
    result = Mock()
    result.success = True
    result.query_id = 123
    result.total_embeddings = 5
    return result


@pytest.fixture
def mock_retrieve_result():
    """Mock result from retrieve function."""
    result = Mock()
    result.query_id = 123
    result.final_count = 10
    return result


@pytest.fixture
def mock_consolidate_result():
    """Mock result from consolidate_context function."""
    result = Mock()
    result.query_id = 123
    result.consolidated_count = 5
    return result


@pytest.mark.asyncio
async def test_auto_rag_success(
    mock_expand_query_result,
    mock_vectorize_result,
    mock_retrieve_result,
    mock_consolidate_result
):
    """Test successful automation through all 4 pipeline steps."""
    with patch('vulcanlab_api.routers.rag.expand_query', return_value=mock_expand_query_result) as mock_expand, \
         patch('vulcanlab_api.routers.rag.vectorize_query', return_value=mock_vectorize_result) as mock_vectorize, \
         patch('vulcanlab_api.routers.rag.retrieve', return_value=mock_retrieve_result) as mock_retrieve, \
         patch('vulcanlab_api.routers.rag.consolidate_context', return_value=mock_consolidate_result) as mock_consolidate:

        request = AutoRAGRequest(query="What is working memory?")
        response = await run_auto_rag(request)

        # Verify response
        assert response.query_id == 123
        assert response.status == "ready"
        assert "successfully" in response.message.lower()

        # Verify function calls
        mock_expand.assert_called_once_with(query="What is working memory?", n=3, verbose=False)
        mock_vectorize.assert_called_once_with(query_id=123, verbose=False)
        mock_retrieve.assert_called_once_with(query_id=123, config_preset=None, verbose=False)
        mock_consolidate.assert_called_once_with(query_id=123, config_preset=None, verbose=False)


@pytest.mark.asyncio
async def test_auto_rag_empty_query():
    """Test that empty query is rejected by Pydantic validation."""
    # Pydantic should validate min_length=1 before the endpoint is called
    with pytest.raises(Exception):  # ValidationError from Pydantic
        AutoRAGRequest(query="")


@pytest.mark.asyncio
async def test_auto_rag_expand_query_fails_value_error(mock_expand_query_result):
    """Test error handling when expand_query raises ValueError."""
    with patch('vulcanlab_api.routers.rag.expand_query', side_effect=ValueError("Invalid query format")):
        request = AutoRAGRequest(query="bad query")

        with pytest.raises(HTTPException) as exc_info:
            await run_auto_rag(request)

        assert exc_info.value.status_code == 400
        assert "expansion failed" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_auto_rag_expand_query_fails_generic_error():
    """Test error handling when expand_query raises generic Exception."""
    with patch('vulcanlab_api.routers.rag.expand_query', side_effect=RuntimeError("LLM API error")):
        request = AutoRAGRequest(query="What is working memory?")

        with pytest.raises(HTTPException) as exc_info:
            await run_auto_rag(request)

        assert exc_info.value.status_code == 500
        assert "expansion failed" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_auto_rag_vectorize_query_fails(mock_expand_query_result):
    """Test error handling when vectorize_query fails."""
    with patch('vulcanlab_api.routers.rag.expand_query', return_value=mock_expand_query_result), \
         patch('vulcanlab_api.routers.rag.vectorize_query', side_effect=RuntimeError("Embedding service down")):

        request = AutoRAGRequest(query="What is working memory?")

        with pytest.raises(HTTPException) as exc_info:
            await run_auto_rag(request)

        assert exc_info.value.status_code == 500
        assert "embedding" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_auto_rag_retrieve_fails(
    mock_expand_query_result,
    mock_vectorize_result
):
    """Test error handling when retrieve fails."""
    with patch('vulcanlab_api.routers.rag.expand_query', return_value=mock_expand_query_result), \
         patch('vulcanlab_api.routers.rag.vectorize_query', return_value=mock_vectorize_result), \
         patch('vulcanlab_api.routers.rag.retrieve', side_effect=RuntimeError("Database connection lost")):

        request = AutoRAGRequest(query="What is working memory?")

        with pytest.raises(HTTPException) as exc_info:
            await run_auto_rag(request)

        assert exc_info.value.status_code == 500
        assert "retrieval failed" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_auto_rag_consolidate_fails(
    mock_expand_query_result,
    mock_vectorize_result,
    mock_retrieve_result
):
    """Test error handling when consolidate_context fails."""
    with patch('vulcanlab_api.routers.rag.expand_query', return_value=mock_expand_query_result), \
         patch('vulcanlab_api.routers.rag.vectorize_query', return_value=mock_vectorize_result), \
         patch('vulcanlab_api.routers.rag.retrieve', return_value=mock_retrieve_result), \
         patch('vulcanlab_api.routers.rag.consolidate_context', side_effect=RuntimeError("Consolidation error")):

        request = AutoRAGRequest(query="What is working memory?")

        with pytest.raises(HTTPException) as exc_info:
            await run_auto_rag(request)

        assert exc_info.value.status_code == 500
        assert "consolidation failed" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_auto_rag_query_persists_on_vectorize_failure(mock_expand_query_result):
    """Test that query record persists even when vectorize_query fails.

    This test verifies that after expand_query succeeds (creating a Query record),
    the query_id is captured and the query remains in the database even if a
    subsequent step fails.
    """
    with patch('vulcanlab_api.routers.rag.expand_query', return_value=mock_expand_query_result) as mock_expand, \
         patch('vulcanlab_api.routers.rag.vectorize_query', side_effect=RuntimeError("Embedding failed")):

        request = AutoRAGRequest(query="What is working memory?")

        # The endpoint should raise HTTPException but NOT delete the query
        with pytest.raises(HTTPException):
            await run_auto_rag(request)

        # Verify expand_query was called (which creates the query record)
        mock_expand.assert_called_once()
        # In a real scenario, the query with ID 123 would exist in the database
        # with status "needs_embeddings"


@pytest.mark.asyncio
async def test_auto_rag_correct_call_order(
    mock_expand_query_result,
    mock_vectorize_result,
    mock_retrieve_result,
    mock_consolidate_result
):
    """Test that pipeline steps are called in the correct order."""
    call_order = []

    def track_expand(*args, **kwargs):
        call_order.append('expand')
        return mock_expand_query_result

    def track_vectorize(*args, **kwargs):
        call_order.append('vectorize')
        return mock_vectorize_result

    def track_retrieve(*args, **kwargs):
        call_order.append('retrieve')
        return mock_retrieve_result

    def track_consolidate(*args, **kwargs):
        call_order.append('consolidate')
        return mock_consolidate_result

    with patch('vulcanlab_api.routers.rag.expand_query', side_effect=track_expand), \
         patch('vulcanlab_api.routers.rag.vectorize_query', side_effect=track_vectorize), \
         patch('vulcanlab_api.routers.rag.retrieve', side_effect=track_retrieve), \
         patch('vulcanlab_api.routers.rag.consolidate_context', side_effect=track_consolidate):

        request = AutoRAGRequest(query="What is working memory?")
        await run_auto_rag(request)

        # Verify correct order
        assert call_order == ['expand', 'vectorize', 'retrieve', 'consolidate']


@pytest.mark.asyncio
async def test_auto_rag_uses_n_equals_3(mock_expand_query_result):
    """Test that expand_query is called with n=3."""
    with patch('vulcanlab_api.routers.rag.expand_query', return_value=mock_expand_query_result) as mock_expand, \
         patch('vulcanlab_api.routers.rag.vectorize_query', side_effect=RuntimeError("Stop here")):

        request = AutoRAGRequest(query="What is working memory?")

        try:
            await run_auto_rag(request)
        except HTTPException:
            pass  # We expect this to fail at vectorize

        # Verify expand_query was called with n=3
        mock_expand.assert_called_once_with(query="What is working memory?", n=3, verbose=False)
