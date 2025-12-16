"""Unit tests for simple conversion history query logic."""

import pytest
from unittest.mock import MagicMock, PropertyMock
from datetime import datetime, UTC

from vulcanlab.simple_conversion.history import get_simple_conversion_history
from vulcanlab.data.models.enums import DocumentClassification


def test_history_returns_empty_list_when_no_works():
    """Test query returns empty list when no simple conversion works exist."""
    mock_session = MagicMock()

    # Mock query to return empty result
    mock_session.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []

    result = get_simple_conversion_history(mock_session)

    assert result == []


def test_history_returns_works_with_simple_conversion_mode():
    """Test query returns works with simple_conversion_mode in processing_status."""
    mock_session = MagicMock()

    # Create mock row with simple_conversion_mode
    mock_row = MagicMock()
    mock_row.work_id = 1
    mock_row.title = "Test Book"
    mock_row.author = "Test Author"
    mock_row.year = 2024
    mock_row.created_at = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
    mock_row.processing_status = {
        'simple_conversion_mode': 'automatic',
        'simple_conversion_step': 'complete'
    }

    # Mock classification
    mock_classification = MagicMock()
    type(mock_classification).value = PropertyMock(return_value='small')
    mock_row.classification = mock_classification

    mock_row.token_count = 15000
    mock_row.chunk_count = 10
    mock_row.heading_chunk_count = 3
    mock_row.content_chunk_count = 7

    # Mock query to return the row
    mock_session.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [mock_row]

    result = get_simple_conversion_history(mock_session)

    assert len(result) == 1
    assert result[0]['work_id'] == 1
    assert result[0]['title'] == "Test Book"
    assert result[0]['mode'] == 'automatic'


def test_history_sorts_by_created_at_desc():
    """Test query sorts results by created_at DESC (most recent first)."""
    mock_session = MagicMock()

    # Create mock rows with different timestamps
    mock_row1 = MagicMock()
    mock_row1.work_id = 1
    mock_row1.title = "Older Book"
    mock_row1.author = "Author 1"
    mock_row1.year = None
    mock_row1.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    mock_row1.processing_status = {
        'simple_conversion_mode': 'automatic',
        'simple_conversion_step': 'complete'
    }
    mock_row1.classification = None
    mock_row1.token_count = 10000
    mock_row1.chunk_count = 5
    mock_row1.heading_chunk_count = 2
    mock_row1.content_chunk_count = 3

    mock_row2 = MagicMock()
    mock_row2.work_id = 2
    mock_row2.title = "Newer Book"
    mock_row2.author = "Author 2"
    mock_row2.year = 2024
    mock_row2.created_at = datetime(2024, 1, 15, tzinfo=UTC)
    mock_row2.processing_status = {
        'simple_conversion_mode': 'manual',
        'simple_conversion_step': 'complete'
    }
    mock_row2.classification = None
    mock_row2.token_count = 20000
    mock_row2.chunk_count = 12
    mock_row2.heading_chunk_count = 4
    mock_row2.content_chunk_count = 8

    # Return in DESC order (newer first)
    mock_session.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [mock_row2, mock_row1]

    result = get_simple_conversion_history(mock_session)

    assert len(result) == 2
    assert result[0]['work_id'] == 2  # Newer first
    assert result[1]['work_id'] == 1  # Older second


def test_history_chunk_count_aggregation():
    """Test chunk count aggregation correctly differentiates heading vs content chunks."""
    mock_session = MagicMock()

    mock_row = MagicMock()
    mock_row.work_id = 1
    mock_row.title = "Test Book"
    mock_row.author = "Author"
    mock_row.year = 2024
    mock_row.created_at = datetime(2024, 1, 15, tzinfo=UTC)
    mock_row.processing_status = {
        'simple_conversion_mode': 'automatic',
        'simple_conversion_step': 'complete'
    }
    mock_row.classification = None
    mock_row.token_count = 15000
    # 5 heading chunks (H1-H5) + 10 content chunks = 15 total
    mock_row.chunk_count = 15
    mock_row.heading_chunk_count = 5
    mock_row.content_chunk_count = 10

    mock_session.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [mock_row]

    result = get_simple_conversion_history(mock_session)

    assert len(result) == 1
    assert result[0]['chunk_count'] == 15
    assert result[0]['heading_chunk_count'] == 5
    assert result[0]['content_chunk_count'] == 10


def test_history_status_complete():
    """Test status determination: complete when simple_conversion_step = 'complete'."""
    mock_session = MagicMock()

    mock_row = MagicMock()
    mock_row.work_id = 1
    mock_row.title = "Complete Book"
    mock_row.author = "Author"
    mock_row.year = 2024
    mock_row.created_at = datetime(2024, 1, 15, tzinfo=UTC)
    mock_row.processing_status = {
        'simple_conversion_mode': 'automatic',
        'simple_conversion_step': 'complete'
    }
    mock_row.classification = None
    mock_row.token_count = 15000
    mock_row.chunk_count = 10
    mock_row.heading_chunk_count = 3
    mock_row.content_chunk_count = 7

    mock_session.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [mock_row]

    result = get_simple_conversion_history(mock_session)

    assert len(result) == 1
    assert result[0]['status'] == 'complete'
    assert result[0]['error_message'] is None


def test_history_status_failed_with_error():
    """Test status determination: failed when simple_conversion_error exists."""
    mock_session = MagicMock()

    mock_row = MagicMock()
    mock_row.work_id = 1
    mock_row.title = "Failed Book"
    mock_row.author = "Author"
    mock_row.year = 2024
    mock_row.created_at = datetime(2024, 1, 15, tzinfo=UTC)
    mock_row.processing_status = {
        'simple_conversion_mode': 'automatic',
        'simple_conversion_step': 'parsing',
        'simple_conversion_error': 'Failed to parse document'
    }
    mock_row.classification = None
    mock_row.token_count = None
    mock_row.chunk_count = 0
    mock_row.heading_chunk_count = 0
    mock_row.content_chunk_count = 0

    mock_session.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [mock_row]

    result = get_simple_conversion_history(mock_session)

    assert len(result) == 1
    assert result[0]['status'] == 'failed'
    assert result[0]['error_message'] == 'Failed to parse document'


def test_history_status_failed_step():
    """Test status determination: failed when simple_conversion_step = 'failed'."""
    mock_session = MagicMock()

    mock_row = MagicMock()
    mock_row.work_id = 1
    mock_row.title = "Failed Book"
    mock_row.author = "Author"
    mock_row.year = 2024
    mock_row.created_at = datetime(2024, 1, 15, tzinfo=UTC)
    mock_row.processing_status = {
        'simple_conversion_mode': 'manual',
        'simple_conversion_step': 'failed',
        'error_message': 'Sanitization failed'
    }
    mock_row.classification = None
    mock_row.token_count = None
    mock_row.chunk_count = 0
    mock_row.heading_chunk_count = 0
    mock_row.content_chunk_count = 0

    mock_session.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [mock_row]

    result = get_simple_conversion_history(mock_session)

    assert len(result) == 1
    assert result[0]['status'] == 'failed'
    assert result[0]['error_message'] == 'Sanitization failed'


def test_history_error_message_extraction():
    """Test error message extracted correctly from processing_status JSON."""
    mock_session = MagicMock()

    mock_row = MagicMock()
    mock_row.work_id = 1
    mock_row.title = "Error Book"
    mock_row.author = "Author"
    mock_row.year = 2024
    mock_row.created_at = datetime(2024, 1, 15, tzinfo=UTC)
    mock_row.processing_status = {
        'simple_conversion_mode': 'automatic',
        'simple_conversion_step': 'sanitizing',
        'simple_conversion_error': 'LLM API timeout'
    }
    mock_row.classification = None
    mock_row.token_count = 15000
    mock_row.chunk_count = 0
    mock_row.heading_chunk_count = 0
    mock_row.content_chunk_count = 0

    mock_session.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [mock_row]

    result = get_simple_conversion_history(mock_session)

    assert len(result) == 1
    assert result[0]['error_message'] == 'LLM API timeout'


def test_history_mode_extraction():
    """Test mode extracted correctly (automatic/manual) from processing_status."""
    mock_session = MagicMock()

    # Test automatic mode
    mock_row1 = MagicMock()
    mock_row1.work_id = 1
    mock_row1.title = "Auto Book"
    mock_row1.author = "Author 1"
    mock_row1.year = 2024
    mock_row1.created_at = datetime(2024, 1, 15, tzinfo=UTC)
    mock_row1.processing_status = {
        'simple_conversion_mode': 'automatic',
        'simple_conversion_step': 'complete'
    }
    mock_row1.classification = None
    mock_row1.token_count = 15000
    mock_row1.chunk_count = 10
    mock_row1.heading_chunk_count = 3
    mock_row1.content_chunk_count = 7

    # Test manual mode
    mock_row2 = MagicMock()
    mock_row2.work_id = 2
    mock_row2.title = "Manual Book"
    mock_row2.author = "Author 2"
    mock_row2.year = 2024
    mock_row2.created_at = datetime(2024, 1, 16, tzinfo=UTC)
    mock_row2.processing_status = {
        'simple_conversion_mode': 'manual',
        'simple_conversion_step': 'complete'
    }
    mock_row2.classification = None
    mock_row2.token_count = 20000
    mock_row2.chunk_count = 15
    mock_row2.heading_chunk_count = 5
    mock_row2.content_chunk_count = 10

    mock_session.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [mock_row2, mock_row1]

    result = get_simple_conversion_history(mock_session)

    assert len(result) == 2
    assert result[0]['mode'] == 'manual'
    assert result[1]['mode'] == 'automatic'


def test_history_includes_all_required_fields():
    """Test response includes all required fields per spec."""
    mock_session = MagicMock()

    mock_row = MagicMock()
    mock_row.work_id = 1
    mock_row.title = "Complete Book"
    mock_row.author = "Test Author"
    mock_row.year = 2024
    mock_row.created_at = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
    mock_row.processing_status = {
        'simple_conversion_mode': 'automatic',
        'simple_conversion_step': 'complete'
    }

    # Mock classification with enum-like behavior
    mock_classification = MagicMock()
    type(mock_classification).value = PropertyMock(return_value='small')
    mock_row.classification = mock_classification

    mock_row.token_count = 15000
    mock_row.chunk_count = 10
    mock_row.heading_chunk_count = 3
    mock_row.content_chunk_count = 7

    mock_session.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [mock_row]

    result = get_simple_conversion_history(mock_session)

    assert len(result) == 1
    item = result[0]

    # Check all required fields exist
    assert 'work_id' in item
    assert 'title' in item
    assert 'author' in item
    assert 'year' in item
    assert 'created_at' in item
    assert 'classification' in item
    assert 'mode' in item
    assert 'status' in item
    assert 'token_count' in item
    assert 'chunk_count' in item
    assert 'heading_chunk_count' in item
    assert 'content_chunk_count' in item
    assert 'error_message' in item

    # Check values
    assert item['work_id'] == 1
    assert item['title'] == "Complete Book"
    assert item['author'] == "Test Author"
    assert item['year'] == 2024
    assert item['classification'] == 'small'
    assert item['mode'] == 'automatic'
    assert item['status'] == 'complete'
    assert item['token_count'] == 15000
    assert item['chunk_count'] == 10
    assert item['heading_chunk_count'] == 3
    assert item['content_chunk_count'] == 7
    assert item['error_message'] is None


def test_history_handles_null_values():
    """Test query handles null/missing values gracefully."""
    mock_session = MagicMock()

    mock_row = MagicMock()
    mock_row.work_id = 1
    mock_row.title = "Minimal Book"
    mock_row.author = None  # No author
    mock_row.year = None  # No year
    mock_row.created_at = datetime(2024, 1, 15, tzinfo=UTC)
    mock_row.processing_status = {
        'simple_conversion_mode': 'manual',
        'simple_conversion_step': 'complete'
    }
    mock_row.classification = None  # Not yet classified
    mock_row.token_count = None  # Not yet counted
    mock_row.chunk_count = 0  # No chunks yet
    mock_row.heading_chunk_count = 0
    mock_row.content_chunk_count = 0

    mock_session.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [mock_row]

    result = get_simple_conversion_history(mock_session)

    assert len(result) == 1
    assert result[0]['work_id'] == 1
    assert result[0]['author'] is None
    assert result[0]['year'] is None
    assert result[0]['classification'] is None
    assert result[0]['token_count'] is None
    assert result[0]['chunk_count'] == 0
