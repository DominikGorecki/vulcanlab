"""Unit tests for JSONL export API endpoint."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.responses import StreamingResponse


@pytest.mark.asyncio
async def test_export_experiment_answers_jsonl_success():
    """Test successful JSONL export returns correct response."""
    from vulcanlab_api.routers.eval import export_experiment_answers_jsonl

    experiment_id = 1

    # Mock the generator function
    def mock_generator():
        yield '{"prompt_text":"Test","answer_x":"X","answer_y":"Y"}\n'

    with patch('vulcanlab_api.routers.eval.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.eval.get_experiment_by_id') as mock_get_exp, \
         patch('vulcanlab_api.routers.eval.export_experiment_answers_to_jsonl') as mock_export:

        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_exp.return_value = MagicMock(id=experiment_id)
        mock_export.return_value = mock_generator()

        # Call endpoint
        response = await export_experiment_answers_jsonl(experiment_id)

        # Verify response is StreamingResponse
        assert isinstance(response, StreamingResponse)

        # Verify media type
        assert response.media_type == "application/x-ndjson"

        # Verify Content-Disposition header
        assert "Content-Disposition" in response.headers
        assert response.headers["Content-Disposition"] == f"attachment; filename=experiment_{experiment_id}_answers.jsonl"

        # Verify core function was called
        mock_export.assert_called_once_with(mock_session, experiment_id)

        # Verify experiment existence was checked
        mock_get_exp.assert_called_once_with(mock_session, experiment_id)


@pytest.mark.asyncio
async def test_export_experiment_answers_jsonl_experiment_not_found():
    """Test JSONL export with non-existent experiment returns 404."""
    from vulcanlab_api.routers.eval import export_experiment_answers_jsonl

    experiment_id = 999

    with patch('vulcanlab_api.routers.eval.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.eval.get_experiment_by_id') as mock_get_exp:

        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_exp.side_effect = ValueError(f"Experiment with id {experiment_id} not found")

        # Call endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await export_experiment_answers_jsonl(experiment_id)

        # Verify 404 status code
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_export_experiment_answers_jsonl_filename_format():
    """Test JSONL export has correct filename format."""
    from vulcanlab_api.routers.eval import export_experiment_answers_jsonl

    experiment_id = 42

    # Mock the generator function
    def mock_generator():
        yield '{"prompt_text":"Test","answer_x":"X","answer_y":"Y"}\n'

    with patch('vulcanlab_api.routers.eval.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.eval.get_experiment_by_id') as mock_get_exp, \
         patch('vulcanlab_api.routers.eval.export_experiment_answers_to_jsonl') as mock_export:

        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_exp.return_value = MagicMock(id=experiment_id)
        mock_export.return_value = mock_generator()

        # Call endpoint
        response = await export_experiment_answers_jsonl(experiment_id)

        # Verify filename contains experiment ID
        expected_filename = f"experiment_{experiment_id}_answers.jsonl"
        assert expected_filename in response.headers["Content-Disposition"]


@pytest.mark.asyncio
async def test_export_experiment_answers_jsonl_streaming_response():
    """Test JSONL export returns a streaming response that can be consumed."""
    from vulcanlab_api.routers.eval import export_experiment_answers_jsonl

    experiment_id = 1

    # Mock the generator function with multiple lines
    def mock_generator():
        yield '{"prompt_text":"Prompt 1","answer_x":"X1","answer_y":"Y1"}\n'
        yield '{"prompt_text":"Prompt 2","answer_x":"X2","answer_y":"Y2"}\n'
        yield '{"prompt_text":"Prompt 3","answer_x":"X3","answer_y":"Y3"}\n'

    with patch('vulcanlab_api.routers.eval.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.eval.get_experiment_by_id') as mock_get_exp, \
         patch('vulcanlab_api.routers.eval.export_experiment_answers_to_jsonl') as mock_export:

        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_exp.return_value = MagicMock(id=experiment_id)
        mock_export.return_value = mock_generator()

        # Call endpoint
        response = await export_experiment_answers_jsonl(experiment_id)

        # Verify it's a StreamingResponse
        assert isinstance(response, StreamingResponse)

        # Consume the body iterator to verify it works
        body_parts = []
        async for chunk in response.body_iterator:
            body_parts.append(chunk)

        # Verify we got 3 lines
        assert len(body_parts) == 3
        assert all(part.endswith('\n') for part in body_parts)


@pytest.mark.asyncio
async def test_export_experiment_answers_jsonl_empty_experiment():
    """Test JSONL export with experiment that has no completed evaluations."""
    from vulcanlab_api.routers.eval import export_experiment_answers_jsonl

    experiment_id = 1

    # Mock empty generator
    def mock_generator():
        return
        yield  # Make it a generator but yield nothing

    with patch('vulcanlab_api.routers.eval.get_session') as mock_get_session, \
         patch('vulcanlab_api.routers.eval.get_experiment_by_id') as mock_get_exp, \
         patch('vulcanlab_api.routers.eval.export_experiment_answers_to_jsonl') as mock_export:

        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_exp.return_value = MagicMock(id=experiment_id)
        mock_export.return_value = mock_generator()

        # Call endpoint
        response = await export_experiment_answers_jsonl(experiment_id)

        # Verify response is still valid StreamingResponse
        assert isinstance(response, StreamingResponse)
        assert response.media_type == "application/x-ndjson"

        # Consume the body iterator - should be empty
        body_parts = []
        async for chunk in response.body_iterator:
            body_parts.append(chunk)

        assert len(body_parts) == 0


@pytest.mark.asyncio
async def test_export_experiment_answers_jsonl_server_error():
    """Test JSONL export handles unexpected server errors."""
    from vulcanlab_api.routers.eval import export_experiment_answers_jsonl

    experiment_id = 1

    with patch('vulcanlab_api.routers.eval.get_session') as mock_get_session:

        # Setup mocks to raise unexpected error
        mock_get_session.side_effect = RuntimeError("Database connection failed")

        # Call endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await export_experiment_answers_jsonl(experiment_id)

        # Verify 500 status code
        assert exc_info.value.status_code == 500
        assert "Failed to export JSONL" in str(exc_info.value.detail)
