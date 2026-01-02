"""Unit tests for answer deletion and retrieval functions."""

import pytest
from unittest.mock import MagicMock, Mock, patch

from vulcanlab.eval.answers import delete_answer_pair, get_answer_with_evaluation
from vulcanlab.data.models.experiment import ExperimentAnswer, ExperimentEvaluation


class TestDeleteAnswerPair:
    """Test delete_answer_pair() function."""

    def test_delete_answer_pair_success(self):
        """Test successful answer deletion."""
        # Setup
        mock_session = MagicMock()
        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.prompt_id = 10

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_answer

        # Execute
        delete_answer_pair(mock_session, 1)

        # Verify
        mock_session.delete.assert_called_once_with(mock_answer)
        mock_session.flush.assert_called_once()

    def test_delete_answer_pair_not_found(self):
        """Test deletion of non-existent answer raises ValueError."""
        # Setup
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            delete_answer_pair(mock_session, 999)

        assert "999" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()
        mock_session.delete.assert_not_called()

    @patch('vulcanlab.eval.answers.logger')
    def test_delete_answer_pair_logs_deletion(self, mock_logger):
        """Test that deletion is logged."""
        # Setup
        mock_session = MagicMock()
        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.prompt_id = 10

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_answer

        # Execute
        delete_answer_pair(mock_session, 1)

        # Verify logging
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "Deleted answer pair" in log_message
        assert "id=1" in log_message
        assert "prompt_id=10" in log_message


class TestGetAnswerWithEvaluation:
    """Test get_answer_with_evaluation() function."""

    def test_get_answer_with_evaluation_success(self):
        """Test retrieval with evaluation."""
        # Setup
        mock_session = MagicMock()
        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.evaluation = Mock(spec=ExperimentEvaluation)

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_answer

        # Execute
        result = get_answer_with_evaluation(mock_session, 1)

        # Verify
        assert result == mock_answer
        assert result.evaluation is not None

    def test_get_answer_without_evaluation_success(self):
        """Test retrieval without evaluation."""
        # Setup
        mock_session = MagicMock()
        mock_answer = Mock(spec=ExperimentAnswer)
        mock_answer.id = 1
        mock_answer.evaluation = None

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_answer

        # Execute
        result = get_answer_with_evaluation(mock_session, 1)

        # Verify
        assert result == mock_answer
        assert result.evaluation is None

    def test_get_answer_not_found(self):
        """Test retrieval of non-existent answer raises ValueError."""
        # Setup
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            get_answer_with_evaluation(mock_session, 999)

        assert "999" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()
