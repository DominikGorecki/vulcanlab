"""Unit tests for evaluation CSV export formatting."""

import pytest
import csv
import io
from unittest.mock import MagicMock
from vulcanlab.eval.evaluations import export_experiment_evaluations_to_csv

def test_export_experiment_evaluations_to_csv_formatting():
    """Test CSV formatting logic including headers and dimensions."""
    session = MagicMock()
    experiment_id = 1
    
    # Mock data that would be returned by get_experiment_evaluation_data_for_export
    mock_eval_data = [
        {
            "prompt": "Test Prompt 1",
            "grouping_id": 1,
            "overall_score": 5,
            "justification": "Good response",
            "dimension_scores": {"coherence": 8, "accuracy": 9}
        },
        {
            "prompt": "Test Prompt 2",
            "grouping_id": 2,
            "overall_score": -2,
            "justification": "Bad response",
            "dimension_scores": {"coherence": 4, "accuracy": 2}
        }
    ]
    
    # Patch get_experiment_evaluation_data_for_export
    import vulcanlab.eval.evaluations as eval_module
    original_get_data = eval_module.get_experiment_evaluation_data_for_export
    eval_module.get_experiment_evaluation_data_for_export = MagicMock(return_value=mock_eval_data)
    
    try:
        csv_output = export_experiment_evaluations_to_csv(session, experiment_id)
        
        # Parse CSV to verify
        reader = csv.DictReader(io.StringIO(csv_output))
        rows = list(reader)
        
        assert len(rows) == 2
        
        # Verify headers (R1 order: prompt, grouping_id, overall_score, sorted dims, justification)
        expected_headers = ["prompt", "grouping_id", "overall_score", "accuracy", "coherence", "justification"]
        assert reader.fieldnames == expected_headers
        
        # Verify first row
        assert rows[0]["prompt"] == "Test Prompt 1"
        assert rows[0]["grouping_id"] == "1"
        assert rows[0]["overall_score"] == "5"
        assert rows[0]["accuracy"] == "9"
        assert rows[0]["coherence"] == "8"
        assert rows[0]["justification"] == "Good response"
        
        # Verify second row
        assert rows[1]["prompt"] == "Test Prompt 2"
        assert rows[1]["grouping_id"] == "2"
        assert rows[1]["overall_score"] == "-2"
        assert rows[1]["accuracy"] == "2"
        assert rows[1]["coherence"] == "4"
        assert rows[1]["justification"] == "Bad response"
        
    finally:
        eval_module.get_experiment_evaluation_data_for_export = original_get_data

def test_export_experiment_evaluations_to_csv_sanitization():
    """Test that special characters in text are correctly handled."""
    session = MagicMock()
    experiment_id = 1
    
    # Prompt with comma and double quotes, justification with newline
    special_text = 'Prompt with "quotes", and comma'
    justification_with_newline = "Line 1\nLine 2"
    
    mock_eval_data = [
        {
            "prompt": special_text,
            "grouping_id": 1,
            "overall_score": 0,
            "justification": justification_with_newline,
            "dimension_scores": {}
        }
    ]
    
    import vulcanlab.eval.evaluations as eval_module
    original_get_data = eval_module.get_experiment_evaluation_data_for_export
    eval_module.get_experiment_evaluation_data_for_export = MagicMock(return_value=mock_eval_data)
    
    try:
        csv_output = export_experiment_evaluations_to_csv(session, experiment_id)
        
        # Verify the raw string contains quotes for the field with commas/quotes
        assert f'"{special_text.replace('"', '""')}"' in csv_output
        assert f'"{justification_with_newline}"' in csv_output
        
        # Parse CSV to verify data integrity
        reader = csv.DictReader(io.StringIO(csv_output))
        rows = list(reader)
        
        assert rows[0]["prompt"] == special_text
        assert rows[0]["justification"] == justification_with_newline
        
    finally:
        eval_module.get_experiment_evaluation_data_for_export = original_get_data

def test_export_experiment_evaluations_to_csv_missing_dimensions():
    """Test handling of evaluations with inconsistent dimension sets."""
    session = MagicMock()
    experiment_id = 1
    
    mock_eval_data = [
        {
            "prompt": "P1",
            "grouping_id": 1,
            "overall_score": 1,
            "justification": "J1",
            "dimension_scores": {"dim_a": 10}
        },
        {
            "prompt": "P2",
            "grouping_id": 2,
            "overall_score": 2,
            "justification": "J2",
            "dimension_scores": {"dim_b": 5}
        }
    ]
    
    import vulcanlab.eval.evaluations as eval_module
    original_get_data = eval_module.get_experiment_evaluation_data_for_export
    eval_module.get_experiment_evaluation_data_for_export = MagicMock(return_value=mock_eval_data)
    
    try:
        csv_output = export_experiment_evaluations_to_csv(session, experiment_id)
        
        reader = csv.DictReader(io.StringIO(csv_output))
        rows = list(reader)
        
        # Both dimensions should be in headers
        assert "dim_a" in reader.fieldnames
        assert "dim_b" in reader.fieldnames
        
        # Row 1 has dim_a but not dim_b
        assert rows[0]["dim_a"] == "10"
        assert rows[0]["dim_b"] == ""
        
        # Row 2 has dim_b but not dim_a
        assert rows[1]["dim_a"] == ""
        assert rows[1]["dim_b"] == "5"
        
    finally:
        eval_module.get_experiment_evaluation_data_for_export = original_get_data

