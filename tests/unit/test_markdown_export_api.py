"""
Unit tests for markdown export API endpoints.

Tests POST /api/v1/markdown/export/{work_id} endpoint.

Usage:
    pytest tests/unit/test_markdown_export_api.py -v
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from pathlib import Path

from vulcanlab_api.routers.markdown import router
from vulcanlab_api.dependencies import get_db_session
from fastapi import HTTPException


# Global mock session to control in tests
mock_session_instance = None


def get_mock_db_session():
    """Override dependency to return controllable mock session."""
    return mock_session_instance


# Create test app
app = FastAPI()
app.include_router(router, prefix="/api/v1/markdown")
app.dependency_overrides[get_db_session] = get_mock_db_session

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_session():
    """Reset mock session before each test."""
    global mock_session_instance
    mock_session_instance = MagicMock()
    yield
    mock_session_instance = None


class TestExportWorkEndpoint:
    """Tests for POST /api/v1/markdown/export/{work_id} endpoint."""

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_success(self, mock_export_work):
        """Test successful work export returns correct response."""
        mock_export_work.return_value = "/path/to/exports/test-work.md"

        response = client.post('/api/v1/markdown/export/1')

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['export_path'] == "/path/to/exports/test-work.md"

        # Verify export_work was called with correct arguments
        mock_export_work.assert_called_once_with(1, mock_session_instance)

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_not_found(self, mock_export_work):
        """Test export returns 404 when work not found."""
        mock_export_work.side_effect = HTTPException(status_code=404, detail="Work not found: 999")

        response = client.post('/api/v1/markdown/export/999')

        assert response.status_code == 404
        assert "Work not found" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_markdown_unavailable(self, mock_export_work):
        """Test export returns 400 when markdown unavailable."""
        mock_export_work.side_effect = HTTPException(
            status_code=400,
            detail="No markdown available for work 1 (title: Test Work)"
        )

        response = client.post('/api/v1/markdown/export/1')

        assert response.status_code == 400
        assert "No markdown available" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_write_error(self, mock_export_work):
        """Test export returns 500 on write error."""
        mock_export_work.side_effect = HTTPException(
            status_code=500,
            detail="Failed to write export file: Permission denied"
        )

        response = client.post('/api/v1/markdown/export/1')

        assert response.status_code == 500
        assert "Failed to write export file" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_unexpected_error(self, mock_export_work):
        """Test export handles unexpected errors gracefully."""
        mock_export_work.side_effect = RuntimeError("Unexpected error")

        response = client.post('/api/v1/markdown/export/1')

        assert response.status_code == 500
        assert "Unexpected error during export" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_invalid_id_type(self, mock_export_work):
        """Test export rejects invalid work ID type."""
        response = client.post('/api/v1/markdown/export/invalid')

        # FastAPI will return 422 for validation error
        assert response.status_code == 422

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_response_format(self, mock_export_work):
        """Test export returns correct response format."""
        mock_export_work.return_value = "/exports/psychology-book.md"

        response = client.post('/api/v1/markdown/export/42')

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert isinstance(data, dict)
        assert 'success' in data
        assert 'export_path' in data
        assert isinstance(data['success'], bool)
        assert isinstance(data['export_path'], str)

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_zero_id(self, mock_export_work):
        """Test export with work ID zero."""
        mock_export_work.side_effect = HTTPException(status_code=404, detail="Work not found: 0")

        response = client.post('/api/v1/markdown/export/0')

        assert response.status_code == 404

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_negative_id(self, mock_export_work):
        """Test export with negative work ID."""
        mock_export_work.side_effect = HTTPException(status_code=404, detail="Work not found: -1")

        response = client.post('/api/v1/markdown/export/-1')

        # Should still process (DB won't find it)
        assert response.status_code == 404

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_large_id(self, mock_export_work):
        """Test export with large work ID."""
        large_id = 999999999
        mock_export_work.return_value = f"/exports/work-{large_id}.md"

        response = client.post(f'/api/v1/markdown/export/{large_id}')

        assert response.status_code == 200
        mock_export_work.assert_called_once_with(large_id, mock_session_instance)

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_session_passed(self, mock_export_work):
        """Test that database session is passed to export_work."""
        mock_export_work.return_value = "/exports/test.md"

        response = client.post('/api/v1/markdown/export/1')

        # Verify session was passed as second argument
        assert response.status_code == 200
        call_args = mock_export_work.call_args
        assert call_args[0][0] == 1  # work_id
        assert call_args[0][1] == mock_session_instance  # session
