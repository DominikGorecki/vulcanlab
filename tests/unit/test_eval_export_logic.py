"""Unit tests for evaluation export logic."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from vulcanlab.eval.evaluations import get_experiment_evaluation_data_for_export
from vulcanlab.data.models.experiment import (
    ExperimentPrompt,
    ExperimentAnswer,
    ExperimentEvaluation,
    ExperimentDimensionResult,
)
from tests.unit.mock_helpers import create_mock_query_chain

def test_get_experiment_evaluation_data_for_export_logic():
    """Test retrieval and grouping logic for CSV export."""
    session = MagicMock()
    experiment_id = 1
    
    # 1. Mock Prompts (to establish grouping_id)
    t1 = datetime(2023, 1, 1, 10, 0, 0)
    t2 = t1 + timedelta(minutes=10)
    
    p1 = MagicMock(spec=ExperimentPrompt)
    p1.id = 101
    p1.created_at = t1
    p1.prompt_text = "Prompt 1"
    
    p2 = MagicMock(spec=ExperimentPrompt)
    p2.id = 102
    p2.created_at = t2
    p2.prompt_text = "Prompt 2"
    
    # 2. Mock Evaluations
    # Eval 1 for Prompt 1
    e1 = MagicMock(spec=ExperimentEvaluation)
    e1.id = 1
    e1.overall_score = 5
    e1.justification = "Justification 1"
    e1.answer = MagicMock(spec=ExperimentAnswer)
    e1.answer.prompt_id = 101
    e1.answer.prompt = p1
    dr1 = MagicMock(spec=ExperimentDimensionResult)
    dr1.dimension_name = "coherence"
    dr1.score = 8
    e1.dimension_results = [dr1]
    
    # Eval 2 for Prompt 2
    e2 = MagicMock(spec=ExperimentEvaluation)
    e2.id = 2
    e2.overall_score = -2
    e2.justification = "Justification 2"
    e2.answer = MagicMock(spec=ExperimentAnswer)
    e2.answer.prompt_id = 102
    e2.answer.prompt = p2
    dr2 = MagicMock(spec=ExperimentDimensionResult)
    dr2.dimension_name = "coherence"
    dr2.score = 4
    e2.dimension_results = [dr2]
    
    # Eval 3 for Prompt 1 (second evaluation for same prompt)
    e3 = MagicMock(spec=ExperimentEvaluation)
    e3.id = 3
    e3.overall_score = 7
    e3.justification = "Justification 3"
    e3.answer = MagicMock(spec=ExperimentAnswer)
    e3.answer.prompt_id = 101
    e3.answer.prompt = p1
    dr3 = MagicMock(spec=ExperimentDimensionResult)
    dr3.dimension_name = "coherence"
    dr3.score = 9
    e3.dimension_results = [dr3]

    # Mock the queries
    def mock_query(model):
        if model == ExperimentPrompt:
            q = create_mock_query_chain(return_data=[p1, p2])
            q.options = MagicMock(return_value=q)
            return q
        elif model == ExperimentEvaluation:
            q = create_mock_query_chain(return_data=[e1, e2, e3])
            q.options = MagicMock(return_value=q)
            return q
        q = create_mock_query_chain()
        q.options = MagicMock(return_value=q)
        return q
    
    session.query.side_effect = mock_query
    
    # Execute
    results = get_experiment_evaluation_data_for_export(session, experiment_id)
    
    # Verify results
    assert len(results) == 3
    
    # Check grouping_id stability (p1 is first, so grouping_id=1)
    assert results[0]["grouping_id"] == 1
    assert results[0]["prompt"] == "Prompt 1"
    assert results[0]["overall_score"] == 5
    assert results[0]["dimension_scores"] == {"coherence": 8}
    
    assert results[1]["grouping_id"] == 2
    assert results[1]["prompt"] == "Prompt 2"
    assert results[1]["overall_score"] == -2
    assert results[1]["dimension_scores"] == {"coherence": 4}
    
    # Third result is for p1, should have grouping_id=1
    assert results[2]["grouping_id"] == 1
    assert results[2]["prompt"] == "Prompt 1"
    assert results[2]["overall_score"] == 7
    assert results[2]["dimension_scores"] == {"coherence": 9}

def test_get_experiment_evaluation_data_for_export_ordering():
    """Test that grouping_id follows prompt creation order."""
    session = MagicMock()
    experiment_id = 1
    
    t1 = datetime(2023, 1, 1, 10, 0, 0)
    t2 = t1 - timedelta(hours=1) # t2 is earlier
    
    p1 = MagicMock(spec=ExperimentPrompt)
    p1.id = 101
    p1.created_at = t1
    p1.prompt_text = "P1"
    
    p2 = MagicMock(spec=ExperimentPrompt)
    p2.id = 102
    p2.created_at = t2
    p2.prompt_text = "P2"
    
    # In order_by(created_at.asc()), p2 should come before p1
    
    # Evaluations
    e1 = MagicMock(spec=ExperimentEvaluation)
    e1.answer = MagicMock(spec=ExperimentAnswer)
    e1.answer.prompt_id = 101
    e1.answer.prompt = p1
    e1.dimension_results = []
    
    e2 = MagicMock(spec=ExperimentEvaluation)
    e2.answer = MagicMock(spec=ExperimentAnswer)
    e2.answer.prompt_id = 102
    e2.answer.prompt = p2
    e2.dimension_results = []

    def mock_query(model):
        if model == ExperimentPrompt:
            # Sorted by created_at asc
            q = create_mock_query_chain(return_data=[p2, p1])
            q.options = MagicMock(return_value=q)
            return q
        elif model == ExperimentEvaluation:
            q = create_mock_query_chain(return_data=[e1, e2])
            q.options = MagicMock(return_value=q)
            return q
        q = create_mock_query_chain()
        q.options = MagicMock(return_value=q)
        return q
    
    session.query.side_effect = mock_query
    
    results = get_experiment_evaluation_data_for_export(session, experiment_id)
    
    # p2 is grouping_id 1 because it's earlier
    # e1 is for p1 -> grouping_id 2
    # e2 is for p2 -> grouping_id 1
    
    # Map results by prompt for easier assertion
    p1_res = next(r for r in results if r["prompt"] == p1.prompt_text)
    p2_res = next(r for r in results if r["prompt"] == p2.prompt_text)
    
    assert p1_res["grouping_id"] == 2
    assert p2_res["grouping_id"] == 1

def test_get_experiment_evaluation_data_for_export_mapping_inversion():
    """Test that scores are inverted correctly based on is_x_mapped_to_a."""
    session = MagicMock()
    experiment_id = 1
    
    p1 = MagicMock(spec=ExperimentPrompt)
    p1.id = 101
    p1.created_at = datetime.now()
    p1.prompt_text = "Prompt 1"
    
    # Eval 1: X is A (is_x_mapped_to_a = True), no inversion
    e1 = MagicMock(spec=ExperimentEvaluation)
    e1.id = 1
    e1.overall_score = 5
    e1.answer = MagicMock(spec=ExperimentAnswer)
    e1.answer.prompt_id = 101
    e1.answer.prompt = p1
    e1.answer.is_x_mapped_to_a = True
    dr1 = MagicMock(spec=ExperimentDimensionResult)
    dr1.dimension_name = "coherence"
    dr1.score = 8
    e1.dimension_results = [dr1]
    
    # Eval 2: X is B (is_x_mapped_to_a = False), SHOULD INVERT
    e2 = MagicMock(spec=ExperimentEvaluation)
    e2.id = 2
    e2.overall_score = 5
    e2.answer = MagicMock(spec=ExperimentAnswer)
    e2.answer.prompt_id = 101
    e2.answer.prompt = p1
    e2.answer.is_x_mapped_to_a = False
    dr2 = MagicMock(spec=ExperimentDimensionResult)
    dr2.dimension_name = "coherence"
    dr2.score = 8
    e2.dimension_results = [dr2]
    
    def mock_query(model):
        if model == ExperimentPrompt:
            q = create_mock_query_chain(return_data=[p1])
            q.options = MagicMock(return_value=q)
            return q
        elif model == ExperimentEvaluation:
            q = create_mock_query_chain(return_data=[e1, e2])
            q.options = MagicMock(return_value=q)
            return q
        q = create_mock_query_chain()
        q.options = MagicMock(return_value=q)
        return q
    
    session.query.side_effect = mock_query
    
    results = get_experiment_evaluation_data_for_export(session, experiment_id)
    
    assert len(results) == 2
    
    # Eval 1 (no inversion)
    assert results[0]["overall_score"] == 5
    assert results[0]["dimension_scores"]["coherence"] == 8
    
    # Eval 2 (inverted)
    assert results[1]["overall_score"] == -5
    assert results[1]["dimension_scores"]["coherence"] == -8

