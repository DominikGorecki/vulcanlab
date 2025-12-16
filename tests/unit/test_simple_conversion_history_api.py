"""Unit tests for simple conversion history API endpoint."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC

from vulcanlab_api.routers.simple_conversion import router
from vulcanlab_api.dependencies import get_db_session
from fastapi import FastAPI


# Global mock session to control in tests
mock_session_instance = None


def get_mock_db_session():
    """Override dependency to return controllable mock session."""
    return mock_session_instance


app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db_session] = get_mock_db_session

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_session():
    """Reset mock session before each test."""
    global mock_session_instance
    mock_session_instance = MagicMock()
    yield
    mock_session_instance = None


@patch('vulcanlab_api.routers.simple_conversion.get_simple_conversion_history')
def test_get_history_success(mock_get_history):
    """Test GET /api/simple-conversion/history returns list of works."""
    # Mock history data
    mock_get_history.return_value = [
        {
            'work_id': 1,
            'title': 'Book One',
            'author': 'Author One',
            'year': 2024,
            'created_at': datetime(2024, 1, 15, tzinfo=UTC),
            'classification': 'small',
            'mode': 'automatic',
            'status': 'complete',
            'token_count': 15000,
            'chunk_count': 10,
            'heading_chunk_count': 3,
            'content_chunk_count': 7,
            'error_message': None
        },
        {
            'work_id': 2,
            'title': 'Book Two',
            'author': 'Author Two',
            'year': 2023,
            'created_at': datetime(2024, 1, 10, tzinfo=UTC),
            'classification': 'large',
            'mode': 'manual',
            'status': 'complete',
            'token_count': 45000,
            'chunk_count': 25,
            'heading_chunk_count': 8,
            'content_chunk_count': 17,
            'error_message': None
        }
    ]

    response = client.get('/api/simple-conversion/history')

    assert response.status_code == 200
    data = response.json()

    assert 'items' in data
    assert len(data['items']) == 2

    # Check first item
    assert data['items'][0]['work_id'] == 1
    assert data['items'][0]['title'] == 'Book One'
    assert data['items'][0]['classification'] == 'small'
    assert data['items'][0]['mode'] == 'automatic'
    assert data['items'][0]['status'] == 'complete'
    assert data['items'][0]['chunk_count'] == 10

    # Check second item
    assert data['items'][1]['work_id'] == 2
    assert data['items'][1]['title'] == 'Book Two'
    assert data['items'][1]['classification'] == 'large'
    assert data['items'][1]['mode'] == 'manual'


@patch('vulcanlab_api.routers.simple_conversion.get_simple_conversion_history')
def test_get_history_empty(mock_get_history):
    """Test GET /api/simple-conversion/history returns empty array when no conversions exist."""
    # Mock empty history
    mock_get_history.return_value = []

    response = client.get('/api/simple-conversion/history')

    assert response.status_code == 200
    data = response.json()

    assert 'items' in data
    assert len(data['items']) == 0


@patch('vulcanlab_api.routers.simple_conversion.get_simple_conversion_history')
def test_get_history_failed_conversion(mock_get_history):
    """Test GET /api/simple-conversion/history includes failed conversions with error message."""
    # Mock history with failed conversion
    mock_get_history.return_value = [
        {
            'work_id': 1,
            'title': 'Failed Book',
            'author': 'Author',
            'year': 2024,
            'created_at': datetime(2024, 1, 15, tzinfo=UTC),
            'classification': None,
            'mode': 'automatic',
            'status': 'failed',
            'token_count': None,
            'chunk_count': 0,
            'heading_chunk_count': 0,
            'content_chunk_count': 0,
            'error_message': 'Parse failed: invalid document structure'
        }
    ]

    response = client.get('/api/simple-conversion/history')

    assert response.status_code == 200
    data = response.json()

    assert len(data['items']) == 1
    assert data['items'][0]['status'] == 'failed'
    assert data['items'][0]['error_message'] == 'Parse failed: invalid document structure'


@patch('vulcanlab_api.routers.simple_conversion.get_simple_conversion_history')
def test_get_history_sorted_by_date(mock_get_history):
    """Test GET /api/simple-conversion/history returns items sorted by created_at DESC."""
    # Mock history data in DESC order
    mock_get_history.return_value = [
        {
            'work_id': 2,
            'title': 'Newer Book',
            'author': 'Author 2',
            'year': 2024,
            'created_at': datetime(2024, 1, 20, tzinfo=UTC),
            'classification': 'small',
            'mode': 'manual',
            'status': 'complete',
            'token_count': 12000,
            'chunk_count': 8,
            'heading_chunk_count': 2,
            'content_chunk_count': 6,
            'error_message': None
        },
        {
            'work_id': 1,
            'title': 'Older Book',
            'author': 'Author 1',
            'year': 2023,
            'created_at': datetime(2024, 1, 10, tzinfo=UTC),
            'classification': 'large',
            'mode': 'automatic',
            'status': 'complete',
            'token_count': 40000,
            'chunk_count': 20,
            'heading_chunk_count': 7,
            'content_chunk_count': 13,
            'error_message': None
        }
    ]

    response = client.get('/api/simple-conversion/history')

    assert response.status_code == 200
    data = response.json()

    assert len(data['items']) == 2
    # Most recent first
    assert data['items'][0]['work_id'] == 2
    assert data['items'][0]['title'] == 'Newer Book'
    # Older second
    assert data['items'][1]['work_id'] == 1
    assert data['items'][1]['title'] == 'Older Book'


@patch('vulcanlab_api.routers.simple_conversion.get_simple_conversion_history')
def test_get_history_all_fields_present(mock_get_history):
    """Test GET /api/simple-conversion/history includes all required fields."""
    # Mock complete history item
    mock_get_history.return_value = [
        {
            'work_id': 1,
            'title': 'Complete Book',
            'author': 'Test Author',
            'year': 2024,
            'created_at': datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
            'classification': 'small',
            'mode': 'automatic',
            'status': 'complete',
            'token_count': 15000,
            'chunk_count': 10,
            'heading_chunk_count': 3,
            'content_chunk_count': 7,
            'error_message': None
        }
    ]

    response = client.get('/api/simple-conversion/history')

    assert response.status_code == 200
    data = response.json()

    assert len(data['items']) == 1
    item = data['items'][0]

    # Check all required fields are present
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


@patch('vulcanlab_api.routers.simple_conversion.get_simple_conversion_history')
def test_get_history_chunk_counts(mock_get_history):
    """Test GET /api/simple-conversion/history correctly reports chunk counts."""
    # Mock history with chunk counts
    mock_get_history.return_value = [
        {
            'work_id': 1,
            'title': 'Test Book',
            'author': 'Author',
            'year': 2024,
            'created_at': datetime(2024, 1, 15, tzinfo=UTC),
            'classification': 'large',
            'mode': 'automatic',
            'status': 'complete',
            'token_count': 40000,
            'chunk_count': 30,  # Total chunks
            'heading_chunk_count': 10,  # H1-H5
            'content_chunk_count': 20,  # Content chunks
            'error_message': None
        }
    ]

    response = client.get('/api/simple-conversion/history')

    assert response.status_code == 200
    data = response.json()

    assert len(data['items']) == 1
    item = data['items'][0]

    # Verify chunk counts
    assert item['chunk_count'] == 30
    assert item['heading_chunk_count'] == 10
    assert item['content_chunk_count'] == 20
    # Verify heading + content <= total
    assert item['heading_chunk_count'] + item['content_chunk_count'] <= item['chunk_count']


@patch('vulcanlab_api.routers.simple_conversion.get_simple_conversion_history')
def test_get_history_null_values(mock_get_history):
    """Test GET /api/simple-conversion/history handles null/missing values."""
    # Mock history with null values
    mock_get_history.return_value = [
        {
            'work_id': 1,
            'title': 'Minimal Book',
            'author': None,
            'year': None,
            'created_at': datetime(2024, 1, 15, tzinfo=UTC),
            'classification': None,
            'mode': 'manual',
            'status': 'complete',
            'token_count': None,
            'chunk_count': 0,
            'heading_chunk_count': 0,
            'content_chunk_count': 0,
            'error_message': None
        }
    ]

    response = client.get('/api/simple-conversion/history')

    assert response.status_code == 200
    data = response.json()

    assert len(data['items']) == 1
    item = data['items'][0]

    # Check null values are handled
    assert item['author'] is None
    assert item['year'] is None
    assert item['classification'] is None
    assert item['token_count'] is None
    assert item['error_message'] is None


@patch('vulcanlab_api.routers.simple_conversion.get_simple_conversion_history')
def test_get_history_database_error(mock_get_history):
    """Test GET /api/simple-conversion/history handles database errors."""
    # Mock database error
    mock_get_history.side_effect = Exception("Database connection failed")

    response = client.get('/api/simple-conversion/history')

    # Should return 500 error
    assert response.status_code == 500


@patch('vulcanlab_api.routers.simple_conversion.get_simple_conversion_history')
def test_get_history_mixed_statuses(mock_get_history):
    """Test GET /api/simple-conversion/history includes both complete and failed conversions."""
    # Mock mixed history
    mock_get_history.return_value = [
        {
            'work_id': 1,
            'title': 'Success Book',
            'author': 'Author 1',
            'year': 2024,
            'created_at': datetime(2024, 1, 15, tzinfo=UTC),
            'classification': 'small',
            'mode': 'automatic',
            'status': 'complete',
            'token_count': 15000,
            'chunk_count': 10,
            'heading_chunk_count': 3,
            'content_chunk_count': 7,
            'error_message': None
        },
        {
            'work_id': 2,
            'title': 'Failed Book',
            'author': 'Author 2',
            'year': 2024,
            'created_at': datetime(2024, 1, 10, tzinfo=UTC),
            'classification': 'large',
            'mode': 'manual',
            'status': 'failed',
            'token_count': 40000,
            'chunk_count': 0,
            'heading_chunk_count': 0,
            'content_chunk_count': 0,
            'error_message': 'Sanitization timeout'
        }
    ]

    response = client.get('/api/simple-conversion/history')

    assert response.status_code == 200
    data = response.json()

    assert len(data['items']) == 2

    # Check complete conversion
    assert data['items'][0]['status'] == 'complete'
    assert data['items'][0]['error_message'] is None

    # Check failed conversion
    assert data['items'][1]['status'] == 'failed'
    assert data['items'][1]['error_message'] == 'Sanitization timeout'
