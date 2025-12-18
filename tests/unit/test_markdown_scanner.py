"""
Unit tests for markdown file scanner.

Tests list_markdown_files() function.

Usage:
    pytest tests/unit/test_markdown_scanner.py -v
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from vulcanlab.markdown_import.scanner import list_markdown_files
from vulcanlab.config import AppConfig, PathsConfig


class TestListMarkdownFiles:
    """Tests for list_markdown_files() function."""

    def test_list_markdown_files_with_metadata(self):
        """Test listing markdown files with valid metadata."""
        with TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "test1.md"
            file1.write_text("""---
title: "Book One"
author: "Author One"
year: 2023
---

Content""", encoding='utf-8')

            file2 = Path(tmpdir) / "test2.md"
            file2.write_text("""---
title: "Book Two"
---

Content""", encoding='utf-8')

            # Mock config
            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.input_dir = tmpdir

            with patch('vulcanlab.markdown_import.scanner.load_config', return_value=mock_config):
                files = list_markdown_files()

                assert len(files) == 2

                # Check first file
                assert files[0].filename == "test1.md"
                assert files[0].has_metadata is True
                assert files[0].metadata.title == "Book One"
                assert files[0].metadata.author == "Author One"
                assert files[0].metadata.year == 2023

                # Check second file
                assert files[1].filename == "test2.md"
                assert files[1].has_metadata is True
                assert files[1].metadata.title == "Book Two"

    def test_list_markdown_files_without_metadata(self):
        """Test listing markdown files without metadata."""
        with TemporaryDirectory() as tmpdir:
            # Create file without metadata
            file1 = Path(tmpdir) / "no-metadata.md"
            file1.write_text("# Just Content\n\nNo metadata here.", encoding='utf-8')

            # Mock config
            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.input_dir = tmpdir

            with patch('vulcanlab.markdown_import.scanner.load_config', return_value=mock_config):
                files = list_markdown_files()

                assert len(files) == 1
                assert files[0].filename == "no-metadata.md"
                assert files[0].has_metadata is False
                assert files[0].metadata is None

    def test_list_markdown_files_empty_directory(self):
        """Test listing files from empty directory."""
        with TemporaryDirectory() as tmpdir:
            # Mock config
            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.input_dir = tmpdir

            with patch('vulcanlab.markdown_import.scanner.load_config', return_value=mock_config):
                files = list_markdown_files()

                assert len(files) == 0

    def test_list_markdown_files_skips_hidden(self):
        """Test that hidden files are skipped."""
        with TemporaryDirectory() as tmpdir:
            # Create visible and hidden files
            visible = Path(tmpdir) / "visible.md"
            visible.write_text("# Content", encoding='utf-8')

            hidden = Path(tmpdir) / ".hidden.md"
            hidden.write_text("# Hidden", encoding='utf-8')

            # Mock config
            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.input_dir = tmpdir

            with patch('vulcanlab.markdown_import.scanner.load_config', return_value=mock_config):
                files = list_markdown_files()

                assert len(files) == 1
                assert files[0].filename == "visible.md"

    def test_list_markdown_files_only_md_extension(self):
        """Test that only .md files are listed."""
        with TemporaryDirectory() as tmpdir:
            # Create various files
            md_file = Path(tmpdir) / "document.md"
            md_file.write_text("# Content", encoding='utf-8')

            txt_file = Path(tmpdir) / "readme.txt"
            txt_file.write_text("Text file", encoding='utf-8')

            # Mock config
            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.input_dir = tmpdir

            with patch('vulcanlab.markdown_import.scanner.load_config', return_value=mock_config):
                files = list_markdown_files()

                assert len(files) == 1
                assert files[0].filename == "document.md"

    def test_list_markdown_files_sorted(self):
        """Test that files are returned in sorted order."""
        with TemporaryDirectory() as tmpdir:
            # Create files in non-alphabetical order
            (Path(tmpdir) / "c.md").write_text("# C", encoding='utf-8')
            (Path(tmpdir) / "a.md").write_text("# A", encoding='utf-8')
            (Path(tmpdir) / "b.md").write_text("# B", encoding='utf-8')

            # Mock config
            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.input_dir = tmpdir

            with patch('vulcanlab.markdown_import.scanner.load_config', return_value=mock_config):
                files = list_markdown_files()

                assert len(files) == 3
                assert files[0].filename == "a.md"
                assert files[1].filename == "b.md"
                assert files[2].filename == "c.md"

    def test_list_markdown_files_no_config(self):
        """Test that ValueError raised when input_dir not configured."""
        mock_config = Mock(spec=AppConfig)
        mock_config.paths = Mock(spec=PathsConfig)
        mock_config.paths.input_dir = None

        with patch('vulcanlab.markdown_import.scanner.load_config', return_value=mock_config):
            with pytest.raises(ValueError, match="input_dir not configured"):
                list_markdown_files()

    def test_list_markdown_files_empty_config(self):
        """Test that ValueError raised when input_dir is empty string."""
        mock_config = Mock(spec=AppConfig)
        mock_config.paths = Mock(spec=PathsConfig)
        mock_config.paths.input_dir = ""

        with patch('vulcanlab.markdown_import.scanner.load_config', return_value=mock_config):
            with pytest.raises(ValueError, match="input_dir not configured"):
                list_markdown_files()

    def test_list_markdown_files_nonexistent_directory(self):
        """Test that empty list returned when directory doesn't exist."""
        mock_config = Mock(spec=AppConfig)
        mock_config.paths = Mock(spec=PathsConfig)
        mock_config.paths.input_dir = "/nonexistent/directory"

        with patch('vulcanlab.markdown_import.scanner.load_config', return_value=mock_config):
            files = list_markdown_files()
            assert len(files) == 0

    def test_list_markdown_files_not_directory(self):
        """Test that ValueError raised when input_dir is a file."""
        with TemporaryDirectory() as tmpdir:
            # Create a file instead of directory
            file_path = Path(tmpdir) / "not-a-dir.txt"
            file_path.write_text("content", encoding='utf-8')

            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.input_dir = str(file_path)

            with patch('vulcanlab.markdown_import.scanner.load_config', return_value=mock_config):
                with pytest.raises(ValueError, match="is not a directory"):
                    list_markdown_files()

    def test_list_markdown_files_mixed_valid_invalid(self):
        """Test listing with mix of valid and invalid markdown files."""
        with TemporaryDirectory() as tmpdir:
            # Valid file
            valid = Path(tmpdir) / "valid.md"
            valid.write_text("""---
title: "Valid"
---
Content""", encoding='utf-8')

            # Invalid YAML
            invalid = Path(tmpdir) / "invalid.md"
            invalid.write_text("""---
invalid: [yaml
---
Content""", encoding='utf-8')

            # No metadata
            no_meta = Path(tmpdir) / "no-meta.md"
            no_meta.write_text("# Content", encoding='utf-8')

            # Mock config
            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.input_dir = tmpdir

            with patch('vulcanlab.markdown_import.scanner.load_config', return_value=mock_config):
                files = list_markdown_files()

                assert len(files) == 3

                # Valid file should have metadata
                valid_file = next(f for f in files if f.filename == "valid.md")
                assert valid_file.has_metadata is True

                # Invalid and no-meta should not have metadata
                invalid_file = next(f for f in files if f.filename == "invalid.md")
                assert invalid_file.has_metadata is False

                no_meta_file = next(f for f in files if f.filename == "no-meta.md")
                assert no_meta_file.has_metadata is False

    def test_list_markdown_files_file_paths(self):
        """Test that file_path contains full path."""
        with TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "test.md"
            file1.write_text("# Content", encoding='utf-8')

            # Mock config
            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.input_dir = tmpdir

            with patch('vulcanlab.markdown_import.scanner.load_config', return_value=mock_config):
                files = list_markdown_files()

                assert len(files) == 1
                assert files[0].file_path == str(file1)
                assert Path(files[0].file_path).exists()
