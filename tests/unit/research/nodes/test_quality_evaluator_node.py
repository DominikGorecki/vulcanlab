import pytest
from unittest.mock import MagicMock, patch
from vulcanlab.research.nodes.quality_evaluator_node import QualityEvaluatorNode
from vulcanlab.data.models.enums import ResearchPhase

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def base_state():
    return {
        "collection_id": 1,
        "thread_id": "test-thread",
        "sections": {
            "sq1": {
                "content": "Test content sq1.",
                "sources": [{"work_id": 1, "work_title": "Source 1"}],
                "metadata": {"citation_count": 1, "word_count": 100, "source_diversity": 1}
            }
        },
        "quality_metrics": {},
        "refinement_needed": [],
        "current_phase": "evaluation"
    }

def test_quality_evaluator_node_pass(base_state, mock_session):
    # Mock evaluate_quality to return high quality
    quality_result = {
        "citation_coverage": 0.8,
        "source_diversity": 3,
        "coherence_score": "High",
        "completeness_score": "High"
    }
    
    with patch("vulcanlab.research.nodes.quality_evaluator_node.evaluate_quality", return_value=quality_result), \
         patch("vulcanlab.research.nodes.quality_evaluator_node.check_citation_coverage", return_value=[]):
        
        new_state = QualityEvaluatorNode(base_state, mock_session)
        
        assert new_state["current_phase"] == ResearchPhase.COMPLETED.value
        assert new_state["refinement_needed"] == []
        assert "sq1" in new_state["quality_metrics"]
        assert new_state["quality_metrics"]["sq1"]["citation_coverage"] == 0.8

def test_quality_evaluator_node_refinement_needed(base_state, mock_session):
    # Mock evaluate_quality to return low quality (low citation coverage)
    quality_result = {
        "citation_coverage": 0.5,
        "source_diversity": 3,
        "coherence_score": "High",
        "completeness_score": "High"
    }
    
    with patch("vulcanlab.research.nodes.quality_evaluator_node.evaluate_quality", return_value=quality_result), \
         patch("vulcanlab.research.nodes.quality_evaluator_node.check_citation_coverage", return_value=[]):
        
        new_state = QualityEvaluatorNode(base_state, mock_session)
        
        assert new_state["current_phase"] == ResearchPhase.REFINEMENT.value
        assert new_state["refinement_needed"] == ["sq1"]
        assert new_state["quality_metrics"]["sq1"]["citation_coverage"] == 0.5

def test_quality_evaluator_node_broken_citations(base_state, mock_session):
    # Mock evaluate_quality to return okay quality, but with broken citations
    quality_result = {
        "citation_coverage": 0.8,
        "source_diversity": 3,
        "coherence_score": "High",
        "completeness_score": "High"
    }
    
    with patch("vulcanlab.research.nodes.quality_evaluator_node.evaluate_quality", return_value=quality_result), \
         patch("vulcanlab.research.nodes.quality_evaluator_node.check_citation_coverage", return_value=["[Unknown 2023]"]):
        
        new_state = QualityEvaluatorNode(base_state, mock_session)
        
        assert new_state["current_phase"] == ResearchPhase.REFINEMENT.value
        assert "sq1" in new_state["refinement_needed"]
        assert new_state["quality_metrics"]["sq1"]["broken_citations"] == 1

def test_quality_evaluator_node_no_sections(mock_session):
    state = {
        "sections": {},
        "current_phase": "evaluation"
    }
    new_state = QualityEvaluatorNode(state, mock_session)
    assert new_state["current_phase"] == ResearchPhase.COMPLETED.value
