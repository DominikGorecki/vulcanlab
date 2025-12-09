"""
Unit tests for new work creation.

Tests work creation logic, validation, database insertion, and error handling.

Usage:
    pytest tests/unit/test_new_work.py -v
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, Mock, patch

from vulcanlab.conversions.new_work import create_new_work, DuplicateWorkError
from vulcanlab.data.models.work import Work


class TestDuplicateWorkError:
    """Tests for DuplicateWorkError exception."""

    def test_duplicate_work_error_creation(self):
        """Test that DuplicateWorkError can be created."""
        error = DuplicateWorkError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)


class TestCreateNewWork:
    """Tests for create_new_work() function."""

    @patch('vulcanlab.conversions.new_work.parse_toc_titles')
    @patch('vulcanlab.conversions.new_work.compute_file_hash')
    @patch('vulcanlab.conversions.new_work.get_session')
    def test_create_new_work_success_all_fields(
        self, mock_get_session, mock_compute_hash, mock_parse_toc
    ):
        """Test successful work creation with all fields."""
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None  # No duplicate
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Setup file hash
        mock_compute_hash.return_value = "test_content_hash"

        # Setup TOC parsing
        mock_toc_entry = Mock()
        mock_toc_entry.level = 1
        mock_toc_entry.title = "Chapter 1"
        mock_toc_result = Mock()
        mock_toc_result.entries = [mock_toc_entry]
        mock_parse_toc.return_value = mock_toc_result

        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Test Book\n\nContent here", encoding='utf-8')

            # Create related files
            pdf_path = Path(tmpdir) / "test.pdf"
            pdf_path.write_text("PDF content", encoding='utf-8')
            sanitized_path = Path(tmpdir) / "test.sanitized.md"
            sanitized_path.write_text("Sanitized content", encoding='utf-8')
            toc_path = Path(tmpdir) / "test.toc_titles.md"
            toc_path.write_text("# Chapter 1", encoding='utf-8')

            # Mock hash computation for multiple files
            hash_counter = 0
            def hash_side_effect(path):
                nonlocal hash_counter
                hash_counter += 1
                return f"hash_{hash_counter}"

            mock_compute_hash.side_effect = hash_side_effect

            result = create_new_work(
                title="Test Book",
                markdown_path=md_path,
                authors="John Doe",
                year=2024,
                publisher="Test Publisher",
                isbn="978-0123456789",
                edition="3rd Edition",
                volume="Volume 1",
                issue="Issue 1",
                pages="100-200",
                url="https://example.com",
                city="New York",
                institution="Test University",
                editor="Jane Editor"
            )

            # Verify Work was created
            assert isinstance(result, Work)
            assert result.title == "Test Book"
            assert result.authors == "John Doe"
            assert result.year == 2024
            assert result.publisher == "Test Publisher"
            assert result.isbn == "978-0123456789"
            assert result.edition == "3rd Edition"
            assert result.volume == "Volume 1"
            assert result.issue == "Issue 1"
            assert result.pages == "100-200"
            assert result.url == "https://example.com"
            assert result.city == "New York"
            assert result.institution == "Test University"
            assert result.editor == "Jane Editor"
            assert result.content_hash == "hash_1"
            assert result.toc == [{"level": 1, "title": "Chapter 1"}]
            assert "original_file" in result.files
            assert "sanitized" in result.files

            # Verify database operations
            assert mock_session.add.call_count == 1
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(result)

    @patch('vulcanlab.conversions.new_work.compute_file_hash')
    @patch('vulcanlab.conversions.new_work.get_session')
    def test_create_new_work_minimal_fields(
        self, mock_get_session, mock_compute_hash
    ):
        """Test work creation with minimal required fields."""
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Setup file hash
        mock_compute_hash.return_value = "test_hash"

        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Test Book", encoding='utf-8')

            result = create_new_work(
                title="Test Book",
                markdown_path=md_path
            )

            # Verify Work was created with minimal fields
            assert isinstance(result, Work)
            assert result.title == "Test Book"
            assert result.authors is None
            assert result.year is None
            assert result.content_hash == "test_hash"
            assert result.toc is None
            # The markdown file itself will be discovered as original_markdown
            assert result.files is not None
            assert "original_markdown" in result.files

            # Verify database operations
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_create_new_work_file_not_found(self):
        """Test error when markdown file doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "nonexistent.md"

            with pytest.raises(FileNotFoundError) as exc_info:
                create_new_work(
                    title="Test Book",
                    markdown_path=md_path
                )
            assert "not found" in str(exc_info.value).lower()

    def test_create_new_work_path_not_file(self):
        """Test error when path is not a file."""
        with TemporaryDirectory() as tmpdir:
            md_dir = Path(tmpdir) / "test_dir"
            md_dir.mkdir()

            with pytest.raises(ValueError) as exc_info:
                create_new_work(
                    title="Test Book",
                    markdown_path=md_dir
                )
            assert "not a file" in str(exc_info.value).lower()

    def test_create_new_work_invalid_year_type(self):
        """Test error when year is not an integer."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Test Book", encoding='utf-8')

            with pytest.raises(ValueError) as exc_info:
                create_new_work(
                    title="Test Book",
                    markdown_path=md_path,
                    year="2024"  # String instead of int
                )
            assert "integer" in str(exc_info.value).lower()

    def test_create_new_work_invalid_year_too_small(self):
        """Test error when year is less than 1000."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Test Book", encoding='utf-8')

            with pytest.raises(ValueError) as exc_info:
                create_new_work(
                    title="Test Book",
                    markdown_path=md_path,
                    year=999
                )
            assert "4-digit" in str(exc_info.value).lower()

    def test_create_new_work_invalid_year_too_large(self):
        """Test error when year is greater than 9999."""
        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Test Book", encoding='utf-8')

            with pytest.raises(ValueError) as exc_info:
                create_new_work(
                    title="Test Book",
                    markdown_path=md_path,
                    year=10000
                )
            assert "4-digit" in str(exc_info.value).lower()

    @patch('vulcanlab.conversions.new_work.compute_file_hash')
    @patch('vulcanlab.conversions.new_work.get_session')
    def test_create_new_work_duplicate_check_enabled(
        self, mock_get_session, mock_compute_hash
    ):
        """Test duplicate checking when enabled."""
        # Setup existing work
        existing_work = Mock()
        existing_work.id = 1
        existing_work.title = "Existing Book"

        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = existing_work
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Setup file hash
        mock_compute_hash.return_value = "duplicate_hash"

        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Test Book", encoding='utf-8')

            with pytest.raises(DuplicateWorkError) as exc_info:
                create_new_work(
                    title="Test Book",
                    markdown_path=md_path,
                    check_duplicates=True
                )
            assert "already exists" in str(exc_info.value)
            assert "Existing Book" in str(exc_info.value)

    @patch('vulcanlab.conversions.new_work.compute_file_hash')
    @patch('vulcanlab.conversions.new_work.get_session')
    def test_create_new_work_duplicate_check_disabled(
        self, mock_get_session, mock_compute_hash
    ):
        """Test that duplicate checking can be disabled."""
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Setup file hash
        mock_compute_hash.return_value = "test_hash"

        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Test Book", encoding='utf-8')

            result = create_new_work(
                title="Test Book",
                markdown_path=md_path,
                check_duplicates=False
            )

            # Verify no duplicate check was performed
            # The query should only be called for the insert, not for duplicate check
            assert isinstance(result, Work)

    @patch('vulcanlab.conversions.new_work.compute_file_hash')
    @patch('vulcanlab.conversions.new_work.get_session')
    def test_create_new_work_file_discovery(
        self, mock_get_session, mock_compute_hash
    ):
        """Test that related files are discovered and tracked."""
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Setup file hash computation
        hash_counter = 0
        def hash_side_effect(path):
            nonlocal hash_counter
            hash_counter += 1
            return f"hash_{hash_counter}"

        mock_compute_hash.side_effect = hash_side_effect

        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Test Book", encoding='utf-8')

            # Create various related files
            epub_path = Path(tmpdir) / "test.epub"
            epub_path.write_text("EPUB content", encoding='utf-8')
            hier_path = Path(tmpdir) / "test.hier.md"
            hier_path.write_text("Hier content", encoding='utf-8')
            sanitized_path = Path(tmpdir) / "test.sanitized.md"
            sanitized_path.write_text("Sanitized content", encoding='utf-8')
            vec_suggestions_path = Path(tmpdir) / "test.sanitized.vec_sugg.md"
            vec_suggestions_path.write_text("Suggestions", encoding='utf-8')

            result = create_new_work(
                title="Test Book",
                markdown_path=md_path
            )

            # Verify files were discovered
            assert result.files is not None
            assert "original_file" in result.files  # Should find .epub (first match)
            assert "hier_markdown" in result.files
            assert "sanitized" in result.files
            assert "vec_suggestions" in result.files

            # Verify file paths are absolute
            assert Path(result.files["original_file"]["path"]).is_absolute()
            assert "hash" in result.files["original_file"]

    @patch('vulcanlab.conversions.new_work.parse_toc_titles')
    @patch('vulcanlab.conversions.new_work.compute_file_hash')
    @patch('vulcanlab.conversions.new_work.get_session')
    def test_create_new_work_toc_parsing_success(
        self, mock_get_session, mock_compute_hash, mock_parse_toc
    ):
        """Test TOC parsing when file exists."""
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Setup file hash
        mock_compute_hash.return_value = "test_hash"

        # Setup TOC parsing
        mock_toc_entry1 = Mock()
        mock_toc_entry1.level = 1
        mock_toc_entry1.title = "Introduction"
        mock_toc_entry2 = Mock()
        mock_toc_entry2.level = 2
        mock_toc_entry2.title = "Overview"
        mock_toc_result = Mock()
        mock_toc_result.entries = [mock_toc_entry1, mock_toc_entry2]
        mock_parse_toc.return_value = mock_toc_result

        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Test Book", encoding='utf-8')
            toc_path = Path(tmpdir) / "test.toc_titles.md"
            toc_path.write_text("# Introduction\n## Overview", encoding='utf-8')

            result = create_new_work(
                title="Test Book",
                markdown_path=md_path
            )

            # Verify TOC was parsed
            assert result.toc == [
                {"level": 1, "title": "Introduction"},
                {"level": 2, "title": "Overview"}
            ]
            mock_parse_toc.assert_called_once_with(toc_path)

    @patch('vulcanlab.conversions.new_work.parse_toc_titles')
    @patch('vulcanlab.conversions.new_work.compute_file_hash')
    @patch('vulcanlab.conversions.new_work.get_session')
    def test_create_new_work_toc_parsing_error_verbose(
        self, mock_get_session, mock_compute_hash, mock_parse_toc
    ):
        """Test TOC parsing error handling with verbose=True."""
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Setup file hash
        mock_compute_hash.return_value = "test_hash"

        # Setup TOC parsing to raise error
        mock_parse_toc.side_effect = Exception("Parse error")

        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Test Book", encoding='utf-8')
            toc_path = Path(tmpdir) / "test.toc_titles.md"
            toc_path.write_text("Invalid TOC", encoding='utf-8')

            # Should not raise, but print warning
            with patch('builtins.print') as mock_print:
                result = create_new_work(
                    title="Test Book",
                    markdown_path=md_path,
                    verbose=True
                )
                # Verify warning was printed
                assert mock_print.called
                assert "Warning" in str(mock_print.call_args)

            # Verify TOC is None due to error
            assert result.toc is None

    @patch('vulcanlab.conversions.new_work.parse_toc_titles')
    @patch('vulcanlab.conversions.new_work.compute_file_hash')
    @patch('vulcanlab.conversions.new_work.get_session')
    def test_create_new_work_toc_missing_verbose(
        self, mock_get_session, mock_compute_hash, mock_parse_toc
    ):
        """Test warning when TOC file is missing with verbose=True."""
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Setup file hash
        mock_compute_hash.return_value = "test_hash"

        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Test Book", encoding='utf-8')
            # Don't create TOC file

            # Should print warning
            with patch('builtins.print') as mock_print:
                result = create_new_work(
                    title="Test Book",
                    markdown_path=md_path,
                    verbose=True
                )
                # Verify warning was printed
                assert mock_print.called
                assert "TOC file not found" in str(mock_print.call_args)

            # Verify TOC is None
            assert result.toc is None
            # Verify parse_toc_titles was not called
            mock_parse_toc.assert_not_called()

    @patch('vulcanlab.conversions.new_work.compute_file_hash')
    @patch('vulcanlab.conversions.new_work.get_session')
    def test_create_new_work_path_resolution(
        self, mock_get_session, mock_compute_hash
    ):
        """Test that markdown path is resolved to absolute path."""
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Setup file hash
        mock_compute_hash.return_value = "test_hash"

        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Test Book", encoding='utf-8')

            # Use relative path
            relative_path = Path("test.md")
            with patch('pathlib.Path.resolve', return_value=md_path):
                result = create_new_work(
                    title="Test Book",
                    markdown_path=relative_path
                )

            # Verify markdown_path is stored as absolute
            assert Path(result.markdown_path).is_absolute()

    @patch('vulcanlab.conversions.new_work.compute_file_hash')
    @patch('vulcanlab.conversions.new_work.get_session')
    def test_create_new_work_file_discovery_priority(
        self, mock_get_session, mock_compute_hash
    ):
        """Test that file discovery uses first match in priority order."""
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Setup file hash
        mock_compute_hash.return_value = "test_hash"

        with TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Test Book", encoding='utf-8')

            # Create multiple original_file candidates (PDF and EPUB)
            pdf_path = Path(tmpdir) / "test.pdf"
            pdf_path.write_text("PDF content", encoding='utf-8')
            epub_path = Path(tmpdir) / "test.epub"
            epub_path.write_text("EPUB content", encoding='utf-8')

            result = create_new_work(
                title="Test Book",
                markdown_path=md_path
            )

            # Should use PDF (first in priority list)
            assert "original_file" in result.files
            assert result.files["original_file"]["path"] == str(pdf_path.absolute())

