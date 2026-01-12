"""
Unit tests for ContextAssemblerNode.
"""

import pytest
from unittest.mock import Mock, patch

from vulcanlab.research.nodes.context_assembler_node import ContextAssemblerNode
from vulcanlab.data.models.enums import ResearchPhase


@pytest.fixture
def mock_session():
    return Mock()


@pytest.fixture
def initial_state():
    return {
        "collection_id": 1,
        "thread_id": "test_thread",
        "current_phase": "research",
        "research_plan": {
            "sub_questions": [
                {
                    "question_id": "sq1",
                    "question": "What is the impact of X?",
                    "relevant_items": [101, 102]
                },
                {
                    "question_id": "sq2",
                    "question": "How does Y relate to Z?",
                    "relevant_items": [103]
                }
            ]
        },
        "reused_sections": {
            "sq1": {"source_result_ids": [501], "reuse_type": "exact_reuse"}
        }
    }


def test_context_assembler_node_success(mock_session, initial_state):
    """Test that ContextAssemblerNode correctly assembles context for all sub-questions."""
    
    with patch("vulcanlab.research.nodes.context_assembler_node.assemble_context_for_question") as mock_assemble:
        # Mock responses for each sub-question
        mock_assemble.side_effect = [
            {"context": "Context for sq1", "token_count": 100, "sources": [{"item_id": 101}]},
            {"context": "Context for sq2", "token_count": 50, "sources": [{"item_id": 103}]}
        ]
        
        # Call the node
        final_state = ContextAssemblerNode(initial_state, mock_session)
        
        # Assertions
        assert mock_assemble.call_count == 2
        
        # Verify first call (with reuse_info)
        mock_assemble.assert_any_call(
            question_id="sq1",
            relevant_item_ids=[101, 102],
            reuse_info={"source_result_ids": [501], "reuse_type": "exact_reuse"},
            session=mock_session
        )
        
        # Verify second call (no reuse_info)
        mock_assemble.assert_any_call(
            question_id="sq2",
            relevant_item_ids=[103],
            reuse_info=None,
            session=mock_session
        )
        
        # Verify state updates
        assert final_state["current_phase"] == ResearchPhase.SYNTHESIS.value
        assert "sq1" in final_state["context_per_question"]
        assert "sq2" in final_state["context_per_question"]
        assert final_state["context_per_question"]["sq1"]["context"] == "Context for sq1"
        assert final_state["context_per_question"]["sq2"]["context"] == "Context for sq2"


def test_context_assembler_node_no_questions(mock_session):
    """Test ContextAssemblerNode when no sub-questions are provided."""
    state = {
        "research_plan": {"sub_questions": []},
        "current_phase": "research"
    }
    
    final_state = ContextAssemblerNode(state, mock_session)
    
    assert final_state["current_phase"] == ResearchPhase.SYNTHESIS.value
    assert final_state["context_per_question"] == {}


def test_context_assembler_node_handles_error(mock_session, initial_state):
    """Test that ContextAssemblerNode handles errors in context assembly gracefully."""
    
    with patch("vulcanlab.research.nodes.context_assembler_node.assemble_context_for_question") as mock_assemble:
        # One success, one failure
        mock_assemble.side_effect = [
            {"context": "Context for sq1", "token_count": 100, "sources": []},
            Exception("Assembly failed")
        ]
        
        final_state = ContextAssemblerNode(initial_state, mock_session)
        
        assert "sq1" in final_state["context_per_question"]
        assert "sq2" in final_state["context_per_question"]
        assert final_state["context_per_question"]["sq2"]["context"] == ""
        assert final_state["context_per_question"]["sq2"]["token_count"] == 0
        assert final_state["current_phase"] == ResearchPhase.SYNTHESIS.value
