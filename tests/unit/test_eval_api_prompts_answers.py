"""
Unit tests for evaluation prompt and answer API endpoints.

Tests API router endpoints for prompts and answers with mocked database and core logic.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.experiment import ExperimentPrompt, ExperimentAnswer
from vulcanlab_api.routers.eval import (
    create_experiment_prompt,
    list_experiment_prompts,
    get_prompt,
    delete_prompt_endpoint,
    create_prompt_answer_pair,
    list_prompt_answers,
)
from vulcanlab_api.schemas.eval import (
    PromptCreate,
    AnswerPairCreate,
)


class TestCreatePromptEndpoint:
    """Test POST /experiments/{id}/prompts endpoint."""

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    @patch('vulcanlab_api.routers.eval.create_prompt')
    async def test_create_prompt_success(self, mock_create, mock_get_exp, mock_get_session):
        """Test successful prompt creation."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()
        # Use MagicMock for prompt object
        mock_prompt = MagicMock()
        mock_prompt.id = 1
        mock_prompt.experiment_id = 1
        mock_prompt.prompt_text = "What is the capital of France?"
        mock_prompt.created_at = now
        mock_prompt.updated_at = now
        mock_create.return_value = mock_prompt

        request_data = PromptCreate(prompt_text="What is the capital of France?")
        result = await create_experiment_prompt(1, request_data)

        assert result.id == 1
        assert result.prompt_text == "What is the capital of France?"
        mock_create.assert_called_once_with(
            session=mock_session,
            experiment_id=1,
            prompt_text="What is the capital of France?"
        )

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    async def test_create_prompt_experiment_not_found(self, mock_get_exp, mock_get_session):
        """Test 404 when experiment doesn't exist."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_exp.side_effect = ValueError("Experiment with id 999 not found")

        request_data = PromptCreate(prompt_text="Test prompt")

        with pytest.raises(HTTPException) as exc_info:
            await create_experiment_prompt(999, request_data)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    @patch('vulcanlab_api.routers.eval.create_prompt')
    async def test_create_prompt_validation_error(self, mock_create, mock_get_exp, mock_get_session):
        """Test 400 when validation fails."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_create.side_effect = ValueError("Prompt text is required")

        request_data = PromptCreate(prompt_text=" ")

        with pytest.raises(HTTPException) as exc_info:
            await create_experiment_prompt(1, request_data)

        assert exc_info.value.status_code == 400

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    @patch('vulcanlab_api.routers.eval.create_prompt')
    async def test_create_prompt_integrity_error(self, mock_create, mock_get_exp, mock_get_session):
        """Test 409 on integrity constraint violation."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_create.side_effect = IntegrityError("statement", "params", "orig")

        request_data = PromptCreate(prompt_text="Test prompt")

        with pytest.raises(HTTPException) as exc_info:
            await create_experiment_prompt(1, request_data)

        assert exc_info.value.status_code == 409


class TestListPromptsEndpoint:
    """Test GET /experiments/{id}/prompts endpoint."""

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    async def test_list_prompts_success(self, mock_get_exp, mock_get_session):
        """Test successful listing of prompts."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()

        # Use MagicMock for prompts
        prompt1 = MagicMock()
        prompt1.id = 1
        prompt1.experiment_id = 1
        prompt1.prompt_text = "Prompt 1"
        prompt1.created_at = now

        prompt2 = MagicMock()
        prompt2.id = 2
        prompt2.experiment_id = 1
        prompt2.prompt_text = "Prompt 2"
        prompt2.created_at = now

        mock_query_result = [
            (prompt1, 5),
            (prompt2, 3),
        ]

        mock_query = mock_session.query.return_value
        mock_outerjoin1 = mock_query.outerjoin.return_value
        mock_outerjoin2 = mock_outerjoin1.outerjoin.return_value
        mock_filter = mock_outerjoin2.filter.return_value
        mock_group_by = mock_filter.group_by.return_value
        mock_order_by = mock_group_by.order_by.return_value
        mock_order_by.all.return_value = mock_query_result

        result = await list_experiment_prompts(1)

        assert len(result) == 2
        assert result[0].prompt_text == "Prompt 1"
        assert result[0].eval_count == 5
        assert result[1].eval_count == 3

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    async def test_list_prompts_experiment_not_found(self, mock_get_exp, mock_get_session):
        """Test 404 when experiment doesn't exist."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_exp.side_effect = ValueError("Experiment with id 999 not found")

        with pytest.raises(HTTPException) as exc_info:
            await list_experiment_prompts(999)

        assert exc_info.value.status_code == 404


class TestGetPromptEndpoint:
    """Test GET /prompts/{id} endpoint."""

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_prompt_by_id')
    async def test_get_prompt_success(self, mock_get_prompt, mock_get_session):
        """Test successful retrieval of prompt."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()
        # Use MagicMock for prompt
        mock_prompt = MagicMock()
        mock_prompt.id = 1
        mock_prompt.experiment_id = 1
        mock_prompt.prompt_text = "What is AI?"
        mock_prompt.created_at = now
        mock_prompt.updated_at = now
        mock_get_prompt.return_value = mock_prompt

        result = await get_prompt(1)

        assert result.id == 1
        assert result.prompt_text == "What is AI?"

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_prompt_by_id')
    async def test_get_prompt_not_found(self, mock_get_prompt, mock_get_session):
        """Test 404 when prompt doesn't exist."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_prompt.side_effect = ValueError("Prompt with id 999 not found")

        with pytest.raises(HTTPException) as exc_info:
            await get_prompt(999)

        assert exc_info.value.status_code == 404


class TestDeletePromptEndpoint:
    """Test DELETE /prompts/{id} endpoint."""

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.delete_prompt')
    async def test_delete_prompt_success(self, mock_delete, mock_get_session):
        """Test successful deletion of prompt."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        await delete_prompt_endpoint(1)

        mock_delete.assert_called_once_with(mock_session, 1)
        mock_session.commit.assert_called_once()

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.delete_prompt')
    async def test_delete_prompt_not_found(self, mock_delete, mock_get_session):
        """Test 404 when prompt doesn't exist."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_delete.side_effect = ValueError("Prompt with id 999 not found")

        with pytest.raises(HTTPException) as exc_info:
            await delete_prompt_endpoint(999)

        assert exc_info.value.status_code == 404


class TestCreateAnswerPairEndpoint:
    """Test POST /prompts/{id}/answers endpoint."""

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_prompt_by_id')
    @patch('vulcanlab_api.routers.eval.create_answer_pair')
    async def test_create_answer_pair_success(self, mock_create, mock_get_prompt, mock_get_session):
        """Test successful answer pair creation."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()
        # Create mock answer (answer_a/answer_b are computed properties)
        mock_answer = MagicMock()
        mock_answer.id = 1
        mock_answer.prompt_id = 1
        mock_answer.answer_x = "Paris"
        mock_answer.answer_y = "The capital is Paris"
        mock_answer.is_x_mapped_to_a = True
        mock_answer.answer_a = "Paris"  # Computed property
        mock_answer.answer_b = "The capital is Paris"  # Computed property
        mock_answer.created_at = now
        mock_answer.updated_at = now
        mock_create.return_value = mock_answer

        request_data = AnswerPairCreate(
            answer_x="Paris",
            answer_y="The capital is Paris"
        )
        result = await create_prompt_answer_pair(1, request_data)

        assert result.id == 1
        assert result.answer_x == "Paris"
        assert result.answer_y == "The capital is Paris"
        assert result.is_x_mapped_to_a is True
        mock_create.assert_called_once_with(
            session=mock_session,
            prompt_id=1,
            answer_x="Paris",
            answer_y="The capital is Paris"
        )

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_prompt_by_id')
    async def test_create_answer_pair_prompt_not_found(self, mock_get_prompt, mock_get_session):
        """Test 404 when prompt doesn't exist."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_prompt.side_effect = ValueError("Prompt with id 999 not found")

        request_data = AnswerPairCreate(answer_x="X", answer_y="Y")

        with pytest.raises(HTTPException) as exc_info:
            await create_prompt_answer_pair(999, request_data)

        assert exc_info.value.status_code == 404

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_prompt_by_id')
    @patch('vulcanlab_api.routers.eval.create_answer_pair')
    async def test_create_answer_pair_validation_error(self, mock_create, mock_get_prompt, mock_get_session):
        """Test 400 when validation fails."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_create.side_effect = ValueError("Answer X is required")

        request_data = AnswerPairCreate(answer_x=" ", answer_y="Y")

        with pytest.raises(HTTPException) as exc_info:
            await create_prompt_answer_pair(1, request_data)

        assert exc_info.value.status_code == 400

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_prompt_by_id')
    @patch('vulcanlab_api.routers.eval.create_answer_pair')
    async def test_create_answer_pair_integrity_error(self, mock_create, mock_get_prompt, mock_get_session):
        """Test 409 on integrity constraint violation."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_create.side_effect = IntegrityError("statement", "params", "orig")

        request_data = AnswerPairCreate(answer_x="X", answer_y="Y")

        with pytest.raises(HTTPException) as exc_info:
            await create_prompt_answer_pair(1, request_data)

        assert exc_info.value.status_code == 409


class TestListAnswersEndpoint:
    """Test GET /prompts/{id}/answers endpoint."""

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_prompt_by_id')
    async def test_list_answers_success(self, mock_get_prompt, mock_get_session):
        """Test successful listing of answers."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()

        # Create mock answers
        answer1 = MagicMock()
        answer1.id = 1
        answer1.prompt_id = 1
        answer1.answer_x = "X1"
        answer1.answer_y = "Y1"
        answer1.is_x_mapped_to_a = True
        answer1.created_at = now

        answer2 = MagicMock()
        answer2.id = 2
        answer2.prompt_id = 1
        answer2.answer_x = "X2"
        answer2.answer_y = "Y2"
        answer2.is_x_mapped_to_a = False
        answer2.created_at = now

        mock_query_result = [
            (answer1, 100),  # evaluation_id = 100
            (answer2, None), # evaluation_id = None
        ]

        mock_query = mock_session.query.return_value
        mock_outerjoin = mock_query.outerjoin.return_value
        mock_filter = mock_outerjoin.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = mock_query_result

        result = await list_prompt_answers(1)

        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].has_evaluation is True
        assert result[1].has_evaluation is False

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_prompt_by_id')
    async def test_list_answers_prompt_not_found(self, mock_get_prompt, mock_get_session):
        """Test 404 when prompt doesn't exist."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_prompt.side_effect = ValueError("Prompt with id 999 not found")

        with pytest.raises(HTTPException) as exc_info:
            await list_prompt_answers(999)

        assert exc_info.value.status_code == 404
