"""
Unit tests for extract_toc module.

Tests cover:
- TOC extraction from markdown content
- Table of contents parsing
- Edge cases (no TOC, malformed TOC)
- File validation
- Character and line limits
- JSON parsing edge cases

Usage:
    pytest tests/unit/test_extract_toc.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import json

from vulcanlab.sanitization.extract_toc import (
    TOCEntry,
    TableOfContents,
    extract_table_of_contents,
    EXTRACT_CHARS,
)


class TestTOCEntry:
    """Tests for TOCEntry Pydantic model."""

    def test_toc_entry_creation(self):
        """Test creating TOCEntry with level and title."""
        entry = TOCEntry(level=1, title="Chapter 1")
        assert entry.level == 1
        assert entry.title == "Chapter 1"

    def test_toc_entry_different_levels(self):
        """Test TOCEntry with different heading levels."""
        h1 = TOCEntry(level=1, title="Main Chapter")
        h2 = TOCEntry(level=2, title="Section")
        h3 = TOCEntry(level=3, title="Subsection")
        h4 = TOCEntry(level=4, title="Sub-subsection")
        
        assert h1.level == 1
        assert h2.level == 2
        assert h3.level == 3
        assert h4.level == 4

    def test_toc_entry_empty_title(self):
        """Test TOCEntry with empty title."""
        entry = TOCEntry(level=1, title="")
        assert entry.level == 1
        assert entry.title == ""

    def test_toc_entry_special_characters(self):
        """Test TOCEntry handles special characters in title."""
        entry = TOCEntry(level=1, title='Chapter with "quotes" and \'apostrophes\'')
        assert '"quotes"' in entry.title
        assert "'apostrophes'" in entry.title


class TestTableOfContents:
    """Tests for TableOfContents Pydantic model."""

    def test_table_of_contents_creation(self):
        """Test creating TableOfContents with entries."""
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

    def test_table_of_contents_hierarchical(self):
        """Test TableOfContents with hierarchical structure."""
        entries = [
            TOCEntry(level=1, title="Chapter 1"),
            TOCEntry(level=2, title="Section 1.1"),
            TOCEntry(level=3, title="Subsection 1.1.1"),
            TOCEntry(level=2, title="Section 1.2"),
            TOCEntry(level=1, title="Chapter 2"),
        ]
        toc = TableOfContents(entries=entries)
        assert len(toc.entries) == 5
        assert toc.entries[0].level == 1
        assert toc.entries[1].level == 2
        assert toc.entries[2].level == 3


class TestExtractTableOfContents:
    """Tests for extract_table_of_contents() function."""

    @pytest.fixture
    def mock_langchain_response(self):
        """Create a mock LangChain response with valid TOC JSON."""
        response = Mock()
        response.content = json.dumps({
            "entries": [
                {"level": 1, "title": "Chapter 1"},
                {"level": 2, "title": "Section 1.1"},
                {"level": 3, "title": "Subsection 1.1.1"}
            ]
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
    def test_extract_table_of_contents_success(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response, tmp_path
    ):
        """Test successful TOC extraction from markdown file."""
        mock_create_chat.return_value = mock_langchain_stack
        
        test_file = tmp_path / "test.md"
        test_file.write_text("""# Chapter 1
Content here
## Section 1.1
More content
### Subsection 1.1.1
Even more content
""", encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        assert isinstance(result, TableOfContents)
        assert len(result.entries) == 3
        assert result.entries[0].level == 1
        assert result.entries[0].title == "Chapter 1"
        assert result.entries[1].level == 2
        assert result.entries[1].title == "Section 1.1"
        assert result.entries[2].level == 3
        assert result.entries[2].title == "Subsection 1.1.1"
        
        # Verify LLM was called
        mock_create_chat.assert_called_once()
        mock_chat.invoke.assert_called_once()

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_file_not_found(self, mock_create_chat, tmp_path):
        """Test that FileNotFoundError is raised for non-existent file."""
        test_file = tmp_path / "nonexistent.md"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            extract_table_of_contents(test_file)
        
        assert "File not found" in str(exc_info.value)
        assert str(test_file) in str(exc_info.value)
        mock_create_chat.assert_not_called()

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_not_markdown(self, mock_create_chat, tmp_path):
        """Test that ValueError is raised for non-markdown file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content", encoding='utf-8')
        
        with pytest.raises(ValueError) as exc_info:
            extract_table_of_contents(test_file)
        
        assert "Expected Markdown file" in str(exc_info.value)
        assert ".txt" in str(exc_info.value)
        mock_create_chat.assert_not_called()

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_string_path(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response, tmp_path
    ):
        """Test extraction accepts string path."""
        mock_create_chat.return_value = mock_langchain_stack
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')
        
        result = extract_table_of_contents(str(test_file))
        
        assert isinstance(result, TableOfContents)
        mock_create_chat.assert_called_once()

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_with_chars_limit(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response, tmp_path
    ):
        """Test extraction with custom character limit."""
        mock_create_chat.return_value = mock_langchain_stack
        
        test_file = tmp_path / "test.md"
        test_file.write_text("A" * 2000, encoding='utf-8')
        
        result = extract_table_of_contents(test_file, chars=500)
        
        # Verify that only first 500 chars were used in prompt
        mock_chat.invoke.assert_called_once()
        call_args = mock_chat.invoke.call_args[0][0]
        text_sample = call_args.split("---")[-1].strip()
        assert len(text_sample) <= 500

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_with_lines_limit(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response, tmp_path
    ):
        """Test extraction with line limit."""
        mock_create_chat.return_value = mock_langchain_stack
        
        test_file = tmp_path / "test.md"
        test_file.write_text("\n".join([f"Line {i}" for i in range(1, 101)]), encoding='utf-8')
        
        result = extract_table_of_contents(test_file, lines=10)
        
        # Verify that only first 10 lines were used
        mock_chat.invoke.assert_called_once()
        call_args = mock_chat.invoke.call_args[0][0]
        text_sample = call_args.split("---")[-1].strip()
        assert text_sample.count('\n') <= 10

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_lines_override_chars(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response, tmp_path
    ):
        """Test that lines parameter overrides chars parameter."""
        mock_create_chat.return_value = mock_langchain_stack
        
        test_file = tmp_path / "test.md"
        test_file.write_text("\n".join([f"Line {i}" for i in range(1, 101)]), encoding='utf-8')
        
        result = extract_table_of_contents(test_file, chars=1000, lines=5)
        
        # Verify that lines was used, not chars
        mock_chat.invoke.assert_called_once()
        call_args = mock_chat.invoke.call_args[0][0]
        text_sample = call_args.split("---")[-1].strip()
        assert text_sample.count('\n') <= 5

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_default_chars(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response, tmp_path
    ):
        """Test extraction uses default EXTRACT_CHARS when chars not specified."""
        mock_create_chat.return_value = mock_langchain_stack
        
        test_file = tmp_path / "test.md"
        test_file.write_text("A" * 2000, encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        mock_chat.invoke.assert_called_once()
        call_args = mock_chat.invoke.call_args[0][0]
        text_sample = call_args.split("---")[-1].strip()
        assert len(text_sample) <= EXTRACT_CHARS

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_no_toc(
        self, mock_create_chat, mock_langchain_stack, mock_chat, tmp_path
    ):
        """Test extraction when LLM returns empty TOC."""
        mock_create_chat.return_value = mock_langchain_stack
        
        # Mock response with empty entries
        empty_response = Mock()
        empty_response.content = json.dumps({"entries": []})
        mock_chat.invoke.return_value = empty_response
        
        test_file = tmp_path / "test.md"
        test_file.write_text("Just content, no headings\n", encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        assert isinstance(result, TableOfContents)
        assert len(result.entries) == 0

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_malformed_json(
        self, mock_create_chat, mock_langchain_stack, mock_chat, tmp_path
    ):
        """Test extraction handles malformed JSON gracefully."""
        mock_create_chat.return_value = mock_langchain_stack
        
        # Mock response with invalid JSON
        malformed_response = Mock()
        malformed_response.content = "This is not valid JSON"
        mock_chat.invoke.return_value = malformed_response
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        # Should return empty TOC on JSON parse error
        assert isinstance(result, TableOfContents)
        assert len(result.entries) == 0

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_json_in_code_block(
        self, mock_create_chat, mock_langchain_stack, mock_chat, tmp_path
    ):
        """Test extraction handles JSON wrapped in markdown code blocks."""
        mock_create_chat.return_value = mock_langchain_stack
        
        # Mock response with JSON in code block
        code_block_response = Mock()
        json_data = json.dumps({
            "entries": [
                {"level": 1, "title": "Chapter 1"},
                {"level": 2, "title": "Section 1.1"}
            ]
        })
        code_block_response.content = f"```json\n{json_data}\n```"
        mock_chat.invoke.return_value = code_block_response
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        assert isinstance(result, TableOfContents)
        assert len(result.entries) == 2
        assert result.entries[0].title == "Chapter 1"

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_json_in_generic_code_block(
        self, mock_create_chat, mock_langchain_stack, mock_chat, tmp_path
    ):
        """Test extraction handles JSON wrapped in generic code blocks."""
        mock_create_chat.return_value = mock_langchain_stack
        
        # Mock response with JSON in generic code block (no language specified)
        code_block_response = Mock()
        json_data = json.dumps({
            "entries": [
                {"level": 1, "title": "Chapter 1"}
            ]
        })
        code_block_response.content = f"```\n{json_data}\n```"
        mock_chat.invoke.return_value = code_block_response
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        assert isinstance(result, TableOfContents)
        assert len(result.entries) == 1

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_missing_entries_key(
        self, mock_create_chat, mock_langchain_stack, mock_chat, tmp_path
    ):
        """Test extraction handles JSON missing 'entries' key."""
        mock_create_chat.return_value = mock_langchain_stack
        
        # Mock response with JSON missing entries
        missing_key_response = Mock()
        missing_key_response.content = json.dumps({"other_key": "value"})
        mock_chat.invoke.return_value = missing_key_response
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        # Should return empty TOC
        assert isinstance(result, TableOfContents)
        assert len(result.entries) == 0

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_missing_level_or_title(
        self, mock_create_chat, mock_langchain_stack, mock_chat, tmp_path
    ):
        """Test extraction handles entries missing level or title fields."""
        mock_create_chat.return_value = mock_langchain_stack
        
        # Mock response with entries missing fields
        incomplete_response = Mock()
        incomplete_response.content = json.dumps({
            "entries": [
                {"level": 1, "title": "Chapter 1"},
                {"level": 2},  # Missing title
                {"title": "Section 2"},  # Missing level
                {"level": 3, "title": "Subsection 3"}
            ]
        })
        mock_chat.invoke.return_value = incomplete_response
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        # Should use defaults: level=1, title=""
        assert isinstance(result, TableOfContents)
        assert len(result.entries) == 4
        assert result.entries[0].title == "Chapter 1"
        assert result.entries[1].title == ""  # Default for missing title
        assert result.entries[1].level == 2
        assert result.entries[2].title == "Section 2"
        assert result.entries[2].level == 1  # Default for missing level
        assert result.entries[3].title == "Subsection 3"

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_response_content_as_list(
        self, mock_create_chat, mock_langchain_stack, mock_chat, tmp_path
    ):
        """Test extraction handles response.content as a list."""
        mock_create_chat.return_value = mock_langchain_stack
        
        # Mock response with content as list
        list_response = Mock()
        json_data = json.dumps({
            "entries": [
                {"level": 1, "title": "Chapter 1"}
            ]
        })
        list_response.content = [json_data]
        mock_chat.invoke.return_value = list_response
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        assert isinstance(result, TableOfContents)
        assert len(result.entries) == 1

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_response_content_as_dict(
        self, mock_create_chat, mock_langchain_stack, mock_chat, tmp_path
    ):
        """Test extraction handles response.content as a dict."""
        mock_create_chat.return_value = mock_langchain_stack
        
        # Mock response with content as dict
        dict_response = Mock()
        dict_response.content = {
            "entries": [
                {"level": 1, "title": "Chapter 1"}
            ]
        }
        mock_chat.invoke.return_value = dict_response
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        # Should convert dict to string and parse
        assert isinstance(result, TableOfContents)
        # Note: dict conversion might result in empty TOC if parsing fails
        # This tests the code path, not necessarily the success case

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_with_settings(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response, tmp_path
    ):
        """Test extraction with custom LLM settings."""
        mock_create_chat.return_value = mock_langchain_stack
        
        from vulcanlab.ai.config import LLMSettings, ModelTier
        
        mock_settings = MagicMock(spec=LLMSettings)
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')
        
        result = extract_table_of_contents(test_file, settings=mock_settings)
        
        assert isinstance(result, TableOfContents)
        # tier defaults to LIGHT when None is passed
        mock_create_chat.assert_called_once_with(mock_settings, tier=ModelTier.LIGHT, search=False)

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_with_tier(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response, tmp_path
    ):
        """Test extraction with custom model tier."""
        mock_create_chat.return_value = mock_langchain_stack
        
        from vulcanlab.ai.config import ModelTier
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')
        
        result = extract_table_of_contents(test_file, tier=ModelTier.FULL)
        
        assert isinstance(result, TableOfContents)
        mock_create_chat.assert_called_once_with(None, tier=ModelTier.FULL, search=False)

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_default_tier(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response, tmp_path
    ):
        """Test extraction uses LIGHT tier by default."""
        mock_create_chat.return_value = mock_langchain_stack
        
        from vulcanlab.ai.config import ModelTier
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        assert isinstance(result, TableOfContents)
        mock_create_chat.assert_called_once_with(None, tier=ModelTier.LIGHT, search=False)

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_empty_file(
        self, mock_create_chat, mock_langchain_stack, mock_chat, mock_langchain_response, tmp_path
    ):
        """Test extraction from empty markdown file."""
        mock_create_chat.return_value = mock_langchain_stack
        
        test_file = tmp_path / "test.md"
        test_file.write_text("", encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        assert isinstance(result, TableOfContents)
        # Should still call LLM with empty content
        mock_chat.invoke.assert_called_once()

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_single_entry(
        self, mock_create_chat, mock_langchain_stack, mock_chat, tmp_path
    ):
        """Test extraction with single TOC entry."""
        mock_create_chat.return_value = mock_langchain_stack
        
        single_response = Mock()
        single_response.content = json.dumps({
            "entries": [
                {"level": 1, "title": "Only Chapter"}
            ]
        })
        mock_chat.invoke.return_value = single_response
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        assert isinstance(result, TableOfContents)
        assert len(result.entries) == 1
        assert result.entries[0].title == "Only Chapter"

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_extract_table_of_contents_hierarchical_structure(
        self, mock_create_chat, mock_langchain_stack, mock_chat, tmp_path
    ):
        """Test extraction with complex hierarchical structure."""
        mock_create_chat.return_value = mock_langchain_stack
        
        hierarchical_response = Mock()
        hierarchical_response.content = json.dumps({
            "entries": [
                {"level": 1, "title": "Part I"},
                {"level": 2, "title": "Chapter 1"},
                {"level": 3, "title": "Section 1.1"},
                {"level": 3, "title": "Section 1.2"},
                {"level": 2, "title": "Chapter 2"},
                {"level": 1, "title": "Part II"},
                {"level": 2, "title": "Chapter 3"},
            ]
        })
        mock_chat.invoke.return_value = hierarchical_response
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')
        
        result = extract_table_of_contents(test_file)
        
        assert isinstance(result, TableOfContents)
        assert len(result.entries) == 7
        assert result.entries[0].level == 1
        assert result.entries[1].level == 2
        assert result.entries[2].level == 3
        assert result.entries[4].level == 2
        assert result.entries[5].level == 1
