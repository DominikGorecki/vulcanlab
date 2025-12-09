"""
Unit tests for apply_title_edits module.

Tests cover:
- Title edit application logic
- Edit processing (various edit types)
- Edit validation
- Error handling
"""

import tempfile
from pathlib import Path

import pytest

from vulcanlab.sanitization.apply_title_edits import (
    apply_title_edits,
    _parse_title_edits,
    _remove_heading_markers,
)


class TestParseTitleEdits:
    """Tests for _parse_title_edits function."""

    def test_parse_simple_edits(self):
        """Test parsing simple line number and title pairs."""
        title_edits = """10: # New Chapter Title
15: ## Updated Section
20: ### Subsection"""
        
        edits_map = _parse_title_edits(title_edits)
        
        assert edits_map == {
            10: "# New Chapter Title",
            15: "## Updated Section",
            20: "### Subsection"
        }

    def test_parse_with_whitespace(self):
        """Test parsing handles whitespace correctly."""
        # Note: The parser allows spaces after colon but not before
        # Trailing spaces are stripped by line.strip() in the parser
        title_edits = "  10:  # Title with spaces  \n  15:  ## Another Title  "
        
        edits_map = _parse_title_edits(title_edits)
        
        assert edits_map == {
            10: "# Title with spaces",
            15: "## Another Title"
        }

    def test_parse_special_formats(self):
        """Test parsing special edit formats."""
        title_edits = """5: ***MISSING***
10: -
15: --"""
        
        edits_map = _parse_title_edits(title_edits)
        
        assert edits_map == {
            5: "***MISSING***",
            10: "-",
            15: "--"
        }

    def test_parse_empty_string(self):
        """Test parsing empty string returns empty dict."""
        edits_map = _parse_title_edits("")
        assert edits_map == {}

    def test_parse_with_blank_lines(self):
        """Test parsing ignores blank lines."""
        title_edits = """10: # Title

15: ## Section

20: ### Subsection"""
        
        edits_map = _parse_title_edits(title_edits)
        
        assert edits_map == {
            10: "# Title",
            15: "## Section",
            20: "### Subsection"
        }

    def test_parse_invalid_lines_ignored(self):
        """Test parsing ignores lines that don't match the format."""
        title_edits = """10: # Valid Line
invalid line format
15: ## Another Valid Line
also invalid
20: ### Final Valid"""
        
        edits_map = _parse_title_edits(title_edits)
        
        assert edits_map == {
            10: "# Valid Line",
            15: "## Another Valid Line",
            20: "### Final Valid"
        }

    def test_parse_duplicate_line_numbers(self):
        """Test parsing handles duplicate line numbers (last one wins)."""
        title_edits = """10: # First Title
10: # Second Title
10: # Third Title"""
        
        edits_map = _parse_title_edits(title_edits)
        
        assert edits_map == {
            10: "# Third Title"
        }


class TestRemoveHeadingMarkers:
    """Tests for _remove_heading_markers function."""

    def test_remove_h1_marker(self):
        """Test removing H1 marker."""
        line = "# Title\n"
        result = _remove_heading_markers(line)
        assert result == "Title\n"

    def test_remove_h2_marker(self):
        """Test removing H2 marker."""
        line = "## Section Title\n"
        result = _remove_heading_markers(line)
        assert result == "Section Title\n"

    def test_remove_h3_marker(self):
        """Test removing H3 marker."""
        line = "### Subsection\n"
        result = _remove_heading_markers(line)
        assert result == "Subsection\n"

    def test_remove_h6_marker(self):
        """Test removing H6 marker (deepest level)."""
        line = "###### Deep Title\n"
        result = _remove_heading_markers(line)
        assert result == "Deep Title\n"

    def test_preserve_line_ending(self):
        """Test that line ending is preserved."""
        line_no_newline = "# Title"
        result = _remove_heading_markers(line_no_newline)
        assert result == "Title"
        assert not result.endswith("\n")

    def test_non_heading_line_unchanged(self):
        """Test that non-heading lines are returned unchanged."""
        line = "Regular text line\n"
        result = _remove_heading_markers(line)
        assert result == line

    def test_line_without_space_after_hash(self):
        """Test that lines without space after # are unchanged."""
        line = "#No space here\n"
        result = _remove_heading_markers(line)
        assert result == line


class TestApplyTitleEdits:
    """Tests for apply_title_edits function."""

    def test_apply_simple_replacement(self, tmp_path):
        """Test applying simple title replacement."""
        markdown_file = tmp_path / "test.md"
        markdown_content = """# Original Title
Some content here
## Section Title
More content"""
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        title_edits = """1: # New Title
3: ## Updated Section"""
        
        apply_title_edits(markdown_file, title_edits)
        
        result = markdown_file.read_text(encoding='utf-8')
        lines = result.splitlines()
        assert lines[0] == "# New Title"
        assert lines[1] == "Some content here"
        assert lines[2] == "## Updated Section"
        assert lines[3] == "More content"

    def test_apply_missing_edit(self, tmp_path):
        """Test applying ***MISSING*** edit (no change)."""
        markdown_file = tmp_path / "test.md"
        markdown_content = """# Original Title
Some content
## Section Title"""
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        title_edits = """1: ***MISSING***
3: ## Updated Section"""
        
        apply_title_edits(markdown_file, title_edits)
        
        result = markdown_file.read_text(encoding='utf-8')
        lines = result.splitlines()
        assert lines[0] == "# Original Title"  # Unchanged
        assert lines[2] == "## Updated Section"  # Changed

    def test_apply_remove_heading_markers(self, tmp_path):
        """Test applying '-' edit to remove heading markers."""
        markdown_file = tmp_path / "test.md"
        markdown_content = """# Chapter Title
Some content
## Section Title
More content"""
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        title_edits = """1: -
3: -"""
        
        apply_title_edits(markdown_file, title_edits)
        
        result = markdown_file.read_text(encoding='utf-8')
        lines = result.splitlines()
        assert lines[0] == "Chapter Title"  # Markers removed
        assert lines[2] == "Section Title"  # Markers removed

    def test_apply_blank_line_edit(self, tmp_path):
        """Test applying '--' edit to replace with blank line."""
        markdown_file = tmp_path / "test.md"
        markdown_content = """# Title
Some content
## Section to Remove
More content"""
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        title_edits = """3: --"""
        
        apply_title_edits(markdown_file, title_edits)
        
        result = markdown_file.read_text(encoding='utf-8')
        lines = result.splitlines()
        assert lines[0] == "# Title"
        assert lines[1] == "Some content"
        assert lines[2] == ""  # Blank line
        assert lines[3] == "More content"

    def test_apply_multiple_edit_types(self, tmp_path):
        """Test applying multiple different edit types."""
        markdown_file = tmp_path / "test.md"
        markdown_content = """# Title 1
Content 1
## Title 2
Content 2
### Title 3
Content 3"""
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        title_edits = """1: # New Title 1
3: ***MISSING***
5: -
6: --"""
        
        apply_title_edits(markdown_file, title_edits)
        
        result = markdown_file.read_text(encoding='utf-8')
        lines = result.splitlines()
        assert lines[0] == "# New Title 1"  # Replaced
        assert lines[2] == "## Title 2"  # Unchanged (MISSING)
        assert lines[4] == "Title 3"  # Markers removed
        assert lines[5] == ""  # Blank line (line 6 became blank)

    def test_preserve_line_endings(self, tmp_path):
        """Test that line endings are preserved correctly."""
        markdown_file = tmp_path / "test.md"
        # File with mixed line endings
        markdown_content = "# Title\n## Section\n### Subsection"
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        title_edits = """1: # New Title
2: ## New Section"""
        
        apply_title_edits(markdown_file, title_edits)
        
        result = markdown_file.read_text(encoding='utf-8')
        # Should preserve original structure
        assert result.startswith("# New Title\n")
        assert "## New Section\n" in result

    def test_apply_no_edits(self, tmp_path):
        """Test applying empty edits leaves file unchanged."""
        markdown_file = tmp_path / "test.md"
        markdown_content = """# Original Title
Some content"""
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        original_content = markdown_file.read_text(encoding='utf-8')
        
        apply_title_edits(markdown_file, "")
        
        result = markdown_file.read_text(encoding='utf-8')
        assert result == original_content

    def test_apply_edit_to_nonexistent_line(self, tmp_path):
        """Test applying edit to line number beyond file length."""
        markdown_file = tmp_path / "test.md"
        markdown_content = """# Title
Content"""
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        title_edits = """100: # New Title"""
        
        # Should not raise error, just ignore the edit
        apply_title_edits(markdown_file, title_edits)
        
        result = markdown_file.read_text(encoding='utf-8')
        lines = result.splitlines()
        assert len(lines) == 2
        assert lines[0] == "# Title"

    def test_file_not_found_error(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        nonexistent_file = tmp_path / "nonexistent.md"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            apply_title_edits(nonexistent_file, "1: # Title")
        
        assert "Markdown file not found" in str(exc_info.value)
        assert str(nonexistent_file) in str(exc_info.value)

    def test_invalid_file_extension_error(self, tmp_path):
        """Test that non-markdown file raises ValueError."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("Some content", encoding='utf-8')
        
        with pytest.raises(ValueError) as exc_info:
            apply_title_edits(text_file, "1: # Title")
        
        assert "File must be a markdown file" in str(exc_info.value)
        assert str(text_file) in str(exc_info.value)

    def test_markdown_extension_case_insensitive(self, tmp_path):
        """Test that .MARKDOWN extension is accepted."""
        markdown_file = tmp_path / "test.MARKDOWN"
        markdown_content = "# Title\nContent"
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        title_edits = """1: # New Title"""
        
        # Should not raise error
        apply_title_edits(markdown_file, title_edits)
        
        result = markdown_file.read_text(encoding='utf-8')
        assert "# New Title" in result

    def test_complex_markdown_structure(self, tmp_path):
        """Test applying edits to complex markdown structure."""
        markdown_file = tmp_path / "test.md"
        markdown_content = """# Main Title

Introduction paragraph.

## Section One

Content for section one.

### Subsection 1.1

More content.

## Section Two

Final content."""
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        title_edits = """1: # Updated Main Title
5: ## Updated Section One
9: -
13: ## Completely New Section"""
        
        apply_title_edits(markdown_file, title_edits)
        
        result = markdown_file.read_text(encoding='utf-8')
        lines = result.splitlines()
        assert lines[0] == "# Updated Main Title"
        assert lines[4] == "## Updated Section One"
        assert lines[8] == "Subsection 1.1"  # Markers removed
        assert lines[12] == "## Completely New Section"

    def test_edit_with_colon_in_title(self, tmp_path):
        """Test editing with colon in title text."""
        markdown_file = tmp_path / "test.md"
        markdown_content = """# Title
Content"""
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        title_edits = """1: # Title: With Colon"""
        
        apply_title_edits(markdown_file, title_edits)
        
        result = markdown_file.read_text(encoding='utf-8')
        assert "# Title: With Colon" in result

    def test_multiple_edits_same_line(self, tmp_path):
        """Test that last edit for same line number wins."""
        markdown_file = tmp_path / "test.md"
        markdown_content = """# Title
Content"""
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        title_edits = """1: # First Edit
1: # Second Edit
1: # Third Edit"""
        
        apply_title_edits(markdown_file, title_edits)
        
        result = markdown_file.read_text(encoding='utf-8')
        assert "# Third Edit" in result
        assert "# First Edit" not in result
        assert "# Second Edit" not in result

    def test_unicode_content(self, tmp_path):
        """Test applying edits to file with unicode content."""
        markdown_file = tmp_path / "test.md"
        markdown_content = """# Título Original
Contenido con caracteres especiales: áéíóú
## Sección"""
        markdown_file.write_text(markdown_content, encoding='utf-8')
        
        title_edits = """1: # Nuevo Título
3: ## Nueva Sección"""
        
        apply_title_edits(markdown_file, title_edits)
        
        result = markdown_file.read_text(encoding='utf-8')
        assert "# Nuevo Título" in result
        assert "## Nueva Sección" in result
        assert "áéíóú" in result  # Unicode preserved
