"""Unit tests for result models API endpoints.

Tests the result_models router for listing and creating models.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.result_model import ResultModel
from vulcanlab_api.routers.result_models import (
    list_result_models,
    create_result_model,
    get_or_create_result_model,
)
from vulcanlab_api.schemas.result_models import (
    ResultModelCreateRequest,
)
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_list_result_models_empty():
    """Test GET /result-models returns empty list when no models exist."""
    with patch('vulcanlab_api.routers.result_models.get_session') as mock_get_session:
        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock query to return empty list
        mock_session.query.return_value.order_by.return_value.all.return_value = []

        # Call endpoint
        response = await list_result_models()

        # Verify
        assert response.models == []
        assert response.total == 0


@pytest.mark.asyncio
async def test_list_result_models_returns_all():
    """Test GET /result-models returns all models ordered by name."""
    from datetime import datetime, timezone

    with patch('vulcanlab_api.routers.result_models.get_session') as mock_get_session:
        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Create mock models with proper attributes
        now = datetime.now(timezone.utc)

        # Create ResultModel instances directly for proper attribute access
        mock_model1 = ResultModel(id=1, name="claude-sonnet-3.5")
        mock_model1.created_at = now

        mock_model2 = ResultModel(id=2, name="gpt-4")
        mock_model2.created_at = now

        mock_model3 = ResultModel(id=3, name="gpt-4o")
        mock_model3.created_at = now

        mock_models = [mock_model1, mock_model2, mock_model3]
        mock_session.query.return_value.order_by.return_value.all.return_value = mock_models

        # Call endpoint
        response = await list_result_models()

        # Verify
        assert response.total == 3
        assert len(response.models) == 3
        assert response.models[0].name == "claude-sonnet-3.5"
        assert response.models[1].name == "gpt-4"
        assert response.models[2].name == "gpt-4o"


@pytest.mark.asyncio
async def test_create_result_model_success():
    """Test POST /result-models creates model and returns 201."""
    from datetime import datetime, timezone

    with patch('vulcanlab_api.routers.result_models.get_session') as mock_get_session:
        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Create return values
        now = datetime.now(timezone.utc)

        # Mock session.refresh to update the model with proper values
        def mock_refresh(obj):
            obj.id = 1
            obj.created_at = now

        mock_session.refresh = mock_refresh

        # Call endpoint
        request = ResultModelCreateRequest(name="gpt-4")
        response = await create_result_model(request)

        # Verify
        assert response.id == 1
        assert response.name == "gpt-4"
        assert response.message == "Model created successfully"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_result_model_duplicate_returns_409():
    """Test POST /result-models with duplicate name returns 409 Conflict."""
    with patch('vulcanlab_api.routers.result_models.get_session') as mock_get_session:
        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock commit to raise IntegrityError (duplicate name)
        mock_session.commit.side_effect = IntegrityError("", "", "")

        # Call endpoint and expect HTTPException
        request = ResultModelCreateRequest(name="gpt-4")
        with pytest.raises(HTTPException) as exc_info:
            await create_result_model(request)

        # Verify
        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail
        mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_create_result_model_empty_name_returns_400():
    """Test POST /result-models with empty name returns 400 Bad Request."""
    with patch('vulcanlab_api.routers.result_models.get_session') as mock_get_session:
        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Call endpoint with empty name
        request = ResultModelCreateRequest(name="   ")
        with pytest.raises(HTTPException) as exc_info:
            await create_result_model(request)

        # Verify
        assert exc_info.value.status_code == 400
        assert "cannot be empty" in exc_info.value.detail


def test_get_or_create_result_model_creates_new():
    """Test get_or_create_result_model creates new model if not exists."""
    # Mock session
    mock_session = MagicMock()

    # Mock query to return None (model doesn't exist)
    mock_session.query.return_value.filter.return_value.first.return_value = None

    # Call function
    result = get_or_create_result_model("gpt-4", mock_session)

    # Verify - result is a ResultModel instance
    assert isinstance(result, ResultModel)
    assert result.name == "gpt-4"
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


def test_get_or_create_result_model_returns_existing():
    """Test get_or_create_result_model returns existing model if exists."""
    # Mock session
    mock_session = MagicMock()

    # Create mock existing model using ResultModel
    mock_existing_model = ResultModel(id=5, name="gpt-4")

    # Mock query to return existing model
    mock_session.query.return_value.filter.return_value.first.return_value = mock_existing_model

    # Call function
    result = get_or_create_result_model("gpt-4", mock_session)

    # Verify
    assert result.id == 5
    assert result.name == "gpt-4"
    # Should not call add or flush
    mock_session.add.assert_not_called()
    mock_session.flush.assert_not_called()


def test_get_or_create_result_model_handles_race_condition():
    """Test get_or_create_result_model handles concurrent creation (unique constraint)."""
    # Mock session
    mock_session = MagicMock()

    # Create mock existing model using ResultModel
    mock_existing_model = ResultModel(id=5, name="gpt-4")

    # First query returns None, second query returns existing model
    mock_session.query.return_value.filter.return_value.first.side_effect = [
        None,  # First check - model doesn't exist
        mock_existing_model  # After rollback - model exists (created by another request)
    ]

    # Mock flush to raise IntegrityError (race condition)
    mock_session.flush.side_effect = IntegrityError("", "", "")

    # Call function
    result = get_or_create_result_model("gpt-4", mock_session)

    # Verify
    assert result.id == 5
    assert result.name == "gpt-4"
    mock_session.rollback.assert_called_once()


def test_get_or_create_result_model_empty_name_raises_error():
    """Test get_or_create_result_model raises ValueError for empty name."""
    mock_session = MagicMock()

    with pytest.raises(ValueError) as exc_info:
        get_or_create_result_model("   ", mock_session)

    assert "cannot be empty" in str(exc_info.value)


def test_get_or_create_result_model_strips_whitespace():
    """Test get_or_create_result_model strips whitespace from name."""
    # Mock session
    mock_session = MagicMock()

    # Create mock existing model using ResultModel
    mock_existing_model = ResultModel(id=5, name="gpt-4")

    # Mock query to return existing model
    mock_session.query.return_value.filter.return_value.first.return_value = mock_existing_model

    # Call function with whitespace
    result = get_or_create_result_model("  gpt-4  ", mock_session)

    # Verify it found the model (whitespace was stripped)
    assert result.id == 5
    assert result.name == "gpt-4"
