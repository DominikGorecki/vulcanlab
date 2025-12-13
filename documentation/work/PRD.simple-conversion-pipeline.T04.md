# T04: Small Document Sanitization Module

**Status**: PENDING
**Priority**: High
**Type**: Backend-Only
**Depends On**: T01 (Database schema), T03 (Parse & classify)
**Blocks**: T07 (API endpoints), T10/T11 (Frontend workflows)

## Overview

Implement the sanitization module for SMALL documents (<15k tokens). This module takes the full markdown content, sends it to an LLM using a database-backed prompt template, receives sanitized markdown with heading modifications, and saves the SanitizedMarkdown record with associated HeadingModification records.

## Acceptance Criteria

- [ ] Module loads prompt template from DB (`simple_sanitize_small` tag)
- [ ] Template uses LangChain format with `{markdown}` variable
- [ ] Fallback to hardcoded template if DB template unavailable
- [ ] LLM call with full markdown content
- [ ] Parse LLM response for sanitized markdown and modification list
- [ ] Create SanitizedMarkdown record with compressed content
- [ ] Create HeadingModification records for each heading action
- [ ] CLI tool runs standalone with `--work-id` argument
- [ ] All unit tests pass and use mocks (no database or LLM calls)
- [ ] Manual test plan completed successfully

## Technical Implementation

### 1. Prompt Template Setup

**Template Function Tag**: `simple_sanitize_small`

**Default Template** (to be seeded in DB via T01):

```
You are an expert document sanitizer. Your task is to clean up markdown content by:
1. Removing duplicate or redundant headings
2. Fixing heading hierarchy issues
3. Removing unnecessary metadata sections
4. Keeping all substantive content intact

Input markdown:
{markdown}

Respond in the following JSON format:
{{
  "sanitized_markdown": "... full sanitized markdown here ...",
  "modifications": [
    {{"original": "Heading Text", "action": "remove", "reason": "Duplicate heading"}},
    {{"original": "Another Heading", "action": "change", "new": "Better Heading", "reason": "Improved clarity"}},
    {{"original": "Good Heading", "action": "keep", "reason": "Already appropriate"}}
  ]
}}

Important:
- Return ONLY valid JSON, no additional commentary
- Include ALL headings in the modifications list
- Use action: "remove", "change", or "keep" for each heading
- Preserve all non-heading content exactly as-is
```

### 2. Core Module: Small Document Sanitization

**File**: `src/vulcanlab/simple_conversion/sanitize_small.py` (NEW)

```python
"""
Small document sanitization module for simple conversion pipeline.

Processes documents classified as SMALL (<threshold tokens) by sending
the entire markdown content to an LLM for sanitization.
"""

import logging
import json
from typing import Dict, List, Any
from datetime import datetime, UTC

from sqlalchemy.orm import Session
from langchain_core.prompts import PromptTemplate as LCPromptTemplate

from vulcanlab.data.models.work import Work
from vulcanlab.data.models.parsed_markdown import ParsedMarkdown
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.data.models.heading_modifications import HeadingModification, ModificationAction
from vulcanlab.data.database import get_session
from vulcanlab.data.template_loader import load_template
from vulcanlab.llm.client import get_llm_client  # Assumes existing LLM client

logger = logging.getLogger(__name__)


def get_hardcoded_template_small() -> str:
    """
    Fallback hardcoded template for small document sanitization.

    Returns:
        Template string with {markdown} placeholder
    """
    return '''You are an expert document sanitizer. Your task is to clean up markdown content by:
1. Removing duplicate or redundant headings
2. Fixing heading hierarchy issues
3. Removing unnecessary metadata sections
4. Keeping all substantive content intact

Input markdown:
{markdown}

Respond in the following JSON format:
{{
  "sanitized_markdown": "... full sanitized markdown here ...",
  "modifications": [
    {{"original": "Heading Text", "action": "remove", "reason": "Duplicate heading"}},
    {{"original": "Another Heading", "action": "change", "new": "Better Heading", "reason": "Improved clarity"}},
    {{"original": "Good Heading", "action": "keep", "reason": "Already appropriate"}}
  ]
}}

Important:
- Return ONLY valid JSON, no additional commentary
- Include ALL headings in the modifications list
- Use action: "remove", "change", or "keep" for each heading
- Preserve all non-heading content exactly as-is'''


def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """
    Parse LLM JSON response into structured data.

    Args:
        response_text: Raw LLM response (should be JSON)

    Returns:
        Dictionary with 'sanitized_markdown' and 'modifications' keys

    Raises:
        ValueError: If response is not valid JSON or missing required fields
    """
    try:
        # Try to extract JSON from response (handle cases where LLM adds extra text)
        # Look for first { and last }
        start = response_text.find('{')
        end = response_text.rfind('}')

        if start == -1 or end == -1:
            raise ValueError("No JSON found in response")

        json_str = response_text[start:end+1]
        data = json.loads(json_str)

        # Validate required fields
        if 'sanitized_markdown' not in data:
            raise ValueError("Response missing 'sanitized_markdown' field")
        if 'modifications' not in data:
            raise ValueError("Response missing 'modifications' field")

        return data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError(f"Invalid JSON response: {e}")


def create_heading_modifications(
    modifications_list: List[Dict[str, str]],
    sanitized_id: int,
    session: Session
) -> List[HeadingModification]:
    """
    Create HeadingModification records from LLM response.

    Args:
        modifications_list: List of modification dicts from LLM
        sanitized_id: ID of parent SanitizedMarkdown record
        session: Database session

    Returns:
        List of created HeadingModification records
    """
    records = []

    for mod in modifications_list:
        # Parse action
        action_str = mod.get('action', '').lower()
        if action_str == 'remove':
            action = ModificationAction.REMOVE
        elif action_str == 'change':
            action = ModificationAction.CHANGE
        elif action_str == 'keep':
            action = ModificationAction.KEEP
        else:
            logger.warning(f"Unknown action '{action_str}', defaulting to KEEP")
            action = ModificationAction.KEEP

        # Create record
        heading_mod = HeadingModification(
            sanitized_markdown_id=sanitized_id,
            original_heading=mod.get('original', ''),
            action=action,
            new_heading=mod.get('new'),  # None for remove/keep
            reason=mod.get('reason', ''),
            created_at=datetime.now(UTC)
        )

        session.add(heading_mod)
        records.append(heading_mod)

    return records


def sanitize_small_document(work_id: int, session: Session) -> SanitizedMarkdown:
    """
    Sanitize a small document using full LLM processing.

    This function:
    1. Retrieves ParsedMarkdown for the work
    2. Loads template from DB (with fallback)
    3. Formats prompt with full markdown content
    4. Calls LLM
    5. Parses response
    6. Creates SanitizedMarkdown record
    7. Creates HeadingModification records
    8. Updates Work.processing_status

    Args:
        work_id: ID of the Work to process
        session: Database session

    Returns:
        Created SanitizedMarkdown record

    Raises:
        ValueError: If work not found, not parsed, or wrong classification
    """
    # Get work
    work = session.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise ValueError(f"Work {work_id} not found")

    # Get ParsedMarkdown
    parsed = session.query(ParsedMarkdown).filter(
        ParsedMarkdown.work_id == work_id
    ).first()

    if not parsed:
        raise ValueError(f"Work {work_id} has not been parsed yet")

    if parsed.classification.value != 'small':
        raise ValueError(
            f"Work {work_id} is classified as {parsed.classification.value}, "
            f"expected 'small'"
        )

    logger.info(f"Sanitizing small document for work {work_id}")

    # Load template
    template = load_template('simple_sanitize_small', get_hardcoded_template_small)

    # Format prompt
    prompt = template.format(markdown=parsed.content)

    # Call LLM
    llm_client = get_llm_client()
    logger.info(f"Calling LLM for small document sanitization (work {work_id})")
    response = llm_client.generate(prompt)

    # Parse response
    parsed_response = parse_llm_response(response)
    sanitized_content = parsed_response['sanitized_markdown']
    modifications = parsed_response['modifications']

    # Create SanitizedMarkdown record
    sanitized = SanitizedMarkdown(
        parsed_markdown_id=parsed.id,
        content=sanitized_content,  # Auto-compressed if >1MB
        created_at=datetime.now(UTC)
    )

    session.add(sanitized)
    session.flush()  # Get sanitized.id for heading modifications

    # Create HeadingModification records
    heading_records = create_heading_modifications(
        modifications,
        sanitized.id,
        session
    )

    logger.info(
        f"Created {len(heading_records)} heading modifications for work {work_id}"
    )

    # Update Work.processing_status
    if not work.processing_status:
        work.processing_status = {}

    work.processing_status['simple_conversion_step'] = 'sanitized'
    work.processing_status['sanitized_heading_count'] = len(heading_records)

    session.commit()
    session.refresh(sanitized)

    logger.info(f"Sanitization complete for work {work_id}")

    return sanitized


def sanitize_small_document_standalone(work_id: int) -> int:
    """
    Standalone version for CLI usage.

    Args:
        work_id: ID of the Work to process

    Returns:
        Number of heading modifications created

    Raises:
        ValueError: If validation fails
    """
    with get_session() as session:
        sanitized = sanitize_small_document(work_id, session)

        # Count modifications
        mod_count = session.query(HeadingModification).filter(
            HeadingModification.sanitized_markdown_id == sanitized.id
        ).count()

        return mod_count
```

### 3. CLI Tool

**File**: `src/vulcanlab/cli/simple_sanitize_small.py` (NEW)

```python
#!/usr/bin/env python3
"""
Standalone CLI tool for sanitizing small documents.

Usage:
    python -m vulcanlab.cli.simple_sanitize_small --work-id 123

This tool runs the small document sanitization step of the simple conversion
pipeline, sending the full markdown to an LLM for sanitization.
"""

import argparse
import logging
import sys

from vulcanlab.simple_conversion.sanitize_small import sanitize_small_document_standalone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Sanitize small document for simple conversion pipeline'
    )
    parser.add_argument(
        '--work-id',
        type=int,
        required=True,
        help='ID of the Work to process (must be classified as SMALL)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        logger.info(f"Sanitizing small document for work {args.work_id}")

        mod_count = sanitize_small_document_standalone(args.work_id)

        print(f"\n{'='*60}")
        print(f"Small Document Sanitization Complete")
        print(f"{'='*60}")
        print(f"Work ID:              {args.work_id}")
        print(f"Heading Modifications: {mod_count}")
        print(f"{'='*60}\n")

        sys.exit(0)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(2)


if __name__ == '__main__':
    main()
```

## Unit Tests

**File**: `tests/unit/test_sanitize_small.py` (NEW)

```python
"""Unit tests for small document sanitization module."""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC

from vulcanlab.simple_conversion.sanitize_small import (
    get_hardcoded_template_small,
    parse_llm_response,
    create_heading_modifications,
    sanitize_small_document
)
from vulcanlab.data.models.heading_modifications import ModificationAction


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

    with pytest.raises(ValueError, match="Invalid JSON"):
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
    assert records[1].new_heading == 'Better Heading'
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


@patch('vulcanlab.simple_conversion.sanitize_small.get_llm_client')
@patch('vulcanlab.simple_conversion.sanitize_small.load_template')
def test_sanitize_small_document_success(mock_load_template, mock_llm_client):
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
    llm_response = json.dumps({
        'sanitized_markdown': '# Sanitized Content\n\nCleaned text.',
        'modifications': [
            {'original': 'Original Heading', 'action': 'change', 'new': 'Better Heading', 'reason': 'Clarity'}
        ]
    })
    mock_llm = MagicMock()
    mock_llm.generate.return_value = llm_response
    mock_llm_client.return_value = mock_llm

    # Execute
    result = sanitize_small_document(1, mock_session)

    # Verify template loaded
    mock_load_template.assert_called_once_with(
        'simple_sanitize_small',
        get_hardcoded_template_small
    )

    # Verify LLM called
    assert mock_llm.generate.called

    # Verify SanitizedMarkdown added
    assert mock_session.add.call_count >= 2  # Sanitized + modifications

    # Verify processing_status updated
    assert mock_work.processing_status['simple_conversion_step'] == 'sanitized'

    # Verify commit called
    assert mock_session.commit.called


@patch('vulcanlab.simple_conversion.sanitize_small.get_llm_client')
@patch('vulcanlab.simple_conversion.sanitize_small.load_template')
def test_sanitize_small_document_work_not_found(mock_load_template, mock_llm_client):
    """Test error when work doesn't exist."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="Work 999 not found"):
        sanitize_small_document(999, mock_session)


@patch('vulcanlab.simple_conversion.sanitize_small.get_llm_client')
@patch('vulcanlab.simple_conversion.sanitize_small.load_template')
def test_sanitize_small_document_not_parsed(mock_load_template, mock_llm_client):
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


@patch('vulcanlab.simple_conversion.sanitize_small.get_llm_client')
@patch('vulcanlab.simple_conversion.sanitize_small.load_template')
def test_sanitize_small_document_wrong_classification(mock_load_template, mock_llm_client):
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

    from vulcanlab.simple_conversion.sanitize_small import sanitize_small_document_standalone
    result = sanitize_small_document_standalone(1)

    assert result == 3
```

**File**: `tests/unit/test_simple_sanitize_small_cli.py` (NEW)

```python
"""Unit tests for small sanitization CLI tool."""

import pytest
from unittest.mock import patch

from vulcanlab.cli.simple_sanitize_small import main


@patch('vulcanlab.cli.simple_sanitize_small.sanitize_small_document_standalone')
@patch('sys.argv', ['simple_sanitize_small.py', '--work-id', '123'])
def test_cli_success(mock_sanitize, capsys):
    """Test CLI with successful execution."""
    mock_sanitize.return_value = 5

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert 'Work ID:              123' in captured.out
    assert 'Heading Modifications: 5' in captured.out


@patch('vulcanlab.cli.simple_sanitize_small.sanitize_small_document_standalone')
@patch('sys.argv', ['simple_sanitize_small.py', '--work-id', '999'])
def test_cli_work_not_found(mock_sanitize):
    """Test CLI with non-existent work."""
    mock_sanitize.side_effect = ValueError("Work 999 not found")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


@patch('vulcanlab.cli.simple_sanitize_small.sanitize_small_document_standalone')
@patch('sys.argv', ['simple_sanitize_small.py', '--work-id', '123'])
def test_cli_unexpected_error(mock_sanitize):
    """Test CLI with unexpected error."""
    mock_sanitize.side_effect = Exception("LLM timeout")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2
```

## Manual Test Plan

### Setup
1. Ensure database initialized with T01 schema
2. Seed `simple_sanitize_small` template in DB (via T01 migration)
3. Create test Work with SMALL classification (via T03)
4. Configure LLM client credentials

### Test Cases

#### TC1: Sanitize Small Document Successfully
**Steps**:
1. Parse and classify a small work (work_id=1, ~5k tokens)
2. Run CLI: `python -m vulcanlab.cli.simple_sanitize_small --work-id 1`
3. Verify CLI output shows heading modification count
4. Query DB: `SELECT * FROM sanitized_markdown WHERE parsed_markdown_id = X`
5. Verify sanitized content saved
6. Query DB: `SELECT * FROM heading_modifications WHERE sanitized_markdown_id = Y`
7. Verify modification records created

**Expected**: Sanitized markdown saved, modifications tracked

#### TC2: Template Loaded from Database
**Steps**:
1. Update `simple_sanitize_small` template in DB
2. Run sanitization
3. Check logs for "Loaded template from database" message
4. Verify LLM prompt uses updated template

**Expected**: Template loaded from DB, not fallback

#### TC3: Template Fallback
**Steps**:
1. Delete `simple_sanitize_small` template from DB
2. Run sanitization
3. Check logs for "using fallback" message
4. Verify sanitization still works

**Expected**: Falls back to hardcoded template gracefully

#### TC4: LLM Response Parsing
**Steps**:
1. Run sanitization with verbose logging
2. Examine LLM response in logs
3. Verify JSON parsing extracted modifications correctly
4. Check HeadingModification records match LLM output

**Expected**: LLM JSON parsed correctly

#### TC5: Heading Modification Actions
**Steps**:
1. Run sanitization on document with varied headings
2. Query `heading_modifications` table
3. Verify all three action types present: REMOVE, CHANGE, KEEP
4. For CHANGE actions, verify `new_heading` is populated
5. For REMOVE/KEEP actions, verify `new_heading` is NULL

**Expected**: All action types handled correctly

#### TC6: Content Compression
**Steps**:
1. Sanitize a document resulting in >1MB sanitized markdown
2. Query: `SELECT pg_column_size(content) FROM sanitized_markdown WHERE id = X`
3. Verify compressed size < original size

**Expected**: Large content compressed automatically

#### TC7: Wrong Classification Error
**Steps**:
1. Create work classified as LARGE
2. Try to run small sanitization CLI
3. Verify error about wrong classification

**Expected**: Validation prevents processing large docs with small module

#### TC8: Work Not Parsed Error
**Steps**:
1. Create work without ParsedMarkdown record
2. Try to run sanitization
3. Verify error about work not parsed

**Expected**: Validation prevents sanitizing unparsed works

## Dependencies

- **Internal**: T01 (models), T03 (ParsedMarkdown), template_loader, LLM client
- **External**: LangChain, LLM provider (OpenAI/Anthropic)
- **Testing**: pytest, pytest-mock

## Assumptions

1. LLM client exists at `vulcanlab.llm.client` with `get_llm_client()` and `.generate(prompt)` method
2. LLM reliably returns valid JSON responses
3. Template system from T01 is functional
4. ParsedMarkdown.content property handles decompression automatically
5. Heading modification list from LLM includes all headings in document

## Notes

- This is a **backend-only** ticket
- CLI tool is standalone and functional
- All tests use mocks - no database or LLM calls
- JSON parsing handles LLM adding extra text around JSON
- Template follows existing pattern from `template_loader.py`
- Heading modifications tracked for audit trail and potential UI display
- Processing status updated to track sanitization completion

## Definition of Done

- [ ] All code implemented as specified
- [ ] All unit tests pass (12 tests total)
- [ ] Manual test plan executed and passed
- [ ] CLI tool runs standalone with `--help` working
- [ ] No database or LLM calls in unit tests (mocks only)
- [ ] Code follows existing project patterns
- [ ] Template loads from DB with fallback working
- [ ] LLM JSON response parsed correctly
- [ ] All heading modification actions (REMOVE/CHANGE/KEEP) handled
- [ ] Content compression works for large sanitized output
