"""
Unit tests for augmentation module.

Tests the augment.py module functions for generating RAG prompts.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from vulcanlab.augmentation.augment import (
    get_query_with_context,
    format_context_blocks,
    generate_augmented_prompt,
)
from vulcanlab.data.models.query import Query
from vulcanlab.data.models.work import Work
from vulcanlab.config.app_config import AppConfig, LoggingConfig


class TestGetQueryWithContext:
    """Tests for get_query_with_context function."""
    
    @patch('vulcanlab.augmentation.augment.get_session')
    def test_get_query_with_context_success(self, mock_get_session):
        """Test successful retrieval of query with contexts."""
        # Setup mock query
        mock_query = Mock(spec=Query)
        mock_query.id = 1
        mock_query.original_query = "What is cognitive dissonance?"
        mock_query.clean_retrieval_context = [
            {"work_id": 1, "content": "Content 1", "score": 0.9, "start_line": 10, "end_line": 20},
            {"work_id": 2, "content": "Content 2", "score": 0.8, "start_line": 30, "end_line": 40},
            {"work_id": 3, "content": "Content 3", "score": 0.7, "start_line": 50, "end_line": 60},
        ]
        
        # Setup mock session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Call function
        query, contexts = get_query_with_context(1, top_n=2)
        
        # Assertions
        assert query.id == 1
        assert len(contexts) == 2
        assert contexts[0]["score"] == 0.9
        assert contexts[1]["score"] == 0.8
    
    @patch('vulcanlab.augmentation.augment.get_default_config')
    @patch('vulcanlab.augmentation.augment.get_session')
    def test_get_query_not_found(self, mock_get_session, mock_get_default_config):
        """Test error when query not found."""
        mock_get_default_config.return_value = {"augmentation": {"top_n_contexts": 5}}
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        with pytest.raises(ValueError, match="Query with id=999 not found"):
            get_query_with_context(999)
    
    @patch('vulcanlab.augmentation.augment.get_default_config')
    @patch('vulcanlab.augmentation.augment.get_session')
    def test_get_query_no_contexts(self, mock_get_session, mock_get_default_config):
        """Test query with no contexts."""
        mock_get_default_config.return_value = {"augmentation": {"top_n_contexts": 5}}
        mock_query = Mock(spec=Query)
        mock_query.id = 1
        mock_query.clean_retrieval_context = None
        
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        query, contexts = get_query_with_context(1)
        
        assert query.id == 1
        assert contexts == []
    
    @patch('vulcanlab.augmentation.augment.get_session')
    def test_get_query_sorts_by_score(self, mock_get_session):
        """Test that contexts are sorted by score descending."""
        mock_query = Mock(spec=Query)
        mock_query.clean_retrieval_context = [
            {"work_id": 1, "score": 0.5},
            {"work_id": 2, "score": 0.9},
            {"work_id": 3, "score": 0.7},
        ]
        
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        _, contexts = get_query_with_context(1, top_n=10)
        
        assert contexts[0]["score"] == 0.9
        assert contexts[1]["score"] == 0.7
        assert contexts[2]["score"] == 0.5


class TestFormatContextBlocks:
    """Tests for format_context_blocks function."""
    
    def test_format_single_context(self):
        """Test formatting a single context block."""
        contexts = [
            {
                "work_id": 1,
                "content": "Cognitive Dissonance\nThis is a theory about mental discomfort.",
                "start_line": 10,
                "end_line": 15,
                "score": 0.9
            }
        ]
        
        mock_work = Mock(spec=Work)
        mock_work.title = "Psychology Textbook"
        
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        
        result = format_context_blocks(contexts, mock_session)
        
        assert "[S1]" in result
        assert "Psychology Textbook" in result
        assert "Cognitive Dissonance" in result
        assert "work_id=1" in result
        assert "start-line=10" in result
        assert "end-line=15" in result
        assert "This is a theory about mental discomfort." in result
    
    def test_format_multiple_contexts(self):
        """Test formatting multiple context blocks."""
        contexts = [
            {
                "work_id": 1,
                "content": "Title 1\nContent 1",
                "start_line": 10,
                "end_line": 15,
                "score": 0.9
            },
            {
                "work_id": 2,
                "content": "Title 2\nContent 2",
                "start_line": 20,
                "end_line": 25,
                "score": 0.8
            }
        ]
        
        mock_work1 = Mock(spec=Work)
        mock_work1.title = "Book 1"
        mock_work2 = Mock(spec=Work)
        mock_work2.title = "Book 2"
        
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.side_effect = [mock_work1, mock_work2]
        
        result = format_context_blocks(contexts, mock_session)
        
        assert "[S1]" in result
        assert "[S2]" in result
        assert "Book 1" in result
        assert "Book 2" in result
    
    def test_format_no_contexts(self):
        """Test formatting with no contexts."""
        mock_session = MagicMock(spec=Session)
        result = format_context_blocks([], mock_session)
        
        assert result == "(No context available)"
    
    def test_format_work_not_found(self):
        """Test formatting when work not found in database."""
        contexts = [
            {
                "work_id": 999,
                "content": "Title\nContent",
                "start_line": 10,
                "end_line": 15,
                "score": 0.9
            }
        ]
        
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = format_context_blocks(contexts, mock_session)
        
        assert "Unknown Work (id=999)" in result
    
    def test_format_strips_whitespace(self):
        """Test that content is properly stripped of whitespace."""
        contexts = [
            {
                "work_id": 1,
                "content": "Title\n\n\n  Content with spaces  \n\n\n",
                "start_line": 10,
                "end_line": 15,
                "score": 0.9
            }
        ]
        
        mock_work = Mock(spec=Work)
        mock_work.title = "Book"
        
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work
        
        result = format_context_blocks(contexts, mock_session)
        
        # Should not have excessive newlines
        assert "\n\n\nContent with spaces" not in result
        assert "Content with spaces" in result


class TestGenerateAugmentedPrompt:
    """Tests for generate_augmented_prompt function."""
    
    @patch('vulcanlab.augmentation.augment.get_session')
    @patch('vulcanlab.augmentation.augment.get_query_with_context')
    @patch('vulcanlab.augmentation.augment.format_context_blocks')
    def test_generate_prompt_with_all_fields(self, mock_format, mock_get_query, mock_get_session):
        """Test prompt generation with all query fields populated."""
        # Setup mock query
        mock_query = Mock(spec=Query)
        mock_query.original_query = "What is cognitive dissonance?"
        mock_query.intent = "DEFINITION"
        mock_query.entities = ["cognitive dissonance", "Leon Festinger"]
        
        mock_contexts = [{"work_id": 1, "content": "Test", "score": 0.9}]
        
        mock_get_query.return_value = (mock_query, mock_contexts)
        mock_format.return_value = "[S1] Test context"
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        result = generate_augmented_prompt(1, top_n=5)
        
        # Check that prompt contains expected elements
        assert "You are an academic assistant" in result
        assert "What is cognitive dissonance?" in result
        assert "DEFINITION" in result
        assert "cognitive dissonance, Leon Festinger" in result
        assert "[S1] Test context" in result
        assert "HYBRID EVIDENCE POLICY" in result
        assert "CITATION RULES" in result
    
    @patch('vulcanlab.augmentation.augment.get_session')
    @patch('vulcanlab.augmentation.augment.get_query_with_context')
    @patch('vulcanlab.augmentation.augment.format_context_blocks')
    def test_generate_prompt_with_missing_intent(self, mock_format, mock_get_query, mock_get_session):
        """Test prompt generation when intent is None."""
        mock_query = Mock(spec=Query)
        mock_query.original_query = "Test question"
        mock_query.intent = None
        mock_query.entities = []
        
        mock_get_query.return_value = (mock_query, [])
        mock_format.return_value = "(No context available)"
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        result = generate_augmented_prompt(1)
        
        assert "GENERAL" in result
        assert "None specified" in result
    
    @patch('vulcanlab.augmentation.augment.get_session')
    @patch('vulcanlab.augmentation.augment.get_query_with_context')
    @patch('vulcanlab.augmentation.augment.format_context_blocks')
    def test_generate_prompt_with_empty_entities(self, mock_format, mock_get_query, mock_get_session):
        """Test prompt generation when entities is empty list."""
        mock_query = Mock(spec=Query)
        mock_query.original_query = "Test question"
        mock_query.intent = "MECHANISM"
        mock_query.entities = []
        
        mock_get_query.return_value = (mock_query, [])
        mock_format.return_value = "(No context available)"
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        result = generate_augmented_prompt(1)
        
        assert "None specified" in result
    
    @patch('vulcanlab.augmentation.augment.get_query_with_context')
    def test_generate_prompt_query_not_found(self, mock_get_query):
        """Test that ValueError is raised when query not found."""
        mock_get_query.side_effect = ValueError("Query with id=999 not found")
        
        with pytest.raises(ValueError, match="Query with id=999 not found"):
            generate_augmented_prompt(999)
    
    @patch('vulcanlab.augmentation.augment.get_session')
    @patch('vulcanlab.augmentation.augment.get_query_with_context')
    @patch('vulcanlab.augmentation.augment.format_context_blocks')
    def test_generate_prompt_structure(self, mock_format, mock_get_query, mock_get_session):
        """Test that the prompt has all required structural sections."""
        mock_query = Mock(spec=Query)
        mock_query.original_query = "Test"
        mock_query.intent = "DEFINITION"
        mock_query.entities = ["test"]
        
        mock_get_query.return_value = (mock_query, [])
        mock_format.return_value = "Test context"
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        result = generate_augmented_prompt(1)
        
        # Check for all major sections
        assert "Your job is to:" in result
        assert "HYBRID EVIDENCE POLICY" in result
        assert "CITATION RULES" in result
        assert "STRUCTURE YOUR ANSWER AS FOLLOWS" in result
        assert "INTENT AND ENTITIES" in result
        assert "TONE AND STYLE" in result
        assert "CONTEXT (RETRIEVED SOURCE PASSAGES)" in result
        assert "USER QUESTION" in result
        assert "Test" in result  # The actual question





class TestAugmentationLogging:
    """Tests for logging functionality in augmentation."""

    @patch('vulcanlab.augmentation.augment.load_config')
    @patch('vulcanlab.augmentation.augment._save_augmentation_log')
    @patch('vulcanlab.augmentation.augment.get_session')
    @patch('vulcanlab.augmentation.augment.get_query_with_context')
    @patch('vulcanlab.augmentation.augment.format_context_blocks')
    def test_generate_prompt_logging_enabled(
        self, mock_format, mock_get_query, mock_get_session, mock_save_log, mock_load_config
    ):
        """Test that logging is called when enabled in config."""
        # Setup config
        mock_config = AppConfig(logging=LoggingConfig(enabled=True))
        mock_load_config.return_value = mock_config

        # Setup mocks
        mock_query = Mock(spec=Query)
        mock_query.original_query = "Test"
        mock_query.intent = "GENERAL"
        mock_query.entities = []
        mock_get_query.return_value = (mock_query, [])
        mock_format.return_value = "Context"
        mock_get_session.return_value.__enter__.return_value = MagicMock()

        generate_augmented_prompt(1)

        mock_save_log.assert_called_once()
        args = mock_save_log.call_args[0]
        assert args[0] == 1  # query_id
        assert "final_prompt" in args[1]

    @patch('vulcanlab.augmentation.augment.load_config')
    @patch('vulcanlab.augmentation.augment._save_augmentation_log')
    @patch('vulcanlab.augmentation.augment.get_session')
    @patch('vulcanlab.augmentation.augment.get_query_with_context')
    @patch('vulcanlab.augmentation.augment.format_context_blocks')
    def test_generate_prompt_logging_disabled(
        self, mock_format, mock_get_query, mock_get_session, mock_save_log, mock_load_config
    ):
        """Test that logging is NOT called when disabled."""
        # Setup config
        mock_config = AppConfig(logging=LoggingConfig(enabled=False))
        mock_load_config.return_value = mock_config

        # Setup mocks
        mock_query = Mock(spec=Query)
        mock_query.original_query = "Test"
        mock_query.intent = "GENERAL"
        mock_query.entities = []
        mock_get_query.return_value = (mock_query, [])
        mock_format.return_value = "Context"
        mock_get_session.return_value.__enter__.return_value = MagicMock()

        generate_augmented_prompt(1)

        mock_save_log.assert_not_called()


