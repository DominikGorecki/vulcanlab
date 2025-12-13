"""
Unit tests for Work model path helper methods.
"""

import sys
import pytest

from vulcanlab.data.models.work import Work


class TestWorkModelPathHelpers:
    """Tests for Work model path helper methods."""

    def test_set_markdown_path_extracts_filename_linux(self):
        """Test set_markdown_path extracts filename from Linux path."""
        work = Work(title="Test")
        work.set_markdown_path("/home/user/data/file.md")

        assert work.markdown_path == "file.md"

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows path test - Path.name behavior is platform-specific")
    def test_set_markdown_path_extracts_filename_windows(self):
        """Test set_markdown_path extracts filename from Windows path."""
        work = Work(title="Test")
        work.set_markdown_path("C:\\data\\file.md")

        assert work.markdown_path == "file.md"

    def test_set_markdown_path_plain_filename(self):
        """Test set_markdown_path with plain filename (no path)."""
        work = Work(title="Test")
        work.set_markdown_path("file.md")

        assert work.markdown_path == "file.md"

    def test_set_markdown_path_none(self):
        """Test set_markdown_path with None value."""
        work = Work(title="Test")
        work.set_markdown_path(None)

        assert work.markdown_path is None

    def test_set_markdown_path_empty_string(self):
        """Test set_markdown_path with empty string."""
        work = Work(title="Test")
        work.set_markdown_path("")

        assert work.markdown_path == ""

    def test_set_file_path_extracts_filename(self):
        """Test set_file_path extracts filename from full path."""
        work = Work(title="Test")
        work.files = None

        work.set_file_path("sanitized", "/full/path/file.md", "hash123")

        assert work.files == {"sanitized": {"path": "file.md", "hash": "hash123"}}

    def test_set_file_path_updates_existing_key(self):
        """Test set_file_path updates existing file key."""
        work = Work(title="Test")
        work.files = {"sanitized": {"path": "old.md", "hash": "old_hash"}}

        work.set_file_path("sanitized", "/new/path/new.md", "new_hash")

        assert work.files["sanitized"]["path"] == "new.md"
        assert work.files["sanitized"]["hash"] == "new_hash"

    def test_set_file_path_no_hash_preserves_existing(self):
        """Test set_file_path without hash argument preserves existing hash."""
        work = Work(title="Test")
        work.files = {"sanitized": {"path": "old.md", "hash": "old_hash"}}

        work.set_file_path("sanitized", "new.md")  # No hash arg

        assert work.files["sanitized"]["path"] == "new.md"
        assert work.files["sanitized"]["hash"] == "old_hash"

    def test_set_file_path_creates_files_dict(self):
        """Test set_file_path creates files dict when None."""
        work = Work(title="Test")
        work.files = None

        work.set_file_path("original_file", "input.pdf")

        assert work.files == {"original_file": {"path": "input.pdf"}}

    def test_set_file_path_adds_new_key_to_existing_files(self):
        """Test set_file_path adds new key to existing files dict."""
        work = Work(title="Test")
        work.files = {"sanitized": {"path": "test.md", "hash": "abc"}}

        work.set_file_path("titles", "test.titles.md", "def")

        assert "sanitized" in work.files
        assert work.files["titles"] == {"path": "test.titles.md", "hash": "def"}

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows path test - Path.name behavior is platform-specific")
    def test_set_file_path_with_windows_path(self):
        """Test set_file_path with Windows-style path."""
        work = Work(title="Test")
        work.files = None

        work.set_file_path("sanitized", "C:\\Users\\test\\output\\file.md", "hash123")

        assert work.files["sanitized"]["path"] == "file.md"
        assert work.files["sanitized"]["hash"] == "hash123"

    def test_set_file_path_with_none_value(self):
        """Test set_file_path with None path value."""
        work = Work(title="Test")
        work.files = None

        work.set_file_path("sanitized", None, "hash123")

        assert work.files["sanitized"]["path"] is None
        assert work.files["sanitized"]["hash"] == "hash123"

    def test_set_file_path_creates_nested_dict_if_missing(self):
        """Test set_file_path creates nested dict for new key."""
        work = Work(title="Test")
        work.files = {}

        work.set_file_path("sanitized", "/path/file.md", "hash")

        assert "sanitized" in work.files
        assert "path" in work.files["sanitized"]
        assert "hash" in work.files["sanitized"]

    def test_set_markdown_path_with_nested_directories(self):
        """Test set_markdown_path extracts filename from deeply nested path."""
        work = Work(title="Test")
        work.set_markdown_path("/home/user/projects/vulcanlab/data/output/subfolder/file.md")

        assert work.markdown_path == "file.md"

    def test_set_file_path_updates_path_preserves_other_keys(self):
        """Test set_file_path preserves other metadata keys."""
        work = Work(title="Test")
        work.files = {"sanitized": {"path": "old.md", "hash": "hash", "custom": "value"}}

        work.set_file_path("sanitized", "new.md")

        assert work.files["sanitized"]["path"] == "new.md"
        assert work.files["sanitized"]["hash"] == "hash"
        assert work.files["sanitized"]["custom"] == "value"
