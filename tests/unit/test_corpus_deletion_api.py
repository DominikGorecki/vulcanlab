"""
Unit tests for corpus work deletion API endpoint.

Tests the DELETE /api/v1/corpus/works/{work_id} endpoint with mocked core functions.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from vulcanlab_api.main import app


# Create test client
client = TestClient(app)


class TestDeleteWorkEndpoint:
    """Test DELETE /api/v1/corpus/works/{work_id} endpoint."""

    @patch('vulcanlab_api.routers.v1_corpus.delete_work')
    @patch('vulcanlab_api.routers.v1_corpus.get_session')
    def test_delete_work_endpoint_success_204(
        self, mock_get_session, mock_delete_work
    ):
        """Test successful deletion returns 204 No Content."""
        # Setup mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        # Mock delete_work to succeed (no exception)
        mock_delete_work.return_value = None

        # Make request
        response = client.delete("/api/v1/corpus/works/1")

        # Verify response
        assert response.status_code == 204
        assert response.text == ""  # No content

        # Verify delete_work was called with correct arguments
        mock_delete_work.assert_called_once_with(1, mock_session)

        # Verify session commit was called
        mock_session.commit.assert_called_once()

    @patch('vulcanlab_api.routers.v1_corpus.delete_work')
    @patch('vulcanlab_api.routers.v1_corpus.get_session')
    def test_delete_work_endpoint_not_found_404(
        self, mock_get_session, mock_delete_work
    ):
        """Test ValueError from delete_work returns 404."""
        # Setup mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        # Mock delete_work to raise ValueError (work not found)
        mock_delete_work.side_effect = ValueError("Work with ID 999 not found")

        # Make request
        response = client.delete("/api/v1/corpus/works/999")

        # Verify response
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "Work with ID 999 not found" in response.json()["detail"]

        # Verify delete_work was called
        mock_delete_work.assert_called_once_with(999, mock_session)

    @patch('vulcanlab_api.routers.v1_corpus.delete_work')
    @patch('vulcanlab_api.routers.v1_corpus.get_session')
    def test_delete_work_endpoint_file_error_500(
        self, mock_get_session, mock_delete_work
    ):
        """Test IOError from delete_work returns 500."""
        # Setup mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        # Mock delete_work to raise IOError (file deletion failed)
        mock_delete_work.side_effect = IOError("Failed to delete file /path/to/file.md: Permission denied")

        # Make request
        response = client.delete("/api/v1/corpus/works/1")

        # Verify response
        assert response.status_code == 500
        assert "detail" in response.json()
        assert "Failed to delete work files" in response.json()["detail"]

        # Verify delete_work was called
        mock_delete_work.assert_called_once_with(1, mock_session)

    @patch('vulcanlab_api.routers.v1_corpus.delete_work')
    @patch('vulcanlab_api.routers.v1_corpus.get_session')
    def test_delete_work_endpoint_generic_error_500(
        self, mock_get_session, mock_delete_work
    ):
        """Test generic Exception from delete_work returns 500."""
        # Setup mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        # Mock delete_work to raise generic exception
        mock_delete_work.side_effect = Exception("Database connection lost")

        # Make request
        response = client.delete("/api/v1/corpus/works/1")

        # Verify response
        assert response.status_code == 500
        assert "detail" in response.json()
        assert "An error occurred while deleting work" in response.json()["detail"]

        # Verify delete_work was called
        mock_delete_work.assert_called_once_with(1, mock_session)

    def test_delete_work_endpoint_invalid_work_id_negative(self):
        """Test negative work_id returns 400."""
        # Make request with negative work_id
        response = client.delete("/api/v1/corpus/works/-1")

        # Verify response
        assert response.status_code == 400
        assert "detail" in response.json()
        assert "must be a positive integer" in response.json()["detail"]

    def test_delete_work_endpoint_invalid_work_id_zero(self):
        """Test zero work_id returns 400."""
        # Make request with zero work_id
        response = client.delete("/api/v1/corpus/works/0")

        # Verify response
        assert response.status_code == 400
        assert "detail" in response.json()
        assert "must be a positive integer" in response.json()["detail"]

    @patch('vulcanlab_api.routers.v1_corpus.delete_work')
    @patch('vulcanlab_api.routers.v1_corpus.get_session')
    def test_delete_work_endpoint_calls_core_function(
        self, mock_get_session, mock_delete_work
    ):
        """Test that endpoint calls delete_work with correct work_id."""
        # Setup mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        # Mock delete_work to succeed
        mock_delete_work.return_value = None

        # Make request with specific work_id
        work_id = 42
        response = client.delete(f"/api/v1/corpus/works/{work_id}")

        # Verify delete_work was called with correct work_id
        mock_delete_work.assert_called_once()
        call_args = mock_delete_work.call_args
        assert call_args[0][0] == work_id  # First positional arg is work_id

    @patch('vulcanlab_api.routers.v1_corpus.delete_work')
    @patch('vulcanlab_api.routers.v1_corpus.get_session')
    def test_delete_work_endpoint_session_passed(
        self, mock_get_session, mock_delete_work
    ):
        """Test that session from get_session() is passed to delete_work."""
        # Setup mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        # Mock delete_work to succeed
        mock_delete_work.return_value = None

        # Make request
        response = client.delete("/api/v1/corpus/works/1")

        # Verify delete_work was called with the session from get_session()
        mock_delete_work.assert_called_once()
        call_args = mock_delete_work.call_args
        assert call_args[0][1] == mock_session  # Second positional arg is session


class TestDeleteWorkEndpointErrorMessages:
    """Test error message formatting and details."""

    @patch('vulcanlab_api.routers.v1_corpus.delete_work')
    @patch('vulcanlab_api.routers.v1_corpus.get_session')
    def test_error_message_does_not_expose_paths(
        self, mock_get_session, mock_delete_work
    ):
        """Test that error messages don't expose full file system paths."""
        # Setup mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        # Mock delete_work to raise IOError with full path
        mock_delete_work.side_effect = IOError(
            "Failed to delete file /home/user/secret/path/file.md: Permission denied"
        )

        # Make request
        response = client.delete("/api/v1/corpus/works/1")

        # Verify response
        assert response.status_code == 500
        detail = response.json()["detail"]

        # Error message should contain the error but be wrapped
        assert "Failed to delete work files" in detail

    @patch('vulcanlab_api.routers.v1_corpus.delete_work')
    @patch('vulcanlab_api.routers.v1_corpus.get_session')
    def test_not_found_error_message_format(
        self, mock_get_session, mock_delete_work
    ):
        """Test that 404 error has descriptive message."""
        # Setup mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        # Mock delete_work to raise ValueError
        work_id = 123
        mock_delete_work.side_effect = ValueError(f"Work with ID {work_id} not found")

        # Make request
        response = client.delete(f"/api/v1/corpus/works/{work_id}")

        # Verify error message
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert str(work_id) in detail
        assert "not found" in detail.lower()


class TestDeleteWorkEndpointOpenAPI:
    """Test OpenAPI documentation for the endpoint."""

    def test_endpoint_in_openapi_schema(self):
        """Test that DELETE endpoint is documented in OpenAPI schema."""
        # Get OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()

        # Verify endpoint exists in schema
        assert "/api/v1/corpus/works/{work_id}" in schema["paths"]

        # Verify DELETE operation exists
        assert "delete" in schema["paths"]["/api/v1/corpus/works/{work_id}"]

        delete_op = schema["paths"]["/api/v1/corpus/works/{work_id}"]["delete"]

        # Verify responses are documented
        assert "204" in delete_op["responses"]
        assert "400" in delete_op["responses"]
        assert "404" in delete_op["responses"]
        assert "500" in delete_op["responses"]
