"""
Unit tests for evaluation experiment API endpoints.

Tests API router endpoints with mocked database and core logic.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.experiment import Experiment
from vulcanlab_api.routers.eval import (
    list_experiments,
    get_experiment,
    create_new_experiment,
    delete_experiment_endpoint,
)
from vulcanlab_api.schemas.eval import ExperimentCreate


@pytest.mark.asyncio
class TestListExperiments:
    """Test GET /experiments endpoint."""

    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_list_experiments_success(self, mock_get_session):
        """Test successful listing of experiments."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()
        # Mock the query chain
        mock_query_result = [
            (Experiment(id=1, name="Exp 1", description_x="X1", description_y="Y1", created_at=now, updated_at=now), 5, 3),
            (Experiment(id=2, name="Exp 2", description_x="X2", description_y="Y2", created_at=now, updated_at=now), 2, 1),
        ]

        mock_query = mock_session.query.return_value
        mock_outerjoin1 = mock_query.outerjoin.return_value
        mock_outerjoin2 = mock_outerjoin1.outerjoin.return_value
        mock_outerjoin3 = mock_outerjoin2.outerjoin.return_value
        mock_group_by = mock_outerjoin3.group_by.return_value
        mock_order_by = mock_group_by.order_by.return_value
        mock_order_by.all.return_value = mock_query_result

        result = await list_experiments()

        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == "Exp 1"
        assert result[0].prompt_count == 5
        assert result[0].eval_count == 3
        assert result[1].id == 2
        assert result[1].name == "Exp 2"
        assert result[1].prompt_count == 2
        assert result[1].eval_count == 1

    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_list_experiments_empty(self, mock_get_session):
        """Test listing experiments when none exist."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        mock_query = mock_session.query.return_value
        mock_outerjoin1 = mock_query.outerjoin.return_value
        mock_outerjoin2 = mock_outerjoin1.outerjoin.return_value
        mock_outerjoin3 = mock_outerjoin2.outerjoin.return_value
        mock_group_by = mock_outerjoin3.group_by.return_value
        mock_order_by = mock_group_by.order_by.return_value
        mock_order_by.all.return_value = []

        result = await list_experiments()

        assert len(result) == 0
        assert result == []

    @patch('vulcanlab_api.routers.eval.get_session')
    async def test_list_experiments_error(self, mock_get_session):
        """Test error handling when listing experiments fails."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            await list_experiments()

        assert exc_info.value.status_code == 500
        assert "Failed to list experiments" in exc_info.value.detail


@pytest.mark.asyncio
class TestGetExperiment:
    """Test GET /experiments/{id} endpoint."""

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    async def test_get_experiment_success(self, mock_get_exp, mock_get_session):
        """Test successful retrieval of experiment."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()
        mock_experiment = Experiment(
            id=1,
            name="Test Experiment",
            description_x="X desc",
            description_y="Y desc",
            model_x="gpt-4",
            model_y="claude",
            judge_model="gpt-4o",
            created_at=now,
            updated_at=now,
        )
        mock_get_exp.return_value = mock_experiment

        result = await get_experiment(1)

        assert result.id == 1
        assert result.name == "Test Experiment"
        assert result.model_x == "gpt-4"
        mock_get_exp.assert_called_once_with(mock_session, 1)

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    async def test_get_experiment_not_found(self, mock_get_exp, mock_get_session):
        """Test 404 when experiment not found."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_exp.side_effect = ValueError("Experiment with id 999 not found")

        with pytest.raises(HTTPException) as exc_info:
            await get_experiment(999)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.get_experiment_by_id')
    async def test_get_experiment_error(self, mock_get_exp, mock_get_session):
        """Test error handling when retrieval fails."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_exp.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            await get_experiment(1)

        assert exc_info.value.status_code == 500
        assert "Failed to get experiment" in exc_info.value.detail


@pytest.mark.asyncio
class TestCreateExperiment:
    """Test POST /experiments endpoint."""

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.create_experiment')
    async def test_create_experiment_success(self, mock_create_exp, mock_get_session):
        """Test successful creation of experiment."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        now = datetime.now()
        mock_experiment = Experiment(
            id=1,
            name="New Experiment",
            description_x="X desc",
            description_y="Y desc",
            model_x="gpt-4",
            model_y="claude",
            judge_model="gpt-4o",
            created_at=now,
            updated_at=now,
        )
        mock_create_exp.return_value = mock_experiment

        request_data = ExperimentCreate(
            name="New Experiment",
            description_x="X desc",
            description_y="Y desc",
            model_x="gpt-4",
            model_y="claude",
            judge_model="gpt-4o",
        )

        result = await create_new_experiment(request_data)

        assert result.id == 1
        assert result.name == "New Experiment"
        mock_create_exp.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_experiment)

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.create_experiment')
    async def test_create_experiment_validation_error(self, mock_create_exp, mock_get_session):
        """Test 400 when validation fails."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_create_exp.side_effect = ValueError("Experiment name is required")

        # Use a whitespace-only name which passes pydantic but fails business logic
        request_data = ExperimentCreate(name=" ")

        with pytest.raises(HTTPException) as exc_info:
            await create_new_experiment(request_data)

        assert exc_info.value.status_code == 400
        assert "required" in exc_info.value.detail.lower()

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.create_experiment')
    async def test_create_experiment_integrity_error(self, mock_create_exp, mock_get_session):
        """Test 409 when integrity constraint violated."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_create_exp.side_effect = IntegrityError("", "", "")

        request_data = ExperimentCreate(name="Test")

        with pytest.raises(HTTPException) as exc_info:
            await create_new_experiment(request_data)

        assert exc_info.value.status_code == 409
        assert "Integrity constraint violation" in exc_info.value.detail

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.create_experiment')
    async def test_create_experiment_error(self, mock_create_exp, mock_get_session):
        """Test error handling when creation fails."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_create_exp.side_effect = Exception("Database error")

        request_data = ExperimentCreate(name="Test")

        with pytest.raises(HTTPException) as exc_info:
            await create_new_experiment(request_data)

        assert exc_info.value.status_code == 500
        assert "Failed to create experiment" in exc_info.value.detail


@pytest.mark.asyncio
class TestDeleteExperiment:
    """Test DELETE /experiments/{id} endpoint."""

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.delete_experiment')
    async def test_delete_experiment_success(self, mock_delete_exp, mock_get_session):
        """Test successful deletion of experiment."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_delete_exp.return_value = None

        await delete_experiment_endpoint(1)

        mock_delete_exp.assert_called_once_with(mock_session, 1)
        mock_session.commit.assert_called_once()

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.delete_experiment')
    async def test_delete_experiment_not_found(self, mock_delete_exp, mock_get_session):
        """Test 404 when experiment not found."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_delete_exp.side_effect = ValueError("Experiment with id 999 not found")

        with pytest.raises(HTTPException) as exc_info:
            await delete_experiment_endpoint(999)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.delete_experiment')
    async def test_delete_experiment_error(self, mock_delete_exp, mock_get_session):
        """Test error handling when deletion fails."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_delete_exp.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            await delete_experiment_endpoint(1)

        assert exc_info.value.status_code == 500
        assert "Failed to delete experiment" in exc_info.value.detail
