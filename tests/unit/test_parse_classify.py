"""Unit tests for parse and classify module."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC

from vulcanlab.simple_conversion.parse_classify import (
    count_tokens,
    classify_document,
    get_markdown_from_citation,
    parse_and_classify,
    parse_and_classify_standalone
)
from vulcanlab.data.models.enums import DocumentClassification


def test_count_tokens_empty_string():
    """Test token counting with empty string."""
    result = count_tokens("")
    assert result == 0


def test_count_tokens_simple_text():
    """Test token counting with simple text."""
    text = "Hello world, this is a test."
    result = count_tokens(text)
    assert result > 0
    assert isinstance(result, int)


def test_count_tokens_large_text():
    """Test token counting with large document."""
    text = "word " * 10000  # 10k words
    result = count_tokens(text)
    assert result > 5000  # Should be ~13k tokens


@patch('vulcanlab.simple_conversion.parse_classify.ENCODING.encode')
def test_count_tokens_fallback_on_error(mock_encode):
    """Test fallback token counting when tiktoken fails."""
    mock_encode.side_effect = Exception("Encoding error")

    text = "one two three four five"  # 5 words
    result = count_tokens(text)

    # Fallback: 5 words / 0.75 ≈ 6-7 tokens
    assert 6 <= result <= 7


def test_classify_document_small():
    """Test classification of small document."""
    result = classify_document(token_count=10000, threshold=15000)
    assert result == DocumentClassification.SMALL


def test_classify_document_large():
    """Test classification of large document."""
    result = classify_document(token_count=20000, threshold=15000)
    assert result == DocumentClassification.LARGE


def test_classify_document_at_threshold():
    """Test classification exactly at threshold (should be LARGE)."""
    result = classify_document(token_count=15000, threshold=15000)
    assert result == DocumentClassification.LARGE


def test_get_markdown_from_citation_no_citation():
    """Test error when work has no citation."""
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.citation_id = None
    mock_session = MagicMock()

    with pytest.raises(ValueError, match="has no citation"):
        get_markdown_from_citation(mock_work, mock_session)


def test_get_markdown_from_citation_not_implemented():
    """Test that citation API integration raises NotImplementedError."""
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.citation_id = 123
    mock_session = MagicMock()

    # Currently raises NotImplementedError until Citation API is integrated
    with pytest.raises(NotImplementedError, match="Citation API integration"):
        get_markdown_from_citation(mock_work, mock_session)


@patch('vulcanlab.simple_conversion.parse_classify.get_markdown_from_citation')
@patch('vulcanlab.simple_conversion.parse_classify.count_tokens')
@patch('vulcanlab.simple_conversion.parse_classify.get_token_threshold')
def test_parse_and_classify_small_document(mock_threshold, mock_count, mock_get_md):
    """Test parsing and classifying a small document."""
    # Setup mocks
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.citation_id = 123
    mock_work.processing_status = {}

    mock_session.query.return_value.filter.return_value.first.return_value = mock_work
    mock_get_md.return_value = "# Small Doc\n\nContent."
    mock_count.return_value = 5000
    mock_threshold.return_value = 15000

    # Execute
    result = parse_and_classify(1, mock_session)

    # Verify ParsedMarkdown was created
    assert mock_session.add.called
    parsed = mock_session.add.call_args[0][0]
    assert parsed.work_id == 1
    assert parsed.token_count == 5000
    assert parsed.classification == DocumentClassification.SMALL

    # Verify Work.processing_status updated
    assert mock_work.processing_status['simple_conversion_step'] == 'parsed'
    assert mock_work.processing_status['simple_conversion_classification'] == 'small'
    assert mock_work.processing_status['simple_conversion_token_count'] == 5000

    # Verify commit called
    assert mock_session.commit.called


@patch('vulcanlab.simple_conversion.parse_classify.get_markdown_from_citation')
@patch('vulcanlab.simple_conversion.parse_classify.count_tokens')
@patch('vulcanlab.simple_conversion.parse_classify.get_token_threshold')
def test_parse_and_classify_large_document(mock_threshold, mock_count, mock_get_md):
    """Test parsing and classifying a large document."""
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 2
    mock_work.citation_id = 456
    mock_work.processing_status = None  # Test None initialization

    mock_session.query.return_value.filter.return_value.first.return_value = mock_work
    mock_get_md.return_value = "# Large Doc\n\n" + ("Content. " * 5000)
    mock_count.return_value = 25000
    mock_threshold.return_value = 15000

    # Execute
    result = parse_and_classify(2, mock_session)

    # Verify classification is LARGE
    parsed = mock_session.add.call_args[0][0]
    assert parsed.classification == DocumentClassification.LARGE
    assert parsed.token_count == 25000

    # Verify processing_status was initialized from None
    assert mock_work.processing_status is not None
    assert mock_work.processing_status['simple_conversion_classification'] == 'large'


def test_parse_and_classify_work_not_found():
    """Test error when work doesn't exist."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="Work 999 not found"):
        parse_and_classify(999, mock_session)


def test_parse_and_classify_work_not_converted():
    """Test error when work has no citation."""
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.citation_id = None

    mock_session.query.return_value.filter.return_value.first.return_value = mock_work

    with pytest.raises(ValueError, match="has not been converted yet"):
        parse_and_classify(1, mock_session)


@patch('vulcanlab.simple_conversion.parse_classify.get_session')
@patch('vulcanlab.simple_conversion.parse_classify.parse_and_classify')
def test_parse_and_classify_standalone(mock_parse, mock_session):
    """Test standalone function for CLI usage."""
    mock_parsed = MagicMock()
    mock_parsed.token_count = 12000
    mock_parsed.classification.value = 'small'
    mock_parse.return_value = mock_parsed

    # Mock context manager
    mock_session_instance = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_session_instance
    mock_session.return_value.__exit__.return_value = None

    token_count, classification = parse_and_classify_standalone(1)

    assert token_count == 12000
    assert classification == 'small'
    mock_parse.assert_called_once_with(1, mock_session_instance)
