"""Unit tests for answer API endpoints."""

import pytest
from unittest.mock import MagicMock, Mock, patch
from fastapi import HTTPException

from vulcanlab_api.routers.eval import delete_answer_endpoint, get_answer_detail
from vulcanlab.data.models.experiment import ExperimentAnswer, ExperimentEvaluation


class TestDeleteAnswerEndpoint:
    """Test DELETE /answers/{answer_id} endpoint."""

    @pytest.mark.asyncio
    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.delete_answer_pair')
    async def test_delete_returns_204_on_success(self, mock_delete, mock_get_session):
        """Test successful deletion returns 204."""
        # Setup
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_delete.return_value = None

        # Execute
        result = await delete_answer_endpoint(1)

        # Verify
        assert result is None  # 204 returns None
        mock_delete.assert_called_once_with(mock_session, 1)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.delete_answer_pair')
    async def test_delete_returns_404_when_not_found(self, mock_delete, mock_get_session):
        """Test 404 when answer not found."""
        # Setup
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_delete.side_effect = ValueError("Answer with id 999 not found")

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await delete_answer_endpoint(999)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


class TestGetAnswerDetailEndpoint:
    """Test GET /answers/{answer_id} endpoint."""

    @pytest.mark.asyncio
    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_answer_with_evaluation')
    async def test_get_detail_returns_answer_with_evaluation(
        self, mock_get_answer, mock_get_session
    ):
        """Test retrieval with evaluation."""
        # Setup
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Create mock evaluation with dimension result
        mock_dim_result = Mock()
        mock_dim_result.dimension_name = "clarity"
        mock_dim_result.score = 7

        mock_evaluation = Mock(spec=ExperimentEvaluation)
        mock_evaluation.id = 1
        mock_evaluation.overall_score = 8
        mock_evaluation.justification = "Test justification"
        mock_evaluation.dimension_results = [mock_dim_result]
        mock_evaluation.created_at = "2024-01-01T00:00:00"

        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.prompt_id = 10
        mock_answer.answer_x = "Answer X"
        mock_answer.answer_y = "Answer Y"
        mock_answer.is_x_mapped_to_a = True
        mock_answer.answer_a = "Answer X"
        mock_answer.answer_b = "Answer Y"
        mock_answer.created_at = "2024-01-01T00:00:00"
        mock_answer.updated_at = "2024-01-01T00:00:00"
        mock_answer.evaluation = mock_evaluation

        mock_get_answer.return_value = mock_answer

        # Execute
        result = await get_answer_detail(1)

        # Verify
        assert result.id == 1
        assert result.answer_x == "Answer X"
        assert result.evaluation is not None
        assert result.evaluation.overall_score == 8
        assert result.evaluation.unblinded_score == 8  # X→A, so positive

    @pytest.mark.asyncio
    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_answer_with_evaluation')
    async def test_get_detail_unblinded_score_when_x_mapped_to_b(
        self, mock_get_answer, mock_get_session
    ):
        """Test unblinded_score when X mapped to B."""
        # Setup
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_evaluation = Mock(spec=ExperimentEvaluation)
        mock_evaluation.id = 1
        mock_evaluation.overall_score = 8
        mock_evaluation.justification = "Test"
        mock_evaluation.dimension_results = []
        mock_evaluation.created_at = "2024-01-01T00:00:00"

        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.prompt_id = 10
        mock_answer.answer_x = "Answer X"
        mock_answer.answer_y = "Answer Y"
        mock_answer.is_x_mapped_to_a = False  # X→B
        mock_answer.answer_a = "Answer Y"
        mock_answer.answer_b = "Answer X"
        mock_answer.created_at = "2024-01-01T00:00:00"
        mock_answer.updated_at = "2024-01-01T00:00:00"
        mock_answer.evaluation = mock_evaluation

        mock_get_answer.return_value = mock_answer

        # Execute
        result = await get_answer_detail(1)

        # Verify unblinded_score is negated
        assert result.evaluation.unblinded_score == -8  # X→B, so negative

    @pytest.mark.asyncio
    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_answer_with_evaluation')
    async def test_get_detail_returns_404_when_not_found(
        self, mock_get_answer, mock_get_session
    ):
        """Test 404 when answer not found."""
        # Setup
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_answer.side_effect = ValueError("Answer with id 999 not found")

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await get_answer_detail(999)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_answer_with_evaluation')
    async def test_get_detail_returns_answer_without_evaluation(
        self, mock_get_answer, mock_get_session
    ):
        """Test retrieval of answer without evaluation."""
        # Setup
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.prompt_id = 10
        mock_answer.answer_x = "Answer X"
        mock_answer.answer_y = "Answer Y"
        mock_answer.is_x_mapped_to_a = True
        mock_answer.answer_a = "Answer X"
        mock_answer.answer_b = "Answer Y"
        mock_answer.created_at = "2024-01-01T00:00:00"
        mock_answer.updated_at = "2024-01-01T00:00:00"
        mock_answer.evaluation = None

        mock_get_answer.return_value = mock_answer

        # Execute
        result = await get_answer_detail(1)

        # Verify
        assert result.id == 1
        assert result.answer_x == "Answer X"
        assert result.evaluation is None
