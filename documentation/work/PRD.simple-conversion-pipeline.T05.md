COMPLETE

# T05: Large Document Sanitization Module

**Status**: COMPLETE
**Priority**: High
**Type**: Backend-Only
**Depends On**: T01 (Database schema), T03 (Parse & classify)
**Blocks**: T07 (API endpoints), T10/T11 (Frontend workflows)

## Overview

Implement the sanitization module for LARGE documents (>=15k tokens). This module uses a heuristic approach to extract headings with surrounding context, creates a condensed representation, sends it to an LLM for analysis, and saves the SanitizedMarkdown record with heading modifications. This avoids sending massive documents to the LLM.

## Acceptance Criteria

- [ ] Module extracts headings from markdown using regex
- [ ] Each heading includes 100 chars before and after for context
- [ ] Condensed document created with heading + context snippets
- [ ] Prompt template loaded from DB (`simple_sanitize_large` tag)
- [ ] Template uses LangChain format with `{condensed_markdown}` variable
- [ ] LLM analyzes condensed version instead of full document
- [ ] Full sanitized markdown reconstructed by applying LLM modifications
- [ ] Create SanitizedMarkdown record with compressed content
- [ ] Create HeadingModification records
- [ ] CLI tool runs standalone with `--work-id` argument
- [ ] All unit tests pass and use mocks (no database or LLM calls)
- [ ] Manual test plan completed successfully

## Technical Implementation

### 1. Prompt Template Setup

**Template Function Tag**: `simple_sanitize_large`

**Default Template** (to be seeded in DB via T01):

```
You are an expert document sanitizer analyzing a LARGE document. Due to size, you're seeing only headings with surrounding context (100 chars before/after each heading).

Condensed markdown (headings + context):
{condensed_markdown}

Your task is to analyze the headings and decide which to keep, remove, or change:
- REMOVE: Duplicate, redundant, or unnecessary headings
- CHANGE: Headings that need rewording for clarity or consistency
- KEEP: Appropriate headings that should remain as-is

Respond in the following JSON format:
{{
  "modifications": [
    {{"original": "Heading Text", "action": "remove", "reason": "Duplicate heading"}},
    {{"original": "Another Heading", "action": "change", "new": "Better Heading", "reason": "Improved clarity"}},
    {{"original": "Good Heading", "action": "keep", "reason": "Already appropriate"}}
  ]
}}

Important:
- Return ONLY valid JSON, no additional commentary
- Include ALL headings from the condensed markdown in modifications list
- Use action: "remove", "change", or "keep"
- Base decisions on context snippets provided
```

### 2. Core Module: Large Document Sanitization

**File**: `src/vulcanlab/simple_conversion/sanitize_large.py` (NEW)

```python
"""
Large document sanitization module for simple conversion pipeline.

Processes documents classified as LARGE (>=threshold tokens) by extracting
headings with context, creating condensed representation, and using LLM
to analyze headings without processing the entire document.
"""

import logging
import json
import re
from typing import Dict, List, Tuple, Any
from datetime import datetime, UTC

from sqlalchemy.orm import Session
from langchain_core.prompts import PromptTemplate as LCPromptTemplate

from vulcanlab.data.models.work import Work
from vulcanlab.data.models.parsed_markdown import ParsedMarkdown
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.data.models.heading_modifications import HeadingModification, ModificationAction
from vulcanlab.data.database import get_session
from vulcanlab.data.template_loader import load_template
from vulcanlab.llm.client import get_llm_client

logger = logging.getLogger(__name__)

# Context window around each heading (chars before/after)
CONTEXT_WINDOW = 100

# Regex pattern for markdown headings (# through ######)
HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)


def extract_headings_with_context(markdown: str) -> List[Dict[str, Any]]:
    """
    Extract all headings from markdown with surrounding context.

    Args:
        markdown: Full markdown content

    Returns:
        List of dicts with keys: level, text, context_before, context_after, position
    """
    headings = []

    for match in HEADING_PATTERN.finditer(markdown):
        level = len(match.group(1))  # Number of # symbols
        text = match.group(2).strip()
        start_pos = match.start()
        end_pos = match.end()

        # Extract context before (up to CONTEXT_WINDOW chars)
        context_before_start = max(0, start_pos - CONTEXT_WINDOW)
        context_before = markdown[context_before_start:start_pos].strip()

        # Extract context after (up to CONTEXT_WINDOW chars)
        context_after_end = min(len(markdown), end_pos + CONTEXT_WINDOW)
        context_after = markdown[end_pos:context_after_end].strip()

        headings.append({
            'level': level,
            'text': text,
            'context_before': context_before,
            'context_after': context_after,
            'position': start_pos
        })

    logger.info(f"Extracted {len(headings)} headings from markdown")
    return headings


def create_condensed_markdown(headings: List[Dict[str, Any]]) -> str:
    """
    Create condensed markdown with headings and context snippets.

    Args:
        headings: List of heading dicts from extract_headings_with_context

    Returns:
        Condensed markdown string
    """
    lines = []
    lines.append("# Condensed Document (Headings + Context)\n")

    for i, heading in enumerate(headings, 1):
        lines.append(f"\n## Heading {i}")
        lines.append(f"**Level:** {heading['level']}")
        lines.append(f"**Text:** {heading['text']}")

        if heading['context_before']:
            lines.append(f"**Before:** ...{heading['context_before']}")

        if heading['context_after']:
            lines.append(f"**After:** {heading['context_after']}...")

    condensed = '\n'.join(lines)
    logger.debug(f"Created condensed markdown: {len(condensed)} chars")

    return condensed


def get_hardcoded_template_large() -> str:
    """
    Fallback hardcoded template for large document sanitization.

    Returns:
        Template string with {condensed_markdown} placeholder
    """
    return '''You are an expert document sanitizer analyzing a LARGE document. Due to size, you're seeing only headings with surrounding context (100 chars before/after each heading).

Condensed markdown (headings + context):
{condensed_markdown}

Your task is to analyze the headings and decide which to keep, remove, or change:
- REMOVE: Duplicate, redundant, or unnecessary headings
- CHANGE: Headings that need rewording for clarity or consistency
- KEEP: Appropriate headings that should remain as-is

Respond in the following JSON format:
{{
  "modifications": [
    {{"original": "Heading Text", "action": "remove", "reason": "Duplicate heading"}},
    {{"original": "Another Heading", "action": "change", "new": "Better Heading", "reason": "Improved clarity"}},
    {{"original": "Good Heading", "action": "keep", "reason": "Already appropriate"}}
  ]
}}

Important:
- Return ONLY valid JSON, no additional commentary
- Include ALL headings from the condensed markdown in modifications list
- Use action: "remove", "change", or "keep"
- Base decisions on context snippets provided'''


def apply_modifications_to_markdown(
    original_markdown: str,
    modifications: List[Dict[str, Any]]
) -> str:
    """
    Apply heading modifications to original markdown.

    Args:
        original_markdown: Full original markdown content
        modifications: List of modification dicts from LLM

    Returns:
        Sanitized markdown with modifications applied
    """
    result = original_markdown

    # Build modification lookup by original heading text
    mod_map = {mod['original']: mod for mod in modifications}

    # Find and replace headings
    def replace_heading(match):
        level = match.group(1)  # The # symbols
        text = match.group(2).strip()

        if text in mod_map:
            mod = mod_map[text]
            action = mod.get('action', '').lower()

            if action == 'remove':
                # Remove entire heading line
                return ''
            elif action == 'change':
                # Replace with new heading
                new_text = mod.get('new', text)
                return f"{level} {new_text}"
            else:  # keep or unknown
                # Keep as-is
                return match.group(0)
        else:
            # No modification for this heading, keep as-is
            return match.group(0)

    result = HEADING_PATTERN.sub(replace_heading, result)

    # Clean up multiple consecutive blank lines left by removals
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result


def parse_llm_response_large(response_text: str) -> List[Dict[str, Any]]:
    """
    Parse LLM JSON response for large document sanitization.

    Args:
        response_text: Raw LLM response (should contain JSON)

    Returns:
        List of modification dicts

    Raises:
        ValueError: If response is not valid JSON or missing modifications
    """
    try:
        # Extract JSON from response
        start = response_text.find('{')
        end = response_text.rfind('}')

        if start == -1 or end == -1:
            raise ValueError("No JSON found in response")

        json_str = response_text[start:end+1]
        data = json.loads(json_str)

        if 'modifications' not in data:
            raise ValueError("Response missing 'modifications' field")

        return data['modifications']

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError(f"Invalid JSON response: {e}")


def create_heading_modifications_large(
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
            new_heading=mod.get('new'),
            reason=mod.get('reason', ''),
            created_at=datetime.now(UTC)
        )

        session.add(heading_mod)
        records.append(heading_mod)

    return records


def sanitize_large_document(work_id: int, session: Session) -> SanitizedMarkdown:
    """
    Sanitize a large document using condensed heading analysis.

    This function:
    1. Retrieves ParsedMarkdown for the work
    2. Extracts headings with context
    3. Creates condensed markdown
    4. Loads template from DB (with fallback)
    5. Calls LLM with condensed version
    6. Parses LLM response
    7. Applies modifications to full markdown
    8. Creates SanitizedMarkdown record
    9. Creates HeadingModification records
    10. Updates Work.processing_status

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

    if parsed.classification.value != 'large':
        raise ValueError(
            f"Work {work_id} is classified as {parsed.classification.value}, "
            f"expected 'large'"
        )

    logger.info(f"Sanitizing large document for work {work_id}")

    # Extract headings with context
    headings = extract_headings_with_context(parsed.content)

    # Create condensed markdown
    condensed = create_condensed_markdown(headings)
    logger.info(
        f"Condensed from {len(parsed.content)} to {len(condensed)} chars "
        f"({len(headings)} headings)"
    )

    # Load template
    template = load_template('simple_sanitize_large', get_hardcoded_template_large)

    # Format prompt
    prompt = template.format(condensed_markdown=condensed)

    # Call LLM
    llm_client = get_llm_client()
    logger.info(f"Calling LLM for large document sanitization (work {work_id})")
    response = llm_client.generate(prompt)

    # Parse response
    modifications = parse_llm_response_large(response)

    # Apply modifications to full markdown
    sanitized_content = apply_modifications_to_markdown(
        parsed.content,
        modifications
    )

    # Create SanitizedMarkdown record
    sanitized = SanitizedMarkdown(
        parsed_markdown_id=parsed.id,
        content=sanitized_content,  # Auto-compressed if >1MB
        created_at=datetime.now(UTC)
    )

    session.add(sanitized)
    session.flush()  # Get sanitized.id

    # Create HeadingModification records
    heading_records = create_heading_modifications_large(
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
    work.processing_status['condensed_char_count'] = len(condensed)

    session.commit()
    session.refresh(sanitized)

    logger.info(f"Sanitization complete for work {work_id}")

    return sanitized


def sanitize_large_document_standalone(work_id: int) -> Tuple[int, int]:
    """
    Standalone version for CLI usage.

    Args:
        work_id: ID of the Work to process

    Returns:
        Tuple of (heading_count, condensed_char_count)

    Raises:
        ValueError: If validation fails
    """
    with get_session() as session:
        sanitized = sanitize_large_document(work_id, session)

        # Get stats from processing_status
        work = session.query(Work).filter(Work.id == work_id).first()
        heading_count = work.processing_status.get('sanitized_heading_count', 0)
        condensed_chars = work.processing_status.get('condensed_char_count', 0)

        return (heading_count, condensed_chars)
```

### 3. CLI Tool

**File**: `src/vulcanlab/cli/simple_sanitize_large.py` (NEW)

```python
#!/usr/bin/env python3
"""
Standalone CLI tool for sanitizing large documents.

Usage:
    python -m vulcanlab.cli.simple_sanitize_large --work-id 123

This tool runs the large document sanitization step using condensed
heading analysis instead of processing the full document.
"""

import argparse
import logging
import sys

from vulcanlab.simple_conversion.sanitize_large import sanitize_large_document_standalone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Sanitize large document using condensed heading analysis'
    )
    parser.add_argument(
        '--work-id',
        type=int,
        required=True,
        help='ID of the Work to process (must be classified as LARGE)'
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
        logger.info(f"Sanitizing large document for work {args.work_id}")

        heading_count, condensed_chars = sanitize_large_document_standalone(args.work_id)

        print(f"\n{'='*60}")
        print(f"Large Document Sanitization Complete")
        print(f"{'='*60}")
        print(f"Work ID:               {args.work_id}")
        print(f"Headings Analyzed:     {heading_count}")
        print(f"Condensed Size:        {condensed_chars:,} chars")
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

**File**: `tests/unit/test_sanitize_large.py` (NEW)

```python
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


def test_create_condensed_markdown():
    """Test creating condensed markdown from headings."""
    headings = [
        {
            'level': 1,
            'text': 'Main Heading',
            'context_before': 'intro text',
            'context_after': 'first paragraph',
            'position': 10
        },
        {
            'level': 2,
            'text': 'Sub Heading',
            'context_before': 'previous section',
            'context_after': 'sub content',
            'position': 50
        }
    ]

    condensed = create_condensed_markdown(headings)

    assert '# Condensed Document' in condensed
    assert 'Heading 1' in condensed
    assert 'Main Heading' in condensed
    assert 'Sub Heading' in condensed
    assert 'intro text' in condensed
    assert 'first paragraph' in condensed


def test_get_hardcoded_template_large():
    """Test fallback template contains required placeholder."""
    template = get_hardcoded_template_large()

    assert '{condensed_markdown}' in template
    assert 'LARGE document' in template
    assert 'modifications' in template


def test_apply_modifications_to_markdown_remove():
    """Test removing headings from markdown."""
    markdown = "# Keep This\n\nContent.\n\n# Remove This\n\nMore content."
    modifications = [
        {'original': 'Keep This', 'action': 'keep'},
        {'original': 'Remove This', 'action': 'remove'}
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
        {'original': 'Old Heading', 'action': 'change', 'new': 'New Heading'}
    ]

    result = apply_modifications_to_markdown(markdown, modifications)

    assert '# New Heading' in result
    assert 'Old Heading' not in result
    assert 'Content here.' in result


def test_apply_modifications_to_markdown_keep():
    """Test keeping heading unchanged."""
    markdown = "# Good Heading\n\nContent."
    modifications = [
        {'original': 'Good Heading', 'action': 'keep'}
    ]

    result = apply_modifications_to_markdown(markdown, modifications)

    assert result == markdown


def test_apply_modifications_to_markdown_cleanup_blank_lines():
    """Test that multiple blank lines are cleaned up after removals."""
    markdown = "# Keep\n\n# Remove1\n\n# Remove2\n\n# Keep2"
    modifications = [
        {'original': 'Keep', 'action': 'keep'},
        {'original': 'Remove1', 'action': 'remove'},
        {'original': 'Remove2', 'action': 'remove'},
        {'original': 'Keep2', 'action': 'keep'}
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


@patch('vulcanlab.simple_conversion.sanitize_large.get_llm_client')
@patch('vulcanlab.simple_conversion.sanitize_large.load_template')
def test_sanitize_large_document_success(mock_load_template, mock_llm_client):
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

    # Mock LLM response
    llm_response = json.dumps({
        'modifications': [
            {'original': 'Heading 1', 'action': 'keep', 'reason': 'Good'},
            {'original': 'Heading 2', 'action': 'remove', 'reason': 'Duplicate'}
        ]
    })
    mock_llm = MagicMock()
    mock_llm.generate.return_value = llm_response
    mock_llm_client.return_value = mock_llm

    # Execute
    result = sanitize_large_document(1, mock_session)

    # Verify template loaded
    mock_load_template.assert_called_once_with(
        'simple_sanitize_large',
        get_hardcoded_template_large
    )

    # Verify LLM called
    assert mock_llm.generate.called

    # Verify SanitizedMarkdown added
    assert mock_session.add.call_count >= 2

    # Verify processing_status updated
    assert mock_work.processing_status['simple_conversion_step'] == 'sanitized'
    assert 'condensed_char_count' in mock_work.processing_status

    # Verify commit called
    assert mock_session.commit.called


@patch('vulcanlab.simple_conversion.sanitize_large.get_llm_client')
@patch('vulcanlab.simple_conversion.sanitize_large.load_template')
def test_sanitize_large_document_wrong_classification(mock_load_template, mock_llm_client):
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
```

**File**: `tests/unit/test_simple_sanitize_large_cli.py` (NEW)

```python
"""Unit tests for large sanitization CLI tool."""

import pytest
from unittest.mock import patch

from vulcanlab.cli.simple_sanitize_large import main


@patch('vulcanlab.cli.simple_sanitize_large.sanitize_large_document_standalone')
@patch('sys.argv', ['simple_sanitize_large.py', '--work-id', '123'])
def test_cli_success(mock_sanitize, capsys):
    """Test CLI with successful execution."""
    mock_sanitize.return_value = (15, 3500)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert 'Work ID:               123' in captured.out
    assert 'Headings Analyzed:     15' in captured.out
    assert 'Condensed Size:        3,500 chars' in captured.out


@patch('vulcanlab.cli.simple_sanitize_large.sanitize_large_document_standalone')
@patch('sys.argv', ['simple_sanitize_large.py', '--work-id', '999'])
def test_cli_work_not_found(mock_sanitize):
    """Test CLI with non-existent work."""
    mock_sanitize.side_effect = ValueError("Work 999 not found")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
```

## Manual Test Plan

### Setup
1. Database initialized with T01 schema
2. Seed `simple_sanitize_large` template in DB
3. Create test Work with LARGE classification (via T03)
4. Configure LLM client

### Test Cases

#### TC1: Sanitize Large Document Successfully
**Steps**:
1. Parse and classify a large work (work_id=2, ~25k tokens)
2. Run CLI: `python -m vulcanlab.cli.simple_sanitize_large --work-id 2`
3. Verify CLI output shows heading count and condensed size
4. Query DB: verify SanitizedMarkdown and HeadingModification records created
5. Compare original vs sanitized markdown

**Expected**: Large doc sanitized using condensed approach

#### TC2: Heading Extraction Accuracy
**Steps**:
1. Create markdown with 20 headings at various levels
2. Run sanitization
3. Verify all 20 headings extracted
4. Check condensed markdown includes all headings

**Expected**: All headings captured correctly

#### TC3: Context Window
**Steps**:
1. Create document with long paragraphs between headings
2. Run sanitization with verbose logging
3. Examine extracted context snippets
4. Verify each is ≤ 100 chars before/after

**Expected**: Context properly truncated to window size

#### TC4: Modification Application
**Steps**:
1. Run sanitization on large doc
2. Examine LLM response modifications
3. Compare original markdown to sanitized markdown
4. Verify REMOVE actions eliminated headings
5. Verify CHANGE actions updated heading text
6. Verify KEEP actions left headings unchanged

**Expected**: Modifications correctly applied to full markdown

#### TC5: Condensed Size Reduction
**Steps**:
1. Sanitize document with 50k+ chars
2. Check condensed markdown size in logs
3. Verify condensed is significantly smaller than original
4. Calculate token savings

**Expected**: Condensed version much smaller, reduces LLM cost

#### TC6: Template from Database
**Steps**:
1. Update `simple_sanitize_large` template in DB
2. Run sanitization
3. Verify updated template used

**Expected**: Template loaded from DB

#### TC7: Wrong Classification Error
**Steps**:
1. Try to run large sanitization on SMALL classified doc
2. Verify error message

**Expected**: Validation prevents wrong module usage

## Dependencies

- **Internal**: T01 (models), T03 (ParsedMarkdown), template_loader, LLM client
- **External**: LangChain, LLM provider, regex
- **Testing**: pytest, pytest-mock

## Assumptions

1. Markdown headings follow standard format (# through ######)
2. 100 char context window provides sufficient information for LLM decisions
3. Condensed representation is always <50% of original size
4. LLM can make accurate decisions based on context snippets
5. Heading modifications can be applied via regex replacement

## Notes

- This is a **backend-only** ticket
- Large docs use condensed approach to avoid massive LLM costs
- Heading extraction uses regex for simplicity and performance
- Modifications applied to full markdown, not condensed version
- CLI tool is standalone and functional
- All tests use mocks - no database or LLM calls

## Definition of Done

- [ ] All code implemented as specified
- [ ] All unit tests pass (14 tests total)
- [ ] Manual test plan executed and passed
- [ ] CLI tool runs standalone with `--help`
- [ ] No database or LLM calls in unit tests (mocks only)
- [ ] Heading extraction regex works for all levels (# through ######)
- [ ] Context window correctly limits before/after text
- [ ] Condensed markdown significantly smaller than original
- [ ] Modifications correctly applied to full markdown
- [ ] Template loads from DB with fallback
