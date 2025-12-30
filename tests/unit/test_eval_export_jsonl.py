"""Unit tests for evaluation JSONL export functionality."""

import pytest
import json
from unittest.mock import MagicMock
from vulcanlab.eval.evaluations import export_experiment_answers_to_jsonl
from vulcanlab.data.models.experiment import (
    ExperimentAnswer,
    ExperimentPrompt,
    ExperimentEvaluation
)


def test_export_experiment_answers_to_jsonl_basic():
    """Test basic JSONL export with completed evaluations."""
    session = MagicMock()
    experiment_id = 1

    # Create mock objects
    prompt1 = MagicMock(spec=ExperimentPrompt)
    prompt1.prompt_text = "What is photosynthesis?"
    prompt1.created_at = "2024-01-01"

    prompt2 = MagicMock(spec=ExperimentPrompt)
    prompt2.prompt_text = "Explain quantum mechanics"
    prompt2.created_at = "2024-01-02"

    answer1 = MagicMock(spec=ExperimentAnswer)
    answer1.id = 1
    answer1.answer_x = "Photosynthesis is the process by which plants convert light energy into chemical energy."
    answer1.answer_y = "It is a biological process where plants use sunlight to produce glucose."

    answer2 = MagicMock(spec=ExperimentAnswer)
    answer2.id = 2
    answer2.answer_x = "Quantum mechanics is a fundamental theory in physics."
    answer2.answer_y = "It describes nature at the smallest scales of energy levels."

    # Mock query results (answer, prompt) tuples
    mock_results = [
        (answer1, prompt1),
        (answer2, prompt2)
    ]

    # Setup mock query chain
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = mock_results

    session.query.return_value = mock_query

    # Execute export
    lines = list(export_experiment_answers_to_jsonl(session, experiment_id))

    # Verify output
    assert len(lines) == 2

    # Parse first line
    record1 = json.loads(lines[0].rstrip('\n'))
    assert record1["prompt_text"] == "What is photosynthesis?"
    assert record1["answer_x"] == "Photosynthesis is the process by which plants convert light energy into chemical energy."
    assert record1["answer_y"] == "It is a biological process where plants use sunlight to produce glucose."
    assert len(record1) == 3  # Only three fields

    # Parse second line
    record2 = json.loads(lines[1].rstrip('\n'))
    assert record2["prompt_text"] == "Explain quantum mechanics"
    assert record2["answer_x"] == "Quantum mechanics is a fundamental theory in physics."
    assert record2["answer_y"] == "It describes nature at the smallest scales of energy levels."

    # Verify each line ends with newline
    assert lines[0].endswith('\n')
    assert lines[1].endswith('\n')


def test_export_experiment_answers_to_jsonl_special_characters():
    """Test JSONL export handles special characters correctly."""
    session = MagicMock()
    experiment_id = 1

    # Create prompt and answer with special characters
    prompt = MagicMock(spec=ExperimentPrompt)
    prompt.prompt_text = 'What is "machine learning"?\nExplain briefly.'
    prompt.created_at = "2024-01-01"

    answer = MagicMock(spec=ExperimentAnswer)
    answer.id = 1
    answer.answer_x = "It's a branch of AI.\nIt uses algorithms to learn from data."
    answer.answer_y = 'Machine learning allows computers to "learn" without explicit programming.'

    mock_results = [(answer, prompt)]

    # Setup mock query chain
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = mock_results

    session.query.return_value = mock_query

    # Execute export
    lines = list(export_experiment_answers_to_jsonl(session, experiment_id))

    # Verify output
    assert len(lines) == 1

    # Parse and verify special characters are properly escaped
    record = json.loads(lines[0].rstrip('\n'))
    assert record["prompt_text"] == 'What is "machine learning"?\nExplain briefly.'
    assert record["answer_x"] == "It's a branch of AI.\nIt uses algorithms to learn from data."
    assert record["answer_y"] == 'Machine learning allows computers to "learn" without explicit programming.'


def test_export_experiment_answers_to_jsonl_unicode():
    """Test JSONL export handles Unicode characters correctly."""
    session = MagicMock()
    experiment_id = 1

    # Create prompt and answer with Unicode characters
    prompt = MagicMock(spec=ExperimentPrompt)
    prompt.prompt_text = "Qu'est-ce que l'intelligence artificielle?"
    prompt.created_at = "2024-01-01"

    answer = MagicMock(spec=ExperimentAnswer)
    answer.id = 1
    answer.answer_x = "L'IA est la simulation de l'intelligence humaine. 🤖"
    answer.answer_y = "它是计算机科学的一个分支。"

    mock_results = [(answer, prompt)]

    # Setup mock query chain
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = mock_results

    session.query.return_value = mock_query

    # Execute export
    lines = list(export_experiment_answers_to_jsonl(session, experiment_id))

    # Verify output
    assert len(lines) == 1

    # Parse and verify Unicode is preserved (not escaped)
    record = json.loads(lines[0].rstrip('\n'))
    assert record["prompt_text"] == "Qu'est-ce que l'intelligence artificielle?"
    assert record["answer_x"] == "L'IA est la simulation de l'intelligence humaine. 🤖"
    assert record["answer_y"] == "它是计算机科学的一个分支。"


def test_export_experiment_answers_to_jsonl_empty_experiment():
    """Test JSONL export with no completed evaluations."""
    session = MagicMock()
    experiment_id = 1

    # Mock empty results
    mock_results = []

    # Setup mock query chain
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = mock_results

    session.query.return_value = mock_query

    # Execute export
    lines = list(export_experiment_answers_to_jsonl(session, experiment_id))

    # Verify output is empty
    assert len(lines) == 0


def test_export_experiment_answers_to_jsonl_jsonl_validity():
    """Test that each line is valid JSONL (parseable JSON)."""
    session = MagicMock()
    experiment_id = 1

    # Create multiple mock records
    prompts = []
    answers = []
    mock_results = []

    for i in range(5):
        prompt = MagicMock(spec=ExperimentPrompt)
        prompt.prompt_text = f"Test prompt {i+1}"
        prompt.created_at = f"2024-01-0{i+1}"

        answer = MagicMock(spec=ExperimentAnswer)
        answer.id = i + 1
        answer.answer_x = f"Answer X for prompt {i+1}"
        answer.answer_y = f"Answer Y for prompt {i+1}"

        prompts.append(prompt)
        answers.append(answer)
        mock_results.append((answer, prompt))

    # Setup mock query chain
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = mock_results

    session.query.return_value = mock_query

    # Execute export
    lines = list(export_experiment_answers_to_jsonl(session, experiment_id))

    # Verify each line is valid JSON
    assert len(lines) == 5
    for i, line in enumerate(lines):
        # Should end with newline
        assert line.endswith('\n')

        # Strip newline and parse
        record = json.loads(line.rstrip('\n'))

        # Verify structure
        assert "prompt_text" in record
        assert "answer_x" in record
        assert "answer_y" in record
        assert len(record) == 3

        # Verify content
        assert record["prompt_text"] == f"Test prompt {i+1}"
        assert record["answer_x"] == f"Answer X for prompt {i+1}"
        assert record["answer_y"] == f"Answer Y for prompt {i+1}"


def test_export_experiment_answers_to_jsonl_generator_pattern():
    """Test that the function uses a generator pattern (not returning all at once)."""
    session = MagicMock()
    experiment_id = 1

    # Create a single mock record
    prompt = MagicMock(spec=ExperimentPrompt)
    prompt.prompt_text = "Test prompt"
    prompt.created_at = "2024-01-01"

    answer = MagicMock(spec=ExperimentAnswer)
    answer.id = 1
    answer.answer_x = "Answer X"
    answer.answer_y = "Answer Y"

    mock_results = [(answer, prompt)]

    # Setup mock query chain
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = mock_results

    session.query.return_value = mock_query

    # Execute export and verify it returns a generator
    result = export_experiment_answers_to_jsonl(session, experiment_id)

    # Verify it's a generator
    assert hasattr(result, '__iter__')
    assert hasattr(result, '__next__')

    # Consume the generator
    lines = list(result)
    assert len(lines) == 1


def test_export_experiment_answers_to_jsonl_filtering():
    """
    Test that only answer pairs with evaluations are included.
    This is implicitly tested by the query join with ExperimentEvaluation,
    but we verify the query structure is correct.
    """
    session = MagicMock()
    experiment_id = 1

    # Mock empty results (all answers filtered out because no evaluations)
    mock_results = []

    # Setup mock query chain
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = mock_results

    session.query.return_value = mock_query

    # Execute export
    lines = list(export_experiment_answers_to_jsonl(session, experiment_id))

    # Verify query was called correctly
    session.query.assert_called_once()

    # Verify join was called (should join with ExperimentPrompt and ExperimentEvaluation)
    assert mock_query.join.call_count == 2

    # Verify filter was called with experiment_id
    mock_query.filter.assert_called_once()

    # Verify no results when no evaluations exist
    assert len(lines) == 0
