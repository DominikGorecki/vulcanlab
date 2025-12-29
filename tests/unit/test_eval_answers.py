"""
Unit tests for answer pair core logic with cryptographic random assignment.

Tests answer creation, random assignment verification, and retrieval operations.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.experiment import ExperimentAnswer
from vulcanlab.eval.answers import (
    create_answer_pair,
    get_answers_by_prompt,
    get_answer_by_id,
)


class TestCreateAnswerPair:
    """Test answer pair creation with blind random assignment."""

    @patch('vulcanlab.eval.answers.secrets.choice')
    def test_create_answer_pair_x_mapped_to_a(self, mock_choice):
        """Test answer creation when X is mapped to A."""
        mock_session = MagicMock()
        mock_choice.return_value = True  # is_x_mapped_to_a = True

        answer = create_answer_pair(
            session=mock_session,
            prompt_id=1,
            answer_x="Answer from model X",
            answer_y="Answer from model Y"
        )

        # Verify correct assignment
        assert answer.prompt_id == 1
        assert answer.answer_x == "Answer from model X"
        assert answer.answer_y == "Answer from model Y"
        assert answer.is_x_mapped_to_a is True
        assert answer.answer_a == "Answer from model X"
        assert answer.answer_b == "Answer from model Y"

        # Verify session methods called
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @patch('vulcanlab.eval.answers.secrets.choice')
    def test_create_answer_pair_x_mapped_to_b(self, mock_choice):
        """Test answer creation when X is mapped to B (Y to A)."""
        mock_session = MagicMock()
        mock_choice.return_value = False  # is_x_mapped_to_a = False

        answer = create_answer_pair(
            session=mock_session,
            prompt_id=1,
            answer_x="Answer from model X",
            answer_y="Answer from model Y"
        )

        # Verify swapped assignment
        assert answer.is_x_mapped_to_a is False
        assert answer.answer_a == "Answer from model Y"
        assert answer.answer_b == "Answer from model X"

    def test_create_answer_pair_strips_whitespace(self):
        """Test that answers are stripped of leading/trailing whitespace."""
        mock_session = MagicMock()

        with patch('vulcanlab.eval.answers.secrets.choice', return_value=True):
            answer = create_answer_pair(
                session=mock_session,
                prompt_id=1,
                answer_x="  Answer X  \n",
                answer_y="\t  Answer Y  "
            )

        assert answer.answer_x == "Answer X"
        assert answer.answer_y == "Answer Y"
        assert answer.answer_a == "Answer X"
        assert answer.answer_b == "Answer Y"

    def test_create_answer_pair_empty_answer_x_raises_error(self):
        """Test that empty answer_x raises ValueError."""
        mock_session = MagicMock()

        with pytest.raises(ValueError, match="Answer X is required"):
            create_answer_pair(
                session=mock_session,
                prompt_id=1,
                answer_x="",
                answer_y="Answer Y"
            )

        mock_session.add.assert_not_called()

    def test_create_answer_pair_empty_answer_y_raises_error(self):
        """Test that empty answer_y raises ValueError."""
        mock_session = MagicMock()

        with pytest.raises(ValueError, match="Answer Y is required"):
            create_answer_pair(
                session=mock_session,
                prompt_id=1,
                answer_x="Answer X",
                answer_y=""
            )

        mock_session.add.assert_not_called()

    def test_create_answer_pair_whitespace_only_x_raises_error(self):
        """Test that whitespace-only answer_x raises ValueError."""
        mock_session = MagicMock()

        with pytest.raises(ValueError, match="Answer X is required"):
            create_answer_pair(
                session=mock_session,
                prompt_id=1,
                answer_x="   \n\t  ",
                answer_y="Answer Y"
            )

    def test_create_answer_pair_whitespace_only_y_raises_error(self):
        """Test that whitespace-only answer_y raises ValueError."""
        mock_session = MagicMock()

        with pytest.raises(ValueError, match="Answer Y is required"):
            create_answer_pair(
                session=mock_session,
                prompt_id=1,
                answer_x="Answer X",
                answer_y="   \n\t  "
            )

    def test_create_answer_pair_integrity_error(self):
        """Test that IntegrityError is handled correctly."""
        mock_session = MagicMock()
        mock_session.flush.side_effect = IntegrityError("statement", "params", "orig")

        with pytest.raises(IntegrityError):
            create_answer_pair(
                session=mock_session,
                prompt_id=999,  # Non-existent prompt
                answer_x="Answer X",
                answer_y="Answer Y"
            )

        mock_session.rollback.assert_called_once()

    @patch('vulcanlab.eval.answers.logger')
    @patch('vulcanlab.eval.answers.secrets.choice')
    def test_create_answer_pair_logs_success(self, mock_choice, mock_logger):
        """Test that successful creation is logged with mapping info."""
        mock_session = MagicMock()
        mock_choice.return_value = True

        answer = create_answer_pair(
            session=mock_session,
            prompt_id=1,
            answer_x="Answer X",
            answer_y="Answer Y"
        )

        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "Created answer pair" in log_message
        assert "prompt_id=1" in log_message
        assert "is_x_mapped_to_a=True" in log_message

    @patch('vulcanlab.eval.answers.logger')
    @patch('vulcanlab.eval.answers.secrets.choice')
    def test_create_answer_pair_logs_failure(self, mock_choice, mock_logger):
        """Test that failed creation is logged."""
        mock_session = MagicMock()
        mock_session.flush.side_effect = IntegrityError("statement", "params", "orig")

        with pytest.raises(IntegrityError):
            create_answer_pair(
                session=mock_session,
                prompt_id=999,
                answer_x="Answer X",
                answer_y="Answer Y"
            )

        mock_logger.error.assert_called_once()
        log_message = mock_logger.error.call_args[0][0]
        assert "Failed to create answer pair" in log_message


class TestRandomAssignment:
    """Test cryptographic random assignment distribution."""

    @patch('vulcanlab.eval.answers.secrets.choice')
    def test_random_assignment_uses_secrets_choice(self, mock_choice):
        """Test that secrets.choice is called for random assignment."""
        mock_session = MagicMock()
        mock_choice.return_value = True

        create_answer_pair(
            session=mock_session,
            prompt_id=1,
            answer_x="Answer X",
            answer_y="Answer Y"
        )

        # Verify secrets.choice was called with [True, False]
        mock_choice.assert_called_once_with([True, False])

    def test_random_assignment_distribution(self):
        """Test that random assignment produces varied results over multiple calls.

        This test verifies that the random assignment is actually random by creating
        multiple answer pairs and checking that we get both True and False for
        is_x_mapped_to_a. With 100 iterations and cryptographic randomness, it's
        statistically impossible to get all True or all False.
        """
        mock_session = MagicMock()

        # Create 100 answer pairs (using real secrets.choice, not mocked)
        mappings = []
        for i in range(100):
            answer = create_answer_pair(
                session=mock_session,
                prompt_id=1,
                answer_x=f"Answer X {i}",
                answer_y=f"Answer Y {i}"
            )
            mappings.append(answer.is_x_mapped_to_a)

        # Verify we got both True and False (not all one value)
        assert True in mappings, "Random assignment should produce some True values"
        assert False in mappings, "Random assignment should produce some False values"

        # Verify distribution is roughly balanced (30-70% range is reasonable)
        true_count = sum(mappings)
        true_percentage = (true_count / len(mappings)) * 100
        assert 30 <= true_percentage <= 70, \
            f"Distribution should be roughly balanced, got {true_percentage}% True"


class TestGetAnswersByPrompt:
    """Test retrieving answers for a prompt."""

    def test_get_answers_returns_list(self):
        """Test that get_answers_by_prompt returns list of answers."""
        mock_session = MagicMock()

        # Create mock answers (answer_a and answer_b are computed properties)
        answer1 = MagicMock()
        answer1.id = 1
        answer1.prompt_id = 1
        answer1.answer_x = "X1"
        answer1.answer_y = "Y1"
        answer1.is_x_mapped_to_a = True

        answer2 = MagicMock()
        answer2.id = 2
        answer2.prompt_id = 1
        answer2.answer_x = "X2"
        answer2.answer_y = "Y2"
        answer2.is_x_mapped_to_a = False

        # Mock query chain
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = [answer1, answer2]

        answers = get_answers_by_prompt(mock_session, 1)

        assert len(answers) == 2
        assert answers[0].answer_x == "X1"
        assert answers[1].answer_x == "X2"

    def test_get_answers_empty_list(self):
        """Test that empty list is returned when no answers exist."""
        mock_session = MagicMock()

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = []

        answers = get_answers_by_prompt(mock_session, 1)

        assert answers == []

    @patch('vulcanlab.eval.answers.logger')
    def test_get_answers_logs_count(self, mock_logger):
        """Test that retrieval is logged with count."""
        mock_session = MagicMock()

        # Create mock answer
        answer1 = MagicMock()
        answer1.id = 1
        answer1.prompt_id = 1
        answer1.answer_x = "X"
        answer1.answer_y = "Y"
        answer1.is_x_mapped_to_a = True

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = [answer1]

        answers = get_answers_by_prompt(mock_session, 1)

        mock_logger.debug.assert_called_once()
        log_message = mock_logger.debug.call_args[0][0]
        assert "Retrieved 1 answer pairs" in log_message


class TestGetAnswerById:
    """Test retrieving a single answer by ID."""

    def test_get_answer_by_id_success(self):
        """Test successful retrieval of answer by ID."""
        mock_session = MagicMock()

        # Create mock answer
        mock_answer = MagicMock()
        mock_answer.id = 1
        mock_answer.prompt_id = 1
        mock_answer.answer_x = "Answer X"
        mock_answer.answer_y = "Answer Y"
        mock_answer.is_x_mapped_to_a = True

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_answer

        answer = get_answer_by_id(mock_session, 1)

        assert answer.id == 1
        assert answer.answer_x == "Answer X"

    def test_get_answer_by_id_not_found(self):
        """Test that ValueError is raised when answer not found."""
        mock_session = MagicMock()

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        with pytest.raises(ValueError, match="Answer with id 999 not found"):
            get_answer_by_id(mock_session, 999)

    @patch('vulcanlab.eval.answers.logger')
    def test_get_answer_by_id_logs_warning_on_not_found(self, mock_logger):
        """Test that warning is logged when answer not found."""
        mock_session = MagicMock()

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        with pytest.raises(ValueError):
            get_answer_by_id(mock_session, 999)

        mock_logger.warning.assert_called_once()
        assert "Answer not found" in mock_logger.warning.call_args[0][0]
