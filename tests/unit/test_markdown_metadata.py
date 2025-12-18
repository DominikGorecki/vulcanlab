"""
Unit tests for markdown metadata extraction.

Tests extract_metadata(), strip_frontmatter() and related functions.

Usage:
    pytest tests/unit/test_markdown_metadata.py -v
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from vulcanlab.markdown_import.metadata import (
    Metadata,
    MarkdownFile,
    extract_metadata,
    strip_frontmatter,
)


class TestExtractMetadata:
    """Tests for extract_metadata() function."""

    def test_extract_valid_metadata(self):
        """Test extracting valid YAML frontmatter."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Test Book"
author: "John Doe"
year: 2023
---

# Chapter 1

Content here."""
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is not None
            assert metadata.title == "Test Book"
            assert metadata.author == "John Doe"
            assert metadata.year == 2023

    def test_extract_metadata_without_quotes(self):
        """Test extracting YAML without quotes around strings."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: Test Book
author: John Doe
year: 2023
---

Content"""
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is not None
            assert metadata.title == "Test Book"
            assert metadata.author == "John Doe"

    def test_extract_metadata_only_title(self):
        """Test extracting metadata with only title."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Minimal Metadata"
---

Content here."""
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is not None
            assert metadata.title == "Minimal Metadata"
            assert metadata.author is None
            assert metadata.year is None

    def test_extract_metadata_missing_frontmatter(self):
        """Test file without frontmatter returns None."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = "# Just Content\n\nNo metadata here."
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is None

    def test_extract_metadata_invalid_yaml(self):
        """Test invalid YAML returns None."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Test
author: [invalid yaml structure
---

Content"""
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is None

    def test_extract_metadata_missing_title(self):
        """Test frontmatter without title returns None."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
author: "John Doe"
year: 2023
---

Content"""
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is None

    def test_extract_metadata_empty_frontmatter(self):
        """Test empty frontmatter returns None."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
---

Content"""
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is None

    def test_extract_metadata_file_not_found(self):
        """Test nonexistent file returns None."""
        metadata = extract_metadata("/nonexistent/file.md")
        assert metadata is None

    def test_extract_metadata_invalid_year_type(self):
        """Test non-integer year is ignored."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Test Book"
year: "2023-01-01"
---

Content"""
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is not None
            assert metadata.title == "Test Book"
            assert metadata.year is None

    def test_extract_metadata_year_out_of_range(self):
        """Test year outside valid range is ignored."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Test Book"
year: 999
---

Content"""
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is not None
            assert metadata.year is None

    def test_extract_metadata_invalid_author_type(self):
        """Test non-string author is ignored."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Test Book"
author: 12345
---

Content"""
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is not None
            assert metadata.title == "Test Book"
            assert metadata.author is None

    def test_extract_metadata_multiple_authors(self):
        """Test comma-separated authors stored as string."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Test Book"
author: "John Doe, Jane Smith"
---

Content"""
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is not None
            assert metadata.author == "John Doe, Jane Smith"

    def test_extract_metadata_with_special_chars_in_title(self):
        """Test title with special characters."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Psychology: Theory & Practice!"
author: "Dr. Smith"
year: 2023
---

Content"""
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is not None
            assert metadata.title == "Psychology: Theory & Practice!"

    def test_extract_metadata_incomplete_frontmatter(self):
        """Test file with only opening --- returns None."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Test Book"

Content without closing delimiter"""
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is None

    def test_extract_metadata_non_dict_yaml(self):
        """Test YAML that parses to non-dict returns None."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
- item1
- item2
---

Content"""
            test_file.write_text(content, encoding='utf-8')

            metadata = extract_metadata(str(test_file))

            assert metadata is None


class TestStripFrontmatter:
    """Tests for strip_frontmatter() function."""

    def test_strip_valid_frontmatter(self):
        """Test stripping valid frontmatter."""
        content = """---
title: "Test"
author: "Author"
---

# Chapter 1

Content here."""

        result = strip_frontmatter(content)

        assert "---" not in result
        assert "title:" not in result
        assert "# Chapter 1" in result
        assert "Content here." in result

    def test_strip_frontmatter_no_metadata(self):
        """Test content without frontmatter unchanged."""
        content = "# Chapter 1\n\nContent here."

        result = strip_frontmatter(content)

        assert result == content

    def test_strip_frontmatter_removes_whitespace(self):
        """Test that leading/trailing whitespace is removed."""
        content = """---
title: "Test"
---



# Content

   """

        result = strip_frontmatter(content)

        assert result == "# Content"

    def test_strip_frontmatter_empty_content(self):
        """Test stripping frontmatter from file with only metadata."""
        content = """---
title: "Test"
---"""

        result = strip_frontmatter(content)

        assert result == ""

    def test_strip_frontmatter_incomplete(self):
        """Test content with incomplete frontmatter unchanged."""
        content = """---
title: "Test"

Content without closing"""

        result = strip_frontmatter(content)

        # Should return original content since no closing ---
        assert "---" in result
        assert "title:" in result


class TestMetadataDataclass:
    """Tests for Metadata dataclass."""

    def test_metadata_with_all_fields(self):
        """Test creating Metadata with all fields."""
        metadata = Metadata(title="Test", author="Author", year=2023)

        assert metadata.title == "Test"
        assert metadata.author == "Author"
        assert metadata.year == 2023

    def test_metadata_with_only_title(self):
        """Test creating Metadata with only required field."""
        metadata = Metadata(title="Test")

        assert metadata.title == "Test"
        assert metadata.author is None
        assert metadata.year is None


class TestMarkdownFileDataclass:
    """Tests for MarkdownFile dataclass."""

    def test_markdown_file_with_metadata(self):
        """Test creating MarkdownFile with metadata."""
        metadata = Metadata(title="Test", author="Author")
        md_file = MarkdownFile(
            filename="test.md",
            file_path="/path/to/test.md",
            has_metadata=True,
            metadata=metadata
        )

        assert md_file.filename == "test.md"
        assert md_file.file_path == "/path/to/test.md"
        assert md_file.has_metadata is True
        assert md_file.metadata == metadata

    def test_markdown_file_without_metadata(self):
        """Test creating MarkdownFile without metadata."""
        md_file = MarkdownFile(
            filename="test.md",
            file_path="/path/to/test.md",
            has_metadata=False
        )

        assert md_file.has_metadata is False
        assert md_file.metadata is None
