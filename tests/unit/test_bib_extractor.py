"""
Unit tests for bibliographic metadata extraction module.

Tests metadata extraction from markdown, bibliographic info parsing,
edge cases, and extraction character limits.

Usage:
    pytest tests/unit/test_bib_extractor.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json

from vulcanlab.chunking.bib_extractor import (
    BibliographicInfo,
    ExtractedMetadata,
    TOCEntry,
    TableOfContents,
    extract_metadata,
    EXTRACT_CHARS,
)


class TestBibliographicInfo:
    """Tests for BibliographicInfo dataclass."""

    def test_bibliographic_info_creation_with_all_fields(self):
        """Test creating BibliographicInfo with all fields."""
        bib = BibliographicInfo(
            title="Test Book",
            authors=["Author One", "Author Two"],
            publication_date="2024",
            publisher="Test Publisher",
            isbn="978-0-123456-78-9",
            edition="2nd Edition"
        )
        assert bib.title == "Test Book"
        assert bib.authors == ["Author One", "Author Two"]
        assert bib.publication_date == "2024"
        assert bib.publisher == "Test Publisher"
        assert bib.isbn == "978-0-123456-78-9"
        assert bib.edition == "2nd Edition"

    def test_bibliographic_info_defaults(self):
        """Test BibliographicInfo with default values."""
        bib = BibliographicInfo()
        assert bib.title is None
        assert bib.authors == []
        assert bib.publication_date is None
        assert bib.publisher is None
        assert bib.isbn is None
        assert bib.edition is None

    def test_bibliographic_info_partial_fields(self):
        """Test BibliographicInfo with partial fields."""
        bib = BibliographicInfo(
            title="Test Book",
            authors=["Author One"]
        )
        assert bib.title == "Test Book"
        assert bib.authors == ["Author One"]
        assert bib.publication_date is None
        assert bib.publisher is None

    def test_bibliographic_info_empty_authors(self):
        """Test BibliographicInfo with empty authors list."""
        bib = BibliographicInfo(authors=[])
        assert bib.authors == []


class TestTOCEntry:
    """Tests for TOCEntry dataclass."""

    def test_toc_entry_creation(self):
        """Test creating TOCEntry."""
        entry = TOCEntry(level=1, title="Chapter 1")
        assert entry.level == 1
        assert entry.title == "Chapter 1"

    def test_toc_entry_different_levels(self):
        """Test TOCEntry with different heading levels."""
        h1 = TOCEntry(level=1, title="Main Chapter")
        h2 = TOCEntry(level=2, title="Section")
        h3 = TOCEntry(level=3, title="Subsection")
        
        assert h1.level == 1
        assert h2.level == 2
        assert h3.level == 3


class TestTableOfContents:
    """Tests for TableOfContents dataclass."""

    def test_table_of_contents_creation(self):
        """Test creating TableOfContents."""
        entries = [
            TOCEntry(level=1, title="Chapter 1"),
            TOCEntry(level=2, title="Section 1.1"),
        ]
        toc = TableOfContents(entries=entries)
        assert len(toc.entries) == 2
        assert toc.entries[0].title == "Chapter 1"
        assert toc.entries[1].title == "Section 1.1"

    def test_table_of_contents_empty(self):
        """Test TableOfContents with empty entries."""
        toc = TableOfContents(entries=[])
        assert len(toc.entries) == 0


class TestExtractedMetadata:
    """Tests for ExtractedMetadata dataclass."""

    def test_extracted_metadata_creation(self):
        """Test creating ExtractedMetadata."""
        bib = BibliographicInfo(title="Test Book")
        toc = TableOfContents(entries=[TOCEntry(level=1, title="Chapter 1")])
        metadata = ExtractedMetadata(bibliographic=bib, toc=toc)
        
        assert metadata.bibliographic.title == "Test Book"
        assert len(metadata.toc.entries) == 1

    def test_extracted_metadata_empty(self):
        """Test ExtractedMetadata with empty data."""
        bib = BibliographicInfo()
        toc = TableOfContents(entries=[])
        metadata = ExtractedMetadata(bibliographic=bib, toc=toc)
        
        assert metadata.bibliographic.title is None
        assert len(metadata.toc.entries) == 0


class TestExtractCharsConstant:
    """Tests for EXTRACT_CHARS constant."""

    def test_extract_chars_constant(self):
        """Test that EXTRACT_CHARS constant is defined."""
        assert EXTRACT_CHARS == 1000
        assert isinstance(EXTRACT_CHARS, int)
        assert EXTRACT_CHARS > 0


class TestExtractMetadata:
    """Tests for extract_metadata() function."""

    @pytest.fixture
    def mock_langchain_response(self):
        """Create a mock LangChain response."""
        response = Mock()
        response.content = json.dumps({
            "bibliographic": {
                "title": "Test Book",
                "authors": ["Author One", "Author Two"],
                "publication_date": "2024",
                "publisher": "Test Publisher",
                "isbn": "978-0-123456-78-9",
                "edition": "2nd Edition"
            },
            "toc": {
                "entries": [
                    {"level": 1, "title": "Chapter 1"},
                    {"level": 2, "title": "Section 1.1"},
                    {"level": 3, "title": "Subsection 1.1.1"}
                ]
            }
        })
        return response

    @pytest.fixture
    def mock_chat(self, mock_langchain_response):
        """Create a mock chat model."""
        chat = Mock()
        chat.invoke.return_value = mock_langchain_response
        return chat

    @pytest.fixture
    def mock_langchain_stack(self, mock_chat):
        """Create a mock LangChain stack."""
        stack = Mock()
        stack.chat = mock_chat
        return stack

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_success(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response
    ):
        """Test successful metadata extraction."""
        mock_create_chat.return_value = mock_langchain_stack
        
        markdown_text = """
# Test Book

**Authors:** Author One, Author Two
**Publisher:** Test Publisher
**ISBN:** 978-0-123456-78-9
**Edition:** 2nd Edition
**Publication Date:** 2024

## Table of Contents

# Chapter 1
## Section 1.1
### Subsection 1.1.1
"""
        
        result = extract_metadata(markdown_text)
        
        assert isinstance(result, ExtractedMetadata)
        assert result.bibliographic.title == "Test Book"
        assert len(result.bibliographic.authors) == 2
        assert result.bibliographic.authors[0] == "Author One"
        assert len(result.toc.entries) == 3
        assert result.toc.entries[0].level == 1
        assert result.toc.entries[0].title == "Chapter 1"

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_with_custom_chars(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response
    ):
        """Test extraction with custom character limit."""
        mock_create_chat.return_value = mock_langchain_stack
        
        markdown_text = "A" * 2000  # 2000 characters
        result = extract_metadata(markdown_text, chars=500)
        
        # Verify that only first 500 chars were used
        mock_chat.invoke.assert_called_once()
        call_args = mock_chat.invoke.call_args[0][0]
        assert len(call_args.split("---")[-1].strip()) <= 500

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_with_lines(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response
    ):
        """Test extraction with line limit."""
        mock_create_chat.return_value = mock_langchain_stack
        
        markdown_text = "\n".join([f"Line {i}" for i in range(1, 101)])
        result = extract_metadata(markdown_text, lines=10)
        
        # Verify that only first 10 lines were used
        mock_chat.invoke.assert_called_once()
        call_args = mock_chat.invoke.call_args[0][0]
        extracted_text = call_args.split("---")[-1].strip()
        assert extracted_text.count('\n') <= 10

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_lines_override_chars(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response
    ):
        """Test that lines parameter overrides chars parameter."""
        mock_create_chat.return_value = mock_langchain_stack
        
        markdown_text = "\n".join([f"Line {i}" for i in range(1, 101)])
        result = extract_metadata(markdown_text, chars=1000, lines=5)
        
        # Verify that lines was used, not chars
        mock_chat.invoke.assert_called_once()
        call_args = mock_chat.invoke.call_args[0][0]
        extracted_text = call_args.split("---")[-1].strip()
        assert extracted_text.count('\n') <= 5

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_default_chars(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response
    ):
        """Test extraction uses default EXTRACT_CHARS when chars not specified."""
        mock_create_chat.return_value = mock_langchain_stack
        
        markdown_text = "A" * 2000
        result = extract_metadata(markdown_text)
        
        mock_chat.invoke.assert_called_once()
        call_args = mock_chat.invoke.call_args[0][0]
        extracted_text = call_args.split("---")[-1].strip()
        assert len(extracted_text) <= EXTRACT_CHARS

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_missing_bibliographic(
        self, mock_create_chat, mock_langchain_stack
    ):
        """Test extraction with missing bibliographic info."""
        response = Mock()
        response.content = json.dumps({
            "bibliographic": {},
            "toc": {
                "entries": [
                    {"level": 1, "title": "Chapter 1"}
                ]
            }
        })
        mock_chat = Mock()
        mock_chat.invoke.return_value = response
        mock_langchain_stack.chat = mock_chat
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("Test markdown")
        
        assert result.bibliographic.title is None
        assert result.bibliographic.authors == []
        assert len(result.toc.entries) == 1

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_missing_toc(
        self, mock_create_chat, mock_langchain_stack
    ):
        """Test extraction with missing table of contents."""
        response = Mock()
        response.content = json.dumps({
            "bibliographic": {
                "title": "Test Book",
                "authors": ["Author One"]
            },
            "toc": {}
        })
        mock_chat = Mock()
        mock_chat.invoke.return_value = response
        mock_langchain_stack.chat = mock_chat
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("Test markdown")
        
        assert result.bibliographic.title == "Test Book"
        assert len(result.toc.entries) == 0

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_malformed_json(
        self, mock_create_chat, mock_langchain_stack
    ):
        """Test extraction with malformed JSON response."""
        response = Mock()
        response.content = "This is not valid JSON {"
        mock_chat = Mock()
        mock_chat.invoke.return_value = response
        mock_langchain_stack.chat = mock_chat
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("Test markdown")
        
        # Should return empty result on parse failure
        assert result.bibliographic.title is None
        assert len(result.toc.entries) == 0

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_json_in_markdown_code_block(
        self, mock_create_chat, mock_langchain_stack
    ):
        """Test extraction when JSON is wrapped in markdown code block."""
        json_data = {
            "bibliographic": {
                "title": "Test Book"
            },
            "toc": {
                "entries": [{"level": 1, "title": "Chapter 1"}]
            }
        }
        response = Mock()
        response.content = f"```json\n{json.dumps(json_data)}\n```"
        mock_chat = Mock()
        mock_chat.invoke.return_value = response
        mock_langchain_stack.chat = mock_chat
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("Test markdown")
        
        assert result.bibliographic.title == "Test Book"
        assert len(result.toc.entries) == 1

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_json_in_generic_code_block(
        self, mock_create_chat, mock_langchain_stack
    ):
        """Test extraction when JSON is wrapped in generic code block."""
        json_data = {
            "bibliographic": {
                "title": "Test Book"
            },
            "toc": {
                "entries": [{"level": 1, "title": "Chapter 1"}]
            }
        }
        response = Mock()
        response.content = f"```\n{json.dumps(json_data)}\n```"
        mock_chat = Mock()
        mock_chat.invoke.return_value = response
        mock_langchain_stack.chat = mock_chat
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("Test markdown")
        
        assert result.bibliographic.title == "Test Book"
        assert len(result.toc.entries) == 1

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_response_content_as_list(
        self, mock_create_chat, mock_langchain_stack
    ):
        """Test extraction when response.content is a list."""
        json_data = {
            "bibliographic": {
                "title": "Test Book"
            },
            "toc": {
                "entries": []
            }
        }
        response = Mock()
        response.content = [json.dumps(json_data)]
        mock_chat = Mock()
        mock_chat.invoke.return_value = response
        mock_langchain_stack.chat = mock_chat
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("Test markdown")
        
        assert result.bibliographic.title == "Test Book"

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_response_content_as_dict(
        self, mock_create_chat, mock_langchain_stack
    ):
        """Test extraction when response.content is already a dict.
        
        Note: The code converts dict to string using str(), which produces
        Python dict representation (single quotes), not valid JSON. This will
        fail to parse, so we test that it handles this gracefully by returning
        empty result.
        """
        json_data = {
            "bibliographic": {
                "title": "Test Book"
            },
            "toc": {
                "entries": []
            }
        }
        response = Mock()
        response.content = json_data  # Dict gets converted to string with str()
        mock_chat = Mock()
        mock_chat.invoke.return_value = response
        mock_langchain_stack.chat = mock_chat
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("Test markdown")
        
        # str(dict) produces invalid JSON (single quotes), so parsing fails
        # and returns empty result
        assert result.bibliographic.title is None
        assert len(result.toc.entries) == 0

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_empty_response(
        self, mock_create_chat, mock_langchain_stack
    ):
        """Test extraction with empty response."""
        response = Mock()
        response.content = ""
        mock_chat = Mock()
        mock_chat.invoke.return_value = response
        mock_langchain_stack.chat = mock_chat
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("Test markdown")
        
        # Should return empty result on parse failure
        assert result.bibliographic.title is None
        assert len(result.toc.entries) == 0

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_missing_required_fields(
        self, mock_create_chat, mock_langchain_stack
    ):
        """Test extraction with missing required JSON fields."""
        response = Mock()
        response.content = json.dumps({
            "some_other_field": "value"
        })
        mock_chat = Mock()
        mock_chat.invoke.return_value = response
        mock_langchain_stack.chat = mock_chat
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("Test markdown")
        
        # Should handle missing fields gracefully
        assert result.bibliographic.title is None
        assert len(result.toc.entries) == 0

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_toc_entry_missing_level(
        self, mock_create_chat, mock_langchain_stack
    ):
        """Test extraction when TOC entry is missing level field."""
        response = Mock()
        response.content = json.dumps({
            "bibliographic": {},
            "toc": {
                "entries": [
                    {"title": "Chapter 1"}  # Missing level
                ]
            }
        })
        mock_chat = Mock()
        mock_chat.invoke.return_value = response
        mock_langchain_stack.chat = mock_chat
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("Test markdown")
        
        # Should default to level 1
        assert len(result.toc.entries) == 1
        assert result.toc.entries[0].level == 1
        assert result.toc.entries[0].title == "Chapter 1"

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_toc_entry_missing_title(
        self, mock_create_chat, mock_langchain_stack
    ):
        """Test extraction when TOC entry is missing title field."""
        response = Mock()
        response.content = json.dumps({
            "bibliographic": {},
            "toc": {
                "entries": [
                    {"level": 1}  # Missing title
                ]
            }
        })
        mock_chat = Mock()
        mock_chat.invoke.return_value = response
        mock_langchain_stack.chat = mock_chat
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("Test markdown")
        
        # Should default to empty string
        assert len(result.toc.entries) == 1
        assert result.toc.entries[0].level == 1
        assert result.toc.entries[0].title == ""

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_with_settings(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response
    ):
        """Test extraction with custom LLM settings."""
        from vulcanlab.ai.config import ModelTier
        mock_create_chat.return_value = mock_langchain_stack
        mock_settings = Mock()
        
        markdown_text = "Test markdown"
        result = extract_metadata(markdown_text, settings=mock_settings)
        
        mock_create_chat.assert_called_once_with(mock_settings, tier=ModelTier.LIGHT, search=False)

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_with_tier(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response
    ):
        """Test extraction with custom model tier."""
        from vulcanlab.ai.config import ModelTier
        mock_create_chat.return_value = mock_langchain_stack
        
        markdown_text = "Test markdown"
        result = extract_metadata(markdown_text, tier=ModelTier.FULL)
        
        mock_create_chat.assert_called_once_with(None, tier=ModelTier.FULL, search=False)

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_default_tier(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response
    ):
        """Test extraction defaults to LIGHT tier."""
        from vulcanlab.ai.config import ModelTier
        mock_create_chat.return_value = mock_langchain_stack
        
        markdown_text = "Test markdown"
        result = extract_metadata(markdown_text)
        
        mock_create_chat.assert_called_once_with(None, tier=ModelTier.LIGHT, search=False)

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_empty_markdown(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response
    ):
        """Test extraction with empty markdown text."""
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("")
        
        mock_chat.invoke.assert_called_once()
        assert isinstance(result, ExtractedMetadata)

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_very_long_markdown(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response
    ):
        """Test extraction with very long markdown text."""
        mock_create_chat.return_value = mock_langchain_stack
        
        markdown_text = "A" * 10000
        result = extract_metadata(markdown_text, chars=500)
        
        # Verify only first 500 chars were extracted
        # The prompt has "---" markers around the text sample
        mock_chat.invoke.assert_called_once()
        call_args = mock_chat.invoke.call_args[0][0]
        # Extract text between the "---" markers
        parts = call_args.split("---")
        if len(parts) >= 3:
            extracted_text = parts[1].strip()  # Text between first and second "---"
        else:
            extracted_text = parts[-1].strip()  # Fallback to last part
        assert len(extracted_text) == 500

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_null_values_in_json(
        self, mock_create_chat, mock_langchain_stack
    ):
        """Test extraction handles null values in JSON correctly."""
        response = Mock()
        response.content = json.dumps({
            "bibliographic": {
                "title": None,
                "authors": [],
                "publication_date": None,
                "publisher": None,
                "isbn": None,
                "edition": None
            },
            "toc": {
                "entries": []
            }
        })
        mock_chat = Mock()
        mock_chat.invoke.return_value = response
        mock_langchain_stack.chat = mock_chat
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("Test markdown")
        
        assert result.bibliographic.title is None
        assert result.bibliographic.authors == []
        assert result.bibliographic.publication_date is None

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_metadata_multiple_code_blocks(
        self, mock_create_chat, mock_langchain_stack
    ):
        """Test extraction when response has multiple code blocks."""
        json_data = {
            "bibliographic": {
                "title": "Test Book"
            },
            "toc": {
                "entries": []
            }
        }
        response = Mock()
        # Response with multiple code blocks - should extract first JSON block
        response.content = f"Some text ```json\n{json.dumps(json_data)}\n``` More text ```python\ncode\n```"
        mock_chat = Mock()
        mock_chat.invoke.return_value = response
        mock_langchain_stack.chat = mock_chat
        mock_create_chat.return_value = mock_langchain_stack
        
        result = extract_metadata("Test markdown")
        
        assert result.bibliographic.title == "Test Book"

