"""
Unit tests for work deletion module.

Tests work deletion, cascade deletion handling, and error cases.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from vulcanlab.data.work_operations import delete_work
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.parsed_markdown import ParsedMarkdown
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from tests.unit.mock_helpers import (
    mock_session,
    create_mock_work,
    configure_mock_session_query,
    create_mock_query_chain
)


class TestDeleteWork:
    """Test work deletion functionality."""

    @patch('vulcanlab.data.work_operations.load_config')
    def test_delete_work_success(self, mock_load_config, mock_session, tmp_path):
        """Test successful deletion of work and all associated data."""
        # Setup output directory with test files
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create test files
        test_files = [
            output_dir / "test.pdf",
            output_dir / "test_sanitized.md",
            output_dir / "test.hier.md"
        ]
        for f in test_files:
            f.write_text("test content")

        work_id = 1
        work = create_mock_work(
            id=work_id,
            title="Test Work",
            files={
                "original_file": {"path": "test.pdf", "hash": "abc123"},
                "sanitized": {"path": "test_sanitized.md", "hash": "def456"},
                "hier_markdown": {"path": "test.hier.md", "hash": "ghi789"}
            }
        )

        # Configure mock session for Work query
        configure_mock_session_query(mock_session, Work, return_first=work)

        # Configure mock queries for ParsedMarkdown and SanitizedMarkdown deletion
        parsed_query = create_mock_query_chain()
        parsed_query.delete.return_value = 2
        sanitized_query = create_mock_query_chain()
        sanitized_query.delete.return_value = 1

        def query_side_effect(model):
            if model == Work:
                return mock_session.query.return_value
            elif model == ParsedMarkdown:
                return parsed_query
            elif model == SanitizedMarkdown:
                return sanitized_query
            return MagicMock()

        mock_session.query.side_effect = query_side_effect

        # Mock load_config
        mock_config = MagicMock()
        mock_config.paths.output_dir = str(output_dir)
        mock_load_config.return_value = mock_config

        # Execute deletion
        delete_work(work_id, mock_session)

        # Verify Work query was called
        assert any(
            call_args[0][0] == Work
            for call_args in mock_session.query.call_args_list
        )

        # Verify files were deleted
        for f in test_files:
            assert not f.exists()

        # Verify ParsedMarkdown records were deleted
        parsed_query.filter.assert_called_once()
        parsed_query.delete.assert_called_once()

        # Verify SanitizedMarkdown records were deleted
        sanitized_query.filter.assert_called_once()
        sanitized_query.delete.assert_called_once()

        # Verify Work record was deleted
        mock_session.delete.assert_called_once_with(work)

    @patch('vulcanlab.data.work_operations.load_config')
    def test_delete_work_not_found(self, mock_load_config, mock_session):
        """Test error handling when work_id is not found."""
        # Configure query to return None (not found)
        configure_mock_session_query(mock_session, Work, return_first=None)

        # Mock load_config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/test/output"
        mock_load_config.return_value = mock_config

        # Try to delete non-existent work
        with pytest.raises(ValueError, match="Work with ID 999 not found"):
            delete_work(999, mock_session)

    @patch('vulcanlab.data.work_operations.load_config')
    @patch('vulcanlab.data.work_operations.Path.unlink')
    def test_delete_work_cascades_chunks(
        self, mock_unlink, mock_load_config, mock_session
    ):
        """Test that chunks are NOT explicitly deleted (handled by CASCADE)."""
        work_id = 1
        work = create_mock_work(id=work_id, title="Test Work", files=None)

        configure_mock_session_query(mock_session, Work, return_first=work)

        # Configure mock queries for ParsedMarkdown and SanitizedMarkdown
        parsed_query = create_mock_query_chain()
        parsed_query.delete.return_value = 0
        sanitized_query = create_mock_query_chain()
        sanitized_query.delete.return_value = 0

        def query_side_effect(model):
            if model == Work:
                return mock_session.query.return_value
            elif model == ParsedMarkdown:
                return parsed_query
            elif model == SanitizedMarkdown:
                return sanitized_query
            return MagicMock()

        mock_session.query.side_effect = query_side_effect

        mock_config = MagicMock()
        mock_config.paths.output_dir = "/test/output"
        mock_load_config.return_value = mock_config

        # Execute deletion
        delete_work(work_id, mock_session)

        # Verify Work record was deleted
        mock_session.delete.assert_called_once_with(work)

        # Verify chunks were NOT explicitly queried or deleted
        # (They cascade via FK constraint)
        from vulcanlab.data.models.chunk import Chunk
        assert not any(
            call_args[0][0] == Chunk
            for call_args in mock_session.query.call_args_list
        )

    @patch('vulcanlab.data.work_operations.load_config')
    @patch('vulcanlab.data.work_operations.Path.unlink')
    def test_delete_work_deletes_parsed_markdown(
        self, mock_unlink, mock_load_config, mock_session
    ):
        """Test that ParsedMarkdown records are deleted."""
        work_id = 1
        work = create_mock_work(id=work_id, title="Test Work", files=None)

        configure_mock_session_query(mock_session, Work, return_first=work)

        # Configure mock queries
        parsed_query = create_mock_query_chain()
        parsed_query.delete.return_value = 3  # 3 records deleted
        sanitized_query = create_mock_query_chain()
        sanitized_query.delete.return_value = 0

        def query_side_effect(model):
            if model == Work:
                return mock_session.query.return_value
            elif model == ParsedMarkdown:
                return parsed_query
            elif model == SanitizedMarkdown:
                return sanitized_query
            return MagicMock()

        mock_session.query.side_effect = query_side_effect

        mock_config = MagicMock()
        mock_config.paths.output_dir = "/test/output"
        mock_load_config.return_value = mock_config

        # Execute deletion
        delete_work(work_id, mock_session)

        # Verify ParsedMarkdown.delete() was called
        parsed_query.delete.assert_called_once()

    @patch('vulcanlab.data.work_operations.load_config')
    @patch('vulcanlab.data.work_operations.Path.unlink')
    def test_delete_work_deletes_sanitized_markdown(
        self, mock_unlink, mock_load_config, mock_session
    ):
        """Test that SanitizedMarkdown records are deleted."""
        work_id = 1
        work = create_mock_work(id=work_id, title="Test Work", files=None)

        configure_mock_session_query(mock_session, Work, return_first=work)

        # Configure mock queries
        parsed_query = create_mock_query_chain()
        parsed_query.delete.return_value = 0
        sanitized_query = create_mock_query_chain()
        sanitized_query.delete.return_value = 2  # 2 records deleted

        def query_side_effect(model):
            if model == Work:
                return mock_session.query.return_value
            elif model == ParsedMarkdown:
                return parsed_query
            elif model == SanitizedMarkdown:
                return sanitized_query
            return MagicMock()

        mock_session.query.side_effect = query_side_effect

        mock_config = MagicMock()
        mock_config.paths.output_dir = "/test/output"
        mock_load_config.return_value = mock_config

        # Execute deletion
        delete_work(work_id, mock_session)

        # Verify SanitizedMarkdown.delete() was called
        sanitized_query.delete.assert_called_once()

    @patch('vulcanlab.data.work_operations.load_config')
    def test_delete_work_deletes_files(self, mock_load_config, mock_session, tmp_path):
        """Test that all files in Work.files are deleted."""
        # Setup output directory with test files
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        test_files = [
            output_dir / "test.pdf",
            output_dir / "test_sanitized.md",
            output_dir / "test.hier.md",
            output_dir / "test.vec_sugg.md"
        ]
        for f in test_files:
            f.write_text("test content")

        work_id = 1
        work = create_mock_work(
            id=work_id,
            title="Test Work",
            files={
                "original_file": {"path": "test.pdf", "hash": "abc"},
                "sanitized": {"path": "test_sanitized.md", "hash": "def"},
                "hier_markdown": {"path": "test.hier.md", "hash": "ghi"},
                "vec_suggestions": {"path": "test.vec_sugg.md", "hash": "jkl"}
            }
        )

        configure_mock_session_query(mock_session, Work, return_first=work)

        # Configure mock queries
        parsed_query = create_mock_query_chain()
        parsed_query.delete.return_value = 0
        sanitized_query = create_mock_query_chain()
        sanitized_query.delete.return_value = 0

        def query_side_effect(model):
            if model == Work:
                return mock_session.query.return_value
            elif model == ParsedMarkdown:
                return parsed_query
            elif model == SanitizedMarkdown:
                return sanitized_query
            return MagicMock()

        mock_session.query.side_effect = query_side_effect

        mock_config = MagicMock()
        mock_config.paths.output_dir = str(output_dir)
        mock_load_config.return_value = mock_config

        # Execute deletion
        delete_work(work_id, mock_session)

        # Verify all 4 files were deleted
        for f in test_files:
            assert not f.exists()

    @patch('vulcanlab.data.work_operations.load_config')
    def test_delete_work_file_deletion_fails(
        self, mock_load_config, mock_session, tmp_path, monkeypatch
    ):
        """Test that IOError is raised when file deletion fails."""
        # Setup output directory with test file
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        test_file = output_dir / "test.pdf"
        test_file.write_text("test content")

        work_id = 1
        work = create_mock_work(
            id=work_id,
            title="Test Work",
            files={
                "original_file": {"path": "test.pdf", "hash": "abc"}
            }
        )

        configure_mock_session_query(mock_session, Work, return_first=work)

        mock_config = MagicMock()
        mock_config.paths.output_dir = str(output_dir)
        mock_load_config.return_value = mock_config

        # Mock unlink to raise PermissionError
        original_unlink = Path.unlink

        def mock_unlink(self, missing_ok=False):
            raise PermissionError("Cannot delete file")

        monkeypatch.setattr(Path, "unlink", mock_unlink)

        # Should raise IOError
        with pytest.raises(IOError, match="Failed to delete file"):
            delete_work(work_id, mock_session)

    @patch('vulcanlab.data.work_operations.load_config')
    def test_delete_work_missing_file_ignored(
        self, mock_load_config, mock_session, tmp_path
    ):
        """Test that missing files are handled gracefully."""
        # Setup output directory WITHOUT creating the test file
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        work_id = 1
        work = create_mock_work(
            id=work_id,
            title="Test Work",
            files={
                "original_file": {"path": "test.pdf", "hash": "abc"}
            }
        )

        configure_mock_session_query(mock_session, Work, return_first=work)

        # Configure mock queries
        parsed_query = create_mock_query_chain()
        parsed_query.delete.return_value = 0
        sanitized_query = create_mock_query_chain()
        sanitized_query.delete.return_value = 0

        def query_side_effect(model):
            if model == Work:
                return mock_session.query.return_value
            elif model == ParsedMarkdown:
                return parsed_query
            elif model == SanitizedMarkdown:
                return sanitized_query
            return MagicMock()

        mock_session.query.side_effect = query_side_effect

        mock_config = MagicMock()
        mock_config.paths.output_dir = str(output_dir)
        mock_load_config.return_value = mock_config

        # Should succeed without raising (file doesn't exist)
        delete_work(work_id, mock_session)

        # Verify deletion continued
        mock_session.delete.assert_called_once_with(work)

    @patch('vulcanlab.data.work_operations.load_config')
    @patch('vulcanlab.data.work_operations.Path.unlink')
    def test_delete_work_null_files_field(
        self, mock_unlink, mock_load_config, mock_session
    ):
        """Test deletion when Work.files is None."""
        work_id = 1
        work = create_mock_work(id=work_id, title="Test Work", files=None)

        configure_mock_session_query(mock_session, Work, return_first=work)

        # Configure mock queries
        parsed_query = create_mock_query_chain()
        parsed_query.delete.return_value = 0
        sanitized_query = create_mock_query_chain()
        sanitized_query.delete.return_value = 0

        def query_side_effect(model):
            if model == Work:
                return mock_session.query.return_value
            elif model == ParsedMarkdown:
                return parsed_query
            elif model == SanitizedMarkdown:
                return sanitized_query
            return MagicMock()

        mock_session.query.side_effect = query_side_effect

        mock_config = MagicMock()
        mock_config.paths.output_dir = "/test/output"
        mock_load_config.return_value = mock_config

        # Should succeed without file operations
        delete_work(work_id, mock_session)

        # Verify no file deletion attempts
        mock_unlink.assert_not_called()

        # Verify work was still deleted
        mock_session.delete.assert_called_once_with(work)

    @patch('vulcanlab.data.work_operations.load_config')
    @patch('vulcanlab.data.work_operations.Path.unlink')
    def test_delete_work_empty_files_field(
        self, mock_unlink, mock_load_config, mock_session
    ):
        """Test deletion when Work.files is empty dict."""
        work_id = 1
        work = create_mock_work(id=work_id, title="Test Work", files={})

        configure_mock_session_query(mock_session, Work, return_first=work)

        # Configure mock queries
        parsed_query = create_mock_query_chain()
        parsed_query.delete.return_value = 0
        sanitized_query = create_mock_query_chain()
        sanitized_query.delete.return_value = 0

        def query_side_effect(model):
            if model == Work:
                return mock_session.query.return_value
            elif model == ParsedMarkdown:
                return parsed_query
            elif model == SanitizedMarkdown:
                return sanitized_query
            return MagicMock()

        mock_session.query.side_effect = query_side_effect

        mock_config = MagicMock()
        mock_config.paths.output_dir = "/test/output"
        mock_load_config.return_value = mock_config

        # Should succeed without file operations
        delete_work(work_id, mock_session)

        # Verify no file deletion attempts
        mock_unlink.assert_not_called()

        # Verify work was still deleted
        mock_session.delete.assert_called_once_with(work)

    @patch('vulcanlab.data.work_operations.load_config')
    @patch('vulcanlab.data.work_operations.Path')
    def test_delete_work_file_path_resolution(
        self, mock_path_class, mock_load_config, mock_session
    ):
        """Test correct path construction from output_dir + filename."""
        work_id = 1
        work = create_mock_work(
            id=work_id,
            title="Test Work",
            files={
                "sanitized": {"path": "myfile.md", "hash": "abc"}
            }
        )

        configure_mock_session_query(mock_session, Work, return_first=work)

        # Configure mock queries
        parsed_query = create_mock_query_chain()
        parsed_query.delete.return_value = 0
        sanitized_query = create_mock_query_chain()
        sanitized_query.delete.return_value = 0

        def query_side_effect(model):
            if model == Work:
                return mock_session.query.return_value
            elif model == ParsedMarkdown:
                return parsed_query
            elif model == SanitizedMarkdown:
                return sanitized_query
            return MagicMock()

        mock_session.query.side_effect = query_side_effect

        mock_config = MagicMock()
        mock_config.paths.output_dir = "/test/output"
        mock_load_config.return_value = mock_config

        # Mock Path to track construction
        mock_path_instance = MagicMock()
        mock_path_class.return_value = mock_path_instance

        # Execute deletion
        delete_work(work_id, mock_session)

        # Verify Path was constructed with output_dir first
        # The implementation uses: output_dir / file_info["path"]
        # So we need to check the __truediv__ call
        assert mock_path_class.call_count >= 1

    @patch('vulcanlab.data.work_operations.load_config')
    @patch('vulcanlab.data.work_operations.Path.unlink')
    @patch('vulcanlab.data.work_operations.logger')
    def test_delete_work_logs_operations(
        self, mock_logger, mock_unlink, mock_load_config, mock_session
    ):
        """Test that logging includes work_id and file count."""
        work_id = 1
        work = create_mock_work(
            id=work_id,
            title="Test Work",
            files={
                "original_file": {"path": "test.pdf", "hash": "abc"},
                "sanitized": {"path": "test_sanitized.md", "hash": "def"}
            }
        )

        configure_mock_session_query(mock_session, Work, return_first=work)

        # Configure mock queries
        parsed_query = create_mock_query_chain()
        parsed_query.delete.return_value = 1
        sanitized_query = create_mock_query_chain()
        sanitized_query.delete.return_value = 1

        def query_side_effect(model):
            if model == Work:
                return mock_session.query.return_value
            elif model == ParsedMarkdown:
                return parsed_query
            elif model == SanitizedMarkdown:
                return sanitized_query
            return MagicMock()

        mock_session.query.side_effect = query_side_effect

        mock_config = MagicMock()
        mock_config.paths.output_dir = "/test/output"
        mock_load_config.return_value = mock_config

        # Execute deletion
        delete_work(work_id, mock_session)

        # Verify logging includes work_id
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any(f"work_id={work_id}" in call for call in log_calls)

        # Verify logging mentions file count
        assert any("file" in call.lower() for call in log_calls)
