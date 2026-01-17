"""
Unit tests for summarization submit-response endpoint.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from vulcanlab_api.main import app
from vulcanlab.data.models.work import Work
from vulcanlab.summarization.summary_storage import SummaryParseResult

client = TestClient(app)


class TestSummarizeRouterSubmit:
    """Test suite for /api/v1/summarize/works/{work_id}/submit-response."""

    @patch('vulcanlab_api.routers.summarize.get_session')
    @patch('vulcanlab_api.routers.summarize.process_llm_response')
    def test_submit_response_success(self, mock_process, mock_get_session):
        """Test successful response submission."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock Work
        mock_work = MagicMock(spec=Work)
        mock_work.id = 1
        mock_session.get.return_value = mock_work
        
        # Mock expected heading IDs lookup
        mock_session.execute.return_value.scalars.return_value.all.return_value = [101, 102]
        
        # Mock process_llm_response
        mock_process.return_value = SummaryParseResult(
            success=True,
            summaries_saved=2,
            errors=[]
        )
        
        payload = {
            "prompt_index": 0,
            "response_json": '[{"id": 101, "summary": "S1"}, {"id": 102, "summary": "S2"}]'
        }
        
        response = client.post("/api/v1/summarize/works/1/submit-response", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summaries_saved"] == 2
        assert data["errors"] == []
        
        # Verify process_llm_response was called with correct arguments
        mock_process.assert_called_once_with(
            work_id=1,
            prompt_index=0,
            response_json=payload["response_json"],
            expected_heading_ids=[101, 102],
            session=mock_session
        )

    @patch('vulcanlab_api.routers.summarize.get_session')
    def test_submit_response_work_not_found(self, mock_get_session):
        """Test submit returns 404 when work not found."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = None
        
        payload = {"prompt_index": 0, "response_json": "{}"}
        response = client.post("/api/v1/summarize/works/999/submit-response", json=payload)
        assert response.status_code == 404

    @patch('vulcanlab_api.routers.summarize.get_session')
    def test_submit_response_no_expected_headings(self, mock_get_session):
        """Test submit returns 400 when no prompts have been generated."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_work = MagicMock(spec=Work)
        mock_session.get.return_value = mock_work
        
        # No heading IDs found for this prompt index
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        
        payload = {"prompt_index": 0, "response_json": "{}"}
        response = client.post("/api/v1/summarize/works/1/submit-response", json=payload)
        
        assert response.status_code == 400
        assert "No expected headings found" in response.json()["detail"]

    @patch('vulcanlab_api.routers.summarize.get_session')
    @patch('vulcanlab_api.routers.summarize.process_llm_response')
    def test_submit_response_partial_success(self, mock_process, mock_get_session):
        """Test submit returns errors for invalid JSON/partial results."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_work = MagicMock(spec=Work)
        mock_session.get.return_value = mock_work
        mock_session.execute.return_value.scalars.return_value.all.return_value = [101]
        
        mock_process.return_value = SummaryParseResult(
            success=False,
            summaries_saved=0,
            errors=["Invalid JSON syntax"]
        )
        
        payload = {"prompt_index": 0, "response_json": "invalid"}
        response = client.post("/api/v1/summarize/works/1/submit-response", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid JSON syntax" in data["errors"]
