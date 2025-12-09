"""
Unit tests for LLM processor module.

Tests prompt generation, LLM response parsing, error handling for LLM failures,
and mocking of LLM API calls.

Usage:
    pytest tests/unit/test_llm_processor.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from vulcanlab.chunking.llm_processor import (
    _build_prompt,
    process_with_llm,
    TOCEntry,
    BibliographicInfo,
    LLMProcessResult,
    MAX_LINES_DEFAULT,
)


class TestBuildPrompt:
    """Tests for _build_prompt() function."""

    def test_build_prompt_includes_content(self):
        """Test that prompt includes the markdown content."""
        content = "# Test Document\n\nSome content here."
        prompt = _build_prompt(content)
        
        assert content in prompt
        assert "---" in prompt  # Content is wrapped in markers

    def test_build_prompt_includes_instructions(self):
        """Test that prompt includes processing instructions."""
        content = "Test content"
        prompt = _build_prompt(content)
        
        assert "bibliographic" in prompt.lower()
        assert "table of contents" in prompt.lower() or "toc" in prompt.lower()
        assert "heading hierarchy" in prompt.lower()

    def test_build_prompt_includes_json_format(self):
        """Test that prompt includes JSON format specification."""
        content = "Test content"
        prompt = _build_prompt(content)
        
        assert "```json" in prompt
        assert "bibliographic" in prompt
        assert "sanitized_markdown" in prompt
        assert "toc" in prompt

    def test_build_prompt_empty_content(self):
        """Test building prompt with empty content."""
        prompt = _build_prompt("")
        assert "---" in prompt
        assert "```json" in prompt


class TestTOCEntry:
    """Tests for TOCEntry Pydantic model."""

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


class TestBibliographicInfo:
    """Tests for BibliographicInfo Pydantic model."""

    def test_bibliographic_info_creation_with_all_fields(self):
        """Test creating BibliographicInfo with all fields."""
        bib = BibliographicInfo(
            title="Test Book",
            authors=["Author One", "Author Two"],
            year=2024,
            publisher="Test Publisher",
            isbn="978-0-123456-78-9",
            doi="10.1234/test"
        )
        assert bib.title == "Test Book"
        assert bib.authors == ["Author One", "Author Two"]
        assert bib.year == 2024
        assert bib.publisher == "Test Publisher"
        assert bib.isbn == "978-0-123456-78-9"
        assert bib.doi == "10.1234/test"

    def test_bibliographic_info_defaults(self):
        """Test BibliographicInfo with default values."""
        bib = BibliographicInfo()
        assert bib.title is None
        assert bib.authors == []
        assert bib.year is None
        assert bib.publisher is None
        assert bib.isbn is None
        assert bib.doi is None

    def test_bibliographic_info_partial_fields(self):
        """Test BibliographicInfo with partial fields."""
        bib = BibliographicInfo(
            title="Test Book",
            authors=["Author One"]
        )
        assert bib.title == "Test Book"
        assert bib.authors == ["Author One"]
        assert bib.year is None


class TestLLMProcessResult:
    """Tests for LLMProcessResult Pydantic model."""

    def test_llm_process_result_creation(self):
        """Test creating LLMProcessResult."""
        bib = BibliographicInfo(title="Test Book")
        toc = [TOCEntry(level=1, title="Chapter 1")]
        result = LLMProcessResult(
            bibliographic=bib,
            sanitized_markdown="# Test Book\n\nContent",
            toc=toc
        )
        assert result.bibliographic == bib
        assert result.sanitized_markdown == "# Test Book\n\nContent"
        assert result.toc == toc


class TestProcessWithLLM:
    """Tests for process_with_llm() main function."""

    @pytest.fixture
    def mock_langchain_stack(self):
        """Create mock LangChain stack."""
        mock_stack = MagicMock()
        mock_chat = MagicMock()
        mock_stack.chat = mock_chat
        return mock_stack, mock_chat

    @pytest.fixture
    def mock_langchain_response(self):
        """Create mock LLM response."""
        response = Mock()
        json_data = {
            "bibliographic": {
                "title": "Test Book",
                "authors": ["Author One"],
                "year": 2024,
                "publisher": "Test Publisher",
                "isbn": "978-0-123456-78-9",
                "doi": "10.1234/test"
            },
            "sanitized_markdown": "# Test Book\n\nSanitized content",
            "toc": [
                {"level": 1, "title": "Chapter 1"},
                {"level": 2, "title": "Section 1.1"}
            ]
        }
        response.content = json.dumps(json_data)
        return response

    @patch('vulcanlab.chunking.llm_processor.SessionLocal')
    @patch('vulcanlab.chunking.llm_processor.set_file_readonly')
    @patch('vulcanlab.chunking.llm_processor.compute_file_hash')
    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_success(
        self, mock_create_chat, mock_compute_hash, mock_set_readonly,
        mock_session_local, mock_langchain_stack, mock_langchain_response
    ):
        """Test successful LLM processing."""
        mock_stack, mock_chat = mock_langchain_stack
        mock_create_chat.return_value = mock_stack
        mock_chat.invoke.return_value = mock_langchain_response
        mock_compute_hash.return_value = "test_hash"
        
        # Mock database session
        mock_session = MagicMock()
        mock_work = MagicMock()
        mock_work.id = 1
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session

        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.md"
            input_file.write_text("# Test Document\n\nContent here.", encoding='utf-8')
            
            # Patch OUTPUT_DIR to use temp directory
            with patch('vulcanlab.chunking.llm_processor.OUTPUT_DIR', Path(tmpdir)):
                result = process_with_llm(input_file, verbose=False)

            assert isinstance(result, LLMProcessResult)
            assert result.bibliographic.title == "Test Book"
            assert len(result.toc) == 2
            assert "Sanitized content" in result.sanitized_markdown
            mock_chat.invoke.assert_called_once()
            mock_session.add.assert_called_once()

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_file_not_found(self, mock_create_chat):
        """Test error when input file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Input file not found"):
            process_with_llm("nonexistent.md")

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_invalid_file_type(self, mock_create_chat):
        """Test error when input file is not markdown."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.txt"
            input_file.write_text("Content", encoding='utf-8')
            
            with pytest.raises(ValueError, match="must be a markdown file"):
                process_with_llm(input_file)

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_file_too_large(self, mock_create_chat):
        """Test error when file exceeds line limit without force flag."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.md"
            # Create file with more than MAX_LINES_DEFAULT lines
            content = "\n".join(["Line"] * (MAX_LINES_DEFAULT + 100))
            input_file.write_text(content, encoding='utf-8')
            
            with pytest.raises(ValueError, match="exceeding the"):
                process_with_llm(input_file, force=False)

    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_file_too_large_with_force(self, mock_create_chat, mock_langchain_stack, mock_langchain_response):
        """Test that force flag allows processing large files."""
        mock_stack, mock_chat = mock_langchain_stack
        mock_create_chat.return_value = mock_stack
        mock_chat.invoke.return_value = mock_langchain_response

        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.md"
            content = "\n".join(["Line"] * (MAX_LINES_DEFAULT + 100))
            input_file.write_text(content, encoding='utf-8')
            
            with patch('vulcanlab.chunking.llm_processor.SessionLocal') as mock_session_local, \
                 patch('vulcanlab.chunking.llm_processor.set_file_readonly'), \
                 patch('vulcanlab.chunking.llm_processor.compute_file_hash') as mock_compute_hash:
                
                mock_compute_hash.return_value = "test_hash"
                mock_session = MagicMock()
                mock_work = MagicMock()
                mock_work.id = 1
                mock_session.add = MagicMock()
                mock_session.commit = MagicMock()
                mock_session_local.return_value.__enter__.return_value = mock_session
                
                with patch('vulcanlab.chunking.llm_processor.OUTPUT_DIR', Path(tmpdir)):
                    result = process_with_llm(input_file, force=True, verbose=False)
                    assert isinstance(result, LLMProcessResult)

    @patch('vulcanlab.chunking.llm_processor.SessionLocal')
    @patch('vulcanlab.chunking.llm_processor.set_file_readonly')
    @patch('vulcanlab.chunking.llm_processor.compute_file_hash')
    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_json_in_code_block(
        self, mock_create_chat, mock_compute_hash, mock_set_readonly,
        mock_session_local, mock_langchain_stack
    ):
        """Test parsing JSON response wrapped in markdown code block."""
        mock_stack, mock_chat = mock_langchain_stack
        mock_create_chat.return_value = mock_stack
        mock_compute_hash.return_value = "test_hash"
        
        json_data = {
            "bibliographic": {"title": "Test Book"},
            "sanitized_markdown": "# Test Book",
            "toc": []
        }
        response = Mock()
        response.content = f"```json\n{json.dumps(json_data)}\n```"
        mock_chat.invoke.return_value = response

        mock_session = MagicMock()
        mock_work = MagicMock()
        mock_work.id = 1
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session

        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.md"
            input_file.write_text("# Test", encoding='utf-8')
            
            with patch('vulcanlab.chunking.llm_processor.OUTPUT_DIR', Path(tmpdir)):
                result = process_with_llm(input_file, verbose=False)
                assert result.bibliographic.title == "Test Book"

    @patch('vulcanlab.chunking.llm_processor.SessionLocal')
    @patch('vulcanlab.chunking.llm_processor.set_file_readonly')
    @patch('vulcanlab.chunking.llm_processor.compute_file_hash')
    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_malformed_json(
        self, mock_create_chat, mock_compute_hash, mock_set_readonly,
        mock_session_local, mock_langchain_stack
    ):
        """Test handling of malformed JSON response."""
        mock_stack, mock_chat = mock_langchain_stack
        mock_create_chat.return_value = mock_stack
        mock_compute_hash.return_value = "test_hash"
        
        response = Mock()
        response.content = "This is not valid JSON {"
        mock_chat.invoke.return_value = response

        mock_session = MagicMock()
        mock_work = MagicMock()
        mock_work.id = 1
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session

        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.md"
            original_content = "# Original Content\n\nOriginal text"
            input_file.write_text(original_content, encoding='utf-8')
            
            with patch('vulcanlab.chunking.llm_processor.OUTPUT_DIR', Path(tmpdir)):
                result = process_with_llm(input_file, verbose=False)
                # Should return minimal result with original content
                assert isinstance(result, LLMProcessResult)
                assert result.bibliographic.title is None
                assert result.sanitized_markdown == original_content
                assert len(result.toc) == 0

    @patch('vulcanlab.chunking.llm_processor.SessionLocal')
    @patch('vulcanlab.chunking.llm_processor.set_file_readonly')
    @patch('vulcanlab.chunking.llm_processor.compute_file_hash')
    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_response_as_list(
        self, mock_create_chat, mock_compute_hash, mock_set_readonly,
        mock_session_local, mock_langchain_stack
    ):
        """Test handling when response.content is a list."""
        mock_stack, mock_chat = mock_langchain_stack
        mock_create_chat.return_value = mock_stack
        mock_compute_hash.return_value = "test_hash"
        
        json_data = {
            "bibliographic": {"title": "Test Book"},
            "sanitized_markdown": "# Test",
            "toc": []
        }
        response = Mock()
        response.content = [json.dumps(json_data)]  # List format
        mock_chat.invoke.return_value = response

        mock_session = MagicMock()
        mock_work = MagicMock()
        mock_work.id = 1
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session

        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.md"
            input_file.write_text("# Test", encoding='utf-8')
            
            with patch('vulcanlab.chunking.llm_processor.OUTPUT_DIR', Path(tmpdir)):
                result = process_with_llm(input_file, verbose=False)
                assert result.bibliographic.title == "Test Book"

    @patch('vulcanlab.chunking.llm_processor.SessionLocal')
    @patch('vulcanlab.chunking.llm_processor.set_file_readonly')
    @patch('vulcanlab.chunking.llm_processor.compute_file_hash')
    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_response_as_dict(
        self, mock_create_chat, mock_compute_hash, mock_set_readonly,
        mock_session_local, mock_langchain_stack
    ):
        """Test handling when response.content is already a dict."""
        mock_stack, mock_chat = mock_langchain_stack
        mock_create_chat.return_value = mock_stack
        mock_compute_hash.return_value = "test_hash"
        
        json_data = {
            "bibliographic": {"title": "Test Book"},
            "sanitized_markdown": "# Test",
            "toc": []
        }
        response = Mock()
        response.content = json_data  # Dict format (will be converted to JSON string)
        mock_chat.invoke.return_value = response

        mock_session = MagicMock()
        mock_work = MagicMock()
        mock_work.id = 1
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session

        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.md"
            input_file.write_text("# Test", encoding='utf-8')
            
            with patch('vulcanlab.chunking.llm_processor.OUTPUT_DIR', Path(tmpdir)):
                result = process_with_llm(input_file, verbose=False)
                assert result.bibliographic.title == "Test Book"

    @patch('vulcanlab.chunking.llm_processor.SessionLocal')
    @patch('vulcanlab.chunking.llm_processor.set_file_readonly')
    @patch('vulcanlab.chunking.llm_processor.compute_file_hash')
    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_missing_fields(
        self, mock_create_chat, mock_compute_hash, mock_set_readonly,
        mock_session_local, mock_langchain_stack
    ):
        """Test handling when JSON response is missing some fields."""
        mock_stack, mock_chat = mock_langchain_stack
        mock_create_chat.return_value = mock_stack
        mock_compute_hash.return_value = "test_hash"
        
        # Missing bibliographic and toc fields
        json_data = {
            "sanitized_markdown": "# Test Book"
        }
        response = Mock()
        response.content = json.dumps(json_data)
        mock_chat.invoke.return_value = response

        mock_session = MagicMock()
        mock_work = MagicMock()
        mock_work.id = 1
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session

        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.md"
            input_file.write_text("# Test", encoding='utf-8')
            
            with patch('vulcanlab.chunking.llm_processor.OUTPUT_DIR', Path(tmpdir)):
                result = process_with_llm(input_file, verbose=False)
                assert result.bibliographic.title is None
                assert len(result.toc) == 0
                assert result.sanitized_markdown == "# Test Book"

    @patch('vulcanlab.chunking.llm_processor.SessionLocal')
    @patch('vulcanlab.chunking.llm_processor.set_file_readonly')
    @patch('vulcanlab.chunking.llm_processor.compute_file_hash')
    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_custom_settings(
        self, mock_create_chat, mock_compute_hash, mock_set_readonly,
        mock_session_local, mock_langchain_stack, mock_langchain_response
    ):
        """Test processing with custom LLM settings."""
        from vulcanlab.ai.config import LLMSettings, ModelTier
        
        mock_stack, mock_chat = mock_langchain_stack
        mock_create_chat.return_value = mock_stack
        mock_chat.invoke.return_value = mock_langchain_response
        mock_compute_hash.return_value = "test_hash"
        
        mock_settings = MagicMock(spec=LLMSettings)
        
        mock_session = MagicMock()
        mock_work = MagicMock()
        mock_work.id = 1
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session

        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.md"
            input_file.write_text("# Test", encoding='utf-8')
            
            with patch('vulcanlab.chunking.llm_processor.OUTPUT_DIR', Path(tmpdir)):
                result = process_with_llm(input_file, settings=mock_settings, verbose=False)
                mock_create_chat.assert_called_once_with(
                    settings=mock_settings,
                    tier=ModelTier.FULL,
                    search=False,
                    temperature=0.2
                )

    @patch('vulcanlab.chunking.llm_processor.SessionLocal')
    @patch('vulcanlab.chunking.llm_processor.set_file_readonly')
    @patch('vulcanlab.chunking.llm_processor.compute_file_hash')
    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_custom_tier(
        self, mock_create_chat, mock_compute_hash, mock_set_readonly,
        mock_session_local, mock_langchain_stack, mock_langchain_response
    ):
        """Test processing with custom model tier."""
        from vulcanlab.ai.config import ModelTier
        
        mock_stack, mock_chat = mock_langchain_stack
        mock_create_chat.return_value = mock_stack
        mock_chat.invoke.return_value = mock_langchain_response
        mock_compute_hash.return_value = "test_hash"
        
        mock_session = MagicMock()
        mock_work = MagicMock()
        mock_work.id = 1
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session

        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.md"
            input_file.write_text("# Test", encoding='utf-8')
            
            with patch('vulcanlab.chunking.llm_processor.OUTPUT_DIR', Path(tmpdir)):
                result = process_with_llm(input_file, tier=ModelTier.LIGHT, verbose=False)
                mock_create_chat.assert_called_once_with(
                    settings=None,
                    tier=ModelTier.LIGHT,
                    search=False,
                    temperature=0.2
                )

    @patch('vulcanlab.chunking.llm_processor.SessionLocal')
    @patch('vulcanlab.chunking.llm_processor.set_file_readonly')
    @patch('vulcanlab.chunking.llm_processor.compute_file_hash')
    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_default_tier(
        self, mock_create_chat, mock_compute_hash, mock_set_readonly,
        mock_session_local, mock_langchain_stack, mock_langchain_response
    ):
        """Test that default tier is FULL."""
        from vulcanlab.ai.config import ModelTier
        
        mock_stack, mock_chat = mock_langchain_stack
        mock_create_chat.return_value = mock_stack
        mock_chat.invoke.return_value = mock_langchain_response
        mock_compute_hash.return_value = "test_hash"
        
        mock_session = MagicMock()
        mock_work = MagicMock()
        mock_work.id = 1
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session

        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.md"
            input_file.write_text("# Test", encoding='utf-8')
            
            with patch('vulcanlab.chunking.llm_processor.OUTPUT_DIR', Path(tmpdir)):
                result = process_with_llm(input_file, verbose=False)
                mock_create_chat.assert_called_once_with(
                    settings=None,
                    tier=ModelTier.FULL,
                    search=False,
                    temperature=0.2
                )

    @patch('vulcanlab.chunking.llm_processor.SessionLocal')
    @patch('vulcanlab.chunking.llm_processor.set_file_readonly')
    @patch('vulcanlab.chunking.llm_processor.compute_file_hash')
    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_saves_sanitized_file(
        self, mock_create_chat, mock_compute_hash, mock_set_readonly,
        mock_session_local, mock_langchain_stack, mock_langchain_response
    ):
        """Test that sanitized file is saved correctly."""
        mock_stack, mock_chat = mock_langchain_stack
        mock_create_chat.return_value = mock_stack
        mock_chat.invoke.return_value = mock_langchain_response
        mock_compute_hash.return_value = "test_hash"
        
        mock_session = MagicMock()
        mock_work = MagicMock()
        mock_work.id = 1
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session

        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.md"
            input_file.write_text("# Original", encoding='utf-8')
            
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            with patch('vulcanlab.chunking.llm_processor.OUTPUT_DIR', output_dir):
                result = process_with_llm(input_file, verbose=False)
                
                # Check that sanitized file was created
                sanitized_file = output_dir / "test.sanitized.md"
                assert sanitized_file.exists()
                assert sanitized_file.read_text(encoding='utf-8') == "# Test Book\n\nSanitized content"
                mock_set_readonly.assert_called_once_with(sanitized_file)

    @patch('vulcanlab.chunking.llm_processor.SessionLocal')
    @patch('vulcanlab.chunking.llm_processor.set_file_readonly')
    @patch('vulcanlab.chunking.llm_processor.compute_file_hash')
    @patch('vulcanlab.ai.create_langchain_chat')
    def test_process_with_llm_creates_database_entry(
        self, mock_create_chat, mock_compute_hash, mock_set_readonly,
        mock_session_local, mock_langchain_stack, mock_langchain_response
    ):
        """Test that database entry is created correctly."""
        mock_stack, mock_chat = mock_langchain_stack
        mock_create_chat.return_value = mock_stack
        mock_chat.invoke.return_value = mock_langchain_response
        mock_compute_hash.return_value = "test_hash"
        
        mock_session = MagicMock()
        mock_work = MagicMock()
        mock_work.id = 1
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session

        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.md"
            input_file.write_text("# Original", encoding='utf-8')
            
            with patch('vulcanlab.chunking.llm_processor.OUTPUT_DIR', Path(tmpdir)):
                result = process_with_llm(input_file, verbose=False)
                
                # Verify Work was created with correct data
                mock_session.add.assert_called_once()
                work_call = mock_session.add.call_args[0][0]
                from vulcanlab.data.models import Work
                assert isinstance(work_call, Work)
                assert work_call.title == "Test Book"
                assert work_call.authors == "Author One"
                assert work_call.year == 2024
                mock_session.commit.assert_called_once()

