"""
Unit tests for conv_pdf2md module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vulcanlab.conversions.conv_pdf2md import convert_pdf_to_markdown, main


class TestConvertPdfToMarkdown:
    """Tests for the convert_pdf_to_markdown function."""

    def test_file_not_found_raises_error(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            convert_pdf_to_markdown("nonexistent.pdf")

    def test_invalid_extension_raises_error(self, tmp_path):
        """Test that ValueError is raised for non-PDF files."""
        # Create a temporary file with wrong extension
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test content")

        with pytest.raises(ValueError, match="File must be a PDF file"):
            convert_pdf_to_markdown(txt_file)

    @patch("vulcanlab.conversions.conv_pdf2md.DocumentConverter")
    def test_successful_conversion(self, mock_converter_class, tmp_path):
        """Test successful PDF to Markdown conversion in compare mode (default)."""
        # Create mock PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        # Setup mock
        mock_result = MagicMock()
        mock_result.document.export_to_markdown.return_value = "# Test Markdown"
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_converter_class.return_value = mock_converter

        # Run conversion
        result = convert_pdf_to_markdown(pdf_file)

        # Verify - Compare mode returns (style_md, hier_md) tuple
        assert isinstance(result, tuple)
        assert len(result) == 2
        style_md, hier_md = result
        assert isinstance(style_md, str)
        assert isinstance(hier_md, str)

    @patch("vulcanlab.conversions.conv_pdf2md.DocumentConverter")
    def test_output_file_created(self, mock_converter_class, tmp_path):
        """Test that output files are created when output_path is specified."""
        # Create mock PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")
        output_file = tmp_path / "output" / "test.md"

        # Setup mock
        mock_result = MagicMock()
        mock_result.document.export_to_markdown.return_value = "# Test Output"
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_converter_class.return_value = mock_converter

        # Run conversion
        convert_pdf_to_markdown(pdf_file, output_path=output_file)

        # Verify output files were created (compare mode creates .style.md and .hier.md)
        style_path = output_file.parent / "test.style.md"
        hier_path = output_file.parent / "test.hier.md"

        assert style_path.exists(), "Style output file should exist"
        assert hier_path.exists(), "Hierarchical output file should exist"
        assert style_path.read_text(encoding="utf-8") == "# Test Output"
        assert hier_path.read_text(encoding="utf-8") == "# Test Output"

        # Also verify PDF was copied
        pdf_copy = output_file.parent / "test.pdf"
        assert pdf_copy.exists(), "PDF should be copied to output directory"

    @patch("vulcanlab.conversions.conv_pdf2md.DocumentConverter")
    def test_verbose_mode(self, mock_converter_class, tmp_path, capsys):
        """Test verbose output."""
        # Create mock PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        # Setup mock
        mock_result = MagicMock()
        mock_result.document.export_to_markdown.return_value = "# Test"
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_converter_class.return_value = mock_converter

        # Run with verbose
        convert_pdf_to_markdown(pdf_file, verbose=True)

        # Check output
        captured = capsys.readouterr()
        assert "Converting:" in captured.out

    @patch("vulcanlab.conversions.conv_pdf2md.DocumentConverter")
    def test_path_object_input(self, mock_converter_class, tmp_path):
        """Test that Path objects are accepted as input."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake content")

        # Setup mock
        mock_result = MagicMock()
        mock_result.document.export_to_markdown.return_value = "# Test"
        mock_converter_class.return_value.convert.return_value = mock_result

        result = convert_pdf_to_markdown(Path(pdf_file))

        # Compare mode returns tuple
        assert isinstance(result, tuple)
        assert len(result) == 2
        style_md, hier_md = result
        assert isinstance(style_md, str)
        assert isinstance(hier_md, str)


class TestMain:
    """Tests for the main CLI function."""

    @patch("vulcanlab.conversions.conv_pdf2md.convert_pdf_to_markdown")
    def test_main_stdout_output(self, mock_convert, capsys, monkeypatch):
        """Test main function prints to stdout when no output file."""
        # Mock returns tuple in compare mode
        mock_convert.return_value = ("# Style Content", "# Hier Content")
        monkeypatch.setattr("sys.argv", ["conv_pdf2md", "test.pdf"])

        result = main()

        assert result == 0

        # Verify both outputs are printed
        captured = capsys.readouterr()
        assert "# Style Content" in captured.out
        assert "# Hier Content" in captured.out

    @patch("vulcanlab.conversions.conv_pdf2md.convert_pdf_to_markdown")
    def test_main_with_output_file(self, mock_convert, monkeypatch, tmp_path):
        """Test main function with output file argument."""
        output_file = tmp_path / "output.md"
        mock_convert.return_value = ("# Test", "# Test")
        monkeypatch.setattr(
            "sys.argv",
            ["conv_pdf2md", "test.pdf", "-o", str(output_file)]
        )

        result = main()

        assert result == 0
        # Verify convert was called with ALL expected parameters
        mock_convert.assert_called_once_with(
            pdf_path="test.pdf",
            output_path=str(output_file),
            verbose=False,
            ocr=False,
            hierarchical=True,  # NEW: default is True
            compare=True,       # NEW: default is True
            use_gpu=True        # NEW: default is True
        )

    @patch("vulcanlab.conversions.conv_pdf2md.convert_pdf_to_markdown")
    def test_main_file_not_found(self, mock_convert, capsys, monkeypatch):
        """Test main function handles FileNotFoundError."""
        mock_convert.side_effect = FileNotFoundError("File not found")
        monkeypatch.setattr("sys.argv", ["conv_pdf2md", "missing.pdf"])

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    @patch("vulcanlab.conversions.conv_pdf2md.convert_pdf_to_markdown")
    def test_main_value_error(self, mock_convert, capsys, monkeypatch):
        """Test main function handles ValueError."""
        mock_convert.side_effect = ValueError("Invalid file")
        monkeypatch.setattr("sys.argv", ["conv_pdf2md", "test.txt"])

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    @patch("vulcanlab.conversions.conv_pdf2md.convert_pdf_to_markdown")
    def test_main_verbose_flag(self, mock_convert, monkeypatch):
        """Test main function passes verbose flag."""
        mock_convert.return_value = ("# Test", "# Test")
        monkeypatch.setattr("sys.argv", ["conv_pdf2md", "test.pdf", "-v"])

        main()

        # Verify ALL parameters including new defaults
        mock_convert.assert_called_once_with(
            pdf_path="test.pdf",
            output_path=None,
            verbose=True,
            ocr=False,
            hierarchical=True,  # NEW
            compare=True,       # NEW
            use_gpu=True        # NEW
        )
