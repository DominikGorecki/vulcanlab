"""Unit tests for simple conversion API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC

from vulcanlab_api.routers.simple_conversion import router
from vulcanlab_api.dependencies import get_db_session


# Mock app for testing
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


@patch('vulcanlab_api.routers.simple_conversion.Work')
def test_start_conversion_success(mock_work_class):
    """Test POST /api/simple-conversion/start creates work successfully."""
    # Mock Work instance
    mock_work = MagicMock()
    mock_work.id = 42
    mock_work.processing_status = {}
    mock_work_class.return_value = mock_work

    response = client.post(
        '/api/simple-conversion/start',
        json={
            'file_path': '/path/to/test.pdf',
            'title': 'Test Book',
            'author': 'Test Author',
            'year': 2024,
            'mode': 'automatic'
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data['work_id'] == 42
    assert data['status'] == 'converting'
    assert 'automatic' in data['message']


def test_start_conversion_invalid_mode():
    """Test POST /api/simple-conversion/start rejects invalid mode."""
    response = client.post(
        '/api/simple-conversion/start',
        json={
            'file_path': '/path/to/test.pdf',
            'title': 'Test Book',
            'author': 'Test Author',
            'mode': 'invalid_mode'
        }
    )

    assert response.status_code == 422  # Pydantic validation error


def test_get_status_success():
    """Test GET /api/simple-conversion/status/{work_id} returns status."""
    mock_work = MagicMock()
    mock_work.id = 123
    mock_work.processing_status = {
        'simple_conversion_step': 'parsed',
        'simple_conversion_classification': 'small',
        'simple_conversion_token_count': 15000,
        'simple_conversion_mode': 'automatic'
    }

    # Configure mock session
    mock_session_instance.query.return_value.filter.return_value.first.return_value = mock_work

    response = client.get('/api/simple-conversion/status/123')

    assert response.status_code == 200
    data = response.json()
    assert data['work_id'] == 123
    assert data['step'] == 'parsed'
    assert data['classification'] == 'small'
    assert data['token_count'] == 15000
    assert data['mode'] == 'automatic'


def test_get_status_work_not_found():
    """Test GET /api/simple-conversion/status/{work_id} handles missing work."""
    # Configure mock session to return None
    mock_session_instance.query.return_value.filter.return_value.first.return_value = None

    response = client.get('/api/simple-conversion/status/999')

    assert response.status_code == 404


@patch('vulcanlab_api.routers.simple_conversion.parse_and_classify')
@patch('vulcanlab_api.routers.simple_conversion.sanitize_small_document')
@patch('vulcanlab_api.routers.simple_conversion.create_chunks_from_sanitized')
def test_execute_automatic_small_document(mock_chunk, mock_sanitize, mock_parse):
    """Test POST /api/simple-conversion/execute-auto/{work_id} for small document."""
    # Mock work
    mock_work = MagicMock()
    mock_work.id = 100
    mock_work.processing_status = {}

    # Configure mock session
    mock_session_instance.query.return_value.filter.return_value.first.return_value = mock_work

    # Mock parsed (small classification)
    mock_parsed = MagicMock()
    mock_parsed.classification.value = 'small'
    mock_parse.return_value = mock_parsed

    # Mock sanitized
    mock_sanitized = MagicMock()
    mock_sanitize.return_value = mock_sanitized

    # Mock chunks
    mock_chunks = [MagicMock() for _ in range(8)]
    mock_chunk.return_value = mock_chunks

    response = client.post('/api/simple-conversion/execute-auto/100')

    assert response.status_code == 200
    data = response.json()
    assert data['work_id'] == 100
    assert data['status'] == 'complete'
    assert data['chunks_created'] == 8

    # Verify pipeline was called
    mock_parse.assert_called_once_with(100, mock_session_instance)
    mock_sanitize.assert_called_once_with(100, mock_session_instance)
    mock_chunk.assert_called_once_with(100, mock_session_instance)


@patch('vulcanlab_api.routers.simple_conversion.parse_and_classify')
@patch('vulcanlab_api.routers.simple_conversion.sanitize_large_document')
@patch('vulcanlab_api.routers.simple_conversion.create_chunks_from_sanitized')
def test_execute_automatic_large_document(mock_chunk, mock_sanitize, mock_parse):
    """Test POST /api/simple-conversion/execute-auto/{work_id} for large document."""
    # Mock work
    mock_work = MagicMock()
    mock_work.id = 200
    mock_work.processing_status = {}

    # Configure mock session
    mock_session_instance.query.return_value.filter.return_value.first.return_value = mock_work

    # Mock parsed (large classification)
    mock_parsed = MagicMock()
    mock_parsed.classification.value = 'large'
    mock_parse.return_value = mock_parsed

    # Mock sanitized
    mock_sanitized = MagicMock()
    mock_sanitize.return_value = mock_sanitized

    # Mock chunks
    mock_chunks = [MagicMock() for _ in range(25)]
    mock_chunk.return_value = mock_chunks

    response = client.post('/api/simple-conversion/execute-auto/200')

    assert response.status_code == 200
    data = response.json()
    assert data['work_id'] == 200
    assert data['status'] == 'complete'
    assert data['chunks_created'] == 25

    # Verify large sanitization was called
    mock_sanitize.assert_called_once_with(200, mock_session_instance)


def test_execute_automatic_work_not_found():
    """Test POST /api/simple-conversion/execute-auto/{work_id} handles missing work."""
    # Configure mock session to return None
    mock_session_instance.query.return_value.filter.return_value.first.return_value = None

    response = client.post('/api/simple-conversion/execute-auto/999')
    assert response.status_code == 404


@patch('vulcanlab_api.routers.simple_conversion.parse_and_classify')
def test_execute_automatic_pipeline_error(mock_parse):
    """Test POST /api/simple-conversion/execute-auto/{work_id} handles errors."""
    # Mock work exists
    mock_work = MagicMock()
    mock_work.id = 300
    mock_work.processing_status = {}

    # Configure mock session
    mock_session_instance.query.return_value.filter.return_value.first.return_value = mock_work

    # Simulate parse error
    mock_parse.side_effect = Exception("Parse failed")

    response = client.post('/api/simple-conversion/execute-auto/300')

    assert response.status_code == 500


@patch('vulcanlab_api.routers.simple_conversion.load_template')
def test_get_manual_prompt_small_document(mock_load_template):
    """Test GET /api/simple-conversion/manual-prompt/{work_id} for small document."""
    # Mock parsed markdown
    mock_parsed = MagicMock()
    mock_parsed.classification.value = 'small'
    mock_parsed.content = "# Test Document\n\nContent here."

    # Configure mock session
    mock_session_instance.query.return_value.filter.return_value.first.return_value = mock_parsed

    # Mock template
    mock_template = MagicMock()
    mock_template.format.return_value = "Formatted prompt with markdown"
    mock_load_template.return_value = mock_template

    response = client.get('/api/simple-conversion/manual-prompt/100')

    assert response.status_code == 200
    data = response.json()
    assert data['work_id'] == 100
    assert data['classification'] == 'small'
    assert 'prompt' in data
    assert 'instructions' in data
    assert 'JSON' in data['instructions']


@patch('vulcanlab_api.routers.simple_conversion.parse_and_classify')
@patch('vulcanlab_api.routers.simple_conversion.extract_headings_with_context')
@patch('vulcanlab_api.routers.simple_conversion.create_condensed_markdown')
@patch('vulcanlab_api.routers.simple_conversion.load_template')
def test_get_manual_prompt_large_document(mock_load_template, mock_condensed, mock_extract, mock_parse):
    """Test GET /api/simple-conversion/manual-prompt/{work_id} for large document."""
    # Mock parse result
    mock_parsed = MagicMock()
    mock_parsed.classification.value = 'large'
    mock_parsed.content = "# Large Document\n\n" + ("Content " * 1000)
    mock_parse.return_value = mock_parsed

    # Configure mock session to return None (triggers parse_and_classify)
    mock_session_instance.query.return_value.filter.return_value.first.return_value = None

    # Mock heading extraction
    mock_headings = [
        {'level': 'H1', 'text': 'Chapter 1', 'context': 'Intro...'}
    ]
    mock_extract.return_value = mock_headings

    # Mock condensed markdown
    mock_condensed.return_value = "# Condensed version"

    # Mock template
    mock_template = MagicMock()
    mock_template.format.return_value = "Formatted prompt with condensed markdown"
    mock_load_template.return_value = mock_template

    response = client.get('/api/simple-conversion/manual-prompt/200')

    assert response.status_code == 200
    data = response.json()
    assert data['work_id'] == 200
    assert data['classification'] == 'large'
    assert 'LARGE document' in data['instructions']


@patch('vulcanlab_api.routers.simple_conversion.parse_llm_response')
@patch('vulcanlab_api.routers.simple_conversion.create_heading_modifications')
@patch('vulcanlab_api.routers.simple_conversion.create_chunks_from_sanitized')
@patch('vulcanlab_api.routers.simple_conversion.count_tokens')
@patch('vulcanlab_api.routers.simple_conversion.SanitizedMarkdown')
def test_submit_manual_result_small_document(mock_sanitized_class, mock_count_tokens, mock_chunk, mock_create_mods, mock_parse_llm):
    """Test POST /api/simple-conversion/manual-submit/{work_id} for small document."""
    # Mock parsed markdown (small classification)
    mock_parsed = MagicMock()
    mock_parsed.classification.value = 'small'

    # Mock work
    mock_work = MagicMock()
    mock_work.processing_status = {}

    # Configure mock session - first query returns parsed, second returns work
    mock_session_instance.query.return_value.filter.return_value.first.side_effect = [
        mock_parsed,  # ParsedMarkdown query
        mock_work     # Work query
    ]

    # Mock LLM response parsing
    mock_parse_llm.return_value = {
        'sanitized_markdown': "# Clean Document\n\nClean content.",
        'modifications': [{'heading': 'Chapter 1', 'action': 'keep'}]
    }

    # Mock token counting
    mock_count_tokens.return_value = 150

    # Mock chunks
    mock_chunks = [MagicMock() for _ in range(5)]
    mock_chunk.return_value = mock_chunks

    response = client.post(
        '/api/simple-conversion/manual-submit/100',
        json={'llm_response': '{"sanitized_markdown": "...", "modifications": [...]}'}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['work_id'] == 100
    assert data['status'] == 'complete'
    assert '5 chunks' in data['message']


@patch('vulcanlab_api.routers.simple_conversion.parse_llm_response_large')
@patch('vulcanlab_api.routers.simple_conversion.apply_modifications_to_markdown')
@patch('vulcanlab_api.routers.simple_conversion.extract_headings_with_context')
@patch('vulcanlab_api.routers.simple_conversion.create_heading_modifications_large')
@patch('vulcanlab_api.routers.simple_conversion.create_chunks_from_sanitized')
@patch('vulcanlab_api.routers.simple_conversion.count_tokens')
@patch('vulcanlab_api.routers.simple_conversion.SanitizedMarkdown')
def test_submit_manual_result_large_document(mock_sanitized_class, mock_count_tokens, mock_chunk, mock_create_mods, mock_extract, mock_apply, mock_parse_llm):
    """Test POST /api/simple-conversion/manual-submit/{work_id} for large document."""
    # Mock parsed markdown (large classification)
    mock_parsed = MagicMock()
    mock_parsed.classification.value = 'large'
    mock_parsed.content = "# Original Large Document"

    # Mock work
    mock_work = MagicMock()
    mock_work.processing_status = {}

    # Configure mock session - first query returns parsed, second returns work
    mock_session_instance.query.return_value.filter.return_value.first.side_effect = [
        mock_parsed,  # ParsedMarkdown query
        mock_work     # Work query
    ]

    # Mock LLM response parsing (large)
    mock_modifications = [{'heading': 'Chapter 1', 'action': 'keep'}]
    mock_parse_llm.return_value = mock_modifications

    # Mock applying modifications
    mock_apply.return_value = "# Sanitized Large Document"

    # Mock token counting
    mock_count_tokens.return_value = 45000

    # Mock heading extraction
    mock_headings = [{'level': 'H1', 'text': 'Chapter 1', 'line_number': 1}]
    mock_extract.return_value = mock_headings

    # Mock chunks
    mock_chunks = [MagicMock() for _ in range(20)]
    mock_chunk.return_value = mock_chunks

    response = client.post(
        '/api/simple-conversion/manual-submit/200',
        json={'llm_response': '[{"heading": "Chapter 1", "action": "keep"}]'}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['work_id'] == 200
    assert data['status'] == 'complete'
    assert '20 chunks' in data['message']


def test_submit_manual_result_work_not_parsed():
    """Test POST /api/simple-conversion/manual-submit/{work_id} when work not parsed."""
    # Configure mock session to return None
    mock_session_instance.query.return_value.filter.return_value.first.return_value = None

    response = client.post(
        '/api/simple-conversion/manual-submit/999',
        json={'llm_response': '{"sanitized_markdown": "..."}'}
    )

    assert response.status_code == 400


def test_get_results_success():
    """Test GET /api/simple-conversion/results/{work_id} returns results."""
    # Mock work
    mock_work = MagicMock()
    mock_work.id = 123
    mock_work.title = "Test Book"
    mock_work.author = "Test Author"

    # Mock parsed
    mock_parsed = MagicMock()
    mock_parsed.classification.value = 'small'
    mock_parsed.token_count = 15000

    # Mock chunk instances
    mock_chunk1 = MagicMock()
    mock_chunk1.id = 1
    mock_chunk1.level = "H1"
    mock_chunk1.heading_breadcrumbs = "Chapter 1"
    mock_chunk1.start_line = 1
    mock_chunk1.end_line = 50
    mock_chunk1.content = "Short content"

    mock_chunk2 = MagicMock()
    mock_chunk2.id = 2
    mock_chunk2.level = "H2"
    mock_chunk2.heading_breadcrumbs = "Chapter 1 > Section 1.1"
    mock_chunk2.start_line = 51
    mock_chunk2.end_line = 100
    mock_chunk2.content = "A" * 250  # Long content to test preview

    mock_chunks = [mock_chunk1, mock_chunk2]

    # Configure mock session with side effects for different queries
    query_results = {
        'work_first': mock_work,
        'parsed_first': mock_parsed,
        'chunks_all': mock_chunks
    }

    call_count = [0]

    def query_side_effect(*args):
        mock_query = MagicMock()
        call_count[0] += 1

        if call_count[0] == 1:  # First query().filter().first() - Work
            mock_query.filter.return_value.first.return_value = query_results['work_first']
        elif call_count[0] == 2:  # Second query().filter().first() - ParsedMarkdown
            mock_query.filter.return_value.first.return_value = query_results['parsed_first']
        elif call_count[0] == 3:  # Third query().filter().all() - Chunks
            mock_query.filter.return_value.all.return_value = query_results['chunks_all']

        return mock_query

    mock_session_instance.query.side_effect = query_side_effect

    response = client.get('/api/simple-conversion/results/123')

    assert response.status_code == 200
    data = response.json()
    assert data['work_id'] == 123
    assert data['title'] == "Test Book"
    assert data['author'] == "Test Author"
    assert data['classification'] == 'small'
    assert data['token_count'] == 15000
    assert data['chunk_count'] == 2
    assert len(data['chunks']) == 2

    # Check chunk data
    assert data['chunks'][0]['heading_level'] == 'H1'
    assert data['chunks'][0]['heading_text'] == 'Chapter 1'
    assert data['chunks'][1]['content_preview'].endswith('...')  # Preview truncated


def test_get_results_work_not_found():
    """Test GET /api/simple-conversion/results/{work_id} handles missing work."""
    # Configure mock session to return None
    mock_session_instance.query.return_value.filter.return_value.first.return_value = None

    response = client.get('/api/simple-conversion/results/999')
    assert response.status_code == 404


def test_get_results_not_processed():
    """Test GET /api/simple-conversion/results/{work_id} when work not processed."""
    # Mock work exists
    mock_work = MagicMock()
    mock_work.id = 123

    # Configure mock session - first query returns work, second returns None (no parsed)
    mock_session_instance.query.return_value.filter.return_value.first.side_effect = [
        mock_work,  # Work found
        None        # Parsed not found
    ]

    response = client.get('/api/simple-conversion/results/123')

    assert response.status_code == 400
