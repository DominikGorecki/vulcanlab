"""
Unit tests for pdf_bookmarks2toc module.

Tests bookmark parsing, TOC generation, and edge cases.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vulcanlab.conversions.pdf_bookmarks2toc import extract_bookmarks_to_toc


class TestExtractBookmarksToToc:
    """Tests for the extract_bookmarks_to_toc function."""

    def test_file_not_found_raises_error(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            extract_bookmarks_to_toc("nonexistent.pdf")

    def test_invalid_extension_raises_error(self, tmp_path):
        """Test that ValueError is raised for non-PDF files."""
        # Create a temporary file with wrong extension
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test content")

        with pytest.raises(ValueError, match="File must be a PDF file"):
            extract_bookmarks_to_toc(txt_file)

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_bookmark_parsing_basic(self, mock_fitz, tmp_path):
        """Test basic bookmark parsing with simple hierarchy."""
        # Create mock PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        # Setup mock PDF document
        mock_doc = MagicMock()
        # PyMuPDF get_toc() returns list of [level, title, page]
        mock_doc.get_toc.return_value = [
            [1, "Chapter 1", 1],
            [2, "Section 1.1", 2],
            [2, "Section 1.2", 5],
            [1, "Chapter 2", 10],
            [2, "Section 2.1", 11],
        ]
        mock_fitz.open.return_value = mock_doc

        # Run extraction
        result = extract_bookmarks_to_toc(pdf_file)

        # Verify
        expected = "# Chapter 1\n\n## Section 1.1\n\n## Section 1.2\n\n# Chapter 2\n\n## Section 2.1"
        assert result == expected
        mock_fitz.open.assert_called_once_with(str(pdf_file))
        mock_doc.get_toc.assert_called_once()
        mock_doc.close.assert_called_once()

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_toc_generation_hierarchical(self, mock_fitz, tmp_path):
        """Test TOC generation with multiple heading levels."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        mock_doc = MagicMock()
        mock_doc.get_toc.return_value = [
            [1, "Introduction", 1],
            [2, "Overview", 2],
            [3, "Background", 3],
            [3, "Motivation", 4],
            [2, "Scope", 5],
            [1, "Methods", 10],
            [2, "Data Collection", 11],
            [3, "Participants", 12],
            [4, "Demographics", 13],
        ]
        mock_fitz.open.return_value = mock_doc

        result = extract_bookmarks_to_toc(pdf_file)

        # Verify hierarchical structure
        lines = result.split("\n\n")
        assert lines[0] == "# Introduction"
        assert lines[1] == "## Overview"
        assert lines[2] == "### Background"
        assert lines[3] == "### Motivation"
        assert lines[4] == "## Scope"
        assert lines[5] == "# Methods"
        assert lines[6] == "## Data Collection"
        assert lines[7] == "### Participants"
        assert lines[8] == "#### Demographics"

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_level_capping_at_h6(self, mock_fitz, tmp_path):
        """Test that heading levels beyond 6 are capped at H6."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        mock_doc = MagicMock()
        # Include levels beyond 6
        mock_doc.get_toc.return_value = [
            [1, "Level 1", 1],
            [6, "Level 6", 2],
            [7, "Level 7 (should be H6)", 3],
            [8, "Level 8 (should be H6)", 4],
            [10, "Level 10 (should be H6)", 5],
        ]
        mock_fitz.open.return_value = mock_doc

        result = extract_bookmarks_to_toc(pdf_file)

        # Verify all deep levels are capped at H6
        lines = result.split("\n\n")
        assert lines[0] == "# Level 1"
        assert lines[1] == "###### Level 6"
        assert lines[2] == "###### Level 7 (should be H6)"
        assert lines[3] == "###### Level 8 (should be H6)"
        assert lines[4] == "###### Level 10 (should be H6)"

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_no_bookmarks_returns_empty_string(self, mock_fitz, tmp_path):
        """Test that PDF with no bookmarks returns empty string."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        mock_doc = MagicMock()
        mock_doc.get_toc.return_value = []  # Empty bookmarks
        mock_fitz.open.return_value = mock_doc

        result = extract_bookmarks_to_toc(pdf_file)

        assert result == ""
        mock_doc.close.assert_called_once()

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_no_bookmarks_with_verbose(self, mock_fitz, tmp_path, capsys):
        """Test verbose output when no bookmarks are found."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        mock_doc = MagicMock()
        mock_doc.get_toc.return_value = []
        mock_fitz.open.return_value = mock_doc

        result = extract_bookmarks_to_toc(pdf_file, verbose=True)

        assert result == ""
        captured = capsys.readouterr()
        assert "No bookmarks found in PDF" in captured.out

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_output_file_created_default_path(self, mock_fitz, tmp_path):
        """Test that output file is created at default path when not specified."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        mock_doc = MagicMock()
        mock_doc.get_toc.return_value = [
            [1, "Chapter 1", 1],
            [2, "Section 1.1", 2],
        ]
        mock_fitz.open.return_value = mock_doc

        # Change to tmp_path for test
        with patch("vulcanlab.conversions.pdf_bookmarks2toc.Path.cwd", return_value=tmp_path):
            result = extract_bookmarks_to_toc(pdf_file)

        # Verify default output file was created
        output_file = tmp_path / "output" / "test.toc_titles.md"
        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == result
        assert "# Chapter 1" in result

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_output_file_created_custom_path(self, mock_fitz, tmp_path):
        """Test that output file is created at custom path when specified."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")
        output_file = tmp_path / "custom" / "custom_toc.md"

        mock_doc = MagicMock()
        mock_doc.get_toc.return_value = [
            [1, "Chapter 1", 1],
        ]
        mock_fitz.open.return_value = mock_doc

        result = extract_bookmarks_to_toc(pdf_file, output_path=output_file)

        # Verify custom output file was created
        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == result
        assert result == "# Chapter 1"

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_verbose_mode(self, mock_fitz, tmp_path, capsys):
        """Test verbose output."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        mock_doc = MagicMock()
        mock_doc.get_toc.return_value = [
            [1, "Chapter 1", 1],
            [2, "Section 1.1", 2],
        ]
        mock_fitz.open.return_value = mock_doc

        extract_bookmarks_to_toc(pdf_file, verbose=True)

        captured = capsys.readouterr()
        assert "Extracting bookmarks from:" in captured.out
        assert "Found 2 bookmarks" in captured.out
        assert "TOC written to:" in captured.out

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_path_object_input(self, mock_fitz, tmp_path):
        """Test that Path objects are accepted as input."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake content")

        mock_doc = MagicMock()
        mock_doc.get_toc.return_value = [[1, "Test", 1]]
        mock_fitz.open.return_value = mock_doc

        result = extract_bookmarks_to_toc(pdf_file)

        assert result == "# Test"
        # Verify Path object was converted to string for fitz.open
        mock_fitz.open.assert_called_once_with(str(pdf_file))

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_string_path_input(self, mock_fitz, tmp_path):
        """Test that string paths are accepted as input."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake content")

        mock_doc = MagicMock()
        mock_doc.get_toc.return_value = [[1, "Test", 1]]
        mock_fitz.open.return_value = mock_doc

        result = extract_bookmarks_to_toc(str(pdf_file))

        assert result == "# Test"
        mock_fitz.open.assert_called_once_with(str(pdf_file))

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_malformed_bookmarks_handled(self, mock_fitz, tmp_path):
        """Test handling of bookmarks with unusual but valid structure."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        mock_doc = MagicMock()
        # Include edge cases: empty titles, special characters, very long titles
        mock_doc.get_toc.return_value = [
            [1, "", 1],  # Empty title
            [1, "Normal Title", 2],
            [1, "Title with\nnewlines", 3],  # Newlines in title
            [1, "Title with special chars: !@#$%^&*()", 4],
            [1, "A" * 200, 5],  # Very long title
        ]
        mock_fitz.open.return_value = mock_doc

        result = extract_bookmarks_to_toc(pdf_file)

        # Verify all bookmarks are processed
        lines = result.split("\n\n")
        assert len(lines) == 5
        assert lines[0] == "# "  # Empty title still creates heading
        assert lines[1] == "# Normal Title"
        assert "# Title with\nnewlines" in result or "# Title with newlines" in result
        assert "special chars" in result

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_single_bookmark(self, mock_fitz, tmp_path):
        """Test TOC generation with single bookmark."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        mock_doc = MagicMock()
        mock_doc.get_toc.return_value = [
            [1, "Only Chapter", 1],
        ]
        mock_fitz.open.return_value = mock_doc

        result = extract_bookmarks_to_toc(pdf_file)

        assert result == "# Only Chapter"

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_bookmarks_with_page_numbers_ignored(self, mock_fitz, tmp_path):
        """Test that page numbers in TOC data are ignored (not included in output)."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        mock_doc = MagicMock()
        # Page numbers are third element in tuple, should not appear in output
        # Using page numbers that won't appear in titles
        mock_doc.get_toc.return_value = [
            [1, "Chapter One", 1],
            [2, "Section A", 5],
            [2, "Section B", 10],
        ]
        mock_fitz.open.return_value = mock_doc

        result = extract_bookmarks_to_toc(pdf_file)

        # Verify page numbers are not in output
        # Check that standalone page numbers don't appear (they might be in titles)
        lines = result.split("\n\n")
        assert "# Chapter One" in result
        assert "## Section A" in result
        assert "## Section B" in result
        # Verify page numbers (5, 10) don't appear as standalone numbers
        # They should only appear if they're part of a title
        assert " 5" not in result and "\n5" not in result
        assert " 10" not in result and "\n10" not in result

    @patch("vulcanlab.conversions.pdf_bookmarks2toc.fitz")
    def test_output_directory_creation(self, mock_fitz, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")
        output_dir = tmp_path / "new" / "nested" / "dir"
        output_file = output_dir / "toc.md"

        # Verify directory doesn't exist
        assert not output_dir.exists()

        mock_doc = MagicMock()
        mock_doc.get_toc.return_value = [[1, "Test", 1]]
        mock_fitz.open.return_value = mock_doc

        extract_bookmarks_to_toc(pdf_file, output_path=output_file)

        # Verify directory was created and file exists
        assert output_dir.exists()
        assert output_file.exists()

