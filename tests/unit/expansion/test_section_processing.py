"""
Unit tests for the section_processing module.

Tests expand_section, generate_section, and save_manual_response functions.

Usage:
    pytest tests/unit/expansion/test_section_processing.py -v
"""

import pytest
from unittest.mock import MagicMock, patch

from vulcanlab.expansion.section_processing import (
    expand_section,
    generate_section,
    save_manual_response,
    _format_section_context,
)
from vulcanlab.data.models.expansion import (
    ExpansionSection,
    SectionStatus,
)


class TestFormatSectionContext:
    """Tests for _format_section_context helper."""

    def test_empty_context_returns_placeholder(self):
        """Test that empty context returns placeholder text."""
        result = _format_section_context([])
        assert result == "(No context available)"

    def test_single_context_block(self):
        """Test formatting a single context block."""
        context = [
            {
                "work_title": "Test Book",
                "heading_chain": ["Chapter 1", "Section A"],
                "content": "This is the test content.",
                "work_id": 1,
                "start_line": 10,
                "end_line": 20
            }
        ]

        result = _format_section_context(context)

        assert "[S1]" in result
        assert "Test Book > Chapter 1 > Section A" in result
        assert "This is the test content." in result
        assert "work_id=1" in result

    def test_multiple_context_blocks(self):
        """Test formatting multiple context blocks."""
        context = [
            {
                "work_title": "Book A",
                "heading_chain": ["Chapter 1"],
                "content": "Content A",
                "work_id": 1,
                "start_line": 1,
                "end_line": 10
            },
            {
                "work_title": "Book B",
                "heading_chain": ["Chapter 2"],
                "content": "Content B",
                "work_id": 2,
                "start_line": 20,
                "end_line": 30
            }
        ]

        result = _format_section_context(context)

        assert "[S1]" in result
        assert "[S2]" in result
        assert "Book A > Chapter 1" in result
        assert "Book B > Chapter 2" in result

    def test_context_without_heading_chain(self):
        """Test formatting context without heading chain."""
        context = [
            {
                "work_title": "Test Book",
                "heading_chain": [],
                "content": "Content without headings.",
                "work_id": 1,
                "start_line": 1,
                "end_line": 5
            }
        ]

        result = _format_section_context(context)

        assert "[S1]" in result
        assert "Test Book" in result
        # Should not have " > " since no heading chain
        assert "Test Book |" in result or "Test Book\n" in result


class TestExpandSection:
    """Tests for expand_section function."""

    def test_section_not_found_raises(self):
        """Test that expand_section raises if section not found."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            expand_section(section_id=999, session=mock_session)

        assert "not found" in str(exc_info.value)

    @patch('vulcanlab.expansion.section_processing._expand_query_for_section')
    @patch('vulcanlab.expansion.section_processing._generate_embeddings_for_section')
    @patch('vulcanlab.expansion.section_processing._retrieve_for_section')
    @patch('vulcanlab.expansion.section_processing._consolidate_section_context')
    def test_expand_section_updates_status(
        self, mock_consolidate, mock_retrieve, mock_embed, mock_expand
    ):
        """Test that expand_section updates status correctly."""
        mock_session = MagicMock()

        # Create mock section
        mock_section = MagicMock(spec=ExpansionSection)
        mock_section.id = 1
        mock_section.heading = "Test Section"
        mock_section.expansion_prompt = "Test prompt"
        mock_section.status = SectionStatus.PENDING

        mock_session.query.return_value.filter.return_value.first.return_value = mock_section

        # Mock expansion functions
        mock_expand.return_value = MagicMock(
            expanded_queries=["q1", "q2"],
            hyde_answer="hyde",
            intent="DEFINITION",
            entities=["entity1"]
        )
        mock_embed.return_value = {
            "embedding_original": [0.1] * 768,
            "embeddings_mqe": [[0.2] * 768],
            "embedding_hyde": [0.3] * 768
        }
        mock_retrieve.return_value = [{"id": 1, "content": "test"}]
        mock_consolidate.return_value = [{"id": 1, "content": "clean"}]

        mock_llm = MagicMock()

        expand_section(
            section_id=1,
            session=mock_session,
            llm_client=mock_llm
        )

        # Verify status was set to EXPANDING then READY
        mock_session.commit.assert_called()
        assert mock_section.status == SectionStatus.READY

    @patch('vulcanlab.expansion.section_processing._expand_query_for_section')
    def test_expand_section_stores_rag_data(self, mock_expand):
        """Test that expand_section stores RAG pipeline data."""
        mock_session = MagicMock()

        mock_section = MagicMock(spec=ExpansionSection)
        mock_section.id = 1
        mock_section.heading = "Test"
        mock_section.expansion_prompt = "Prompt"
        mock_section.status = SectionStatus.PENDING

        mock_session.query.return_value.filter.return_value.first.return_value = mock_section

        mock_expand.return_value = MagicMock(
            expanded_queries=["query1", "query2", "query3"],
            hyde_answer="Hypothetical answer",
            intent="MECHANISM",
            entities=["entity1", "entity2"]
        )

        # Patch other functions to avoid errors
        with patch('vulcanlab.expansion.section_processing._generate_embeddings_for_section') as mock_embed:
            mock_embed.return_value = {
                "embedding_original": [0.1],
                "embeddings_mqe": [[0.1], [0.1], [0.1]],
                "embedding_hyde": [0.1]
            }
            with patch('vulcanlab.expansion.section_processing._retrieve_for_section') as mock_retrieve:
                mock_retrieve.return_value = []
                with patch('vulcanlab.expansion.section_processing._consolidate_section_context') as mock_consolidate:
                    mock_consolidate.return_value = []

                    mock_llm = MagicMock()

                    expand_section(
                        section_id=1,
                        session=mock_session,
                        llm_client=mock_llm
                    )

        # Verify RAG data was stored
        assert mock_section.expanded_queries == {"queries": ["query1", "query2", "query3"]}
        assert mock_section.hyde_answer == "Hypothetical answer"
        assert mock_section.intent == "MECHANISM"
        assert mock_section.entities == {"entities": ["entity1", "entity2"]}

    @patch('vulcanlab.expansion.section_processing._expand_query_for_section')
    def test_expand_section_failure_sets_status(self, mock_expand):
        """Test that expand_section sets FAILED status on error."""
        mock_session = MagicMock()

        mock_section = MagicMock(spec=ExpansionSection)
        mock_section.id = 1
        mock_section.heading = "Test"
        mock_section.expansion_prompt = "Prompt"
        mock_section.status = SectionStatus.PENDING

        mock_session.query.return_value.filter.return_value.first.return_value = mock_section

        # Make expansion fail
        mock_expand.side_effect = Exception("LLM error")

        mock_llm = MagicMock()

        with pytest.raises(Exception):
            expand_section(
                section_id=1,
                session=mock_session,
                llm_client=mock_llm
            )

        # Verify status was set to FAILED
        assert mock_section.status == SectionStatus.FAILED
        assert "LLM error" in mock_section.error_message


class TestGenerateSection:
    """Tests for generate_section function."""

    def test_section_not_found_raises(self):
        """Test that generate_section raises if section not found."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        mock_llm = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            generate_section(section_id=999, session=mock_session, llm_client=mock_llm)

        assert "not found" in str(exc_info.value)

    def test_section_not_ready_raises(self):
        """Test that generate_section raises if section not ready."""
        mock_session = MagicMock()

        mock_section = MagicMock(spec=ExpansionSection)
        mock_section.id = 1
        mock_section.status = SectionStatus.PENDING  # Not ready

        mock_session.query.return_value.filter.return_value.first.return_value = mock_section

        mock_llm = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            generate_section(section_id=1, session=mock_session, llm_client=mock_llm)

        assert "not ready" in str(exc_info.value)

    @patch('vulcanlab.expansion.section_processing.get_active_template')
    def test_generate_section_stores_response(self, mock_template):
        """Test that generate_section stores the LLM response."""
        mock_template.return_value = "{intent} {entities_str} {context_blocks} {user_question}"

        mock_session = MagicMock()

        mock_section = MagicMock(spec=ExpansionSection)
        mock_section.id = 1
        mock_section.heading = "Test Section"
        mock_section.expansion_prompt = "Test prompt"
        mock_section.status = SectionStatus.READY
        mock_section.clean_retrieval_context = {"chunks": []}
        mock_section.entities = {"entities": ["entity1"]}
        mock_section.intent = "DEFINITION"

        mock_session.query.return_value.filter.return_value.first.return_value = mock_section

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Generated response text"
        mock_llm.invoke.return_value = mock_response

        generate_section(section_id=1, session=mock_session, llm_client=mock_llm)

        # Verify response was stored
        assert mock_section.response_text == "Generated response text"
        assert mock_section.status == SectionStatus.COMPLETED

    @patch('vulcanlab.expansion.section_processing.get_active_template')
    def test_generate_section_failure_sets_status(self, mock_template):
        """Test that generate_section sets FAILED status on error."""
        mock_template.return_value = "{intent} {entities_str} {context_blocks} {user_question}"

        mock_session = MagicMock()

        mock_section = MagicMock(spec=ExpansionSection)
        mock_section.id = 1
        mock_section.heading = "Test"
        mock_section.expansion_prompt = "Prompt"
        mock_section.status = SectionStatus.READY
        mock_section.clean_retrieval_context = {"chunks": []}
        mock_section.entities = None
        mock_section.intent = None

        mock_session.query.return_value.filter.return_value.first.return_value = mock_section

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API error")

        with pytest.raises(Exception):
            generate_section(section_id=1, session=mock_session, llm_client=mock_llm)

        assert mock_section.status == SectionStatus.FAILED
        assert "API error" in mock_section.error_message


class TestSaveManualResponse:
    """Tests for save_manual_response function."""

    def test_section_not_found_raises(self):
        """Test that save_manual_response raises if section not found."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            save_manual_response(
                section_id=999,
                response_text="Response",
                session=mock_session
            )

        assert "not found" in str(exc_info.value)

    def test_save_manual_response_stores_text(self):
        """Test that save_manual_response stores the response text."""
        mock_session = MagicMock()

        mock_section = MagicMock(spec=ExpansionSection)
        mock_section.id = 1
        mock_section.heading = "Test Section"
        mock_section.status = SectionStatus.READY

        mock_session.query.return_value.filter.return_value.first.return_value = mock_section

        response_text = "This is the manually entered response."

        save_manual_response(
            section_id=1,
            response_text=response_text,
            session=mock_session
        )

        assert mock_section.response_text == response_text
        assert mock_section.status == SectionStatus.COMPLETED
        mock_session.commit.assert_called_once()

    def test_save_manual_response_works_from_any_status(self):
        """Test that save_manual_response works regardless of current status."""
        mock_session = MagicMock()

        mock_section = MagicMock(spec=ExpansionSection)
        mock_section.id = 1
        mock_section.heading = "Test"
        mock_section.status = SectionStatus.PENDING  # Can save from any status

        mock_session.query.return_value.filter.return_value.first.return_value = mock_section

        save_manual_response(
            section_id=1,
            response_text="Manual response",
            session=mock_session
        )

        assert mock_section.response_text == "Manual response"
        assert mock_section.status == SectionStatus.COMPLETED
