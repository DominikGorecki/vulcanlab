import pytest
from unittest.mock import MagicMock
from vulcanlab.research.nodes.refinement_coordinator_node import RefinementCoordinatorNode
from vulcanlab.data.models.enums import ResearchPhase

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def base_state():
    return {
        "research_plan": {
            "sub_questions": [
                {
                    "id": "sq1",
                    "question": "What is X?",
                    "rationale": "X is important.",
                    "estimated_tokens": 20000,
                    "relevant_items": [1, 2]
                }
            ]
        },
        "sections": {
            "sq1": {"content": "Old content", "sources": []}
        },
        "quality_metrics": {
            "sq1": {
                "citation_coverage": 0.5,  # Low
                "source_diversity": 1,     # Low
                "coherence_score": "Low"    # Low
            }
        },
        "refinement_needed": ["sq1"],
        "refinement_iteration_count": 0,
        "current_phase": "refinement"
    }

def test_refinement_coordinator_node_adjusts_params(base_state, mock_session):
    new_state = RefinementCoordinatorNode(base_state, mock_session)
    
    # Check parameters adjusted
    sq = new_state["research_plan"]["sub_questions"][0]
    assert sq["estimated_tokens"] == 30000  # 20000 * 1.5
    assert "SEEK ADDITIONAL DIVERSE SOURCES" in sq["rationale"]
    assert "SIMPLIFY AND CLARIFY: " in sq["question"]
    
    # Check section cleared
    assert "sq1" not in new_state["sections"]
    
    # Check state updates
    assert new_state["refinement_iteration_count"] == 1
    assert new_state["current_phase"] == ResearchPhase.RESEARCH.value
    assert new_state["refinement_needed"] == []

def test_refinement_coordinator_node_max_iterations(base_state, mock_session):
    base_state["refinement_iteration_count"] = 2
    new_state = RefinementCoordinatorNode(base_state, mock_session)
    
    assert new_state["current_phase"] == ResearchPhase.COMPLETED.value
    assert new_state["refinement_needed"] == []
    # No changes to params should have happened
    assert new_state["research_plan"]["sub_questions"][0]["estimated_tokens"] == 20000

def test_refinement_coordinator_node_no_refinement_needed(base_state, mock_session):
    base_state["refinement_needed"] = []
    new_state = RefinementCoordinatorNode(base_state, mock_session)
    
    assert new_state["current_phase"] == ResearchPhase.COMPLETED.value
