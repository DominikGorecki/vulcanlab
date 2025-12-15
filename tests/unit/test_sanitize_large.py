"""Unit tests for large document sanitization module."""

import pytest
from unittest.mock import patch, MagicMock
import json

from vulcanlab.simple_conversion.sanitize_large import (
    extract_headings_with_context,
    create_condensed_markdown,
    get_hardcoded_template_large,
    apply_modifications_to_markdown,
    parse_llm_response_large,
    sanitize_large_document,
    sanitize_large_document_standalone,
    CONTEXT_WINDOW
)


def test_extract_headings_with_context_simple():
    """Test extracting headings from simple markdown."""
    markdown = """
Some intro text here.

# Heading One

Content after heading one.

## Heading Two

More content here.
"""

    headings = extract_headings_with_context(markdown)

    assert len(headings) == 2
    assert headings[0]['level'] == 1
    assert headings[0]['text'] == 'Heading One'
    assert 'intro text' in headings[0]['context_before']
    assert 'Content after' in headings[0]['context_after']

    assert headings[1]['level'] == 2
    assert headings[1]['text'] == 'Heading Two'


def test_extract_headings_with_context_multiple_levels():
    """Test extracting headings with different levels."""
    markdown = """
# Level 1
## Level 2
### Level 3
#### Level 4
##### Level 5
###### Level 6
"""

    headings = extract_headings_with_context(markdown)

    assert len(headings) == 6
    assert headings[0]['level'] == 1
    assert headings[5]['level'] == 6


def test_extract_headings_with_context_window():
    """Test context window extraction."""
    # Create text longer than CONTEXT_WINDOW
    before_text = "A" * 200
    after_text = "B" * 200
    markdown = f"{before_text}\n\n# Test Heading\n\n{after_text}"

    headings = extract_headings_with_context(markdown)

    assert len(headings) == 1
    # Context should be truncated to CONTEXT_WINDOW
    assert len(headings[0]['context_before']) <= CONTEXT_WINDOW + 10  # Small buffer
    assert len(headings[0]['context_after']) <= CONTEXT_WINDOW + 10


def test_extract_headings_with_line_numbers():
    """Test that line numbers are tracked correctly."""
    markdown = """Line 1
Line 2
# First Heading
Line 4
Line 5
## Second Heading
"""

    headings = extract_headings_with_context(markdown)

    assert len(headings) == 2
    assert headings[0]['line_number'] == 3
    assert headings[1]['line_number'] == 6


def test_create_condensed_markdown():
    """Test creating condensed markdown from headings."""
    headings = [
        {
            'level': 1,
            'text': 'Main Heading',
            'context_before': 'intro text',
            'context_after': 'first paragraph',
            'position': 10,
            'line_number': 1
        },
        {
            'level': 2,
            'text': 'Sub Heading',
            'context_before': 'previous section',
            'context_after': 'sub content',
            'position': 50,
            'line_number': 5
        }
    ]

    condensed = create_condensed_markdown(headings)

    assert '# Condensed Document' in condensed
    assert 'LINE 1: # Main Heading' in condensed
    assert 'LINE 5: ## Sub Heading' in condensed
    assert 'intro text' in condensed
    assert 'first paragraph' in condensed


def test_get_hardcoded_template_large():
    """Test fallback template contains required placeholder."""
    template = get_hardcoded_template_large()

    assert '{condensed_document}' in template
    assert 'LARGE document' in template
    assert 'modifications' in template


def test_apply_modifications_to_markdown_remove():
    """Test removing headings from markdown."""
    markdown = "# Keep This\n\nContent.\n\n# Remove This\n\nMore content."
    modifications = [
        {'line': 1, 'action': 'keep'},
        {'line': 5, 'action': 'remove'}
    ]

    result = apply_modifications_to_markdown(markdown, modifications)

    assert '# Keep This' in result
    assert 'Remove This' not in result
    assert 'Content.' in result
    assert 'More content.' in result


def test_apply_modifications_to_markdown_change():
    """Test changing heading text."""
    markdown = "# Old Heading\n\nContent here."
    modifications = [
        {'line': 1, 'action': 'change', 'new': '## New Heading'}
    ]

    result = apply_modifications_to_markdown(markdown, modifications)

    assert '## New Heading' in result
    assert '# Old Heading' not in result
    assert 'Content here.' in result


def test_apply_modifications_to_markdown_keep():
    """Test keeping heading unchanged."""
    markdown = "# Good Heading\n\nContent."
    modifications = [
        {'line': 1, 'action': 'keep'}
    ]

    result = apply_modifications_to_markdown(markdown, modifications)

    assert result == markdown


def test_apply_modifications_to_markdown_cleanup_blank_lines():
    """Test that multiple blank lines are cleaned up after removals."""
    markdown = "# Keep\n\n# Remove1\n\n# Remove2\n\n# Keep2"
    modifications = [
        {'line': 1, 'action': 'keep'},
        {'line': 3, 'action': 'remove'},
        {'line': 5, 'action': 'remove'},
        {'line': 7, 'action': 'keep'}
    ]

    result = apply_modifications_to_markdown(markdown, modifications)

    # Should not have 3+ consecutive newlines
    assert '\n\n\n' not in result


def test_parse_llm_response_large_valid():
    """Test parsing valid LLM response for large docs."""
    response = json.dumps({
        'modifications': [
            {'original': 'Heading 1', 'action': 'remove', 'reason': 'Duplicate'},
            {'original': 'Heading 2', 'action': 'keep', 'reason': 'Good'}
        ]
    })

    result = parse_llm_response_large(response)

    assert len(result) == 2
    assert result[0]['action'] == 'remove'
    assert result[1]['action'] == 'keep'


def test_parse_llm_response_large_missing_field():
    """Test error when response missing modifications."""
    response = json.dumps({'some_other_field': 'value'})

    with pytest.raises(ValueError, match="missing 'modifications'"):
        parse_llm_response_large(response)


def test_parse_llm_response_large_no_json():
    """Test error when no JSON found."""
    response = "This is not JSON"

    with pytest.raises(ValueError, match="No JSON found in response"):
        parse_llm_response_large(response)


@patch('vulcanlab.simple_conversion.sanitize_large.create_langchain_chat')
@patch('vulcanlab.simple_conversion.sanitize_large.load_template')
@patch('vulcanlab.simple_conversion.sanitize_large.count_tokens')
def test_sanitize_large_document_success(mock_count, mock_load_template, mock_llm):
    """Test successful large document sanitization."""
    # Setup mocks
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.processing_status = {}

    original_markdown = "# Heading 1\n\nContent.\n\n# Heading 2\n\nMore content."
    mock_parsed = MagicMock()
    mock_parsed.id = 10
    mock_parsed.content = original_markdown
    mock_parsed.classification.value = 'large'

    # Mock query chains
    work_query = MagicMock()
    work_query.filter.return_value.first.return_value = mock_work
    parsed_query = MagicMock()
    parsed_query.filter.return_value.first.return_value = mock_parsed

    mock_session.query.side_effect = [work_query, parsed_query]

    # Mock template
    mock_template_obj = MagicMock()
    mock_template_obj.format.return_value = "Formatted prompt"
    mock_load_template.return_value = mock_template_obj

    # Mock LLM response (new format with line numbers)
    llm_response_text = json.dumps({
        'modifications': [
            {'line': 1, 'action': 'keep', 'vectorize': True},
            {'line': 5, 'action': 'remove', 'vectorize': False}
        ]
    })
    mock_llm_response = MagicMock()
    mock_llm_response.content = llm_response_text

    mock_chat = MagicMock()
    mock_chat.invoke.return_value = mock_llm_response

    mock_llm_stack = MagicMock()
    mock_llm_stack.chat = mock_chat
    mock_llm.return_value = mock_llm_stack

    # Mock token counting
    mock_count.return_value = 10

    # Execute
    result = sanitize_large_document(1, mock_session)

    # Verify template loaded
    mock_load_template.assert_called_once_with(
        'simple_sanitize_large',
        get_hardcoded_template_large
    )

    # Verify LLM called
    assert mock_chat.invoke.called

    # Verify SanitizedMarkdown added
    assert mock_session.add.call_count >= 2

    # Verify processing_status updated
    assert mock_work.processing_status['simple_conversion_step'] == 'sanitized'
    assert 'condensed_char_count' in mock_work.processing_status

    # Verify commit called
    assert mock_session.commit.called


@patch('vulcanlab.simple_conversion.sanitize_large.create_langchain_chat')
@patch('vulcanlab.simple_conversion.sanitize_large.load_template')
def test_sanitize_large_document_work_not_found(mock_load_template, mock_llm):
    """Test error when work doesn't exist."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="Work 999 not found"):
        sanitize_large_document(999, mock_session)


@patch('vulcanlab.simple_conversion.sanitize_large.create_langchain_chat')
@patch('vulcanlab.simple_conversion.sanitize_large.load_template')
def test_sanitize_large_document_not_parsed(mock_load_template, mock_llm):
    """Test error when work not parsed yet."""
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1

    # Work exists, parsed doesn't
    work_query = MagicMock()
    work_query.filter.return_value.first.return_value = mock_work
    parsed_query = MagicMock()
    parsed_query.filter.return_value.first.return_value = None

    mock_session.query.side_effect = [work_query, parsed_query]

    with pytest.raises(ValueError, match="has not been parsed yet"):
        sanitize_large_document(1, mock_session)


@patch('vulcanlab.simple_conversion.sanitize_large.create_langchain_chat')
@patch('vulcanlab.simple_conversion.sanitize_large.load_template')
def test_sanitize_large_document_wrong_classification(mock_load_template, mock_llm):
    """Test error when document classified as SMALL."""
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1

    mock_parsed = MagicMock()
    mock_parsed.classification.value = 'small'

    work_query = MagicMock()
    work_query.filter.return_value.first.return_value = mock_work
    parsed_query = MagicMock()
    parsed_query.filter.return_value.first.return_value = mock_parsed

    mock_session.query.side_effect = [work_query, parsed_query]

    with pytest.raises(ValueError, match="classified as small, expected 'large'"):
        sanitize_large_document(1, mock_session)


@patch('vulcanlab.simple_conversion.sanitize_large.get_session')
@patch('vulcanlab.simple_conversion.sanitize_large.sanitize_large_document')
def test_sanitize_large_document_standalone(mock_sanitize, mock_session):
    """Test standalone function for CLI."""
    mock_sanitized = MagicMock()
    mock_sanitized.id = 5
    mock_sanitize.return_value = mock_sanitized

    mock_work = MagicMock()
    mock_work.processing_status = {
        'sanitized_heading_count': 15,
        'condensed_char_count': 3500
    }

    mock_db_session = MagicMock()
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_work
    mock_session.return_value.__enter__.return_value = mock_db_session
    mock_session.return_value.__exit__.return_value = None

    heading_count, condensed_chars = sanitize_large_document_standalone(1)

    assert heading_count == 15
    assert condensed_chars == 3500
