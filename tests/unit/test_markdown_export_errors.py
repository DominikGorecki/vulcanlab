"""
Unit tests for markdown export error handling.

Tests error scenarios including disk full, permission denied, and invalid filenames.
"""

import errno
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from vulcanlab.markdown_export.export import export_work
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = Mock()
    return session


@pytest.fixture
def sample_work():
    """Create a sample work object."""
    work = Work(
        id=1,
        title="Test Work",
        authors="Test Author",
        year=2023,
        work_type="pdf"
    )
    return work


@pytest.fixture
def sample_sanitized_markdown(sample_work):
    """Create sample sanitized markdown."""
    return SanitizedMarkdown(
        work_id=sample_work.id,
        content="# Test Content\n\nThis is test markdown."
    )


def test_export_work_handles_disk_full_error(mock_session, sample_work, sample_sanitized_markdown):
    """Test that export_work handles disk full errors correctly."""
    # Setup
    mock_session.query.return_value.filter.return_value.first.return_value = sample_work

    # Mock the sanitized markdown query
    def query_side_effect(model):
        if model == Work:
            return mock_session.query.return_value
        elif model == SanitizedMarkdown:
            sanitized_query = Mock()
            sanitized_query.filter.return_value.first.return_value = sample_sanitized_markdown
            return sanitized_query
        return Mock()

    mock_session.query.side_effect = query_side_effect

    # Mock get_exports_dir
    with patch('vulcanlab.markdown_export.export.get_exports_dir') as mock_get_exports_dir:
        mock_exports_dir = Mock(spec=Path)
        mock_get_exports_dir.return_value = mock_exports_dir

        # Mock Path.write_text to raise ENOSPC error
        mock_path = Mock(spec=Path)
        mock_temp_path = Mock(spec=Path)
        mock_path.with_suffix.return_value = mock_temp_path

        disk_full_error = OSError()
        disk_full_error.errno = errno.ENOSPC
        mock_temp_path.write_text.side_effect = disk_full_error
        mock_temp_path.exists.return_value = False  # Temp file doesn't exist for cleanup

        mock_exports_dir.__truediv__ = Mock(return_value=mock_path)

        # Test
        with pytest.raises(HTTPException) as exc_info:
            export_work(1, mock_session)

        # Verify
        assert exc_info.value.status_code == 500
        assert "Disk full" in exc_info.value.detail


def test_export_work_handles_permission_denied_error(mock_session, sample_work, sample_sanitized_markdown):
    """Test that export_work handles permission denied errors correctly."""
    # Setup
    mock_session.query.return_value.filter.return_value.first.return_value = sample_work

    # Mock the sanitized markdown query
    def query_side_effect(model):
        if model == Work:
            return mock_session.query.return_value
        elif model == SanitizedMarkdown:
            sanitized_query = Mock()
            sanitized_query.filter.return_value.first.return_value = sample_sanitized_markdown
            return sanitized_query
        return Mock()

    mock_session.query.side_effect = query_side_effect

    # Mock get_exports_dir
    with patch('vulcanlab.markdown_export.export.get_exports_dir') as mock_get_exports_dir:
        mock_exports_dir = Mock(spec=Path)
        mock_get_exports_dir.return_value = mock_exports_dir

        # Mock Path.write_text to raise permission error
        mock_path = Mock(spec=Path)
        mock_temp_path = Mock(spec=Path)
        mock_path.with_suffix.return_value = mock_temp_path
        mock_temp_path.write_text.side_effect = PermissionError("Access denied")
        mock_temp_path.exists.return_value = False

        mock_exports_dir.__truediv__ = Mock(return_value=mock_path)

        # Test
        with pytest.raises(HTTPException) as exc_info:
            export_work(1, mock_session)

        # Verify
        assert exc_info.value.status_code == 500
        assert "Permission denied" in exc_info.value.detail


def test_export_work_handles_invalid_filename_error(mock_session):
    """Test that export_work handles invalid filename generation."""
    # Setup - create a work with a title that generates an invalid filename
    work = Work(
        id=1,
        title="!!!",  # Title with only special characters
        authors="Test Author",
        year=2023,
        work_type="pdf"
    )

    mock_session.query.return_value.filter.return_value.first.return_value = work

    # Mock the sanitized markdown query
    sanitized_markdown = SanitizedMarkdown(
        work_id=work.id,
        content="# Test Content"
    )

    def query_side_effect(model):
        if model == Work:
            return mock_session.query.return_value
        elif model == SanitizedMarkdown:
            sanitized_query = Mock()
            sanitized_query.filter.return_value.first.return_value = sanitized_markdown
            return sanitized_query
        return Mock()

    mock_session.query.side_effect = query_side_effect

    # Test
    with pytest.raises(HTTPException) as exc_info:
        export_work(1, mock_session)

    # Verify
    assert exc_info.value.status_code == 400
    assert "filename" in exc_info.value.detail.lower()


def test_export_work_handles_empty_markdown_content(mock_session, sample_work):
    """Test that export_work handles empty markdown content."""
    # Setup
    mock_session.query.return_value.filter.return_value.first.return_value = sample_work

    # Mock the sanitized markdown query with empty content
    empty_sanitized = SanitizedMarkdown(
        work_id=sample_work.id,
        content=""  # Empty content
    )

    def query_side_effect(model):
        if model == Work:
            return mock_session.query.return_value
        elif model == SanitizedMarkdown:
            sanitized_query = Mock()
            sanitized_query.filter.return_value.first.return_value = empty_sanitized
            return sanitized_query
        return Mock()

    mock_session.query.side_effect = query_side_effect

    # Test
    with pytest.raises(HTTPException) as exc_info:
        export_work(1, mock_session)

    # Verify
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()


def test_export_work_cleans_up_temp_file_on_error(mock_session, sample_work, sample_sanitized_markdown):
    """Test that export_work cleans up temporary files on error."""
    # Setup
    mock_session.query.return_value.filter.return_value.first.return_value = sample_work

    # Mock the sanitized markdown query
    def query_side_effect(model):
        if model == Work:
            return mock_session.query.return_value
        elif model == SanitizedMarkdown:
            sanitized_query = Mock()
            sanitized_query.filter.return_value.first.return_value = sample_sanitized_markdown
            return sanitized_query
        return Mock()

    mock_session.query.side_effect = query_side_effect

    # Mock get_exports_dir
    with patch('vulcanlab.markdown_export.export.get_exports_dir') as mock_get_exports_dir:
        mock_exports_dir = Mock(spec=Path)
        mock_get_exports_dir.return_value = mock_exports_dir

        # Create mock paths
        mock_export_path = Mock(spec=Path)
        mock_temp_path = Mock(spec=Path)
        mock_temp_path.exists.return_value = True

        mock_export_path.with_suffix.return_value = mock_temp_path
        mock_exports_dir.__truediv__ = Mock(return_value=mock_export_path)

        # Make write_text succeed but replace fail
        mock_temp_path.write_text.return_value = None
        mock_temp_path.replace.side_effect = OSError("Replace failed")

        # Test
        with pytest.raises(HTTPException):
            export_work(1, mock_session)

        # Verify temp file unlink was called
        mock_temp_path.unlink.assert_called_once()


def test_export_work_handles_read_only_filesystem(mock_session, sample_work, sample_sanitized_markdown):
    """Test that export_work handles read-only filesystem errors."""
    # Setup
    mock_session.query.return_value.filter.return_value.first.return_value = sample_work

    # Mock the sanitized markdown query
    def query_side_effect(model):
        if model == Work:
            return mock_session.query.return_value
        elif model == SanitizedMarkdown:
            sanitized_query = Mock()
            sanitized_query.filter.return_value.first.return_value = sample_sanitized_markdown
            return sanitized_query
        return Mock()

    mock_session.query.side_effect = query_side_effect

    # Mock get_exports_dir
    with patch('vulcanlab.markdown_export.export.get_exports_dir') as mock_get_exports_dir:
        mock_exports_dir = Mock(spec=Path)
        mock_get_exports_dir.return_value = mock_exports_dir

        # Mock Path.write_text to raise EROFS error
        mock_path = Mock(spec=Path)
        mock_temp_path = Mock(spec=Path)
        mock_path.with_suffix.return_value = mock_temp_path

        ro_error = OSError()
        ro_error.errno = errno.EROFS
        mock_temp_path.write_text.side_effect = ro_error
        mock_temp_path.exists.return_value = False

        mock_exports_dir.__truediv__ = Mock(return_value=mock_path)

        # Test
        with pytest.raises(HTTPException) as exc_info:
            export_work(1, mock_session)

        # Verify
        assert exc_info.value.status_code == 500
        assert "read-only" in exc_info.value.detail.lower()
