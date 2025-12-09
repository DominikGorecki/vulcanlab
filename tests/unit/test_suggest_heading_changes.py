
import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from vulcanlab.sanitization.suggest_heading_changes import (
    suggest_heading_changes,
    suggest_heading_changes_from_work,
    _parse_llm_response,
    _extract_text_from_response,
    _build_prompt,
    build_prompt_for_work,
    save_title_changes_from_response,
)
from vulcanlab.sanitization.extract_titles import HashMismatchError
from vulcanlab.data.models import Work
from tests.unit.mock_helpers import (
    mock_session,
    create_mock_work,
    configure_mock_session_query,
)

# Test Data
SAMPLE_TITLES_CONTENT = """./original.md

```
10: # Chapter 1
15: ## Section A
20: ### Subsection B
```
"""

SAMPLE_LLM_RESPONSE = """
Here are the changes:
```
10 : NO_CHANGE : Chapter 1
15 : H1 : Section A
20 : H2 : Subsection B
```
"""

SAMPLE_LLM_RESPONSE_NO_BLOCK = """
10 : NO_CHANGE : Chapter 1
15 : H1 : Section A
20 : H2 : Subsection B
"""

INVALID_LLM_RESPONSE = "I cannot do that."

@pytest.fixture
def mock_compute_hash():
    with patch('vulcanlab.sanitization.suggest_heading_changes.compute_file_hash') as m:
        m.return_value = "hash123"
        yield m

@pytest.fixture
def mock_path_exists():
    with patch('pathlib.Path.exists') as m:
        m.return_value = True
        yield m

@pytest.fixture
def mock_path_read_text():
    with patch('pathlib.Path.read_text') as m:
        m.return_value = SAMPLE_TITLES_CONTENT
        yield m

@pytest.fixture
def mock_load_template():
    with patch('vulcanlab.sanitization.suggest_heading_changes.load_template') as m:
        m.return_value = MagicMock()
        m.return_value.format.return_value = "Formatted Prompt"
        yield m

@pytest.fixture
def mock_llm():
    with patch('vulcanlab.ai.create_langchain_chat') as m:
        chat_mock = MagicMock()
        chat_mock.invoke.return_value = MagicMock(content=SAMPLE_LLM_RESPONSE)
        m.return_value.chat = chat_mock
        yield m

class TestSuggestionParsing:
    """Test parsing of LLM responses."""

    def test_parse_llm_response_block(self):
        changes = _parse_llm_response(SAMPLE_LLM_RESPONSE)
        assert len(changes) == 3
        assert changes[0] == "10 : NO_CHANGE : Chapter 1"
        assert changes[1] == "15 : H1 : Section A"
        assert changes[2] == "20 : H2 : Subsection B"

    def test_parse_llm_response_no_block(self):
        changes = _parse_llm_response(SAMPLE_LLM_RESPONSE_NO_BLOCK)
        assert len(changes) == 3
        assert changes[0] == "10 : NO_CHANGE : Chapter 1"
        assert changes[1] == "15 : H1 : Section A"
        assert changes[2] == "20 : H2 : Subsection B"

    def test_parse_llm_response_invalid(self):
        changes = _parse_llm_response(INVALID_LLM_RESPONSE)
        assert len(changes) == 0

    def test_extract_text_string(self):
        assert _extract_text_from_response("some text") == "some text"

    def test_extract_text_list(self):
        assert _extract_text_from_response(["some text"]) == "some text"
        assert _extract_text_from_response([{"text": "some text"}]) == "some text"

    def test_extract_text_dict(self):
        assert _extract_text_from_response({"text": "some text"}) == "some text"

class TestPromptBuilding:
    """Test prompt construction logic."""

    def test_build_prompt(self, mock_load_template):
        prompt = _build_prompt("Title", "Author", [], "titles block")
        assert prompt == "Formatted Prompt"
        mock_load_template.assert_called_once()


class TestSuggestionGeneration:
    """Test the main suggestion generation workflow."""
    
    @patch('vulcanlab.sanitization.suggest_heading_changes.SessionLocal')
    @patch('vulcanlab.sanitization.suggest_heading_changes._log_llm_interaction')
    def test_suggest_heading_changes_success(
        self,
        mock_log_llm,
        mock_session_local,
        mock_session,
        mock_compute_hash,
        mock_path_exists,
        mock_path_read_text,
        mock_load_template,
        mock_llm
    ):
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Setup mock work
        work = create_mock_work(title="Test Work", content_hash="hash123")
        configure_mock_session_query(mock_session, Work, return_first=work)
        
        # Mock Path.write_text to avoid file system writes
        with patch('pathlib.Path.write_text') as mock_write:
            output_path = suggest_heading_changes("test.titles.md")
            
            assert output_path.name.endswith(".title_changes.md")
            mock_write.assert_called_once()
            
            # Verify LLM was called
            mock_llm.return_value.chat.invoke.assert_called_once()

    @patch('vulcanlab.sanitization.suggest_heading_changes.SessionLocal')
    def test_suggest_heading_changes_work_not_found(
        self, 
        mock_session_local,
        mock_session,
        mock_compute_hash,
        mock_path_exists,
        mock_path_read_text
    ):
        mock_session_local.return_value.__enter__.return_value = mock_session
        configure_mock_session_query(mock_session, Work, return_first=None)

        with pytest.raises(ValueError, match="Document not found"):
            suggest_heading_changes("test.titles.md")

    def test_suggest_heading_changes_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            suggest_heading_changes("nonexistent.titles.md")

class TestSuggestionFromWork:
    """Test generating suggestions from Work ID."""
    
    @patch('vulcanlab.sanitization.suggest_heading_changes.get_session')
    def test_suggest_from_work_success(
        self,
        mock_get_session,
        mock_session,
        mock_compute_hash,
        mock_path_exists,
        mock_path_read_text
    ):
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        work = create_mock_work(id=1, title="Test Work")
        work.files = {
            "original_markdown": {"path": "/abs/path/orig.md", "hash": "hash123"},
            "titles": {"path": "/abs/path/titles.md", "hash": "hash123"}
        }
        configure_mock_session_query(mock_session, Work, return_first=work)
        
        # Mock save_title_changes... since it does file IO and logic we want to skip or verify logic integration
        # But here we are testing `build_prompt_for_work` logic implicitly via the flow or explicit test
        
        result = build_prompt_for_work(1, "original_markdown")
        assert result["work_title"] == "Test Work"
        assert "prompt" in result

    @patch('vulcanlab.sanitization.suggest_heading_changes.get_session')
    def test_suggest_from_work_hash_mismatch(
        self,
        mock_get_session,
        mock_session,
        mock_path_exists,
        mock_path_read_text
    ):
        # Mock compute_hash to return DIFFERENT hash
        with patch('vulcanlab.sanitization.suggest_heading_changes.compute_file_hash') as m:
            m.return_value = "new_hash"
            
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            work = create_mock_work(id=1)
            work.files = {
                "original_markdown": {"path": "/abs/path/orig.md", "hash": "old_hash"},
                "titles": {"path": "/abs/path/titles.md", "hash": "old_hash"}
            }
            configure_mock_session_query(mock_session, Work, return_first=work)
            
            with pytest.raises(HashMismatchError):
                build_prompt_for_work(1, "original_markdown")

    @patch('vulcanlab.sanitization.suggest_heading_changes.get_session')
    def test_suggest_from_work_force(
        self,
        mock_get_session,
        mock_session,
        mock_path_exists,
        mock_path_read_text,
         mock_load_template
    ):
        # Mock compute_hash to return DIFFERENT hash
        with patch('vulcanlab.sanitization.suggest_heading_changes.compute_file_hash') as m:
            m.return_value = "new_hash"
        
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            work = create_mock_work(id=1)
            work.files = {
                "original_markdown": {"path": "/abs/path/orig.md", "hash": "old_hash"},
                "titles": {"path": "/abs/path/titles.md", "hash": "old_hash"}
            }
            configure_mock_session_query(mock_session, Work, return_first=work)
            
            # Should NOT raise error
            result = build_prompt_for_work(1, "original_markdown", force=True)
            assert result["work_title"] == "Test Work" # default from helper

class TestSaveTitleChanges:
    @patch('vulcanlab.sanitization.suggest_heading_changes.get_session')
    def test_save_changes_success(
        self,
        mock_get_session,
        mock_session,
        mock_compute_hash, # for output hash
        mock_path_exists
    ):
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        work = create_mock_work(id=1)
        work.files = {
            "original_markdown": {"path": "/abs/path/orig.md", "hash": "hash123"},
            "titles": {"path": "/abs/path/titles.md", "hash": "hash123"}
        }
        configure_mock_session_query(mock_session, Work, return_first=work)
        
        with patch('pathlib.Path.write_text') as mock_write, \
             patch('vulcanlab.sanitization.suggest_heading_changes.set_file_writable') as mock_set_writable, \
             patch('vulcanlab.sanitization.suggest_heading_changes.set_file_readonly') as mock_set_readonly:
             
            mock_compute_hash.return_value = "full_output_hash"
            
            mock_path_exists.return_value = True # ensure markdown path exists

            output_path = save_title_changes_from_response(
                1, 
                "original_markdown", 
                SAMPLE_LLM_RESPONSE
            )
            
            mock_write.assert_called_once()
            mock_set_readonly.assert_called_once()
            assert "title_changes" in work.files
            assert work.files["title_changes"]["hash"] == "full_output_hash"
