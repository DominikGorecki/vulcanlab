"""
Unit tests for prompt core logic.

Tests CRUD operations for prompts with mocked database sessions.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.experiment import ExperimentPrompt
from vulcanlab.eval.prompts import (
    create_prompt,
    get_prompts_by_experiment,
    get_prompt_by_id,
    delete_prompt,
)


class TestCreatePrompt:
    """Test prompt creation logic."""

    def test_create_prompt_success(self):
        """Test creating prompt with valid data."""
        mock_session = MagicMock()

        prompt = create_prompt(
            session=mock_session,
            experiment_id=1,
            prompt_text="What is the capital of France?"
        )

        # Verify prompt was created with correct data
        assert prompt.experiment_id == 1
        assert prompt.prompt_text == "What is the capital of France?"

        # Verify session methods called
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_create_prompt_strips_whitespace(self):
        """Test that prompt text is stripped of leading/trailing whitespace."""
        mock_session = MagicMock()

        prompt = create_prompt(
            session=mock_session,
            experiment_id=1,
            prompt_text="  What is AI?  \n"
        )

        assert prompt.prompt_text == "What is AI?"

    def test_create_prompt_empty_text_raises_error(self):
        """Test that empty prompt text raises ValueError."""
        mock_session = MagicMock()

        with pytest.raises(ValueError, match="Prompt text is required"):
            create_prompt(
                session=mock_session,
                experiment_id=1,
                prompt_text=""
            )

        mock_session.add.assert_not_called()

    def test_create_prompt_whitespace_only_raises_error(self):
        """Test that whitespace-only prompt text raises ValueError."""
        mock_session = MagicMock()

        with pytest.raises(ValueError, match="Prompt text is required"):
            create_prompt(
                session=mock_session,
                experiment_id=1,
                prompt_text="   \n\t  "
            )

        mock_session.add.assert_not_called()

    def test_create_prompt_integrity_error(self):
        """Test that IntegrityError is handled correctly."""
        mock_session = MagicMock()
        mock_session.flush.side_effect = IntegrityError("statement", "params", "orig")

        with pytest.raises(IntegrityError):
            create_prompt(
                session=mock_session,
                experiment_id=999,  # Non-existent experiment
                prompt_text="Test prompt"
            )

        mock_session.rollback.assert_called_once()

    @patch('vulcanlab.eval.prompts.logger')
    def test_create_prompt_logs_success(self, mock_logger):
        """Test that successful creation is logged."""
        mock_session = MagicMock()

        prompt = create_prompt(
            session=mock_session,
            experiment_id=1,
            prompt_text="Test prompt"
        )

        # Verify info log was called
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "Created prompt" in log_message
        assert "experiment_id=1" in log_message


class TestGetPromptsByExperiment:
    """Test retrieving prompts for an experiment."""

    def test_get_prompts_returns_list(self):
        """Test that get_prompts_by_experiment returns list of prompts."""
        mock_session = MagicMock()

        # Mock query chain
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = [
            ExperimentPrompt(id=1, experiment_id=1, prompt_text="Prompt 1"),
            ExperimentPrompt(id=2, experiment_id=1, prompt_text="Prompt 2"),
        ]

        prompts = get_prompts_by_experiment(mock_session, 1)

        assert len(prompts) == 2
        assert prompts[0].prompt_text == "Prompt 1"
        assert prompts[1].prompt_text == "Prompt 2"

    def test_get_prompts_empty_list(self):
        """Test that empty list is returned when no prompts exist."""
        mock_session = MagicMock()

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = []

        prompts = get_prompts_by_experiment(mock_session, 1)

        assert prompts == []

    @patch('vulcanlab.eval.prompts.logger')
    def test_get_prompts_logs_count(self, mock_logger):
        """Test that retrieval is logged with count."""
        mock_session = MagicMock()

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = [
            ExperimentPrompt(id=1, experiment_id=1, prompt_text="Prompt 1"),
        ]

        prompts = get_prompts_by_experiment(mock_session, 1)

        mock_logger.debug.assert_called_once()
        log_message = mock_logger.debug.call_args[0][0]
        assert "Retrieved 1 prompts" in log_message


class TestGetPromptById:
    """Test retrieving a single prompt by ID."""

    def test_get_prompt_by_id_success(self):
        """Test successful retrieval of prompt by ID."""
        mock_session = MagicMock()
        mock_prompt = ExperimentPrompt(
            id=1,
            experiment_id=1,
            prompt_text="Test prompt"
        )

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_prompt

        prompt = get_prompt_by_id(mock_session, 1)

        assert prompt.id == 1
        assert prompt.prompt_text == "Test prompt"

    def test_get_prompt_by_id_not_found(self):
        """Test that ValueError is raised when prompt not found."""
        mock_session = MagicMock()

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        with pytest.raises(ValueError, match="Prompt with id 999 not found"):
            get_prompt_by_id(mock_session, 999)

    @patch('vulcanlab.eval.prompts.logger')
    def test_get_prompt_by_id_logs_warning_on_not_found(self, mock_logger):
        """Test that warning is logged when prompt not found."""
        mock_session = MagicMock()

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        with pytest.raises(ValueError):
            get_prompt_by_id(mock_session, 999)

        mock_logger.warning.assert_called_once()
        assert "Prompt not found" in mock_logger.warning.call_args[0][0]


class TestDeletePrompt:
    """Test deleting a prompt."""

    def test_delete_prompt_success(self):
        """Test successful deletion of prompt."""
        mock_session = MagicMock()
        mock_prompt = ExperimentPrompt(
            id=1,
            experiment_id=1,
            prompt_text="Test prompt"
        )

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_prompt

        delete_prompt(mock_session, 1)

        # Verify delete was called
        mock_session.delete.assert_called_once_with(mock_prompt)
        mock_session.flush.assert_called_once()

    def test_delete_prompt_not_found(self):
        """Test that ValueError is raised when deleting non-existent prompt."""
        mock_session = MagicMock()

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        with pytest.raises(ValueError, match="Prompt with id 999 not found"):
            delete_prompt(mock_session, 999)

        mock_session.delete.assert_not_called()

    @patch('vulcanlab.eval.prompts.logger')
    def test_delete_prompt_logs_success(self, mock_logger):
        """Test that successful deletion is logged."""
        mock_session = MagicMock()
        mock_prompt = ExperimentPrompt(
            id=1,
            experiment_id=1,
            prompt_text="Test prompt"
        )

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_prompt

        delete_prompt(mock_session, 1)

        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "Deleted prompt" in log_message
        assert "id=1" in log_message
