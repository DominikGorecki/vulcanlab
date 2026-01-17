"""
Unit tests for summarization retrieval endpoints.
"""

from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from vulcanlab_api.main import app
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.summary_result import SummaryResult
from vulcanlab.data.models.chunk import Chunk

client = TestClient(app)


class TestSummarizeRouterRetrieval:
    """Test suite for /api/v1/summarize/works retrieval endpoints."""

    @patch('vulcanlab_api.routers.summarize.get_session')
    def test_get_summary_success(self, mock_get_session):
        """Test successful retrieval of work summary."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock Work
        mock_work = MagicMock(spec=Work)
        mock_work.id = 1
        mock_work.title = "Test Work"
        mock_session.get.return_value = mock_work
        
        # Mock SummaryResult and Chunk rows
        res1 = MagicMock(spec=SummaryResult)
        res1.chunk_id = 101
        res1.summary_content = "Summary 1"
        
        chunk1 = MagicMock(spec=Chunk)
        chunk1.heading_title = "Heading 1"
        chunk1.start_line = 10
        
        res2 = MagicMock(spec=SummaryResult)
        res2.chunk_id = 102
        res2.summary_content = "Summary 2"
        
        chunk2 = MagicMock(spec=Chunk)
        chunk2.heading_title = "Heading 2"
        chunk2.start_line = 50
        
        mock_session.execute.return_value.all.return_value = [
            (res1, chunk1),
            (res2, chunk2)
        ]
        
        response = client.get("/api/v1/summarize/works/1/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["work_id"] == 1
        assert data["work_title"] == "Test Work"
        assert len(data["sections"]) == 2
        assert data["sections"][0]["heading"] == "Heading 1"
        assert data["sections"][1]["heading"] == "Heading 2"
        assert data["sections"][0]["start_line"] == 10

    @patch('vulcanlab_api.routers.summarize.get_session')
    def test_get_summary_no_summaries(self, mock_get_session):
        """Test 404 when no summaries exist for work."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_work = MagicMock(spec=Work)
        mock_session.get.return_value = mock_work
        
        mock_session.execute.return_value.all.return_value = []
        
        response = client.get("/api/v1/summarize/works/1/summary")
        assert response.status_code == 404
        assert "No summaries found" in response.json()["detail"]

    @patch('vulcanlab_api.routers.summarize.get_session')
    def test_list_works_with_summaries(self, mock_get_session):
        """Test listing works that have summaries."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock row data
        row1 = MagicMock()
        row1.id = 1
        row1.title = "Work 1"
        row1.summary_count = 5
        row1.last_updated = datetime(2023, 1, 1, tzinfo=timezone.utc)
        
        row2 = MagicMock()
        row2.id = 2
        row2.title = "Work 2"
        row2.summary_count = 3
        row2.last_updated = datetime(2023, 1, 2, tzinfo=timezone.utc)
        
        mock_session.execute.return_value.all.return_value = [row2, row1] # Descending order
        
        response = client.get("/api/v1/summarize/works")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["works"]) == 2
        assert data["works"][0]["work_id"] == 2
        assert data["works"][0]["summary_count"] == 3
        assert "2023-01-02" in data["works"][0]["last_updated"]
