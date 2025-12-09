"""
Unit tests for query_expansion module.

Tests query expansion logic, prompt generation, response parsing, database saving,
and the full expansion pipeline with mocked LLM calls.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from vulcanlab.retrieval.query_expansion import (
    expand_query,
    generate_expansion_prompt,
    parse_expansion_response,
    save_expansion_to_db,
    QueryExpansionResult,
    ParsedExpansion
)
from vulcanlab.data.models.query import Query
from tests.unit.mock_helpers import mock_session, create_mock_query_chain


class TestParsedExpansion:
    """Test ParsedExpansion dataclass."""

    def test_parsed_expansion_creation(self):
        """Test creating a ParsedExpansion instance."""
        parsed = ParsedExpansion(
            expanded_queries=["query1", "query2"],
            hyde_answer="Test answer",
            intent="DEFINITION",
            entities=["entity1", "entity2"]
        )

        assert parsed.expanded_queries == ["query1", "query2"]
        assert parsed.hyde_answer == "Test answer"
        assert parsed.intent == "DEFINITION"
        assert parsed.entities == ["entity1", "entity2"]

    def test_parsed_expansion_empty_fields(self):
        """Test ParsedExpansion with empty fields."""
        parsed = ParsedExpansion(
            expanded_queries=[],
            hyde_answer="",
            intent="",
            entities=[]
        )

        assert parsed.expanded_queries == []
        assert parsed.hyde_answer == ""
        assert parsed.intent == ""
        assert parsed.entities == []


class TestQueryExpansionResult:
    """Test QueryExpansionResult dataclass."""

    def test_query_expansion_result_creation(self):
        """Test creating a QueryExpansionResult instance."""
        result = QueryExpansionResult(
            query_id=1,
            original_query="What is psychology?",
            expanded_queries=["query1", "query2"],
            hyde_answer="Test answer",
            intent="DEFINITION",
            entities=["entity1"]
        )

        assert result.query_id == 1
        assert result.original_query == "What is psychology?"
        assert result.expanded_queries == ["query1", "query2"]
        assert result.hyde_answer == "Test answer"
        assert result.intent == "DEFINITION"
        assert result.entities == ["entity1"]


class TestGenerateExpansionPrompt:
    """Test generate_expansion_prompt function."""

    def test_generate_expansion_prompt_basic(self):
        """Test basic prompt generation."""
        query = "What is working memory?"
        n = 3

        prompt = generate_expansion_prompt(query, n)

        assert isinstance(prompt, str)
        assert query in prompt
        assert str(n) in prompt
        assert "query expansion" in prompt.lower() or "expansion" in prompt.lower()

    def test_generate_expansion_prompt_different_n(self):
        """Test prompt generation with different n values."""
        query = "What is psychology?"

        prompt_n3 = generate_expansion_prompt(query, n=3)
        prompt_n5 = generate_expansion_prompt(query, n=5)

        assert "3" in prompt_n3
        assert "5" in prompt_n5
        assert query in prompt_n3
        assert query in prompt_n5

    def test_generate_expansion_prompt_template_formatting(self):
        """Test that prompt template is properly formatted."""
        query = "Test query"
        n = 2

        prompt = generate_expansion_prompt(query, n)

        # Should contain the query
        assert query in prompt
        # Should contain instructions for n queries
        assert "2" in prompt or "two" in prompt.lower()
        # Should contain JSON structure hints
        assert "queries" in prompt.lower() or "json" in prompt.lower()

    @patch('vulcanlab.retrieval.query_expansion.load_template')
    def test_generate_expansion_prompt_uses_template_loader(self, mock_load_template):
        """Test that prompt generation uses template loader."""
        mock_template = Mock()
        mock_template.format.return_value = "formatted prompt"
        mock_load_template.return_value = mock_template

        result = generate_expansion_prompt("test query", n=3)

        mock_load_template.assert_called_once()
        assert mock_load_template.call_args[0][0] == "query_expansion"
        mock_template.format.assert_called_once_with(query="test query", n=3)
        assert result == "formatted prompt"


class TestParseExpansionResponse:
    """Test parse_expansion_response function."""

    def test_parse_expansion_response_valid_json(self):
        """Test parsing a valid JSON response."""
        response_json = {
            "queries": ["query1", "query2", "query3"],
            "hyde_answer": "This is a hypothetical answer.",
            "intent": "DEFINITION",
            "entities": ["entity1", "entity2"]
        }
        response_text = json.dumps(response_json)

        parsed = parse_expansion_response(response_text)

        assert isinstance(parsed, ParsedExpansion)
        assert parsed.expanded_queries == ["query1", "query2", "query3"]
        assert parsed.hyde_answer == "This is a hypothetical answer."
        assert parsed.intent == "DEFINITION"
        assert parsed.entities == ["entity1", "entity2"]

    def test_parse_expansion_response_json_code_block(self):
        """Test parsing JSON wrapped in markdown code block."""
        response_json = {
            "queries": ["query1"],
            "hyde_answer": "Answer",
            "intent": "MECHANISM",
            "entities": ["entity1"]
        }
        response_text = f"```json\n{json.dumps(response_json)}\n```"

        parsed = parse_expansion_response(response_text)

        assert parsed.expanded_queries == ["query1"]
        assert parsed.hyde_answer == "Answer"
        assert parsed.intent == "MECHANISM"
        assert parsed.entities == ["entity1"]

    def test_parse_expansion_response_generic_code_block(self):
        """Test parsing JSON wrapped in generic markdown code block."""
        response_json = {
            "queries": ["query1"],
            "hyde_answer": "Answer",
            "intent": "COMPARISON",
            "entities": []
        }
        response_text = f"```\n{json.dumps(response_json)}\n```"

        parsed = parse_expansion_response(response_text)

        assert parsed.expanded_queries == ["query1"]
        assert parsed.hyde_answer == "Answer"
        assert parsed.intent == "COMPARISON"

    def test_parse_expansion_response_empty_fields(self):
        """Test parsing response with empty fields."""
        response_json = {
            "queries": [],
            "hyde_answer": "",
            "intent": "",
            "entities": []
        }
        response_text = json.dumps(response_json)

        parsed = parse_expansion_response(response_text)

        assert parsed.expanded_queries == []
        assert parsed.hyde_answer == ""
        assert parsed.intent == ""
        assert parsed.entities == []

    def test_parse_expansion_response_missing_fields(self):
        """Test parsing response with missing fields uses defaults."""
        response_json = {}
        response_text = json.dumps(response_json)

        parsed = parse_expansion_response(response_text)

        assert parsed.expanded_queries == []
        assert parsed.hyde_answer == ""
        assert parsed.intent == ""
        assert parsed.entities == []

    def test_parse_expansion_response_partial_fields(self):
        """Test parsing response with only some fields."""
        response_json = {
            "queries": ["query1"],
            "intent": "APPLICATION"
        }
        response_text = json.dumps(response_json)

        parsed = parse_expansion_response(response_text)

        assert parsed.expanded_queries == ["query1"]
        assert parsed.intent == "APPLICATION"
        assert parsed.hyde_answer == ""
        assert parsed.entities == []

    def test_parse_expansion_response_invalid_json(self):
        """Test parsing invalid JSON raises ValueError."""
        response_text = "This is not valid JSON {"

        with pytest.raises(ValueError) as exc_info:
            parse_expansion_response(response_text)

        assert "Failed to parse LLM response as JSON" in str(exc_info.value)
        assert response_text in str(exc_info.value)

    def test_parse_expansion_response_malformed_json(self):
        """Test parsing malformed JSON raises ValueError."""
        response_text = '{"queries": [invalid json]}'

        with pytest.raises(ValueError) as exc_info:
            parse_expansion_response(response_text)

        assert "Failed to parse LLM response as JSON" in str(exc_info.value)

    def test_parse_expansion_response_with_extra_text(self):
        """Test parsing JSON with extra text before/after (should fail)."""
        response_json = {
            "queries": ["query1"],
            "hyde_answer": "Answer",
            "intent": "DEFINITION",
            "entities": []
        }
        # Extra text before JSON (not in code block)
        response_text = f"Here's the response:\n{json.dumps(response_json)}"

        # Should fail because JSON is not at the start and not in a code block
        with pytest.raises(ValueError) as exc_info:
            parse_expansion_response(response_text)

        assert "Failed to parse LLM response as JSON" in str(exc_info.value)


class TestSaveExpansionToDb:
    """Test save_expansion_to_db function."""

    @patch('vulcanlab.retrieval.query_expansion.get_session')
    def test_save_expansion_to_db_basic(self, mock_get_session, mock_session):
        """Test saving expansion data to database."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        parsed = ParsedExpansion(
            expanded_queries=["query1", "query2", "query3"],
            hyde_answer="This is a hypothetical answer.",
            intent="DEFINITION",
            entities=["entity1", "entity2"]
        )

        # Track the Query object that gets created
        saved_query_obj = None
        def capture_add(obj):
            nonlocal saved_query_obj
            saved_query_obj = obj
            # Set an id when the object is added
            if isinstance(obj, Query):
                obj.id = 123  # Mock ID

        mock_session.add.side_effect = capture_add

        query_id = save_expansion_to_db("What is psychology?", parsed)

        assert query_id is not None
        assert isinstance(query_id, int)
        assert query_id == 123

        # Verify query was saved
        mock_query_chain = create_mock_query_chain(return_first=saved_query_obj)
        mock_session.query.return_value = mock_query_chain
        saved_query = mock_session.query(Query).filter(Query.id == query_id).first()
        
        assert saved_query is not None
        assert saved_query.original_query == "What is psychology?"
        assert saved_query.expanded_queries == ["query1", "query2", "query3"]
        assert saved_query.hyde_answer == "This is a hypothetical answer."
        assert saved_query.intent == "DEFINITION"
        assert saved_query.entities == ["entity1", "entity2"]
        assert saved_query.vector_status == "to_vec"

    @patch('vulcanlab.retrieval.query_expansion.get_session')
    def test_save_expansion_to_db_empty_fields(self, mock_get_session, mock_session):
        """Test saving expansion with empty fields."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        parsed = ParsedExpansion(
            expanded_queries=[],
            hyde_answer="",
            intent="",
            entities=[]
        )

        # Track the Query object that gets created
        saved_query_obj = None
        def capture_add(obj):
            nonlocal saved_query_obj
            saved_query_obj = obj
            # Set an id when the object is added
            if isinstance(obj, Query):
                obj.id = 456  # Mock ID

        mock_session.add.side_effect = capture_add

        query_id = save_expansion_to_db("Test query", parsed)

        # Verify query was saved
        mock_query_chain = create_mock_query_chain(return_first=saved_query_obj)
        mock_session.query.return_value = mock_query_chain
        saved_query = mock_session.query(Query).filter(Query.id == query_id).first()
        
        assert saved_query.original_query == "Test query"
        assert saved_query.expanded_queries == []
        assert saved_query.hyde_answer == ""
        assert saved_query.intent == ""
        assert saved_query.entities == []

    @patch('vulcanlab.retrieval.query_expansion.get_session')
    def test_save_expansion_to_db_returns_id(self, mock_get_session, mock_session):
        """Test that save_expansion_to_db returns the query ID."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        parsed = ParsedExpansion(
            expanded_queries=["q1"],
            hyde_answer="answer",
            intent="MECHANISM",
            entities=["e1"]
        )

        # Track the Query object that gets created
        saved_query_obj = None
        def capture_add(obj):
            nonlocal saved_query_obj
            saved_query_obj = obj
            # Set an id when the object is added
            if isinstance(obj, Query):
                obj.id = 789  # Mock ID

        mock_session.add.side_effect = capture_add

        query_id = save_expansion_to_db("Query", parsed)

        # Verify ID matches database record
        mock_query_chain = create_mock_query_chain(return_first=saved_query_obj)
        mock_session.query.return_value = mock_query_chain
        saved_query = mock_session.query(Query).filter(Query.id == query_id).first()
        assert saved_query.id == query_id


class TestExpandQuery:
    """Test expand_query function (full pipeline)."""

    @pytest.fixture
    def mock_langchain_response(self):
        """Create a mock LangChain response."""
        response = Mock()
        response.content = json.dumps({
            "queries": [
                "working memory definition",
                "what is working memory capacity",
                "working memory psychology concept"
            ],
            "hyde_answer": "Working memory is a cognitive system responsible for temporarily holding and manipulating information. It is essential for complex cognitive tasks such as reasoning, comprehension, and learning.",
            "intent": "DEFINITION",
            "entities": ["working memory", "cognitive system"]
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

    @patch('vulcanlab.retrieval.query_expansion.save_expansion_to_db')
    @patch('vulcanlab.retrieval.query_expansion.parse_expansion_response')
    @patch('vulcanlab.retrieval.query_expansion.generate_expansion_prompt')
    @patch('vulcanlab.ai.llm_factory.create_langchain_chat')
    def test_expand_query_basic(
        self,
        mock_create_chat,
        mock_generate_prompt,
        mock_parse_response,
        mock_save_db,
        mock_langchain_stack,
        mock_chat,
        mock_langchain_response
    ):
        """Test basic query expansion."""
        mock_create_chat.return_value = mock_langchain_stack
        mock_generate_prompt.return_value = "Test prompt"
        mock_parse_response.return_value = ParsedExpansion(
            expanded_queries=["q1", "q2"],
            hyde_answer="answer",
            intent="DEFINITION",
            entities=["e1"]
        )
        mock_save_db.return_value = 123

        result = expand_query("What is working memory?", n=3)

        assert isinstance(result, QueryExpansionResult)
        assert result.query_id == 123
        assert result.original_query == "What is working memory?"
        assert result.expanded_queries == ["q1", "q2"]
        assert result.hyde_answer == "answer"
        assert result.intent == "DEFINITION"
        assert result.entities == ["e1"]

        # Verify function calls (n is passed as positional argument)
        mock_generate_prompt.assert_called_once_with("What is working memory?", 3)
        mock_create_chat.assert_called_once()
        mock_chat.invoke.assert_called_once_with("Test prompt")
        mock_parse_response.assert_called_once_with(mock_langchain_response.content)
        mock_save_db.assert_called_once()

    @patch('vulcanlab.retrieval.query_expansion.save_expansion_to_db')
    @patch('vulcanlab.retrieval.query_expansion.parse_expansion_response')
    @patch('vulcanlab.retrieval.query_expansion.generate_expansion_prompt')
    @patch('vulcanlab.ai.llm_factory.create_langchain_chat')
    def test_expand_query_verbose(
        self,
        mock_create_chat,
        mock_generate_prompt,
        mock_parse_response,
        mock_save_db,
        mock_langchain_stack,
        mock_chat,
        mock_langchain_response,
        capsys
    ):
        """Test query expansion with verbose output."""
        mock_create_chat.return_value = mock_langchain_stack
        mock_generate_prompt.return_value = "Test prompt"
        mock_parse_response.return_value = ParsedExpansion(
            expanded_queries=["q1", "q2", "q3"],
            hyde_answer="answer",
            intent="MECHANISM",
            entities=["e1", "e2"]
        )
        mock_save_db.return_value = 456

        result = expand_query("Test query", n=3, verbose=True)

        assert result.query_id == 456

        # Check verbose output
        captured = capsys.readouterr()
        assert "Expanding query" in captured.out
        assert "Test query" in captured.out
        assert "Generating 3 alternative queries" in captured.out
        assert "Calling LLM" in captured.out
        assert "Generated 3 alternative queries" in captured.out
        assert "Intent: MECHANISM" in captured.out
        assert "Entities: 2" in captured.out
        assert "Saved to database" in captured.out
        assert "456" in captured.out

    @patch('vulcanlab.retrieval.query_expansion.save_expansion_to_db')
    @patch('vulcanlab.retrieval.query_expansion.parse_expansion_response')
    @patch('vulcanlab.retrieval.query_expansion.generate_expansion_prompt')
    @patch('vulcanlab.ai.llm_factory.create_langchain_chat')
    def test_expand_query_different_n(
        self,
        mock_create_chat,
        mock_generate_prompt,
        mock_parse_response,
        mock_save_db,
        mock_langchain_stack,
        mock_chat,
        mock_langchain_response
    ):
        """Test query expansion with different n values."""
        mock_create_chat.return_value = mock_langchain_stack
        mock_generate_prompt.return_value = "Test prompt"
        mock_parse_response.return_value = ParsedExpansion(
            expanded_queries=["q1"],
            hyde_answer="answer",
            intent="DEFINITION",
            entities=[]
        )
        mock_save_db.return_value = 789

        result = expand_query("Query", n=5)

        # Verify n is passed as positional argument
        mock_generate_prompt.assert_called_once_with("Query", 5)
        assert result.query_id == 789

    @patch('vulcanlab.retrieval.query_expansion.save_expansion_to_db')
    @patch('vulcanlab.retrieval.query_expansion.parse_expansion_response')
    @patch('vulcanlab.retrieval.query_expansion.generate_expansion_prompt')
    @patch('vulcanlab.ai.llm_factory.create_langchain_chat')
    def test_expand_query_parse_error(
        self,
        mock_create_chat,
        mock_generate_prompt,
        mock_parse_response,
        mock_save_db,
        mock_langchain_stack,
        mock_chat,
        mock_langchain_response
    ):
        """Test query expansion when parsing fails."""
        mock_create_chat.return_value = mock_langchain_stack
        mock_generate_prompt.return_value = "Test prompt"
        mock_parse_response.side_effect = ValueError("Invalid JSON")

        with pytest.raises(ValueError) as exc_info:
            expand_query("Query", n=3)

        assert "Invalid JSON" in str(exc_info.value)
        mock_save_db.assert_not_called()

    @patch('vulcanlab.retrieval.query_expansion.save_expansion_to_db')
    @patch('vulcanlab.retrieval.query_expansion.parse_expansion_response')
    @patch('vulcanlab.retrieval.query_expansion.generate_expansion_prompt')
    @patch('vulcanlab.ai.llm_factory.create_langchain_chat')
    def test_expand_query_uses_full_model_tier(
        self,
        mock_create_chat,
        mock_generate_prompt,
        mock_parse_response,
        mock_save_db,
        mock_langchain_stack,
        mock_chat,
        mock_langchain_response
    ):
        """Test that expand_query uses FULL model tier."""
        from vulcanlab.ai.config import ModelTier

        mock_create_chat.return_value = mock_langchain_stack
        mock_generate_prompt.return_value = "Test prompt"
        mock_parse_response.return_value = ParsedExpansion(
            expanded_queries=["q1"],
            hyde_answer="answer",
            intent="DEFINITION",
            entities=[]
        )
        mock_save_db.return_value = 999

        expand_query("Query", n=3)

        # Verify ModelTier.FULL is used
        mock_create_chat.assert_called_once_with(tier=ModelTier.FULL)

    @patch('vulcanlab.retrieval.query_expansion.save_expansion_to_db')
    @patch('vulcanlab.retrieval.query_expansion.parse_expansion_response')
    @patch('vulcanlab.retrieval.query_expansion.generate_expansion_prompt')
    @patch('vulcanlab.ai.llm_factory.create_langchain_chat')
    def test_expand_query_no_verbose_output(
        self,
        mock_create_chat,
        mock_generate_prompt,
        mock_parse_response,
        mock_save_db,
        mock_langchain_stack,
        mock_chat,
        mock_langchain_response,
        capsys
    ):
        """Test that verbose=False produces no output."""
        mock_create_chat.return_value = mock_langchain_stack
        mock_generate_prompt.return_value = "Test prompt"
        mock_parse_response.return_value = ParsedExpansion(
            expanded_queries=["q1"],
            hyde_answer="answer",
            intent="DEFINITION",
            entities=[]
        )
        mock_save_db.return_value = 111

        result = expand_query("Query", n=3, verbose=False)

        assert result.query_id == 111

        # Check no verbose output
        captured = capsys.readouterr()
        assert captured.out == ""

