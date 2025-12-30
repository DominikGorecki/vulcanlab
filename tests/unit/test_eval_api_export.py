"""
Unit tests for evaluation CSV export API endpoint.

Tests GET /api/v1/eval/experiments/{id}/export-csv.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from vulcanlab_api.routers.eval import export_experiment_evaluations_csv


@pytest.mark.asyncio
class TestExportExperimentEvaluationsCSV:
    """Test GET /experiments/{id}/export-csv endpoint."""

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.export_experiment_evaluations_to_csv')
    async def test_export_csv_success(self, mock_export, mock_get_session):
        """Test successful CSV export."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        csv_content = "prompt,grouping_id,overall_score,justification\nP1,1,5,J1"
        mock_export.return_value = csv_content
        
        experiment_id = 123
        response = await export_experiment_evaluations_csv(experiment_id)
        
        assert response.status_code == 200
        assert response.media_type == "text/csv"
        assert response.headers["Content-Disposition"] == f"attachment; filename=experiment_{experiment_id}_evaluations.csv"
        # Since it's a Response object, the body is stored in .body
        assert response.body.decode() == csv_content
        
        mock_export.assert_called_once_with(mock_session, experiment_id)

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.export_experiment_evaluations_to_csv')
    async def test_export_csv_not_found(self, mock_export, mock_get_session):
        """Test 404 when experiment does not exist."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_export.side_effect = ValueError("Experiment with id 999 not found")
        
        with pytest.raises(HTTPException) as exc_info:
            await export_experiment_evaluations_csv(999)
            
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @patch('vulcanlab_api.routers.eval.get_session')
    @patch('vulcanlab_api.routers.eval.export_experiment_evaluations_to_csv')
    async def test_export_csv_error(self, mock_export, mock_get_session):
        """Test 500 when an unexpected error occurs."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_export.side_effect = Exception("Unexpected error")
        
        with pytest.raises(HTTPException) as exc_info:
            await export_experiment_evaluations_csv(1)
            
        assert exc_info.value.status_code == 500
        assert "Failed to export CSV" in exc_info.value.detail

