"""Unit tests for small document sanitization module."""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC

from vulcanlab.simple_conversion.sanitize_small import (
    get_hardcoded_template_small,
    parse_llm_response,
    sanitize_small_document,
    sanitize_small_document_standalone
)


def test_get_hardcoded_template_small():
    """Test fallback template contains required placeholder."""
    template = get_hardcoded_template_small()

    assert '{markdown}' in template
    assert 'sanitized_markdown' in template
    assert 'modifications' in template


def test_parse_llm_response_valid_json():
    """Test parsing valid LLM JSON response."""
    response = json.dumps({
        'sanitized_markdown': '# Clean Content\n\nText here.',
        'modifications': [
            {'original': 'Old Heading', 'action': 'remove', 'reason': 'Duplicate'}
        ]
    })

    result = parse_llm_response(response)

    assert result['sanitized_markdown'] == '# Clean Content\n\nText here.'
    assert len(result['modifications']) == 1
    assert result['modifications'][0]['action'] == 'remove'


def test_parse_llm_response_with_extra_text():
    """Test parsing JSON when LLM adds extra text."""
    response = """
    Here is the result:
    {
      "sanitized_markdown": "# Content",
      "modifications": []
    }
    That's the sanitized version.
    """

    result = parse_llm_response(response)

    assert result['sanitized_markdown'] == '# Content'
    assert result['modifications'] == []


def test_parse_llm_response_missing_field():
    """Test error when response missing required field."""
    response = json.dumps({
        'sanitized_markdown': '# Content'
        # Missing 'modifications'
    })

    with pytest.raises(ValueError, match="missing 'modifications'"):
        parse_llm_response(response)


def test_parse_llm_response_invalid_json():
    """Test error when response is not valid JSON."""
    response = "This is not JSON at all"

    with pytest.raises(ValueError, match="No JSON found in response"):
        parse_llm_response(response)


def test_create_heading_modifications_all_actions():
    """Test creating heading modification records for all action types."""
    mock_session = MagicMock()
    modifications = [
        {'original': 'Heading 1', 'action': 'remove', 'reason': 'Duplicate'},
        {'original': 'Heading 2', 'action': 'change', 'new': 'Better Heading', 'reason': 'Clarity'},
        {'original': 'Heading 3', 'action': 'keep', 'reason': 'Good as-is'}
    ]

    records = create_heading_modifications(modifications, 1, mock_session)

    assert len(records) == 3
    assert records[0].action == ModificationAction.REMOVE
    assert records[1].action == ModificationAction.CHANGE
    assert records[1].modified_heading == 'Better Heading'
    assert records[2].action == ModificationAction.KEEP
    assert mock_session.add.call_count == 3


def test_create_heading_modifications_unknown_action():
    """Test handling of unknown action (defaults to KEEP)."""
    mock_session = MagicMock()
    modifications = [
        {'original': 'Heading', 'action': 'invalid_action', 'reason': 'Test'}
    ]

    records = create_heading_modifications(modifications, 1, mock_session)

    assert len(records) == 1
    assert records[0].action == ModificationAction.KEEP


@patch('vulcanlab.simple_conversion.sanitize_small.create_langchain_chat')
@patch('vulcanlab.simple_conversion.sanitize_small.load_template')
@patch('vulcanlab.simple_conversion.sanitize_small.count_tokens')
def test_sanitize_small_document_success(mock_count, mock_load_template, mock_llm):
    """Test successful small document sanitization."""
    # Setup mocks
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.processing_status = {}

    mock_parsed = MagicMock()
    mock_parsed.id = 10
    mock_parsed.content = '# Original Content\n\nText here.'
    mock_parsed.classification.value = 'small'

    # Mock query chains
    work_query = MagicMock()
    work_query.filter.return_value.first.return_value = mock_work
    parsed_query = MagicMock()
    parsed_query.filter.return_value.first.return_value = mock_parsed

    mock_session.query.side_effect = [work_query, parsed_query]

    # Mock template
    mock_template_obj = MagicMock()
    mock_template_obj.format.return_value = "Formatted prompt with markdown"
    mock_load_template.return_value = mock_template_obj

    # Mock LLM response
    llm_response_text = json.dumps({
        'sanitized_markdown': '# Sanitized Content\n\nCleaned text.',
        'modifications': [
            {'original': 'Original Heading', 'action': 'change', 'new': 'Better Heading', 'reason': 'Clarity'}
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
    result = sanitize_small_document(1, mock_session)

    # Verify template loaded
    mock_load_template.assert_called_once_with(
        'simple_sanitize_small',
        get_hardcoded_template_small
    )

    # Verify LLM called
    assert mock_chat.invoke.called

    # Verify SanitizedMarkdown added
    assert mock_session.add.call_count >= 2  # Sanitized + modifications

    # Verify processing_status updated
    assert mock_work.processing_status['simple_conversion_step'] == 'sanitized'

    # Verify commit called
    assert mock_session.commit.called


@patch('vulcanlab.simple_conversion.sanitize_small.create_langchain_chat')
@patch('vulcanlab.simple_conversion.sanitize_small.load_template')
def test_sanitize_small_document_work_not_found(mock_load_template, mock_llm):
    """Test error when work doesn't exist."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="Work 999 not found"):
        sanitize_small_document(999, mock_session)


@patch('vulcanlab.simple_conversion.sanitize_small.create_langchain_chat')
@patch('vulcanlab.simple_conversion.sanitize_small.load_template')
def test_sanitize_small_document_not_parsed(mock_load_template, mock_llm):
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
        sanitize_small_document(1, mock_session)


@patch('vulcanlab.simple_conversion.sanitize_small.create_langchain_chat')
@patch('vulcanlab.simple_conversion.sanitize_small.load_template')
def test_sanitize_small_document_wrong_classification(mock_load_template, mock_llm):
    """Test error when document classified as LARGE."""
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1

    mock_parsed = MagicMock()
    mock_parsed.classification.value = 'large'  # Wrong classification

    work_query = MagicMock()
    work_query.filter.return_value.first.return_value = mock_work
    parsed_query = MagicMock()
    parsed_query.filter.return_value.first.return_value = mock_parsed

    mock_session.query.side_effect = [work_query, parsed_query]

    with pytest.raises(ValueError, match="classified as large, expected 'small'"):
        sanitize_small_document(1, mock_session)


@patch('vulcanlab.simple_conversion.sanitize_small.get_session')
@patch('vulcanlab.simple_conversion.sanitize_small.sanitize_small_document')
def test_sanitize_small_document_standalone(mock_sanitize, mock_session):
    """Test standalone function for CLI."""
    mock_sanitized = MagicMock()
    mock_sanitized.id = 5
    mock_sanitize.return_value = mock_sanitized

    mock_db_session = MagicMock()
    mock_db_session.query.return_value.filter.return_value.count.return_value = 3
    mock_session.return_value.__enter__.return_value = mock_db_session
    mock_session.return_value.__exit__.return_value = None

    result = sanitize_small_document_standalone(1)

    assert result == 3


@patch('vulcanlab.simple_conversion.sanitize_small.get_use_full_model')
@patch('vulcanlab.simple_conversion.sanitize_small.create_langchain_chat')
@patch('vulcanlab.simple_conversion.sanitize_small.load_template')
@patch('vulcanlab.simple_conversion.sanitize_small.count_tokens')
def test_sanitize_small_uses_light_model_when_config_false(mock_count, mock_load_template, mock_llm, mock_get_config):
    """Test sanitize_small_document uses ModelTier.LIGHT when use_full_model is False."""
    from vulcanlab.ai.config import ModelTier

    # Setup config mock
    mock_get_config.return_value = False

    # Setup other mocks
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.processing_status = {}

    mock_parsed = MagicMock()
    mock_parsed.content = '# Test Content'
    mock_parsed.classification.value = 'small'

    work_query = MagicMock()
    work_query.filter.return_value.first.return_value = mock_work
    parsed_query = MagicMock()
    parsed_query.filter.return_value.first.return_value = mock_parsed

    mock_session.query.side_effect = [work_query, parsed_query]

    mock_template_obj = MagicMock()
    mock_template_obj.format.return_value = "Prompt"
    mock_load_template.return_value = mock_template_obj

    mock_llm_response = MagicMock()
    mock_llm_response.content = '# Sanitized Content'

    mock_chat = MagicMock()
    mock_chat.invoke.return_value = mock_llm_response

    mock_llm_stack = MagicMock()
    mock_llm_stack.chat = mock_chat
    mock_llm.return_value = mock_llm_stack

    mock_count.return_value = 10

    # Execute
    sanitize_small_document(1, mock_session)

    # Verify ModelTier.LIGHT was used
    mock_llm.assert_called_once_with(tier=ModelTier.LIGHT, temperature=0.2)


@patch('vulcanlab.simple_conversion.sanitize_small.get_use_full_model')
@patch('vulcanlab.simple_conversion.sanitize_small.create_langchain_chat')
@patch('vulcanlab.simple_conversion.sanitize_small.load_template')
@patch('vulcanlab.simple_conversion.sanitize_small.count_tokens')
def test_sanitize_small_uses_full_model_when_config_true(mock_count, mock_load_template, mock_llm, mock_get_config):
    """Test sanitize_small_document uses ModelTier.FULL when use_full_model is True."""
    from vulcanlab.ai.config import ModelTier

    # Setup config mock
    mock_get_config.return_value = True

    # Setup other mocks
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.processing_status = {}

    mock_parsed = MagicMock()
    mock_parsed.content = '# Test Content'
    mock_parsed.classification.value = 'small'

    work_query = MagicMock()
    work_query.filter.return_value.first.return_value = mock_work
    parsed_query = MagicMock()
    parsed_query.filter.return_value.first.return_value = mock_parsed

    mock_session.query.side_effect = [work_query, parsed_query]

    mock_template_obj = MagicMock()
    mock_template_obj.format.return_value = "Prompt"
    mock_load_template.return_value = mock_template_obj

    mock_llm_response = MagicMock()
    mock_llm_response.content = '# Sanitized Content'

    mock_chat = MagicMock()
    mock_chat.invoke.return_value = mock_llm_response

    mock_llm_stack = MagicMock()
    mock_llm_stack.chat = mock_chat
    mock_llm.return_value = mock_llm_stack

    mock_count.return_value = 10

    # Execute
    sanitize_small_document(1, mock_session)

    # Verify ModelTier.FULL was used
    mock_llm.assert_called_once_with(tier=ModelTier.FULL, temperature=0.2)


@patch('vulcanlab.simple_conversion.sanitize_small.get_use_full_model')
@patch('vulcanlab.simple_conversion.sanitize_small.create_langchain_chat')
@patch('vulcanlab.simple_conversion.sanitize_small.load_template')
@patch('vulcanlab.simple_conversion.sanitize_small.count_tokens')
@patch('vulcanlab.simple_conversion.sanitize_small.logger')
def test_sanitize_small_logs_model_tier(mock_logger, mock_count, mock_load_template, mock_llm, mock_get_config):
    """Test that model tier selection is logged correctly."""
    from vulcanlab.ai.config import ModelTier

    # Setup config mock
    mock_get_config.return_value = True

    # Setup other mocks
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.processing_status = {}

    mock_parsed = MagicMock()
    mock_parsed.content = '# Test Content'
    mock_parsed.classification.value = 'small'

    work_query = MagicMock()
    work_query.filter.return_value.first.return_value = mock_work
    parsed_query = MagicMock()
    parsed_query.filter.return_value.first.return_value = mock_parsed

    mock_session.query.side_effect = [work_query, parsed_query]

    mock_template_obj = MagicMock()
    mock_template_obj.format.return_value = "Prompt"
    mock_load_template.return_value = mock_template_obj

    mock_llm_response = MagicMock()
    mock_llm_response.content = '# Sanitized Content'

    mock_chat = MagicMock()
    mock_chat.invoke.return_value = mock_llm_response

    mock_llm_stack = MagicMock()
    mock_llm_stack.chat = mock_chat
    mock_llm.return_value = mock_llm_stack

    mock_count.return_value = 10

    # Execute
    sanitize_small_document(1, mock_session)

    # Verify logging was called with correct message
    log_calls = [str(call) for call in mock_logger.info.call_args_list]
    assert any('ModelTier.FULL' in str(call) and 'small document sanitization' in str(call) for call in log_calls)
