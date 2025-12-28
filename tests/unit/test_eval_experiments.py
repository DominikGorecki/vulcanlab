"""
Unit tests for experiment core logic.

Tests CRUD operations for experiments with mocked database sessions.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.experiment import Experiment
from vulcanlab.eval.experiments import (
    create_experiment,
    get_experiments,
    get_experiment_by_id,
    delete_experiment,
)


class TestCreateExperiment:
    """Test experiment creation logic."""

    def test_create_experiment_with_all_fields(self):
        """Test creating experiment with all fields populated."""
        mock_session = MagicMock()

        experiment = create_experiment(
            session=mock_session,
            name="Test Experiment",
            description_x="GPT-4 answers",
            description_y="Claude answers",
            model_x="gpt-4",
            model_y="claude-sonnet-3.5",
            judge_model="gpt-4o",
            eval_template_id=1
        )

        # Verify experiment was created
        assert experiment.name == "Test Experiment"
        assert experiment.description_x == "GPT-4 answers"
        assert experiment.description_y == "Claude answers"
        assert experiment.model_x == "gpt-4"
        assert experiment.model_y == "claude-sonnet-3.5"
        assert experiment.judge_model == "gpt-4o"
        assert experiment.eval_template_id == 1

        # Verify session.add was called (1 experiment + 5 core dimensions = 6 calls)
        assert mock_session.add.call_count == 6
        # Verify flush was called (1 for experiment + 5 for dimensions = 6 calls)
        assert mock_session.flush.call_count == 6

    def test_create_experiment_minimal(self):
        """Test creating experiment with only required fields."""
        mock_session = MagicMock()

        experiment = create_experiment(
            session=mock_session,
            name="Minimal Experiment"
        )

        assert experiment.name == "Minimal Experiment"
        assert experiment.description_x is None
        assert experiment.description_y is None
        assert experiment.model_x is None
        assert experiment.model_y is None
        assert experiment.judge_model is None
        assert experiment.eval_template_id is None

        # Verify session.add was called (1 experiment + 5 core dimensions = 6 calls)
        assert mock_session.add.call_count == 6
        # Verify flush was called (1 for experiment + 5 for dimensions = 6 calls)
        assert mock_session.flush.call_count == 6

    def test_create_experiment_strips_whitespace(self):
        """Test that whitespace is stripped from fields."""
        mock_session = MagicMock()

        experiment = create_experiment(
            session=mock_session,
            name="  Test Experiment  ",
            description_x="  Description X  ",
            model_x="  gpt-4  "
        )

        assert experiment.name == "Test Experiment"
        assert experiment.description_x == "Description X"
        assert experiment.model_x == "gpt-4"

    def test_create_experiment_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        mock_session = MagicMock()

        with pytest.raises(ValueError, match="Experiment name is required"):
            create_experiment(session=mock_session, name="")

        with pytest.raises(ValueError, match="Experiment name is required"):
            create_experiment(session=mock_session, name="   ")

        mock_session.add.assert_not_called()

    def test_create_experiment_integrity_error_rollback(self):
        """Test that IntegrityError triggers rollback."""
        mock_session = MagicMock()
        mock_session.flush.side_effect = IntegrityError("", "", "")

        with pytest.raises(IntegrityError):
            create_experiment(session=mock_session, name="Test")

        mock_session.rollback.assert_called_once()

    @patch('vulcanlab.eval.experiments.logger')
    def test_create_experiment_logs_creation(self, mock_logger):
        """Test that experiment creation is logged."""
        mock_session = MagicMock()
        mock_experiment = MagicMock()
        mock_experiment.id = 123
        mock_experiment.name = "Test Experiment"

        # Make the experiment returned from add have an ID
        def set_id(exp):
            exp.id = 123

        mock_session.flush.side_effect = lambda: set_id(mock_session.add.call_args[0][0])

        with patch('vulcanlab.eval.experiments.Experiment', return_value=mock_experiment):
            experiment = create_experiment(session=mock_session, name="Test Experiment")

        mock_logger.info.assert_called_once()
        assert "Created experiment" in str(mock_logger.info.call_args)


class TestGetExperiments:
    """Test listing all experiments."""

    def test_get_experiments_returns_list(self):
        """Test that get_experiments returns list of experiments."""
        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_order_by = mock_query.order_by.return_value
        mock_order_by.all.return_value = [
            Experiment(id=1, name="Exp 1"),
            Experiment(id=2, name="Exp 2"),
            Experiment(id=3, name="Exp 3"),
        ]

        experiments = get_experiments(mock_session)

        assert len(experiments) == 3
        assert experiments[0].name == "Exp 1"
        assert experiments[1].name == "Exp 2"
        assert experiments[2].name == "Exp 3"

        # Verify query was called correctly
        mock_session.query.assert_called_once_with(Experiment)
        mock_query.order_by.assert_called_once()

    def test_get_experiments_empty_list(self):
        """Test that get_experiments handles empty database."""
        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_order_by = mock_query.order_by.return_value
        mock_order_by.all.return_value = []

        experiments = get_experiments(mock_session)

        assert len(experiments) == 0
        assert experiments == []


class TestGetExperimentById:
    """Test retrieving experiment by ID."""

    def test_get_experiment_by_id_success(self):
        """Test successful retrieval of experiment by ID."""
        mock_session = MagicMock()
        mock_experiment = Experiment(id=1, name="Test Experiment")

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_experiment

        experiment = get_experiment_by_id(mock_session, 1)

        assert experiment.id == 1
        assert experiment.name == "Test Experiment"

    def test_get_experiment_by_id_not_found(self):
        """Test that ValueError is raised when experiment not found."""
        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        with pytest.raises(ValueError, match="Experiment with id 999 not found"):
            get_experiment_by_id(mock_session, 999)


class TestDeleteExperiment:
    """Test experiment deletion."""

    def test_delete_experiment_success(self):
        """Test successful deletion of experiment."""
        mock_session = MagicMock()
        mock_experiment = Experiment(id=1, name="Test Experiment")

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_experiment

        delete_experiment(mock_session, 1)

        # Verify delete and flush were called
        mock_session.delete.assert_called_once_with(mock_experiment)
        mock_session.flush.assert_called_once()

    def test_delete_experiment_not_found(self):
        """Test that ValueError is raised when deleting non-existent experiment."""
        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        with pytest.raises(ValueError, match="Experiment with id 999 not found"):
            delete_experiment(mock_session, 999)

        # Verify delete was not called
        mock_session.delete.assert_not_called()

    @patch('vulcanlab.eval.experiments.logger')
    def test_delete_experiment_logs_deletion(self, mock_logger):
        """Test that experiment deletion is logged."""
        mock_session = MagicMock()
        mock_experiment = Experiment(id=1, name="Test Experiment")

        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_experiment

        delete_experiment(mock_session, 1)

        mock_logger.info.assert_called_once()
        assert "Deleted experiment" in str(mock_logger.info.call_args)
        assert "cascade deleted" in str(mock_logger.info.call_args).lower()
