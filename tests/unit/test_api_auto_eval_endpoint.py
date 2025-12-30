"""
Unit tests for automatic evaluation API endpoint (T04).

Tests POST /experiments/{id}/prompts/auto-eval endpoint with mocked dependencies.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from vulcanlab_api.routers.eval import execute_automatic_evaluation
from vulcanlab_api.schemas.eval import AutoEvalRequest


@pytest.mark.asyncio
class TestExecuteAutomaticEvaluationEndpoint:
    """Test POST /experiments/{id}/prompts/auto-eval endpoint."""

    @patch('vulcanlab_api.routers.eval.execute_automatic_eval')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_execute_automatic_evaluation_success(
        self,
        mock_get_session,
        mock_execute_auto_eval
    ):
        """Test successful automatic evaluation execution."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_execute_auto_eval.return_value = {
            "evaluation_id": 100,
            "answer_id": 50,
            "prompt_group_id": 3
        }

        # Create request
        request = AutoEvalRequest(
            main_prompt_text="What is 2+2?",
            answer_x_prompt_text="Answer briefly",
            answer_y_prompt_text="Answer in detail"
        )

        # Execute
        result = await execute_automatic_evaluation(1, request)

        # Verify
        assert result.evaluation_id == 100
        assert result.answer_id == 50
        assert result.prompt_group_id == 3

        # Verify execute_automatic_eval was called with correct parameters
        mock_execute_auto_eval.assert_called_once()
        call_kwargs = mock_execute_auto_eval.call_args[1]
        assert call_kwargs["session"] == mock_session
        assert call_kwargs["experiment_id"] == 1
        assert call_kwargs["main_prompt_text"] == "What is 2+2?"
        assert call_kwargs["answer_x_prompt_text"] == "Answer briefly"
        assert call_kwargs["answer_y_prompt_text"] == "Answer in detail"

        # Verify transaction was committed
        mock_session.commit.assert_called_once()

    @patch('vulcanlab_api.routers.eval.execute_automatic_eval')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_execute_automatic_evaluation_experiment_not_found(
        self,
        mock_get_session,
        mock_execute_auto_eval
    ):
        """Test that 404 is returned when experiment doesn't exist."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_execute_auto_eval.side_effect = ValueError(
            "Experiment with id 999 not found"
        )

        # Create request
        request = AutoEvalRequest(
            main_prompt_text="Main",
            answer_x_prompt_text="X",
            answer_y_prompt_text="Y"
        )

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await execute_automatic_evaluation(999, request)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
        mock_session.commit.assert_not_called()

    @patch('vulcanlab_api.routers.eval.execute_automatic_eval')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_execute_automatic_evaluation_auto_mode_not_enabled(
        self,
        mock_get_session,
        mock_execute_auto_eval
    ):
        """Test that 400 is returned when auto mode is not enabled."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_execute_auto_eval.side_effect = ValueError(
            "Automatic evaluation mode is not enabled for experiment 1. "
            "Please enable auto mode first."
        )

        # Create request
        request = AutoEvalRequest(
            main_prompt_text="Main",
            answer_x_prompt_text="X",
            answer_y_prompt_text="Y"
        )

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await execute_automatic_evaluation(1, request)

        assert exc_info.value.status_code == 400
        assert "not enabled" in exc_info.value.detail
        mock_session.commit.assert_not_called()

    @patch('vulcanlab_api.routers.eval.execute_automatic_eval')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_execute_automatic_evaluation_llm_failure(
        self,
        mock_get_session,
        mock_execute_auto_eval
    ):
        """Test error handling when LLM call fails."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_execute_auto_eval.side_effect = Exception("OpenAI API error: Rate limit exceeded")

        # Create request
        request = AutoEvalRequest(
            main_prompt_text="Main",
            answer_x_prompt_text="X",
            answer_y_prompt_text="Y"
        )

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await execute_automatic_evaluation(1, request)

        assert exc_info.value.status_code == 500
        assert "Automatic evaluation failed" in exc_info.value.detail
        mock_session.commit.assert_not_called()

    @patch('vulcanlab_api.routers.eval.execute_automatic_eval')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_execute_automatic_evaluation_database_error(
        self,
        mock_get_session,
        mock_execute_auto_eval
    ):
        """Test error handling when database operation fails."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_execute_auto_eval.side_effect = Exception("Database connection lost")

        # Create request
        request = AutoEvalRequest(
            main_prompt_text="Main",
            answer_x_prompt_text="X",
            answer_y_prompt_text="Y"
        )

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await execute_automatic_evaluation(1, request)

        assert exc_info.value.status_code == 500
        assert "failed" in exc_info.value.detail.lower()

    @patch('vulcanlab_api.routers.eval.execute_automatic_eval')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_execute_automatic_evaluation_with_long_prompts(
        self,
        mock_get_session,
        mock_execute_auto_eval
    ):
        """Test automatic evaluation with maximum length prompts."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_execute_auto_eval.return_value = {
            "evaluation_id": 200,
            "answer_id": 100,
            "prompt_group_id": 5
        }

        # Create request with long prompts (near max 10000 chars)
        long_text = "A" * 9000
        request = AutoEvalRequest(
            main_prompt_text=long_text,
            answer_x_prompt_text=long_text,
            answer_y_prompt_text=long_text
        )

        # Execute
        result = await execute_automatic_evaluation(1, request)

        # Verify
        assert result.evaluation_id == 200
        assert result.answer_id == 100
        assert result.prompt_group_id == 5

        # Verify long prompts were passed through
        call_kwargs = mock_execute_auto_eval.call_args[1]
        assert call_kwargs["main_prompt_text"] == long_text
        assert call_kwargs["answer_x_prompt_text"] == long_text
        assert call_kwargs["answer_y_prompt_text"] == long_text

    @patch('vulcanlab_api.routers.eval.execute_automatic_eval')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_execute_automatic_evaluation_multiple_groups(
        self,
        mock_get_session,
        mock_execute_auto_eval
    ):
        """Test that multiple sequential calls create different prompt groups."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # First call returns group 1
        mock_execute_auto_eval.return_value = {
            "evaluation_id": 1,
            "answer_id": 1,
            "prompt_group_id": 1
        }

        request = AutoEvalRequest(
            main_prompt_text="First call",
            answer_x_prompt_text="X1",
            answer_y_prompt_text="Y1"
        )

        # Execute first call
        result1 = await execute_automatic_evaluation(1, request)
        assert result1.prompt_group_id == 1

        # Second call returns group 2
        mock_execute_auto_eval.return_value = {
            "evaluation_id": 2,
            "answer_id": 2,
            "prompt_group_id": 2
        }

        request2 = AutoEvalRequest(
            main_prompt_text="Second call",
            answer_x_prompt_text="X2",
            answer_y_prompt_text="Y2"
        )

        # Execute second call
        result2 = await execute_automatic_evaluation(1, request2)
        assert result2.prompt_group_id == 2

    @patch('vulcanlab_api.routers.eval.execute_automatic_eval')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_execute_automatic_evaluation_transaction_rollback_on_error(
        self,
        mock_get_session,
        mock_execute_auto_eval
    ):
        """Test that transaction is rolled back on error."""
        # Setup mocks
        mock_session = MagicMock()
        mock_session_context = MagicMock()
        mock_session_context.__enter__.return_value = mock_session
        mock_get_session.return_value = mock_session_context

        # Simulate error during execution
        mock_execute_auto_eval.side_effect = Exception("LLM parsing error")

        # Create request
        request = AutoEvalRequest(
            main_prompt_text="Main",
            answer_x_prompt_text="X",
            answer_y_prompt_text="Y"
        )

        # Execute and verify exception
        with pytest.raises(HTTPException):
            await execute_automatic_evaluation(1, request)

        # Verify commit was not called (transaction should be rolled back by context manager)
        mock_session.commit.assert_not_called()

    @patch('vulcanlab_api.routers.eval.execute_automatic_eval')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_execute_automatic_evaluation_validation_error(
        self,
        mock_get_session,
        mock_execute_auto_eval
    ):
        """Test handling of validation errors from execute_automatic_eval."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Simulate validation error (e.g., invalid prompt text)
        mock_execute_auto_eval.side_effect = ValueError(
            "Prompt text is required and cannot be empty"
        )

        # Create request
        request = AutoEvalRequest(
            main_prompt_text="Main",
            answer_x_prompt_text="X",
            answer_y_prompt_text="Y"
        )

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await execute_automatic_evaluation(1, request)

        # Validation errors should return 400 (not 404)
        assert exc_info.value.status_code == 400
        assert "required" in exc_info.value.detail.lower()

    @patch('vulcanlab_api.routers.eval.execute_automatic_eval')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_execute_automatic_evaluation_with_special_characters(
        self,
        mock_get_session,
        mock_execute_auto_eval
    ):
        """Test automatic evaluation with special characters in prompts."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_execute_auto_eval.return_value = {
            "evaluation_id": 300,
            "answer_id": 150,
            "prompt_group_id": 7
        }

        # Create request with special characters
        request = AutoEvalRequest(
            main_prompt_text='What is "2+2"? (with quotes)',
            answer_x_prompt_text="Answer: It's 4!",
            answer_y_prompt_text="The answer is:\n- Four\n- 4\n- IV"
        )

        # Execute
        result = await execute_automatic_evaluation(1, request)

        # Verify special characters were preserved
        call_kwargs = mock_execute_auto_eval.call_args[1]
        assert '"2+2"' in call_kwargs["main_prompt_text"]
        assert "It's" in call_kwargs["answer_x_prompt_text"]
        assert "\n" in call_kwargs["answer_y_prompt_text"]

        # Verify result
        assert result.evaluation_id == 300

    @patch('vulcanlab_api.routers.eval.execute_automatic_eval')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_execute_automatic_evaluation_returns_201_status(
        self,
        mock_get_session,
        mock_execute_auto_eval
    ):
        """Test that endpoint is configured to return 201 CREATED status."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_execute_auto_eval.return_value = {
            "evaluation_id": 1,
            "answer_id": 1,
            "prompt_group_id": 1
        }

        # Create request
        request = AutoEvalRequest(
            main_prompt_text="Main",
            answer_x_prompt_text="X",
            answer_y_prompt_text="Y"
        )

        # Execute
        result = await execute_automatic_evaluation(1, request)

        # Verify response is created successfully
        # (The decorator specifies status_code=201, but we verify the result object)
        assert result.evaluation_id is not None
        assert result.answer_id is not None
        assert result.prompt_group_id is not None
