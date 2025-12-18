"""
Unit tests for markdown export core functions.

Tests export_work(), get_markdown_source(), generate_export_filename(),
and create_frontmatter() functions.

Usage:
    pytest tests/unit/test_markdown_export.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import HTTPException

from vulcanlab.markdown_export.export import (
    export_work,
    generate_export_filename,
    create_frontmatter,
    get_markdown_source,
)
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.config import AppConfig, PathsConfig


class TestGenerateExportFilename:
    """Tests for generate_export_filename() function."""

    def test_simple_title(self):
        """Test filename generation with simple title."""
        result = generate_export_filename("The Psychology of Learning")
        assert result == "the-psychology-of-learning.md"

    def test_title_with_special_characters(self):
        """Test filename generation removes special characters."""
        result = generate_export_filename("Cognitive Science: Theory & Practice!")
        assert result == "cognitive-science-theory-practice.md"

    def test_title_with_multiple_spaces(self):
        """Test filename generation handles multiple spaces."""
        result = generate_export_filename("Word   With    Multiple     Spaces")
        assert result == "word-with-multiple-spaces.md"

    def test_title_with_unicode(self):
        """Test filename generation handles unicode characters."""
        result = generate_export_filename("Café Résumé Naïve")
        # Unicode characters should be removed
        assert result == "caf-rsum-nave.md"

    def test_long_title(self):
        """Test filename generation truncates long titles."""
        long_title = "A" * 150
        result = generate_export_filename(long_title)
        # Should be limited to 100 characters before extension
        assert len(result) == 103  # 100 + ".md"
        assert result.endswith(".md")

    def test_title_with_leading_trailing_spaces(self):
        """Test filename generation handles leading/trailing spaces."""
        result = generate_export_filename("  Spaced Title  ")
        assert result == "spaced-title.md"

    def test_title_with_only_special_chars(self):
        """Test filename generation with only special characters."""
        result = generate_export_filename("!@#$%^&*()")
        assert result == ".md"

    def test_title_with_hyphens(self):
        """Test filename generation preserves hyphens."""
        result = generate_export_filename("Self-Directed Learning")
        assert result == "self-directed-learning.md"

    def test_title_with_consecutive_hyphens(self):
        """Test filename generation collapses consecutive hyphens."""
        result = generate_export_filename("Word---With---Hyphens")
        assert result == "word-with-hyphens.md"

    def test_title_with_numbers(self):
        """Test filename generation preserves numbers."""
        result = generate_export_filename("Psychology 101 Chapter 2")
        assert result == "psychology-101-chapter-2.md"


class TestCreateFrontmatter:
    """Tests for create_frontmatter() function."""

    def test_frontmatter_with_all_fields(self):
        """Test frontmatter generation with all fields."""
        result = create_frontmatter("Test Book", "John Doe", 2023)
        expected = '---\ntitle: "Test Book"\nauthor: "John Doe"\nyear: 2023\n---\n'
        assert result == expected

    def test_frontmatter_without_author(self):
        """Test frontmatter generation without author."""
        result = create_frontmatter("Test Book", None, 2023)
        expected = '---\ntitle: "Test Book"\nyear: 2023\n---\n'
        assert result == expected

    def test_frontmatter_without_year(self):
        """Test frontmatter generation without year."""
        result = create_frontmatter("Test Book", "John Doe", None)
        expected = '---\ntitle: "Test Book"\nauthor: "John Doe"\n---\n'
        assert result == expected

    def test_frontmatter_with_only_title(self):
        """Test frontmatter generation with only title."""
        result = create_frontmatter("Test Book", None, None)
        expected = '---\ntitle: "Test Book"\n---\n'
        assert result == expected

    def test_frontmatter_with_title_containing_quotes(self):
        """Test frontmatter generation with title containing quotes."""
        result = create_frontmatter('Book "Title" Here', "Author", 2023)
        # Should still work with quotes
        assert 'title: "Book "Title" Here"' in result

    def test_frontmatter_yaml_structure(self):
        """Test frontmatter has valid YAML structure."""
        result = create_frontmatter("Test", "Author", 2023)
        lines = result.split('\n')
        assert lines[0] == "---"
        assert lines[-2] == "---"
        assert lines[-1] == ""  # Trailing newline


class TestGetMarkdownSource:
    """Tests for get_markdown_source() function."""

    def test_get_markdown_from_db_simple_conversion(self):
        """Test retrieving markdown from database for simple conversion."""
        # Mock work
        mock_work = Mock(spec=Work)
        mock_work.id = 1
        mock_work.title = "Test Work"
        mock_work.files = None

        # Mock sanitized markdown
        mock_sanitized = Mock(spec=SanitizedMarkdown)
        mock_sanitized.content = "# Test Content\n\nThis is test markdown."

        # Mock session query
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_sanitized

        content, source = get_markdown_source(mock_work, mock_session)

        assert content == "# Test Content\n\nThis is test markdown."
        assert source == "db"
        mock_session.query.assert_called_once_with(SanitizedMarkdown)

    def test_get_markdown_from_file_advanced_conversion(self):
        """Test retrieving markdown from output folder for advanced conversion."""
        with TemporaryDirectory() as tmpdir:
            # Create test markdown file
            output_dir = Path(tmpdir)
            test_file = output_dir / "test-sanitized.md"
            test_content = "# Advanced Content\n\nFrom file."
            test_file.write_text(test_content, encoding='utf-8')

            # Mock work with files JSON
            mock_work = Mock(spec=Work)
            mock_work.id = 1
            mock_work.title = "Test Work"
            mock_work.files = {
                'sanitized': {
                    'path': 'test-sanitized.md',
                    'hash': 'abc123'
                }
            }

            # Mock session (no sanitized markdown in DB)
            mock_session = Mock()
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None

            # Mock config
            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.output_dir = tmpdir

            with patch('vulcanlab.markdown_export.export.load_config', return_value=mock_config):
                content, source = get_markdown_source(mock_work, mock_session)

                assert content == test_content
                assert source == "file"

    def test_get_markdown_raises_when_unavailable(self):
        """Test get_markdown_source raises ValueError when markdown unavailable."""
        # Mock work with no files
        mock_work = Mock(spec=Work)
        mock_work.id = 1
        mock_work.title = "Test Work"
        mock_work.files = None

        # Mock session (no sanitized markdown in DB)
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with pytest.raises(ValueError, match="No markdown available"):
            get_markdown_source(mock_work, mock_session)

    def test_get_markdown_raises_when_file_not_found(self):
        """Test get_markdown_source raises ValueError when file not found."""
        with TemporaryDirectory() as tmpdir:
            # Mock work with files JSON but file doesn't exist
            mock_work = Mock(spec=Work)
            mock_work.id = 1
            mock_work.title = "Test Work"
            mock_work.files = {
                'sanitized': {
                    'path': 'nonexistent.md',
                    'hash': 'abc123'
                }
            }

            # Mock session (no sanitized markdown in DB)
            mock_session = Mock()
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None

            # Mock config
            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.output_dir = tmpdir

            with patch('vulcanlab.markdown_export.export.load_config', return_value=mock_config):
                with pytest.raises(ValueError, match="No markdown available"):
                    get_markdown_source(mock_work, mock_session)

    def test_get_markdown_handles_file_read_error(self):
        """Test get_markdown_source handles file read errors."""
        with TemporaryDirectory() as tmpdir:
            # Create test file
            output_dir = Path(tmpdir)
            test_file = output_dir / "test-sanitized.md"
            test_file.write_text("content", encoding='utf-8')

            # Mock work
            mock_work = Mock(spec=Work)
            mock_work.id = 1
            mock_work.title = "Test Work"
            mock_work.files = {
                'sanitized': {
                    'path': 'test-sanitized.md',
                    'hash': 'abc123'
                }
            }

            # Mock session (no sanitized markdown in DB)
            mock_session = Mock()
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None

            # Mock config
            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.output_dir = tmpdir

            with patch('vulcanlab.markdown_export.export.load_config', return_value=mock_config):
                # Mock read_text to raise error
                with patch.object(Path, 'read_text', side_effect=IOError("Read failed")):
                    with pytest.raises(ValueError, match="Failed to read markdown file"):
                        get_markdown_source(mock_work, mock_session)


class TestExportWork:
    """Tests for export_work() function."""

    def test_export_work_success(self):
        """Test successful work export."""
        with TemporaryDirectory() as tmpdir:
            exports_dir = Path(tmpdir) / "exports"
            exports_dir.mkdir()

            # Mock work
            mock_work = Mock(spec=Work)
            mock_work.id = 1
            mock_work.title = "Test Psychology Book"
            mock_work.authors = "John Doe"
            mock_work.year = 2023

            # Mock sanitized markdown
            mock_sanitized = Mock(spec=SanitizedMarkdown)
            mock_sanitized.content = "# Chapter 1\n\nContent here."

            # Mock session
            mock_session = Mock()
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query

            # First call returns work, second call returns sanitized markdown
            call_count = [0]
            def mock_first():
                call_count[0] += 1
                if call_count[0] == 1:
                    return mock_work
                else:
                    return mock_sanitized

            mock_query.first = mock_first

            with patch('vulcanlab.markdown_export.export.get_exports_dir', return_value=exports_dir):
                result = export_work(1, mock_session)

                # Check file was created
                expected_filename = "test-psychology-book.md"
                expected_path = exports_dir / expected_filename
                assert expected_path.exists()

                # Check file content
                content = expected_path.read_text(encoding='utf-8')
                assert 'title: "Test Psychology Book"' in content
                assert 'author: "John Doe"' in content
                assert 'year: 2023' in content
                assert '# Chapter 1' in content
                assert 'Content here.' in content

                # Check return value
                assert result == str(expected_path)

    def test_export_work_not_found(self):
        """Test export_work raises 404 when work not found."""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            export_work(999, mock_session)

        assert exc_info.value.status_code == 404
        assert "Work not found" in exc_info.value.detail

    def test_export_work_markdown_unavailable(self):
        """Test export_work raises 400 when markdown unavailable."""
        # Mock work
        mock_work = Mock(spec=Work)
        mock_work.id = 1
        mock_work.title = "Test Work"
        mock_work.files = None

        # Mock session - work found, but no sanitized markdown
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        call_count = [0]
        def mock_first():
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_work
            else:
                return None

        mock_query.first = mock_first

        with pytest.raises(HTTPException) as exc_info:
            export_work(1, mock_session)

        assert exc_info.value.status_code == 400
        assert "No markdown available" in exc_info.value.detail

    def test_export_work_write_failure(self):
        """Test export_work raises 500 on write failure."""
        with TemporaryDirectory() as tmpdir:
            exports_dir = Path(tmpdir) / "exports"
            exports_dir.mkdir()

            # Mock work
            mock_work = Mock(spec=Work)
            mock_work.id = 1
            mock_work.title = "Test Work"
            mock_work.authors = "Author"
            mock_work.year = 2023

            # Mock sanitized markdown
            mock_sanitized = Mock(spec=SanitizedMarkdown)
            mock_sanitized.content = "Content"

            # Mock session
            mock_session = Mock()
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query

            call_count = [0]
            def mock_first():
                call_count[0] += 1
                if call_count[0] == 1:
                    return mock_work
                else:
                    return mock_sanitized

            mock_query.first = mock_first

            with patch('vulcanlab.markdown_export.export.get_exports_dir', return_value=exports_dir):
                # Mock write_text to raise error
                with patch.object(Path, 'write_text', side_effect=IOError("Write failed")):
                    with pytest.raises(HTTPException) as exc_info:
                        export_work(1, mock_session)

                    assert exc_info.value.status_code == 500
                    assert "Failed to write export file" in exc_info.value.detail

    def test_export_work_exports_dir_error(self):
        """Test export_work raises 500 when exports directory unavailable."""
        # Mock work
        mock_work = Mock(spec=Work)
        mock_work.id = 1
        mock_work.title = "Test Work"

        # Mock sanitized markdown
        mock_sanitized = Mock(spec=SanitizedMarkdown)
        mock_sanitized.content = "Content"

        # Mock session
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        call_count = [0]
        def mock_first():
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_work
            else:
                return mock_sanitized

        mock_query.first = mock_first

        with patch('vulcanlab.markdown_export.export.get_exports_dir', side_effect=ValueError("Config error")):
            with pytest.raises(HTTPException) as exc_info:
                export_work(1, mock_session)

            assert exc_info.value.status_code == 500
            assert "Failed to access exports directory" in exc_info.value.detail
