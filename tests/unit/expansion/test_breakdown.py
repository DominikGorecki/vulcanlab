"""
Unit tests for the breakdown module.

Tests token validation, breakdown parsing, and the breakdown_answer function.

Usage:
    pytest tests/unit/expansion/test_breakdown.py -v
"""

import pytest
from unittest.mock import MagicMock, patch

from vulcanlab.expansion.breakdown import (
    estimate_answer_tokens,
    validate_answer_length,
    parse_breakdown_response,
    breakdown_answer,
    SectionBreakdown,
    BreakdownResponseSchema,
    DEFAULT_MAX_TOKENS,
)
from vulcanlab.data.models.expansion import (
    AnswerExpansion,
    ExpansionSection,
    ExpansionMode,
    ExpansionStatus,
    SectionStatus,
)


class TestEstimateAnswerTokens:
    """Tests for estimate_answer_tokens function."""

    def test_empty_string(self):
        """Test that empty string returns 0 tokens."""
        assert estimate_answer_tokens("") == 0

    def test_none_returns_zero(self):
        """Test that None returns 0 tokens."""
        assert estimate_answer_tokens(None) == 0

    def test_single_word(self):
        """Test single word estimation."""
        result = estimate_answer_tokens("hello")
        # 1 word * 1.3 = 1.3, int = 1
        assert result == 1

    def test_multiple_words(self):
        """Test multiple words estimation."""
        text = "This is a test sentence with seven words"
        result = estimate_answer_tokens(text)
        # 8 words * 1.3 = 10.4, int = 10
        assert result == 10

    def test_large_text(self):
        """Test large text estimation."""
        words = ["word"] * 1000
        text = " ".join(words)
        result = estimate_answer_tokens(text)
        # 1000 words * 1.3 = 1300
        assert result == 1300


class TestValidateAnswerLength:
    """Tests for validate_answer_length function."""

    def test_under_limit_passes(self):
        """Test that text under the limit passes validation."""
        text = "This is a short answer that should pass."
        # Should not raise
        validate_answer_length(text, max_tokens=30000)

    def test_over_limit_raises(self):
        """Test that text over the limit raises ValueError."""
        # Create text with ~31000 tokens
        words = ["word"] * 24000  # 24000 * 1.3 = 31200 tokens
        text = " ".join(words)

        with pytest.raises(ValueError) as exc_info:
            validate_answer_length(text, max_tokens=30000)

        assert "exceeds token limit" in str(exc_info.value)
        assert "31,200" in str(exc_info.value)  # Estimated tokens
        assert "30,000" in str(exc_info.value)  # Max allowed

    def test_exactly_at_limit_passes(self):
        """Test that text exactly at limit passes."""
        # Create text with exactly 30000 tokens
        words = ["word"] * 23077  # 23077 * 1.3 = 30000.1, int = 30000
        text = " ".join(words)

        # Should not raise
        validate_answer_length(text, max_tokens=30000)

    def test_custom_limit(self):
        """Test validation with custom token limit."""
        text = "Short text"

        # Should pass with higher limit
        validate_answer_length(text, max_tokens=100)

        # Should fail with very low limit
        with pytest.raises(ValueError):
            validate_answer_length(text, max_tokens=1)


class TestParseBreakdownResponse:
    """Tests for parse_breakdown_response function."""

    def test_parse_pydantic_response(self):
        """Test parsing a Pydantic BreakdownResponseSchema."""
        response = BreakdownResponseSchema(
            sections=[
                {
                    "heading": "Section 1",
                    "summary": "Summary 1",
                    "expansion_prompt": "Prompt 1"
                },
                {
                    "heading": "Section 2",
                    "summary": "Summary 2",
                    "expansion_prompt": "Prompt 2"
                },
                {
                    "heading": "Section 3",
                    "summary": "Summary 3",
                    "expansion_prompt": "Prompt 3"
                }
            ]
        )

        sections = parse_breakdown_response(response)

        assert len(sections) == 3
        assert sections[0].order == 1
        assert sections[0].heading == "Section 1"
        assert sections[0].summary == "Summary 1"
        assert sections[0].expansion_prompt == "Prompt 1"

    def test_parse_json_string(self):
        """Test parsing a JSON string response."""
        response = '''
        {
            "sections": [
                {
                    "heading": "Test Heading",
                    "summary": "Test Summary",
                    "expansion_prompt": "Test Prompt"
                },
                {
                    "heading": "Another Heading",
                    "summary": "Another Summary",
                    "expansion_prompt": "Another Prompt"
                },
                {
                    "heading": "Third Heading",
                    "summary": "Third Summary",
                    "expansion_prompt": "Third Prompt"
                }
            ]
        }
        '''

        sections = parse_breakdown_response(response)

        assert len(sections) == 3
        assert sections[0].heading == "Test Heading"

    def test_parse_json_with_code_block(self):
        """Test parsing JSON wrapped in markdown code block."""
        response = '''
        Some preamble text.
        ```json
        {
            "sections": [
                {
                    "heading": "Section A",
                    "summary": "Summary A",
                    "expansion_prompt": "Prompt A"
                },
                {
                    "heading": "Section B",
                    "summary": "Summary B",
                    "expansion_prompt": "Prompt B"
                },
                {
                    "heading": "Section C",
                    "summary": "Summary C",
                    "expansion_prompt": "Prompt C"
                }
            ]
        }
        ```
        Some trailing text.
        '''

        sections = parse_breakdown_response(response)

        assert len(sections) == 3
        assert sections[0].heading == "Section A"

    def test_parse_too_few_sections_raises(self):
        """Test that fewer than 3 sections raises ValueError."""
        response = '''
        {
            "sections": [
                {
                    "heading": "Only One",
                    "summary": "Summary",
                    "expansion_prompt": "Prompt"
                },
                {
                    "heading": "Only Two",
                    "summary": "Summary",
                    "expansion_prompt": "Prompt"
                }
            ]
        }
        '''

        with pytest.raises(ValueError) as exc_info:
            parse_breakdown_response(response)

        assert "minimum is 3" in str(exc_info.value)

    def test_parse_too_many_sections_truncates(self):
        """Test that more than 7 sections are truncated."""
        import json
        sections_data = [
            {
                "heading": f"Section {i}",
                "summary": f"Summary {i}",
                "expansion_prompt": f"Prompt {i}"
            }
            for i in range(1, 11)  # 10 sections
        ]
        response = json.dumps({"sections": sections_data})

        sections = parse_breakdown_response(response)

        # Should truncate to 7
        assert len(sections) == 7
        assert sections[6].heading == "Section 7"

    def test_parse_empty_sections_raises(self):
        """Test that empty sections list raises ValueError."""
        response = '{"sections": []}'

        with pytest.raises(ValueError) as exc_info:
            parse_breakdown_response(response)

        assert "no sections" in str(exc_info.value)

    def test_parse_missing_heading_raises(self):
        """Test that missing heading raises ValueError."""
        response = '''
        {
            "sections": [
                {
                    "summary": "Summary",
                    "expansion_prompt": "Prompt"
                },
                {
                    "heading": "Valid",
                    "summary": "Summary",
                    "expansion_prompt": "Prompt"
                },
                {
                    "heading": "Valid",
                    "summary": "Summary",
                    "expansion_prompt": "Prompt"
                }
            ]
        }
        '''

        with pytest.raises(ValueError) as exc_info:
            parse_breakdown_response(response)

        assert "missing required fields" in str(exc_info.value)

    def test_parse_missing_prompt_raises(self):
        """Test that missing expansion_prompt raises ValueError."""
        response = '''
        {
            "sections": [
                {
                    "heading": "Test",
                    "summary": "Summary"
                },
                {
                    "heading": "Valid",
                    "summary": "Summary",
                    "expansion_prompt": "Prompt"
                },
                {
                    "heading": "Valid",
                    "summary": "Summary",
                    "expansion_prompt": "Prompt"
                }
            ]
        }
        '''

        with pytest.raises(ValueError) as exc_info:
            parse_breakdown_response(response)

        assert "missing required fields" in str(exc_info.value)

    def test_parse_invalid_json_raises(self):
        """Test that invalid JSON raises ValueError."""
        response = "This is not JSON"

        with pytest.raises(ValueError) as exc_info:
            parse_breakdown_response(response)

        assert "Failed to parse" in str(exc_info.value)


class TestBreakdownAnswer:
    """Tests for breakdown_answer function."""

    @patch('vulcanlab.expansion.breakdown.get_active_template')
    def test_breakdown_creates_expansion_and_sections(self, mock_template):
        """Test that breakdown_answer creates expansion and section records."""
        mock_template.return_value = "Template: {answer_text}"

        # Create mock session
        mock_session = MagicMock()

        # Create mock result
        mock_result = MagicMock()
        mock_result.id = 1
        mock_result.query_id = 10
        mock_result.response_text = "This is the answer text to break down."

        # Mock query to return the result
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_result,  # First call: Result lookup
            None,  # Second call: Check existing expansion
        ]

        # Create mock LLM client
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured

        # Mock LLM response
        mock_structured.invoke.return_value = BreakdownResponseSchema(
            sections=[
                {"heading": "Section 1", "summary": "Summary 1", "expansion_prompt": "Prompt 1"},
                {"heading": "Section 2", "summary": "Summary 2", "expansion_prompt": "Prompt 2"},
                {"heading": "Section 3", "summary": "Summary 3", "expansion_prompt": "Prompt 3"},
            ]
        )

        # Mock flush to set expansion ID
        def mock_flush():
            for call in mock_session.add.call_args_list:
                obj = call[0][0]
                if isinstance(obj, AnswerExpansion):
                    obj.id = 100
        mock_session.flush.side_effect = mock_flush

        # Call the function
        expansion_id = breakdown_answer(
            result_id=1,
            session=mock_session,
            llm_client=mock_llm,
            mode=ExpansionMode.AUTOMATIC
        )

        # Verify expansion was created
        assert expansion_id == 100

        # Verify session.add was called for expansion and sections
        add_calls = mock_session.add.call_args_list
        assert len(add_calls) == 4  # 1 expansion + 3 sections

        # Check expansion properties
        expansion_arg = add_calls[0][0][0]
        assert isinstance(expansion_arg, AnswerExpansion)
        assert expansion_arg.result_id == 1
        assert expansion_arg.query_id == 10
        assert expansion_arg.mode == ExpansionMode.AUTOMATIC
        assert expansion_arg.status == ExpansionStatus.BREAKDOWN_COMPLETE

        # Check sections were added
        for i in range(1, 4):
            section_arg = add_calls[i][0][0]
            assert isinstance(section_arg, ExpansionSection)
            assert section_arg.expansion_id == 100
            assert section_arg.order == i
            assert section_arg.status == SectionStatus.PENDING

    @patch('vulcanlab.expansion.breakdown.get_active_template')
    def test_breakdown_rejects_oversized_answer(self, mock_template):
        """Test that breakdown_answer rejects answers exceeding token limit."""
        mock_template.return_value = "Template: {answer_text}"

        mock_session = MagicMock()

        # Create result with very long text
        mock_result = MagicMock()
        mock_result.id = 1
        mock_result.query_id = 10
        mock_result.response_text = " ".join(["word"] * 30000)  # ~39000 tokens

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_result,
            None,  # No existing expansion
        ]

        mock_llm = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            breakdown_answer(
                result_id=1,
                session=mock_session,
                llm_client=mock_llm
            )

        assert "exceeds token limit" in str(exc_info.value)

    def test_breakdown_result_not_found_raises(self):
        """Test that breakdown_answer raises if result not found."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        mock_llm = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            breakdown_answer(
                result_id=999,
                session=mock_session,
                llm_client=mock_llm
            )

        assert "not found" in str(exc_info.value)

    @patch('vulcanlab.expansion.breakdown.get_active_template')
    def test_breakdown_existing_expansion_raises(self, mock_template):
        """Test that breakdown_answer raises if expansion already exists."""
        mock_template.return_value = "Template: {answer_text}"

        mock_session = MagicMock()

        mock_result = MagicMock()
        mock_result.id = 1
        mock_result.response_text = "Short answer."

        mock_existing = MagicMock()
        mock_existing.id = 50

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_result,
            mock_existing,  # Existing expansion
        ]

        mock_llm = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            breakdown_answer(
                result_id=1,
                session=mock_session,
                llm_client=mock_llm
            )

        assert "already exists" in str(exc_info.value)

    @patch('vulcanlab.expansion.breakdown.get_active_template')
    def test_breakdown_invalid_json_raises(self, mock_template):
        """Test that breakdown_answer handles malformed LLM response."""
        mock_template.return_value = "Template: {answer_text}"

        mock_session = MagicMock()

        mock_result = MagicMock()
        mock_result.id = 1
        mock_result.query_id = 10
        mock_result.response_text = "Test answer."

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_result,
            None,
        ]

        # Mock LLM that doesn't support structured output
        mock_llm = MagicMock()
        mock_llm.with_structured_output.side_effect = AttributeError()
        mock_llm.invoke.return_value = "Not valid JSON"

        with pytest.raises(ValueError) as exc_info:
            breakdown_answer(
                result_id=1,
                session=mock_session,
                llm_client=mock_llm
            )

        assert "Failed to parse" in str(exc_info.value)
