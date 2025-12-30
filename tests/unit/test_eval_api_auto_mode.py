"""
Unit tests for automatic mode API endpoint (T03).

Tests PATCH /experiments/{id} endpoint with mocked database and validation.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from vulcanlab.data.models.experiment import Experiment
from vulcanlab_api.routers.eval import update_experiment
from vulcanlab_api.schemas.eval import ExperimentUpdateRequest


@pytest.mark.asyncio
class TestUpdateExperimentAutoMode:
    """Test PATCH /experiments/{id} endpoint for auto mode settings."""

    @patch('vulcanlab_api.routers.eval.validate_api_keys_for_auto_mode')
    @patch('vulcanlab_api.routers.eval.get_opposite_provider')
    @patch('vulcanlab_api.routers.eval.compute_experiment_statistics')
    @patch('vulcanlab_api.routers.eval.get_dimensions_by_experiment')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_enable_auto_mode_openai(
        self,
        mock_get_session,
        mock_get_exp,
        mock_get_dims,
        mock_compute_stats,
        mock_get_opposite,
        mock_validate
    ):
        """Test enabling auto mode with OpenAI as answer provider."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()
        mock_experiment = Experiment(
            id=1,
            name="Test Exp",
            description_x="X",
            description_y="Y",
            auto_mode_enabled=False,
            auto_answer_provider=None,
            auto_judge_provider=None,
            created_at=now,
            updated_at=now
        )
        mock_get_exp.return_value = mock_experiment
        mock_get_dims.return_value = []
        mock_compute_stats.return_value = {
            "eval_count": 0,
            "x_win_rate": 0.0,
            "mean_score": 0.0,
            "median_score": 0.0,
            "tie_percentage": 0.0,
            "harm_rate": 0.0,
            "wilcoxon_p_value": None,
        }
        mock_validate.return_value = (True, "")
        mock_get_opposite.return_value = "gemini"

        # Create request
        request = ExperimentUpdateRequest(
            auto_mode_enabled=True,
            auto_answer_provider="openai"
        )

        # Execute
        result = await update_experiment(1, request)

        # Verify
        assert result.id == 1
        assert result.auto_mode_enabled is True
        assert result.auto_answer_provider == "openai"
        assert result.auto_judge_provider == "gemini"
        mock_validate.assert_called_once()
        mock_get_opposite.assert_called_once_with("openai")
        mock_session.commit.assert_called_once()

    @patch('vulcanlab_api.routers.eval.validate_api_keys_for_auto_mode')
    @patch('vulcanlab_api.routers.eval.get_opposite_provider')
    @patch('vulcanlab_api.routers.eval.compute_experiment_statistics')
    @patch('vulcanlab_api.routers.eval.get_dimensions_by_experiment')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_enable_auto_mode_gemini(
        self,
        mock_get_session,
        mock_get_exp,
        mock_get_dims,
        mock_compute_stats,
        mock_get_opposite,
        mock_validate
    ):
        """Test enabling auto mode with Gemini as answer provider."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()
        mock_experiment = Experiment(
            id=1,
            name="Test Exp",
            description_x="X",
            description_y="Y",
            auto_mode_enabled=False,
            auto_answer_provider=None,
            auto_judge_provider=None,
            created_at=now,
            updated_at=now
        )
        mock_get_exp.return_value = mock_experiment
        mock_get_dims.return_value = []
        mock_compute_stats.return_value = {
            "eval_count": 0,
            "x_win_rate": 0.0,
            "mean_score": 0.0,
            "median_score": 0.0,
            "tie_percentage": 0.0,
            "harm_rate": 0.0,
            "wilcoxon_p_value": None,
        }
        mock_validate.return_value = (True, "")
        mock_get_opposite.return_value = "openai"

        # Create request
        request = ExperimentUpdateRequest(
            auto_mode_enabled=True,
            auto_answer_provider="gemini"
        )

        # Execute
        result = await update_experiment(1, request)

        # Verify
        assert result.auto_mode_enabled is True
        assert result.auto_answer_provider == "gemini"
        assert result.auto_judge_provider == "openai"
        mock_get_opposite.assert_called_once_with("gemini")

    @patch('vulcanlab_api.routers.eval.validate_api_keys_for_auto_mode')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_enable_auto_mode_invalid_api_keys(
        self,
        mock_get_session,
        mock_get_exp,
        mock_validate
    ):
        """Test that enabling auto mode fails when API keys are invalid."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()
        mock_experiment = Experiment(
            id=1,
            name="Test Exp",
            description_x="X",
            description_y="Y",
            created_at=now,
            updated_at=now
        )
        mock_get_exp.return_value = mock_experiment
        mock_validate.return_value = (False, "OpenAI API key is not configured")

        # Create request
        request = ExperimentUpdateRequest(
            auto_mode_enabled=True,
            auto_answer_provider="openai"
        )

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await update_experiment(1, request)

        assert exc_info.value.status_code == 400
        assert "OpenAI API key" in exc_info.value.detail
        mock_validate.assert_called_once()
        mock_session.commit.assert_not_called()

    @patch('vulcanlab_api.routers.eval.compute_experiment_statistics')
    @patch('vulcanlab_api.routers.eval.get_dimensions_by_experiment')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_disable_auto_mode(
        self,
        mock_get_session,
        mock_get_exp,
        mock_get_dims,
        mock_compute_stats
    ):
        """Test disabling auto mode clears providers."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()
        mock_experiment = Experiment(
            id=1,
            name="Test Exp",
            description_x="X",
            description_y="Y",
            auto_mode_enabled=True,
            auto_answer_provider="openai",
            auto_judge_provider="gemini",
            created_at=now,
            updated_at=now
        )
        mock_get_exp.return_value = mock_experiment
        mock_get_dims.return_value = []
        mock_compute_stats.return_value = {
            "eval_count": 0,
            "x_win_rate": 0.0,
            "mean_score": 0.0,
            "median_score": 0.0,
            "tie_percentage": 0.0,
            "harm_rate": 0.0,
            "wilcoxon_p_value": None,
        }

        # Create request
        request = ExperimentUpdateRequest(
            auto_mode_enabled=False,
            auto_answer_provider=None
        )

        # Execute
        result = await update_experiment(1, request)

        # Verify
        assert result.auto_mode_enabled is False
        assert result.auto_answer_provider is None
        assert result.auto_judge_provider is None
        mock_session.commit.assert_called_once()

    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_update_experiment_not_found(
        self,
        mock_get_session,
        mock_get_exp
    ):
        """Test that updating non-existent experiment returns 404."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_exp.side_effect = ValueError("Experiment with id 999 not found")

        # Create request
        request = ExperimentUpdateRequest(
            auto_mode_enabled=True,
            auto_answer_provider="openai"
        )

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await update_experiment(999, request)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @patch('vulcanlab_api.routers.eval.validate_api_keys_for_auto_mode')
    @patch('vulcanlab_api.routers.eval.get_opposite_provider')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_update_experiment_database_error(
        self,
        mock_get_session,
        mock_get_exp,
        mock_get_opposite,
        mock_validate
    ):
        """Test error handling when database commit fails."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()
        mock_experiment = Experiment(
            id=1,
            name="Test Exp",
            description_x="X",
            description_y="Y",
            created_at=now,
            updated_at=now
        )
        mock_get_exp.return_value = mock_experiment
        mock_validate.return_value = (True, "")
        mock_get_opposite.return_value = "gemini"
        mock_session.commit.side_effect = Exception("Database error")

        # Create request
        request = ExperimentUpdateRequest(
            auto_mode_enabled=True,
            auto_answer_provider="openai"
        )

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await update_experiment(1, request)

        assert exc_info.value.status_code == 500
        assert "Failed to update experiment" in exc_info.value.detail

    @patch('vulcanlab_api.routers.eval.validate_api_keys_for_auto_mode')
    @patch('vulcanlab_api.routers.eval.get_opposite_provider')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_enable_auto_mode_validation_called_first(
        self,
        mock_get_session,
        mock_get_exp,
        mock_get_opposite,
        mock_validate
    ):
        """Test that API key validation happens before any database changes."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()
        mock_experiment = Experiment(
            id=1,
            name="Test Exp",
            description_x="X",
            description_y="Y",
            created_at=now,
            updated_at=now
        )
        mock_get_exp.return_value = mock_experiment
        mock_validate.return_value = (False, "Both API keys required")

        # Create request
        request = ExperimentUpdateRequest(
            auto_mode_enabled=True,
            auto_answer_provider="openai"
        )

        # Execute and verify exception
        with pytest.raises(HTTPException):
            await update_experiment(1, request)

        # Verify database was not modified
        mock_session.commit.assert_not_called()
        mock_get_opposite.assert_not_called()

    @patch('vulcanlab_api.routers.eval.validate_api_keys_for_auto_mode')
    @patch('vulcanlab_api.routers.eval.compute_experiment_statistics')
    @patch('vulcanlab_api.routers.eval.get_dimensions_by_experiment')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_disable_auto_mode_no_validation(
        self,
        mock_get_session,
        mock_get_exp,
        mock_get_dims,
        mock_compute_stats,
        mock_validate
    ):
        """Test that disabling auto mode does not trigger validation."""
        # Setup mocks
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()
        mock_experiment = Experiment(
            id=1,
            name="Test Exp",
            description_x="X",
            description_y="Y",
            auto_mode_enabled=True,
            auto_answer_provider="openai",
            auto_judge_provider="gemini",
            created_at=now,
            updated_at=now
        )
        mock_get_exp.return_value = mock_experiment
        mock_get_dims.return_value = []
        mock_compute_stats.return_value = {
            "eval_count": 0,
            "x_win_rate": 0.0,
            "mean_score": 0.0,
            "median_score": 0.0,
            "tie_percentage": 0.0,
            "harm_rate": 0.0,
            "wilcoxon_p_value": None,
        }

        # Create request
        request = ExperimentUpdateRequest(
            auto_mode_enabled=False,
            auto_answer_provider=None
        )

        # Execute
        await update_experiment(1, request)

        # Verify validation was not called
        mock_validate.assert_not_called()
