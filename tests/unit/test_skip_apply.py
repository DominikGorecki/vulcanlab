"""
Unit tests for skip_apply module.

Tests cover:
- Skip application logic
- Conditional processing
- Edge cases and error handling
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vulcanlab.sanitization.skip_apply import skip_apply_from_work
from vulcanlab.sanitization.extract_titles import HashMismatchError
from vulcanlab.data.models.work import Work
from tests.unit.mock_helpers import mock_session


class TestSkipApplyFromWork:
    """Tests for skip_apply_from_work function."""

    @patch('vulcanlab.sanitization.skip_apply.compute_file_hash')
    @patch('vulcanlab.sanitization.skip_apply.set_file_readonly')
    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_success_original_markdown(
        self, mock_get_session, mock_set_readonly, mock_compute_hash,
        tmp_path, mock_session
    ):
        """Test successful skip-apply from original_markdown source."""
        # Setup mock session
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        # Create source file
        source_path = tmp_path / "test.md"
        source_content = "# Original Title\nSome content here\n"
        source_path.write_text(source_content, encoding='utf-8')
        source_hash = "source_hash_123"
        sanitized_hash = "sanitized_hash_456"

        # Create work with files metadata
        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(source_path),
                    "hash": source_hash
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work

        # Mock hash computations
        def hash_side_effect(path):
            if path == source_path:
                return source_hash
            else:
                return sanitized_hash
        mock_compute_hash.side_effect = hash_side_effect

        # Execute
        result_path = skip_apply_from_work(
            work_id=1,
            source_key='original_markdown',
            force=False,
            verbose=False
        )

        # Verify output file was created
        output_path = tmp_path / "test.sanitized.md"
        assert result_path == output_path
        assert output_path.exists()

        # Verify content was copied correctly
        assert output_path.read_text(encoding='utf-8') == source_content

        # Verify database was updated
        assert "sanitized" in work.files
        assert work.files["sanitized"]["hash"] == sanitized_hash
        assert work.files["sanitized"]["path"] == str(output_path.resolve())

        # Verify file was set to read-only
        mock_set_readonly.assert_called_once_with(output_path)

        # Verify session commit was called
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(work)

    @patch('vulcanlab.sanitization.skip_apply.compute_file_hash')
    @patch('vulcanlab.sanitization.skip_apply.set_file_readonly')
    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_overwrite_existing_sanitized_with_force(
        self, mock_get_session, mock_set_readonly, mock_compute_hash,
        tmp_path, mock_session
    ):
        """Test successful skip-apply overwriting existing sanitized file with force=True."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        # When source_key is "sanitized", output_path = source_path (same file)
        # So we need to test copying from original_markdown to sanitized with force=True
        # to overwrite existing sanitized file
        source_path = tmp_path / "test.md"
        sanitized_path = tmp_path / "test.sanitized.md"
        
        source_content = "# New Content\nUpdated text\n"
        old_sanitized_content = "# Old Content\n"
        
        source_path.write_text(source_content, encoding='utf-8')
        sanitized_path.write_text(old_sanitized_content, encoding='utf-8')
        
        source_hash = "source_hash_123"
        sanitized_hash = "sanitized_hash_789"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(source_path),
                    "hash": source_hash
                },
                "sanitized": {
                    "path": str(sanitized_path),
                    "hash": "old_hash"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work

        def hash_side_effect(path):
            if path == source_path:
                return source_hash
            else:
                return sanitized_hash
        mock_compute_hash.side_effect = hash_side_effect

        # Execute with force=True to overwrite existing sanitized
        result_path = skip_apply_from_work(
            work_id=1,
            source_key='original_markdown',
            force=True,
            verbose=False
        )

        # Should overwrite the sanitized file
        assert result_path == sanitized_path
        assert sanitized_path.exists()

        # Verify content was updated
        assert sanitized_path.read_text(encoding='utf-8') == source_content

    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_work_not_found(self, mock_get_session, mock_session):
        """Test that missing work raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        mock_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            skip_apply_from_work(work_id=999, source_key='original_markdown')

        assert "Work with ID 999 not found" in str(exc_info.value)

    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_no_files_metadata(self, mock_get_session, mock_session):
        """Test that work without files metadata raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        work = Work(id=1, title="Test Work", files=None)
        mock_session.query.return_value.filter.return_value.first.return_value = work

        with pytest.raises(ValueError) as exc_info:
            skip_apply_from_work(work_id=1, source_key='original_markdown')

        assert "has no files metadata" in str(exc_info.value)

    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_invalid_source_key(self, mock_get_session, mock_session, tmp_path):
        """Test that invalid source_key raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        work = Work(
            id=1,
            title="Test Work",
            files={"original_markdown": {"path": str(tmp_path / "test.md"), "hash": "hash"}}
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work

        with pytest.raises(ValueError) as exc_info:
            skip_apply_from_work(work_id=1, source_key='invalid_key')

        assert "Invalid source_key: invalid_key" in str(exc_info.value)
        assert "Must be 'original_markdown' or 'sanitized'" in str(exc_info.value)

    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_sanitized_already_exists(self, mock_get_session, mock_session, tmp_path):
        """Test that existing sanitized file without force raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        source_path = tmp_path / "test.md"
        source_path.write_text("# Title\n", encoding='utf-8')

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(source_path),
                    "hash": "hash"
                },
                "sanitized": {
                    "path": str(tmp_path / "test.sanitized.md"),
                    "hash": "hash"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work

        with pytest.raises(ValueError) as exc_info:
            skip_apply_from_work(work_id=1, source_key='original_markdown', force=False)

        assert "already has a 'sanitized' file" in str(exc_info.value)
        assert "Use force=True to overwrite" in str(exc_info.value)

    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_source_key_not_in_files(self, mock_get_session, mock_session, tmp_path):
        """Test that missing source_key in files metadata raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        work = Work(
            id=1,
            title="Test Work",
            files={"title_changes": {"path": str(tmp_path / "changes.md"), "hash": "hash"}}
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work

        with pytest.raises(ValueError) as exc_info:
            skip_apply_from_work(work_id=1, source_key='original_markdown')

        assert "does not have 'original_markdown' in files metadata" in str(exc_info.value)

    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_source_file_not_found_on_disk(
        self, mock_get_session, mock_session, tmp_path
    ):
        """Test that missing source file on disk raises FileNotFoundError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        source_path = tmp_path / "nonexistent.md"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(source_path),
                    "hash": "hash"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work

        # Don't create the file
        with pytest.raises(FileNotFoundError) as exc_info:
            skip_apply_from_work(work_id=1, source_key='original_markdown')

        assert "Source file not found on disk" in str(exc_info.value)
        assert str(source_path) in str(exc_info.value)

    @patch('vulcanlab.sanitization.skip_apply.compute_file_hash')
    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_hash_mismatch(
        self, mock_get_session, mock_compute_hash, tmp_path, mock_session
    ):
        """Test that hash mismatch raises HashMismatchError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        source_path = tmp_path / "test.md"
        source_path.write_text("# Title\n", encoding='utf-8')

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(source_path),
                    "hash": "stored_hash_123"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work

        # Mock hash to return different value
        mock_compute_hash.return_value = "current_hash_456"

        with pytest.raises(HashMismatchError) as exc_info:
            skip_apply_from_work(work_id=1, source_key='original_markdown', force=False)

        assert exc_info.value.stored_hash == "stored_hash_123"
        assert exc_info.value.current_hash == "current_hash_456"

    @patch('vulcanlab.sanitization.skip_apply.compute_file_hash')
    @patch('vulcanlab.sanitization.skip_apply.set_file_readonly')
    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_hash_mismatch_with_force(
        self, mock_get_session, mock_set_readonly, mock_compute_hash,
        tmp_path, mock_session
    ):
        """Test that hash mismatch with force=True proceeds anyway."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        source_path = tmp_path / "test.md"
        source_content = "# Title\nContent\n"
        source_path.write_text(source_content, encoding='utf-8')

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(source_path),
                    "hash": "stored_hash_123"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work

        def hash_side_effect(path):
            if path == source_path:
                return "current_hash_456"  # Different from stored
            else:
                return "sanitized_hash_789"
        mock_compute_hash.side_effect = hash_side_effect

        # Should not raise error with force=True
        result_path = skip_apply_from_work(
            work_id=1,
            source_key='original_markdown',
            force=True,
            verbose=False
        )

        assert result_path.exists()
        assert result_path.read_text(encoding='utf-8') == source_content

    @patch('vulcanlab.sanitization.skip_apply.compute_file_hash')
    @patch('vulcanlab.sanitization.skip_apply.set_file_readonly')
    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_output_exists_without_force(
        self, mock_get_session, mock_set_readonly, mock_compute_hash,
        tmp_path, mock_session
    ):
        """Test that existing output file without force raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        source_path = tmp_path / "test.md"
        source_path.write_text("# Title\n", encoding='utf-8')
        output_path = tmp_path / "test.sanitized.md"
        output_path.write_text("# Old Content\n", encoding='utf-8')

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(source_path),
                    "hash": "hash"
                },
                "sanitized": {
                    "path": str(output_path),
                    "hash": "hash"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work

        mock_compute_hash.return_value = "hash"

        with pytest.raises(ValueError) as exc_info:
            skip_apply_from_work(work_id=1, source_key='original_markdown', force=False)

        assert "already has a 'sanitized' file" in str(exc_info.value)
        assert "Use force=True to overwrite" in str(exc_info.value)

    @patch('vulcanlab.sanitization.skip_apply.compute_file_hash')
    @patch('vulcanlab.sanitization.skip_apply.set_file_readonly')
    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_verbose_output(
        self, mock_get_session, mock_set_readonly, mock_compute_hash,
        tmp_path, mock_session, capsys
    ):
        """Test that verbose mode prints progress messages."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        source_path = tmp_path / "test.md"
        source_path.write_text("# Title\n", encoding='utf-8')
        source_hash = "source_hash_123"
        sanitized_hash = "sanitized_hash_456"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(source_path),
                    "hash": source_hash
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work

        def hash_side_effect(path):
            if path == source_path:
                return source_hash
            else:
                return sanitized_hash
        mock_compute_hash.side_effect = hash_side_effect

        skip_apply_from_work(
            work_id=1,
            source_key='original_markdown',
            force=False,
            verbose=True
        )

        # Check verbose output
        captured = capsys.readouterr()
        assert "Source file:" in captured.out
        assert "Output file:" in captured.out
        assert "Copied" in captured.out
        assert "File set to read-only" in captured.out
        assert "Updated work" in captured.out

    @patch('vulcanlab.sanitization.skip_apply.compute_file_hash')
    @patch('vulcanlab.sanitization.skip_apply.set_file_readonly')
    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_verbose_hash_mismatch_warning(
        self, mock_get_session, mock_set_readonly, mock_compute_hash,
        tmp_path, mock_session, capsys
    ):
        """Test that verbose mode warns about hash mismatch with force."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        source_path = tmp_path / "test.md"
        source_path.write_text("# Title\n", encoding='utf-8')

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(source_path),
                    "hash": "stored_hash_123"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work

        def hash_side_effect(path):
            if path == source_path:
                return "current_hash_456"  # Different from stored
            else:
                return "sanitized_hash_789"
        mock_compute_hash.side_effect = hash_side_effect

        skip_apply_from_work(
            work_id=1,
            source_key='original_markdown',
            force=True,
            verbose=True
        )

        # Check verbose output includes hash mismatch warning
        captured = capsys.readouterr()
        assert "Warning: Hash mismatch detected" in captured.out
        assert "proceeding with --force" in captured.out

    @patch('vulcanlab.sanitization.skip_apply.compute_file_hash')
    @patch('vulcanlab.sanitization.skip_apply.set_file_readonly')
    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_preserves_file_metadata(
        self, mock_get_session, mock_set_readonly, mock_compute_hash,
        tmp_path, mock_session
    ):
        """Test that existing files metadata is preserved when adding sanitized."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        source_path = tmp_path / "test.md"
        source_path.write_text("# Title\n", encoding='utf-8')
        source_hash = "source_hash_123"
        sanitized_hash = "sanitized_hash_456"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(source_path),
                    "hash": source_hash
                },
                "title_changes": {
                    "path": str(tmp_path / "changes.md"),
                    "hash": "changes_hash"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work

        def hash_side_effect(path):
            if path == source_path:
                return source_hash
            else:
                return sanitized_hash
        mock_compute_hash.side_effect = hash_side_effect

        skip_apply_from_work(work_id=1, source_key='original_markdown', force=False)

        # Verify existing files are preserved
        assert "original_markdown" in work.files
        assert "title_changes" in work.files
        assert "sanitized" in work.files
        assert work.files["title_changes"]["hash"] == "changes_hash"

    @patch('vulcanlab.sanitization.skip_apply.compute_file_hash')
    @patch('vulcanlab.sanitization.skip_apply.set_file_readonly')
    @patch('vulcanlab.sanitization.skip_apply.get_session')
    def test_skip_apply_empty_files_dict(
        self, mock_get_session, mock_set_readonly, mock_compute_hash,
        tmp_path, mock_session
    ):
        """Test that empty files dict is handled correctly."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        source_path = tmp_path / "test.md"
        source_path.write_text("# Title\n", encoding='utf-8')
        source_hash = "source_hash_123"
        sanitized_hash = "sanitized_hash_456"

        work = Work(id=1, title="Test Work", files={})
        work.files["original_markdown"] = {
            "path": str(source_path),
            "hash": source_hash
        }
        mock_session.query.return_value.filter.return_value.first.return_value = work

        def hash_side_effect(path):
            if path == source_path:
                return source_hash
            else:
                return sanitized_hash
        mock_compute_hash.side_effect = hash_side_effect

        result_path = skip_apply_from_work(work_id=1, source_key='original_markdown', force=False)

        assert result_path.exists()
        assert "sanitized" in work.files
