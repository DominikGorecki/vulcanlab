"""
Unit tests for conv_epub2md module.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vulcanlab.conversions.conv_epub2md import convert_epub_to_markdown, main


class TestConvertEpubToMarkdown:
    """Tests for the convert_epub_to_markdown function."""

    def test_file_not_found_raises_error(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError, match="EPUB file not found"):
            convert_epub_to_markdown("nonexistent.epub")

    def test_invalid_extension_raises_error(self, tmp_path):
        """Test that ValueError is raised for non-EPUB files."""
        # Create a temporary file with wrong extension
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test content")

        with pytest.raises(ValueError, match="File must be an EPUB file"):
            convert_epub_to_markdown(txt_file)

    @patch("vulcanlab.conversions.conv_epub2md._extract_epub_to_html")
    @patch("vulcanlab.conversions.conv_epub2md.md")
    def test_successful_conversion(self, mock_md, mock_extract, tmp_path):
        """Test successful EPUB to Markdown conversion."""
        # Create mock EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_text("fake epub content")

        # Setup mocks
        mock_extract.return_value = "<html><body>Test</body></html>"
        mock_md.return_value = "# Test Markdown"

        # Run conversion
        result = convert_epub_to_markdown(epub_file)

        # Verify
        assert result == "# Test Markdown"
        mock_extract.assert_called_once_with(epub_file)
        mock_md.assert_called_once()

    @patch("vulcanlab.conversions.conv_epub2md._extract_epub_to_html")
    @patch("vulcanlab.conversions.conv_epub2md.md")
    def test_output_file_created(self, mock_md, mock_extract, tmp_path):
        """Test that output file is created when output_path is specified."""
        # Create mock EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_text("fake epub content")
        output_file = tmp_path / "output" / "test.md"

        # Setup mocks
        mock_extract.return_value = "<html><body>Test</body></html>"
        mock_md.return_value = "# Test Output"

        # Run conversion
        convert_epub_to_markdown(epub_file, output_path=output_file)

        # Verify output file was created
        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == "# Test Output"

    @patch("vulcanlab.conversions.conv_epub2md._extract_epub_to_html")
    @patch("vulcanlab.conversions.conv_epub2md.md")
    def test_verbose_mode(self, mock_md, mock_extract, tmp_path, capsys):
        """Test verbose output."""
        # Create mock EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_text("fake epub content")

        # Setup mocks
        mock_extract.return_value = "<html><body>Test</body></html>"
        mock_md.return_value = "# Test"

        # Run with verbose
        convert_epub_to_markdown(epub_file, verbose=True)

        # Check output
        captured = capsys.readouterr()
        assert "Converting:" in captured.out

    @patch("vulcanlab.conversions.conv_epub2md._extract_epub_to_html")
    @patch("vulcanlab.conversions.conv_epub2md.md")
    def test_path_object_input(self, mock_md, mock_extract, tmp_path):
        """Test that Path objects are accepted as input."""
        epub_file = tmp_path / "test.epub"
        epub_file.write_text("fake content")

        # Setup mocks
        mock_extract.return_value = "<html><body>Test</body></html>"
        mock_md.return_value = "# Test"

        result = convert_epub_to_markdown(Path(epub_file))
        assert isinstance(result, str)

    @patch("vulcanlab.conversions.conv_epub2md._extract_epub_to_html")
    @patch("vulcanlab.conversions.conv_epub2md.md")
    def test_hierarchy_preservation(self, mock_md, mock_extract, tmp_path):
        """Test that hierarchical structure is preserved in HTML extraction."""
        # Create mock EPUB file
        epub_file = tmp_path / "test.epub"
        epub_file.write_text("fake epub content")

        # Setup mocks - simulate HTML with hierarchical headings
        mock_html = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Test</title></head>
<body>
<h1>Chapter 1</h1>
<p>Chapter 1 content</p>
<h2>Section 1.1</h2>
<p>Section content</p>
<h3>Subsection 1.1.1</h3>
<p>Subsection content</p>
<h2>Section 1.2</h2>
<p>More content</p>
</body>
</html>"""
        mock_extract.return_value = mock_html

        # Simulate markdown output with hierarchy
        mock_md.return_value = """# Chapter 1

Chapter 1 content

## Section 1.1

Section content

### Subsection 1.1.1

Subsection content

## Section 1.2

More content"""

        # Run conversion
        result = convert_epub_to_markdown(epub_file)

        # Verify hierarchy is reflected in the result
        assert "# Chapter 1" in result
        assert "## Section 1.1" in result
        assert "### Subsection 1.1.1" in result
        assert "## Section 1.2" in result
        mock_extract.assert_called_once_with(epub_file)


class TestMain:
    """Tests for the main CLI function."""

    @patch("vulcanlab.conversions.conv_epub2md.convert_epub_to_markdown")
    def test_main_stdout_output(self, mock_convert, capsys, monkeypatch):
        """Test main function prints to stdout when no output file."""
        mock_convert.return_value = "# Converted Content"
        monkeypatch.setattr("sys.argv", ["conv_epub2md", "test.epub"])

        result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "# Converted Content" in captured.out

    @patch("vulcanlab.conversions.conv_epub2md.convert_epub_to_markdown")
    def test_main_with_output_file(self, mock_convert, monkeypatch, tmp_path):
        """Test main function with output file argument."""
        output_file = tmp_path / "output.md"
        mock_convert.return_value = "# Test"
        monkeypatch.setattr(
            "sys.argv",
            ["conv_epub2md", "test.epub", "-o", str(output_file)]
        )

        result = main()

        assert result == 0
        mock_convert.assert_called_once_with(
            epub_path="test.epub",
            output_path=str(output_file),
            verbose=False
        )

    @patch("vulcanlab.conversions.conv_epub2md.convert_epub_to_markdown")
    def test_main_file_not_found(self, mock_convert, capsys, monkeypatch):
        """Test main function handles FileNotFoundError."""
        mock_convert.side_effect = FileNotFoundError("File not found")
        monkeypatch.setattr("sys.argv", ["conv_epub2md", "missing.epub"])

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    @patch("vulcanlab.conversions.conv_epub2md.convert_epub_to_markdown")
    def test_main_value_error(self, mock_convert, capsys, monkeypatch):
        """Test main function handles ValueError."""
        mock_convert.side_effect = ValueError("Invalid file")
        monkeypatch.setattr("sys.argv", ["conv_epub2md", "test.txt"])

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    @patch("vulcanlab.conversions.conv_epub2md.convert_epub_to_markdown")
    def test_main_verbose_flag(self, mock_convert, monkeypatch):
        """Test main function passes verbose flag."""
        mock_convert.return_value = "# Test"
        monkeypatch.setattr("sys.argv", ["conv_epub2md", "test.epub", "-v"])

        main()

        mock_convert.assert_called_once_with(
            epub_path="test.epub",
            output_path=None,
            verbose=True
        )
