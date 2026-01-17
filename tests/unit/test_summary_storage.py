import json
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from vulcanlab.data.models.summary_result import SummaryResult
from vulcanlab.summarization.summary_storage import (
    parse_llm_response,
    validate_heading_ids,
    save_summaries,
    delete_existing_summaries,
    process_llm_response,
    SummaryParseResult
)


def test_parse_llm_response_valid():
    response = '[{"id": 1, "summary": "Summary 1"}, {"id": "2", "summary": "Summary 2"}]'
    items, errors = parse_llm_response(response)
    assert len(items) == 2
    assert items[0] == {"id": 1, "summary": "Summary 1"}
    assert items[1] == {"id": 2, "summary": "Summary 2"}
    assert len(errors) == 0


def test_parse_llm_response_invalid_json():
    response = '{"id": 1, "summary": "Summary 1"}' # Not an array
    items, errors = parse_llm_response(response)
    assert len(items) == 0
    assert "LLM response must be a JSON array" in errors[0]

    response = 'invalid json'
    items, errors = parse_llm_response(response)
    assert len(items) == 0
    assert "Invalid JSON syntax" in errors[0]


def test_parse_llm_response_missing_fields():
    response = '[{"id": 1}, {"summary": "Summary 2"}]'
    items, errors = parse_llm_response(response)
    assert len(items) == 0
    assert len(errors) == 2
    assert "missing 'summary' field" in errors[0]
    assert "missing 'id' field" in errors[1]


def test_parse_llm_response_invalid_types():
    response = '[{"id": "abc", "summary": "Summary 1"}, {"id": 2, "summary": 123}]'
    items, errors = parse_llm_response(response)
    assert len(items) == 0
    assert len(errors) == 2
    assert "must be a valid integer" in errors[0]
    assert "must be a string" in errors[1]


def test_validate_heading_ids():
    parsed_items = [
        {"id": 1, "summary": "S1"},
        {"id": 2, "summary": "S2"},
        {"id": 3, "summary": "S3"},
    ]
    expected_ids = [1, 2, 4]
    
    valid_items, warnings = validate_heading_ids(parsed_items, expected_ids)
    
    assert len(valid_items) == 2
    assert valid_items[0]["id"] == 1
    assert valid_items[1]["id"] == 2
    
    assert any("Unexpected heading ID" in w and "3" in w for w in warnings)
    assert any("Missing summaries" in w and "4" in w for w in warnings)


def test_validate_heading_ids_duplicates():
    parsed_items = [
        {"id": 1, "summary": "S1"},
        {"id": 1, "summary": "S1-duplicate"},
    ]
    expected_ids = [1]
    
    valid_items, warnings = validate_heading_ids(parsed_items, expected_ids)
    
    assert len(valid_items) == 1
    assert any("Duplicate heading ID" in w and "1" in w for w in warnings)


def test_save_summaries_inserts_and_updates():
    mock_session = MagicMock(spec=Session)
    
    # Mock existing result for id=1
    existing_result = SummaryResult(work_id=10, chunk_id=1, summary_content="Old S1", prompt_index=0)
    
    def mock_query_filter_by(work_id, chunk_id):
        mock_query = MagicMock()
        if chunk_id == 1:
            mock_query.first.return_value = existing_result
        else:
            mock_query.first.return_value = None
        return mock_query

    mock_session.query.return_value.filter_by.side_effect = mock_query_filter_by
    
    items = [
        {"id": 1, "summary": "New S1"},
        {"id": 2, "summary": "S2"},
    ]
    
    count = save_summaries(work_id=10, items=items, prompt_index=1, session=mock_session)
    
    assert count == 2
    assert existing_result.summary_content == "New S1"
    assert existing_result.prompt_index == 1
    
    # Verify add was called for the new item (id=2)
    # The first call was query, the second should be add
    assert mock_session.add.called
    new_call_args = mock_session.add.call_args[0][0]
    assert isinstance(new_call_args, SummaryResult)
    assert new_call_args.chunk_id == 2
    assert new_call_args.summary_content == "S2"
    assert new_call_args.prompt_index == 1


def test_delete_existing_summaries():
    mock_session = MagicMock(spec=Session)
    mock_execute_result = MagicMock()
    mock_execute_result.rowcount = 5
    mock_session.execute.return_value = mock_execute_result
    
    count = delete_existing_summaries(work_id=10, session=mock_session)
    
    assert count == 5
    assert mock_session.execute.call_count == 2 # Delete chunks, then results


def test_process_llm_response_happy_path():
    mock_session = MagicMock(spec=Session)
    
    # Mock save_summaries to return 2
    with patch("vulcanlab.summarization.summary_storage.save_summaries") as mock_save:
        mock_save.return_value = 2
        
        response = '[{"id": 1, "summary": "S1"}, {"id": 2, "summary": "S2"}]'
        expected_ids = [1, 2]
        
        result = process_llm_response(
            work_id=10, 
            prompt_index=1, 
            response_json=response, 
            expected_heading_ids=expected_ids, 
            session=mock_session
        )
        
        assert result.success is True
        assert result.summaries_saved == 2
        assert len(result.errors) == 0
        assert mock_session.commit.called


def test_process_llm_response_partial_failure():
    mock_session = MagicMock(spec=Session)
    
    with patch("vulcanlab.summarization.summary_storage.save_summaries") as mock_save:
        mock_save.return_value = 1
        
        # ID 3 is unexpected, ID 2 is missing
        response = '[{"id": 1, "summary": "S1"}, {"id": 3, "summary": "S3"}]'
        expected_ids = [1, 2]
        
        result = process_llm_response(
            work_id=10, 
            prompt_index=1, 
            response_json=response, 
            expected_heading_ids=expected_ids, 
            session=mock_session
        )
        
        assert result.success is True
        assert result.summaries_saved == 1
        # Should have warnings for unexpected ID 3 and missing ID 2
        assert len(result.errors) == 2
        assert any("Unexpected" in e for e in result.errors)
        assert any("Missing" in e for e in result.errors)
        assert mock_session.commit.called


def test_process_llm_response_db_error():
    mock_session = MagicMock(spec=Session)
    mock_session.commit.side_effect = Exception("DB Fail")
    
    response = '[{"id": 1, "summary": "S1"}]'
    expected_ids = [1]
    
    result = process_llm_response(
        work_id=10, 
        prompt_index=1, 
        response_json=response, 
        expected_heading_ids=expected_ids, 
        session=mock_session
    )
    
    assert result.success is False
    assert any("Database error: DB Fail" in e for e in result.errors)
    assert mock_session.rollback.called
