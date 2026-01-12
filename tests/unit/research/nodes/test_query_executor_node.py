"""
Unit tests for QueryExecutorNode.
"""

import pytest
from unittest.mock import Mock, patch

from vulcanlab.research.nodes.query_executor_node import QueryExecutorNode
from vulcanlab.data.models.result import Result


@pytest.fixture
def mock_session():
    return Mock()


@pytest.fixture
def initial_state():
    return {
        "collection_id": 1,
        "thread_id": "test_thread",
        "research_plan": {
            "sub_questions": [
                {
                    "id": "sq1",
                    "question": "Question 1?",
                    "relevant_items": [101]
                },
                {
                    "id": "sq2",
                    "question": "Question 2?",
                    "relevant_items": [102]
                }
            ]
        },
        "reused_sections": {},
        "context_per_question": {}
    }


def test_query_executor_node_handles_exact_reuse(mock_session, initial_state):
    """Test QueryExecutorNode with exact_reuse strategy."""
    
    # 1. Mock dependencies
    with patch("vulcanlab.research.nodes.query_executor_node.match_results_for_question") as mock_match, \
         patch("vulcanlab.research.nodes.query_executor_node.recommend_reuse_strategy") as mock_recommend, \
         patch("vulcanlab.research.nodes.query_executor_node.get_research_session_by_thread_id") as mock_get_session, \
         patch("vulcanlab.research.nodes.query_executor_node.update_research_session") as mock_update_session:
        
        # Mock session
        mock_res_session = Mock()
        mock_res_session.id = 123
        mock_get_session.return_value = mock_res_session

        # Mock matches for Q1
        mock_match.side_effect = [
            [{"result_id": 501, "similarity": 0.95, "quality_score": 0.8}], # Q1
            [] # Q2
        ]
        
        mock_recommend.return_value = "exact_reuse"
        
        # Mock result fetching
        mock_result = Mock(spec=Result)
        mock_result.response_text = "Reused content for Q1"
        mock_session.get.return_value = mock_result
        
        # 2. Call the node
        final_state = QueryExecutorNode(initial_state, mock_session)
        
        # 3. Assertions
        assert final_state["current_phase"] == "context_assembly"
        
        # Q1 assertions
        assert "sq1" in final_state["reused_sections"]
        assert final_state["reused_sections"]["sq1"]["reuse_type"] == "exact_reuse"
        assert len(final_state["context_per_question"]["sq1"]) == 1
        assert final_state["context_per_question"]["sq1"][0]["content"] == "Reused content for Q1"
        
        # Q2 assertions (no matches)
        assert "sq2" not in final_state["reused_sections"]
        assert len(final_state["context_per_question"]["sq2"]) == 1
        assert final_state["context_per_question"]["sq2"][0]["item_id"] == 102
        assert final_state["context_per_question"]["sq2"][0]["type"] == "unprocessed"


def test_query_executor_node_handles_new_generation(mock_session, initial_state):
    """Test QueryExecutorNode with new_generation strategy (no matches)."""
    
    # 1. Mock dependencies
    with patch("vulcanlab.research.nodes.query_executor_node.match_results_for_question") as mock_match, \
         patch("vulcanlab.research.nodes.query_executor_node.get_research_session_by_thread_id") as mock_get_session:
        
        mock_get_session.return_value = Mock(id=123)
        mock_match.return_value = [] # No matches for any question
        
        # 2. Call the node
        final_state = QueryExecutorNode(initial_state, mock_session)
        
        # 3. Assertions
        assert final_state["reused_sections"] == {}
        assert len(final_state["context_per_question"]["sq1"]) == 1
        assert final_state["context_per_question"]["sq1"][0]["item_id"] == 101
        assert final_state["context_per_question"]["sq1"][0]["type"] == "unprocessed"


def test_query_executor_node_handles_ensemble_reuse(mock_session, initial_state):
    """Test QueryExecutorNode with ensemble strategy."""
    
    # 1. Mock dependencies
    with patch("vulcanlab.research.nodes.query_executor_node.match_results_for_question") as mock_match, \
         patch("vulcanlab.research.nodes.query_executor_node.recommend_reuse_strategy") as mock_recommend, \
         patch("vulcanlab.research.nodes.query_executor_node.get_research_session_by_thread_id") as mock_get_session:
        
        mock_get_session.return_value = Mock(id=123)
        # Mock matches for Q1 (multiple results)
        matches = [
            {"result_id": 501, "similarity": 0.88, "quality_score": 0.9},
            {"result_id": 502, "similarity": 0.87, "quality_score": 0.85}
        ]
        mock_match.side_effect = [matches, []]
        mock_recommend.return_value = "ensemble"
        
        # Mock result fetching
        def mock_get(model, ident):
            res = Mock(spec=Result)
            res.response_text = f"Content for {ident}"
            return res
        mock_session.get.side_effect = mock_get
        
        # 2. Call the node
        final_state = QueryExecutorNode(initial_state, mock_session)
        
        # 3. Assertions
        assert final_state["reused_sections"]["sq1"]["reuse_type"] == "ensemble"
        assert len(final_state["context_per_question"]["sq1"]) == 2
        assert final_state["context_per_question"]["sq1"][0]["result_id"] == 501
        assert final_state["context_per_question"]["sq1"][1]["result_id"] == 502
