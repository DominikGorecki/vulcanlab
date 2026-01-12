"""
Unit tests for ResearchPlannerNode.
"""

import pytest
from unittest.mock import Mock, patch
import json

from vulcanlab.research.nodes.research_planner_node import ResearchPlannerNode
from vulcanlab.research.state import ResearchState
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
        "current_phase": "planning"
    }


@pytest.fixture
def sample_plan():
    return {
        "research_goal": "Test goal",
        "key_themes": ["theme1"],
        "sub_questions": [
            {
                "id": "sq1",
                "question": "Test question?",
                "rationale": "Test rationale",
                "estimated_tokens": 30000,
                "relevant_items": [101]
            }
        ],
        "synthesis_approach": "Test synthesis"
    }


@pytest.fixture
def sample_collection_data():
    return {
        "collection_id": 1,
        "name": "Test Collection",
        "description": "Test description",
        "tags": ["test"],
        "item_count": 1,
        "items": [
            {"id": 101, "type": "excerpt", "note": "Note 1"}
        ]
    }


def test_research_planner_node_updates_state_and_db(
    mock_session, initial_state, sample_plan, sample_collection_data
):
    """Test that ResearchPlannerNode correctly updates state and database."""
    
    # 1. Mock dependencies
    with patch("vulcanlab.research.nodes.research_planner_node.analyze_collection") as mock_analyze, \
         patch("vulcanlab.research.nodes.research_planner_node.generate_research_plan") as mock_generate, \
         patch("vulcanlab.research.nodes.research_planner_node.create_langchain_chat") as mock_create_chat, \
         patch("vulcanlab.research.nodes.research_planner_node.get_research_session_by_thread_id") as mock_get_session, \
         patch("vulcanlab.research.nodes.research_planner_node.update_research_session") as mock_update_session:
        
        mock_analyze.return_value = sample_collection_data
        mock_generate.return_value = sample_plan
        
        # Mock LangChain chat
        mock_chat = Mock()
        mock_create_chat.return_value.chat = mock_chat
        
        # Mock research session
        mock_res_session = Mock(spec=ResearchSession)
        mock_res_session.id = 123
        mock_get_session.return_value = mock_res_session
        
        # 2. Call the node
        final_state = ResearchPlannerNode(initial_state, mock_session)
        
        # 3. Assertions
        mock_analyze.assert_called_once_with(1, mock_session)
        assert mock_generate.called
        mock_get_session.assert_called_once_with(mock_session, "test_thread")
        
        # Verify DB update
        mock_update_session.assert_called_once_with(
            mock_session,
            123,
            {
                "research_plan": sample_plan,
                "current_phase": ResearchPhase.RESEARCH,
            }
        )
        
        # Verify state update
        assert final_state["research_plan"] == sample_plan
        assert final_state["current_phase"] == "research"
        assert final_state["collection_description"] == "Test description"
        assert len(final_state["item_notes"]) == 1
        assert final_state["item_notes"][0]["item_id"] == 101
        assert final_state["item_notes"][0]["note"] == "Note 1"


def test_research_planner_node_raises_if_collection_id_missing(mock_session):
    state = {"thread_id": "test"}
    with pytest.raises(ValueError, match="collection_id missing"):
        ResearchPlannerNode(state, mock_session)


def test_research_planner_node_raises_if_thread_id_missing(mock_session):
    state = {"collection_id": 1}
    with pytest.raises(ValueError, match="thread_id missing"):
        ResearchPlannerNode(state, mock_session)
