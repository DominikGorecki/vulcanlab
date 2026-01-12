"""
Unit tests for SynthesizerNode.
"""

import pytest
from unittest.mock import Mock, patch, ANY

from vulcanlab.research.nodes.synthesizer_node import SynthesizerNode
from vulcanlab.data.models.enums import ResearchPhase
from vulcanlab.data.models.research_session import ResearchSession


@pytest.fixture
def mock_session():
    return Mock()


@pytest.fixture
def initial_state():
    return {
        "collection_id": 1,
        "thread_id": "test_thread",
        "current_phase": "synthesis",
        "research_plan": {
            "sub_questions": [
                {
                    "question_id": "sq1",
                    "question": "What is the impact of X?",
                    "relevant_items": [101]
                }
            ]
        },
        "context_per_question": {
            "sq1": {
                "context": "Context for sq1",
                "token_count": 100,
                "sources": [{"item_id": 101, "work_title": "Source 1"}]
            }
        },
        "reused_sections": {
            "sq1": {"source_result_ids": [501], "reuse_type": "exact_reuse"}
        }
    }


def test_synthesizer_node_success(mock_session, initial_state):
    """Test that SynthesizerNode correctly generates and saves research sections."""
    
    with patch("vulcanlab.research.nodes.synthesizer_node.create_langchain_chat") as mock_create_chat, \
         patch("vulcanlab.research.nodes.synthesizer_node.generate_section") as mock_generate, \
         patch("vulcanlab.research.nodes.synthesizer_node.extract_metadata") as mock_extract, \
         patch("vulcanlab.research.nodes.synthesizer_node.get_research_session_by_thread_id") as mock_get_session, \
         patch("vulcanlab.research.nodes.synthesizer_node.create_research_section") as mock_create_section:
        
        # Mock LangChain chat
        mock_chat = Mock()
        mock_create_chat.return_value.chat = mock_chat
        
        # Mock responses
        mock_generate.return_value = "Generated content for sq1"
        mock_extract.return_value = {"word_count": 10, "citation_count": 1, "source_diversity": 1}
        
        # Mock research session
        mock_res_session = Mock(spec=ResearchSession)
        mock_res_session.id = 123
        mock_get_session.return_value = mock_res_session
        
        # Call the node
        final_state = SynthesizerNode(initial_state, mock_session)
        
        # Assertions
        mock_get_session.assert_called_once_with(mock_session, "test_thread")
        mock_generate.assert_called_once_with(
            question_text="What is the impact of X?",
            context="Context for sq1",
            sources=[{"item_id": 101, "work_title": "Source 1"}],
            llm_client=ANY
        )

        mock_create_section.assert_called_once_with(
            session=mock_session,
            session_id=123,
            question_id="sq1",
            question_text="What is the impact of X?",
            section_content="Generated content for sq1",
            context_data=initial_state["context_per_question"]["sq1"],
            section_metadata={"word_count": 10, "citation_count": 1, "source_diversity": 1},
            reuse_info={"source_result_ids": [501], "reuse_type": "exact_reuse"}
        )
        
        # Verify state updates
        assert final_state["current_phase"] == ResearchPhase.EVALUATION.value
        assert "sq1" in final_state["sections"]
        assert final_state["sections"]["sq1"]["content"] == "Generated content for sq1"
        assert final_state["sections"]["sq1"]["metadata"]["word_count"] == 10


def test_synthesizer_node_no_context(mock_session, initial_state):
    """Test SynthesizerNode when no context is found for a question."""
    initial_state["context_per_question"] = {}
    
    with patch("vulcanlab.research.nodes.synthesizer_node.get_research_session_by_thread_id") as mock_get_session, \
         patch("vulcanlab.research.nodes.synthesizer_node.generate_section") as mock_generate:
        
        mock_res_session = Mock(spec=ResearchSession)
        mock_res_session.id = 123
        mock_get_session.return_value = mock_res_session
        
        final_state = SynthesizerNode(initial_state, mock_session)
        
        assert mock_generate.call_count == 0
        assert final_state["sections"] == {}
        assert final_state["current_phase"] == ResearchPhase.EVALUATION.value


def test_synthesizer_node_missing_thread_id(mock_session):
    """Test SynthesizerNode raises error if thread_id is missing."""
    with pytest.raises(ValueError, match="thread_id missing"):
        SynthesizerNode({}, mock_session)


def test_synthesizer_node_handles_generation_error(mock_session, initial_state):
    """Test SynthesizerNode handles LLM generation errors gracefully."""
    with patch("vulcanlab.research.nodes.synthesizer_node.create_langchain_chat") as mock_create_chat, \
         patch("vulcanlab.research.nodes.synthesizer_node.generate_section") as mock_generate, \
         patch("vulcanlab.research.nodes.synthesizer_node.get_research_session_by_thread_id") as mock_get_session:
        
        mock_create_chat.return_value.chat = Mock()
        mock_generate.side_effect = Exception("LLM Error")
        
        mock_res_session = Mock(spec=ResearchSession)
        mock_res_session.id = 123
        mock_get_session.return_value = mock_res_session
        
        # Should not raise exception
        final_state = SynthesizerNode(initial_state, mock_session)
        
        assert final_state["sections"] == {}
        assert final_state["current_phase"] == ResearchPhase.EVALUATION.value
