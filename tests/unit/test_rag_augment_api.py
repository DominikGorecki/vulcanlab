"""Unit tests for RAG augmentation API endpoints with model tracking.

Tests the modified endpoints that now track model information.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from vulcanlab.data.models import Query, Result
from vulcanlab.data.models.result_model import ResultModel
from vulcanlab_api.routers.rag import (
    save_manual_augment,
    run_augment,
    list_results,
    get_result,
)
from vulcanlab_api.schemas.rag_queries import (
    AugmentManualRequest,
    AugmentRunRequest,
)
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_manual_result_with_model_id():
    """Test manual result endpoint saves result with model_id when model_id provided."""
    with patch('vulcanlab_api.routers.rag.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.result_models.get_or_create_result_model') as mock_get_or_create:

        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock query exists
        mock_query = Mock(id=1, original_query="test query")

        # Create ResultModel for the model query
        mock_model = ResultModel(id=5, name="gpt-4")

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_query,  # First call - verify query exists
            mock_model,  # Second call - get model
        ]

        # Mock commit to set the result ID
        def mock_commit():
            # Find the Result object that was added and give it an ID
            for call in mock_session.add.call_args_list:
                obj = call[0][0]
                if isinstance(obj, Result):
                    obj.id = 42

        mock_session.commit = mock_commit

        # Call endpoint
        request = AugmentManualRequest(
            response_text="This is the response",
            model_id=5
        )

        response = await save_manual_augment(query_id=1, request=request)

        # Verify result was created with model_id
        assert response.query_id == 1
        assert response.result_id == 42
        assert response.model_name == "gpt-4"
        mock_session.add.assert_called_once()
        # Verify the Result object has model_id set
        result_arg = mock_session.add.call_args[0][0]
        assert result_arg.model_id == 5
        # Should not call get_or_create when using model_id directly
        mock_get_or_create.assert_not_called()


@pytest.mark.asyncio
async def test_manual_result_with_new_model_name():
    """Test manual result endpoint creates model and saves result when new_model_name provided."""
    with patch('vulcanlab_api.routers.rag.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.result_models.get_or_create_result_model') as mock_get_or_create:

        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock query exists
        mock_query = Mock(id=1, original_query="test query")
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query

        # Mock get_or_create_result_model to return ResultModel
        mock_model = ResultModel(id=10, name="claude-sonnet-3.5")
        mock_get_or_create.return_value = mock_model

        # Mock commit to set the result ID
        def mock_commit():
            for call in mock_session.add.call_args_list:
                obj = call[0][0]
                if isinstance(obj, Result):
                    obj.id = 43

        mock_session.commit = mock_commit

        # Call endpoint
        request = AugmentManualRequest(
            response_text="This is the response",
            new_model_name="claude-sonnet-3.5"
        )
        response = await save_manual_augment(query_id=1, request=request)

        # Verify
        assert response.query_id == 1
        assert response.result_id == 43
        assert response.model_name == "claude-sonnet-3.5"
        mock_get_or_create.assert_called_once_with("claude-sonnet-3.5", mock_session)

        # Verify result was created with model_id
        result_arg = mock_session.add.call_args[0][0]
        assert result_arg.model_id == 10


@pytest.mark.asyncio
async def test_manual_result_without_model():
    """Test manual result endpoint saves result with NULL model_id when neither provided."""
    with patch('vulcanlab_api.routers.rag.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.result_models.get_or_create_result_model') as mock_get_or_create:

        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock query exists
        mock_query = Mock(id=1, original_query="test query")
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query

        # Mock commit to set the result ID
        def mock_commit():
            for call in mock_session.add.call_args_list:
                obj = call[0][0]
                if isinstance(obj, Result):
                    obj.id = 44

        mock_session.commit = mock_commit

        # Call endpoint
        request = AugmentManualRequest(
            response_text="This is the response"
        )

        response = await save_manual_augment(query_id=1, request=request)

        # Verify
        assert response.query_id == 1
        assert response.result_id == 44
        assert response.model_name == "Unspecified"

        # Verify result was created with NULL model_id
        result_arg = mock_session.add.call_args[0][0]
        assert result_arg.model_id is None
        # Should not call get_or_create when no model specified
        mock_get_or_create.assert_not_called()


@pytest.mark.asyncio
async def test_manual_result_model_not_found():
    """Test manual result endpoint returns 404 when model_id not found."""
    with patch('vulcanlab_api.routers.rag.get_session') as mock_get_session:
        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock query exists, but model doesn't
        mock_query = Mock(id=1, original_query="test query")
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_query,  # First call - verify query exists
            None,  # Second call - model not found
        ]

        # Call endpoint
        request = AugmentManualRequest(
            response_text="This is the response",
            model_id=999
        )

        with pytest.raises(HTTPException) as exc_info:
            await save_manual_augment(query_id=1, request=request)

        # Verify
        assert exc_info.value.status_code == 404
        assert "Model with ID 999 not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_automatic_result_captures_model_from_config():
    """Test automatic result endpoint reads model from config and saves result."""
    with patch('vulcanlab_api.routers.rag.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.rag.generate_augmented_prompt') as mock_generate_prompt, \
         patch('vulcanlab_api.routers.rag.create_langchain_chat') as mock_create_chat, \
         patch('vulcanlab.ai.config.LLMSettings') as mock_llm_settings_class, \
         patch('vulcanlab_api.routers.result_models.get_or_create_result_model') as mock_get_or_create:

        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock generate_augmented_prompt
        mock_generate_prompt.return_value = "Test prompt"

        # Mock LLMSettings to return model name
        mock_llm_settings = Mock()
        mock_llm_settings.get_model.return_value = "gpt-4o"
        mock_llm_settings_class.return_value = mock_llm_settings

        # Mock create_langchain_chat
        mock_chat = Mock()
        mock_response = Mock()
        mock_response.content = "This is the LLM response"
        mock_chat.invoke.return_value = mock_response
        mock_stack = Mock(chat=mock_chat)
        mock_create_chat.return_value = mock_stack

        # Mock get_or_create_result_model to return ResultModel
        mock_model = ResultModel(id=15, name="gpt-4o")
        mock_get_or_create.return_value = mock_model

        # Mock commit to set the result ID
        def mock_commit():
            for call in mock_session.add.call_args_list:
                obj = call[0][0]
                if isinstance(obj, Result):
                    obj.id = 100

        mock_session.commit = mock_commit

        # Call endpoint
        request = AugmentRunRequest()
        response = await run_augment(query_id=1, request=request)

        # Verify
        assert response.query_id == 1
        assert response.result_id == 100
        assert response.model_name == "gpt-4o"
        mock_get_or_create.assert_called_once_with("gpt-4o", mock_session)

        # Verify result was created with model_id
        result_arg = mock_session.add.call_args[0][0]
        assert result_arg.model_id == 15


@pytest.mark.asyncio
async def test_results_list_returns_model_name():
    """Test results list endpoint denormalizes model_name correctly."""
    from datetime import datetime, timezone

    with patch('vulcanlab_api.routers.rag.get_session') as mock_get_session:
        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock query exists
        mock_query = Mock(id=1)

        # Mock results with model names (LEFT JOIN results)
        now = datetime.now(timezone.utc)
        mock_result1 = Mock(id=1, query_id=1, response_text="Response 1", created_at=now)
        mock_result2 = Mock(id=2, query_id=1, response_text="Response 2", created_at=now)

        # First query returns query, second returns results with model names
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query
        mock_session.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.all.return_value = [
            (mock_result1, "gpt-4"),
            (mock_result2, "claude-sonnet-3.5"),
        ]

        # Call endpoint
        response = await list_results(query_id=1)

        # Verify
        assert response.total == 2
        assert response.results[0].model_name == "gpt-4"
        assert response.results[1].model_name == "claude-sonnet-3.5"


@pytest.mark.asyncio
async def test_results_list_shows_unspecified_for_null_model():
    """Test results list endpoint shows 'Unspecified' for NULL model_id."""
    from datetime import datetime, timezone

    with patch('vulcanlab_api.routers.rag.get_session') as mock_get_session:
        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock query exists
        mock_query = Mock(id=1)

        # Mock result with NULL model_id
        now = datetime.now(timezone.utc)
        mock_result = Mock(id=1, query_id=1, response_text="Response", created_at=now)

        # First query returns query, second returns result with NULL model name
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query
        mock_session.query.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.all.return_value = [
            (mock_result, None),  # NULL model_name from LEFT JOIN
        ]

        # Call endpoint
        response = await list_results(query_id=1)

        # Verify
        assert response.total == 1
        assert response.results[0].model_name == "Unspecified"


@pytest.mark.asyncio
async def test_result_detail_returns_model_name():
    """Test result detail endpoint returns model_name."""
    from datetime import datetime, timezone

    with patch('vulcanlab_api.routers.rag.get_session') as mock_get_session:
        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock result with model name
        now = datetime.now(timezone.utc)
        mock_result = Mock(id=5, query_id=1, response_text="Response", created_at=now)

        mock_session.query.return_value.outerjoin.return_value.filter.return_value.first.return_value = (
            mock_result,
            "gpt-4o"
        )

        # Call endpoint
        response = await get_result(query_id=1, result_id=5)

        # Verify
        assert response.id == 5
        assert response.model_name == "gpt-4o"


@pytest.mark.asyncio
async def test_result_detail_shows_unspecified_for_null_model():
    """Test result detail endpoint shows 'Unspecified' for NULL model_id."""
    from datetime import datetime, timezone

    with patch('vulcanlab_api.routers.rag.get_session') as mock_get_session:
        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock result with NULL model_id
        now = datetime.now(timezone.utc)
        mock_result = Mock(id=5, query_id=1, response_text="Response", created_at=now)

        mock_session.query.return_value.outerjoin.return_value.filter.return_value.first.return_value = (
            mock_result,
            None  # NULL model_name from LEFT JOIN
        )

        # Call endpoint
        response = await get_result(query_id=1, result_id=5)

        # Verify
        assert response.id == 5
        assert response.model_name == "Unspecified"
