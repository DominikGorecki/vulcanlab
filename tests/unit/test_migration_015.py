"""
Unit tests for migration 015: Convert absolute paths to filenames.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Import migration module dynamically since filename starts with number
migration_path = Path(__file__).parent.parent.parent / "migrations" / "migration_015_convert_paths_to_filenames.py"
spec = importlib.util.spec_from_file_location("migration_015", migration_path)
migration_015 = importlib.util.module_from_spec(spec)
sys.modules["migration_015"] = migration_015
spec.loader.exec_module(migration_015)

extract_filename = migration_015.extract_filename
extract_paths_from_files_json = migration_015.extract_paths_from_files_json


class TestExtractFilename:
    """Tests for extract_filename helper function."""

    def test_extract_filename_windows_path(self):
        """Test extracting filename from Windows absolute path."""
        path = "D:\\vulcanlab_data\\output\\file.pdf"
        result = extract_filename(path)
        assert result == "file.pdf"

    def test_extract_filename_linux_path(self):
        """Test extracting filename from Linux absolute path."""
        path = "/home/user/vulcanData/output/file.pdf"
        result = extract_filename(path)
        assert result == "file.pdf"

    def test_extract_filename_mixed_separators(self):
        """Test extracting filename from path with mixed separators."""
        path = "D:/data\\output/file.pdf"
        result = extract_filename(path)
        assert result == "file.pdf"

    def test_extract_filename_already_filename(self):
        """Test that already-filename input returns unchanged."""
        path = "file.pdf"
        result = extract_filename(path)
        assert result == "file.pdf"

    def test_extract_filename_null(self):
        """Test extract_filename with None input."""
        result = extract_filename(None)
        assert result is None

    def test_extract_filename_empty(self):
        """Test extract_filename with empty string."""
        result = extract_filename("")
        assert result == ""

    def test_extract_filename_deeply_nested(self):
        """Test extracting filename from deeply nested path."""
        path = "/home/user/projects/vulcanlab/data/output/subfolder/deep/file.md"
        result = extract_filename(path)
        assert result == "file.md"

    def test_extract_filename_windows_drive_only(self):
        """Test path with just drive letter and filename."""
        path = "C:\\file.txt"
        result = extract_filename(path)
        assert result == "file.txt"

    def test_extract_filename_trailing_separator(self):
        """Test path with trailing separator (directory)."""
        path = "/home/user/data/"
        result = extract_filename(path)
        assert result == ""

    def test_extract_filename_no_extension(self):
        """Test filename without extension."""
        path = "/home/user/data/README"
        result = extract_filename(path)
        assert result == "README"


class TestExtractPathsFromFilesJson:
    """Tests for extract_paths_from_files_json helper function."""

    def test_extract_paths_from_files_json_single_entry(self):
        """Test extracting path from single file entry."""
        files_json = {
            "sanitized": {
                "path": "/full/path/file.md",
                "hash": "abc123"
            }
        }
        result = extract_paths_from_files_json(files_json)

        assert result["sanitized"]["path"] == "file.md"
        assert result["sanitized"]["hash"] == "abc123"

    def test_extract_paths_from_files_json_multiple_entries(self):
        """Test extracting paths from multiple file entries."""
        files_json = {
            "original_file": {
                "path": "D:\\input\\book.pdf",
                "hash": "hash1"
            },
            "sanitized": {
                "path": "/output/book.sanitized.md",
                "hash": "hash2"
            },
            "titles": {
                "path": "/output/book.titles.md",
                "hash": "hash3"
            }
        }
        result = extract_paths_from_files_json(files_json)

        assert result["original_file"]["path"] == "book.pdf"
        assert result["sanitized"]["path"] == "book.sanitized.md"
        assert result["titles"]["path"] == "book.titles.md"
        assert result["original_file"]["hash"] == "hash1"
        assert result["sanitized"]["hash"] == "hash2"
        assert result["titles"]["hash"] == "hash3"

    def test_extract_paths_from_files_json_already_filenames(self):
        """Test idempotency - already filenames return unchanged."""
        files_json = {
            "sanitized": {
                "path": "file.md",
                "hash": "abc"
            }
        }
        result = extract_paths_from_files_json(files_json)

        assert result == files_json

    def test_extract_paths_from_files_json_null(self):
        """Test with None input."""
        result = extract_paths_from_files_json(None)
        assert result is None

    def test_extract_paths_from_files_json_empty_dict(self):
        """Test with empty dict."""
        result = extract_paths_from_files_json({})
        assert result == {}

    def test_extract_paths_from_files_json_missing_path_key(self):
        """Test entry without path key doesn't fail."""
        files_json = {
            "sanitized": {
                "hash": "abc123"
            }
        }
        result = extract_paths_from_files_json(files_json)

        # Should return unchanged
        assert result["sanitized"]["hash"] == "abc123"
        assert "path" not in result["sanitized"]

    def test_extract_paths_from_files_json_non_dict_value(self):
        """Test entry with non-dict value is preserved."""
        files_json = {
            "sanitized": {
                "path": "/full/path/file.md",
                "hash": "abc"
            },
            "other_field": "string_value"
        }
        result = extract_paths_from_files_json(files_json)

        assert result["sanitized"]["path"] == "file.md"
        assert result["other_field"] == "string_value"

    def test_extract_paths_from_files_json_preserves_extra_fields(self):
        """Test that extra metadata fields are preserved."""
        files_json = {
            "sanitized": {
                "path": "/full/path/file.md",
                "hash": "abc123",
                "size": 1024,
                "created_at": "2023-01-01"
            }
        }
        result = extract_paths_from_files_json(files_json)

        assert result["sanitized"]["path"] == "file.md"
        assert result["sanitized"]["hash"] == "abc123"
        assert result["sanitized"]["size"] == 1024
        assert result["sanitized"]["created_at"] == "2023-01-01"

    def test_extract_paths_from_files_json_mixed_paths(self):
        """Test with mix of absolute paths and filenames."""
        files_json = {
            "original_file": {
                "path": "/input/book.pdf",  # Absolute
                "hash": "hash1"
            },
            "sanitized": {
                "path": "book.sanitized.md",  # Already filename
                "hash": "hash2"
            }
        }
        result = extract_paths_from_files_json(files_json)

        assert result["original_file"]["path"] == "book.pdf"
        assert result["sanitized"]["path"] == "book.sanitized.md"

    def test_extract_paths_from_files_json_empty_path(self):
        """Test with empty string path."""
        files_json = {
            "sanitized": {
                "path": "",
                "hash": "abc"
            }
        }
        result = extract_paths_from_files_json(files_json)

        assert result["sanitized"]["path"] == ""
        assert result["sanitized"]["hash"] == "abc"

    def test_extract_paths_from_files_json_null_path(self):
        """Test with None path value."""
        files_json = {
            "sanitized": {
                "path": None,
                "hash": "abc"
            }
        }
        result = extract_paths_from_files_json(files_json)

        assert result["sanitized"]["path"] is None
        assert result["sanitized"]["hash"] == "abc"


class TestMigrationIdempotency:
    """Tests for migration idempotency."""

    def test_extract_filename_idempotent(self):
        """Test that running extract_filename twice gives same result."""
        path = "/full/path/file.pdf"
        result1 = extract_filename(path)
        result2 = extract_filename(result1)

        assert result1 == result2 == "file.pdf"

    def test_extract_paths_from_files_json_idempotent(self):
        """Test that running extraction twice gives same result."""
        files_json = {
            "sanitized": {
                "path": "/full/path/file.md",
                "hash": "abc123"
            }
        }
        result1 = extract_paths_from_files_json(files_json)
        result2 = extract_paths_from_files_json(result1)

        assert result1 == result2
        assert result1["sanitized"]["path"] == "file.md"
