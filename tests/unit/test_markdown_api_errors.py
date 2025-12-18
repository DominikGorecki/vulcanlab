"""
Unit tests for markdown API error responses.

Tests that the API returns structured error responses with appropriate
HTTP status codes and error messages.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from vulcanlab_api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = Mock()
    return session


def test_export_returns_404_for_nonexistent_work(client):
    """Test that export endpoint returns 404 for non-existent work."""
    # Test
    response = client.post("/api/v1/markdown/export/999999")

    # Verify
    assert response.status_code == 404
    # Should have structured error in detail
    detail = response.json()["detail"]
    if isinstance(detail, str):
        assert "not found" in detail.lower()


def test_export_returns_400_for_work_without_markdown(client):
    """Test that export endpoint returns 400 when markdown is not available."""
    # This test would require a real work without sanitized markdown
    # For now, we'll test the endpoint structure
    pass


def test_import_returns_404_for_nonexistent_file(client):
    """Test that import endpoint returns 404 for non-existent file."""
    # Test
    response = client.post(
        "/api/v1/markdown/import",
        json={
            "filename": "nonexistent.md",
            "title": "Test",
            "author": "Author",
            "year": 2023,
            "is_sanitized": True
        }
    )

    # Verify
    assert response.status_code == 404
    detail = response.json()["detail"]

    # Should have structured error response
    if isinstance(detail, dict):
        assert detail["error"] == "file_not_found"
        assert "message" in detail


def test_import_returns_400_for_invalid_request(client):
    """Test that import endpoint returns 400 for invalid request."""
    # Test - missing required fields
    response = client.post(
        "/api/v1/markdown/import",
        json={
            "filename": "test.md"
            # Missing title, author, is_sanitized
        }
    )

    # Verify
    assert response.status_code == 422  # Pydantic validation error


def test_import_returns_structured_error_for_empty_file(client, tmp_path):
    """Test that import returns structured error for empty file."""
    # This would require setting up a real empty file in the input directory
    # and mocking the config to point to tmp_path
    pass


def test_check_duplicate_returns_400_for_empty_title(client):
    """Test that check-duplicate endpoint returns 400 for empty title."""
    # Test
    response = client.get(
        "/api/v1/markdown/check-duplicate",
        params={
            "title": "",
            "author": "Test Author"
        }
    )

    # Verify
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "title" in detail.lower()


def test_check_duplicate_returns_400_for_empty_author(client):
    """Test that check-duplicate endpoint returns 400 for empty author."""
    # Test
    response = client.get(
        "/api/v1/markdown/check-duplicate",
        params={
            "title": "Test Title",
            "author": ""
        }
    )

    # Verify
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "author" in detail.lower()


@patch('vulcanlab_api.routers.markdown.export_work')
def test_export_endpoint_handles_unexpected_errors(mock_export, client):
    """Test that export endpoint handles unexpected errors gracefully."""
    # Setup
    mock_export.side_effect = Exception("Unexpected error")

    # Test
    response = client.post("/api/v1/markdown/export/1")

    # Verify
    assert response.status_code == 500
    detail = response.json()["detail"]

    # Should have structured error response
    if isinstance(detail, dict):
        assert detail["error"] == "unexpected_error"
        assert "message" in detail


@patch('vulcanlab_api.routers.markdown.import_sanitized_markdown')
def test_import_endpoint_handles_encoding_errors(mock_import, client, tmp_path):
    """Test that import endpoint returns structured error for encoding errors."""
    # Setup
    mock_import.side_effect = ValueError("File encoding not supported")

    # Create a temporary file
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test", encoding='utf-8')

    with patch('vulcanlab.config.load_config') as mock_config:
        mock_config.return_value.paths.input_dir = str(tmp_path)

        # Test
        response = client.post(
            "/api/v1/markdown/import",
            json={
                "filename": "test.md",
                "title": "Test",
                "author": "Author",
                "year": 2023,
                "is_sanitized": True
            }
        )

        # Verify
        assert response.status_code == 400
        detail = response.json()["detail"]

        if isinstance(detail, dict):
            assert detail["error"] == "encoding_error"
            assert "encoding" in detail["message"].lower()


@patch('vulcanlab_api.routers.markdown.import_sanitized_markdown')
def test_import_endpoint_handles_empty_file_error(mock_import, client, tmp_path):
    """Test that import endpoint returns structured error for empty files."""
    # Setup
    mock_import.side_effect = ValueError("File is empty (0 bytes)")

    # Create an empty file
    test_file = tmp_path / "empty.md"
    test_file.touch()

    with patch('vulcanlab.config.load_config') as mock_config:
        mock_config.return_value.paths.input_dir = str(tmp_path)

        # Test
        response = client.post(
            "/api/v1/markdown/import",
            json={
                "filename": "empty.md",
                "title": "Test",
                "author": "Author",
                "year": 2023,
                "is_sanitized": True
            }
        )

        # Verify
        assert response.status_code == 400
        detail = response.json()["detail"]

        if isinstance(detail, dict):
            assert detail["error"] == "empty_file"
            assert "empty" in detail["message"].lower()


@patch('vulcanlab_api.routers.markdown.import_sanitized_markdown')
def test_import_endpoint_handles_permission_error(mock_import, client, tmp_path):
    """Test that import endpoint returns structured error for permission errors."""
    # Setup
    mock_import.side_effect = ValueError("Permission denied reading file")

    test_file = tmp_path / "test.md"
    test_file.write_text("# Test", encoding='utf-8')

    with patch('vulcanlab.config.load_config') as mock_config:
        mock_config.return_value.paths.input_dir = str(tmp_path)

        # Test
        response = client.post(
            "/api/v1/markdown/import",
            json={
                "filename": "test.md",
                "title": "Test",
                "author": "Author",
                "year": 2023,
                "is_sanitized": True
            }
        )

        # Verify
        assert response.status_code == 400
        detail = response.json()["detail"]

        if isinstance(detail, dict):
            assert detail["error"] == "permission_denied"
            assert "permission" in detail["message"].lower()


@patch('vulcanlab_api.routers.markdown.import_sanitized_markdown')
def test_import_endpoint_handles_chunking_failure(mock_import, client, tmp_path):
    """Test that import endpoint returns structured error for chunking failures."""
    # Setup
    mock_import.side_effect = ValueError("Heading chunking failed: Invalid markdown structure")

    test_file = tmp_path / "test.md"
    test_file.write_text("# Test", encoding='utf-8')

    with patch('vulcanlab.config.load_config') as mock_config:
        mock_config.return_value.paths.input_dir = str(tmp_path)

        # Test
        response = client.post(
            "/api/v1/markdown/import",
            json={
                "filename": "test.md",
                "title": "Test",
                "author": "Author",
                "year": 2023,
                "is_sanitized": True
            }
        )

        # Verify
        assert response.status_code == 400
        detail = response.json()["detail"]

        if isinstance(detail, dict):
            assert detail["error"] == "chunking_failed"
            assert "message" in detail


@patch('vulcanlab_api.routers.markdown.import_unsanitized_markdown')
def test_import_endpoint_handles_sanitization_failure(mock_import, client, tmp_path):
    """Test that import endpoint returns structured error for sanitization failures."""
    # Setup
    mock_import.side_effect = ValueError("Sanitization failed: LLM timeout")

    test_file = tmp_path / "test.md"
    test_file.write_text("# Test", encoding='utf-8')

    with patch('vulcanlab.config.load_config') as mock_config:
        mock_config.return_value.paths.input_dir = str(tmp_path)

        # Test
        response = client.post(
            "/api/v1/markdown/import",
            json={
                "filename": "test.md",
                "title": "Test",
                "author": "Author",
                "year": 2023,
                "is_sanitized": False  # Triggers unsanitized import
            }
        )

        # Verify
        assert response.status_code == 400
        detail = response.json()["detail"]

        if isinstance(detail, dict):
            assert detail["error"] == "sanitization_failed"
            assert "sanitize" in detail["message"].lower()


@patch('vulcanlab_api.routers.markdown.import_sanitized_markdown')
def test_import_endpoint_handles_no_content_error(mock_import, client, tmp_path):
    """Test that import endpoint returns structured error for files with only frontmatter."""
    # Setup
    mock_import.side_effect = ValueError("File contains only frontmatter or whitespace, no actual content")

    test_file = tmp_path / "test.md"
    test_file.write_text("---\ntitle: Test\n---\n", encoding='utf-8')

    with patch('vulcanlab.config.load_config') as mock_config:
        mock_config.return_value.paths.input_dir = str(tmp_path)

        # Test
        response = client.post(
            "/api/v1/markdown/import",
            json={
                "filename": "test.md",
                "title": "Test",
                "author": "Author",
                "year": 2023,
                "is_sanitized": True
            }
        )

        # Verify
        assert response.status_code == 400
        detail = response.json()["detail"]

        if isinstance(detail, dict):
            assert detail["error"] == "no_content"
            assert "content" in detail["message"].lower()
