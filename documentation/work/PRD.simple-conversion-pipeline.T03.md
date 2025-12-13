# T03: Parse & Classify Module

**Status**: PENDING
**Priority**: High
**Type**: Backend-Only
**Depends On**: T01 (Database schema), T02 (Token threshold config)
**Blocks**: T04, T05, T07 (Sanitization and API depend on classification)

## Overview

Implement the parse and classify module that takes a converted Work (with PDF/EPUB converted to markdown), counts tokens, classifies as SMALL or LARGE based on the token threshold from config, and saves the ParsedMarkdown record to the database. Includes standalone CLI tool for manual execution.

## Acceptance Criteria

- [ ] Module parses markdown from Citation API
- [ ] Token counting using tiktoken (cl100k_base encoding)
- [ ] Classification logic (< threshold = SMALL, >= threshold = LARGE)
- [ ] Creates ParsedMarkdown record with compressed content
- [ ] CLI tool can be run standalone with `--work-id` argument
- [ ] CLI tool displays classification result and token count
- [ ] All unit tests pass and use mocks (no database access)
- [ ] Manual test plan completed successfully

## Technical Implementation

### 1. Core Module: Parse & Classify

**File**: `src/vulcanlab/simple_conversion/parse_classify.py` (NEW)

```python
"""
Parse and classify module for simple conversion pipeline.

Takes a Work with converted markdown, counts tokens, classifies the document
as SMALL or LARGE based on configurable threshold, and saves ParsedMarkdown
record to the database.
"""

import logging
from typing import Tuple
from datetime import datetime, UTC

import tiktoken
from sqlalchemy.orm import Session

from vulcanlab.data.models.work import Work
from vulcanlab.data.models.parsed_markdown import ParsedMarkdown, DocumentClassification
from vulcanlab.data.database import get_session
from vulcanlab.config.conversion_config import get_token_threshold

logger = logging.getLogger(__name__)

# Tiktoken encoding for token counting (matches OpenAI's cl100k_base)
ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """
    Count tokens in text using tiktoken cl100k_base encoding.

    Args:
        text: Markdown text to count tokens for

    Returns:
        Number of tokens in the text
    """
    if not text:
        return 0

    try:
        tokens = ENCODING.encode(text)
        return len(tokens)
    except Exception as e:
        logger.error(f"Failed to count tokens: {e}")
        # Fallback to rough word-based estimate (1 token ≈ 0.75 words)
        word_count = len(text.split())
        return int(word_count / 0.75)


def classify_document(token_count: int, threshold: int) -> DocumentClassification:
    """
    Classify document as SMALL or LARGE based on token count.

    Args:
        token_count: Number of tokens in the document
        threshold: Token threshold from configuration

    Returns:
        DocumentClassification.SMALL or DocumentClassification.LARGE
    """
    if token_count < threshold:
        return DocumentClassification.SMALL
    else:
        return DocumentClassification.LARGE


def get_markdown_from_citation(work: Work, session: Session) -> str:
    """
    Get markdown content from Citation API for the given Work.

    This uses the existing citation API pattern to retrieve the
    converted markdown content for the work.

    Args:
        work: Work record with conversion completed
        session: Database session

    Returns:
        Markdown content as string

    Raises:
        ValueError: If work has no citation or markdown not available
    """
    # Import here to avoid circular dependency
    from vulcanlab.api.citation import get_markdown_for_work

    if not work.citation_id:
        raise ValueError(f"Work {work.id} has no citation")

    # Use existing API function to get markdown
    markdown = get_markdown_for_work(work.id, session)

    if not markdown:
        raise ValueError(f"No markdown available for work {work.id}")

    return markdown


def parse_and_classify(work_id: int, session: Session) -> ParsedMarkdown:
    """
    Parse markdown from Citation API and classify the document.

    This function:
    1. Retrieves Work by ID
    2. Gets markdown from Citation API
    3. Counts tokens using tiktoken
    4. Classifies as SMALL or LARGE
    5. Creates ParsedMarkdown record
    6. Updates Work.processing_status

    Args:
        work_id: ID of the Work to process
        session: Database session

    Returns:
        Created ParsedMarkdown record

    Raises:
        ValueError: If work not found or invalid state
    """
    # Get work
    work = session.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise ValueError(f"Work {work_id} not found")

    # Validate work is in correct state
    if not work.citation_id:
        raise ValueError(f"Work {work_id} has not been converted yet")

    logger.info(f"Parsing and classifying work {work_id}")

    # Get markdown from Citation API
    markdown_content = get_markdown_from_citation(work, session)

    # Count tokens
    token_count = count_tokens(markdown_content)
    logger.info(f"Work {work_id} has {token_count} tokens")

    # Get threshold from config
    threshold = get_token_threshold()
    logger.info(f"Using token threshold: {threshold}")

    # Classify
    classification = classify_document(token_count, threshold)
    logger.info(f"Work {work_id} classified as: {classification.value}")

    # Create ParsedMarkdown record
    parsed = ParsedMarkdown(
        work_id=work_id,
        content=markdown_content,  # Auto-compressed by model if >1MB
        token_count=token_count,
        classification=classification,
        created_at=datetime.now(UTC)
    )

    session.add(parsed)

    # Update Work.processing_status
    if not work.processing_status:
        work.processing_status = {}

    work.processing_status['simple_conversion_step'] = 'parsed'
    work.processing_status['simple_conversion_classification'] = classification.value
    work.processing_status['simple_conversion_token_count'] = token_count

    session.commit()
    session.refresh(parsed)

    logger.info(
        f"Created ParsedMarkdown {parsed.id} for work {work_id} "
        f"({classification.value}, {token_count} tokens)"
    )

    return parsed


def parse_and_classify_standalone(work_id: int) -> Tuple[int, str]:
    """
    Standalone version of parse_and_classify for CLI usage.

    Args:
        work_id: ID of the Work to process

    Returns:
        Tuple of (token_count, classification_string)

    Raises:
        ValueError: If work not found or invalid state
    """
    with get_session() as session:
        parsed = parse_and_classify(work_id, session)
        return (parsed.token_count, parsed.classification.value)
```

### 2. CLI Tool

**File**: `src/vulcanlab/cli/simple_parse_classify.py` (NEW)

```python
#!/usr/bin/env python3
"""
Standalone CLI tool for parsing and classifying documents.

Usage:
    python -m vulcanlab.cli.simple_parse_classify --work-id 123

This tool runs the parse & classify step of the simple conversion pipeline,
counting tokens and classifying the document as SMALL or LARGE based on
the configured threshold.
"""

import argparse
import logging
import sys

from vulcanlab.simple_conversion.parse_classify import parse_and_classify_standalone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Parse and classify document for simple conversion pipeline'
    )
    parser.add_argument(
        '--work-id',
        type=int,
        required=True,
        help='ID of the Work to process'
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
        logger.info(f"Processing work {args.work_id}")

        token_count, classification = parse_and_classify_standalone(args.work_id)

        print(f"\n{'='*60}")
        print(f"Parse & Classify Complete")
        print(f"{'='*60}")
        print(f"Work ID:        {args.work_id}")
        print(f"Token Count:    {token_count:,}")
        print(f"Classification: {classification}")
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

### 3. Database Model Updates

**File**: `src/vulcanlab/data/models/parsed_markdown.py` (NEW - from T01)

Ensure this model exists from T01 implementation with:
- `work_id` foreign key
- `content` with compression
- `token_count` integer
- `classification` enum (SMALL/LARGE)
- `created_at` timestamp

### 4. Work Model Processing Status

**File**: `src/vulcanlab/data/models/work.py` (MODIFIED)

Ensure `processing_status` JSON field supports these keys:
- `simple_conversion_step`: 'parsed', 'sanitized', 'chunked', 'complete'
- `simple_conversion_classification`: 'small' or 'large'
- `simple_conversion_token_count`: integer

No code changes needed if `processing_status` is already a JSON column.

## Unit Tests

**File**: `tests/unit/test_parse_classify.py` (NEW)

```python
"""Unit tests for parse and classify module."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC

from vulcanlab.simple_conversion.parse_classify import (
    count_tokens,
    classify_document,
    get_markdown_from_citation,
    parse_and_classify
)
from vulcanlab.data.models.parsed_markdown import DocumentClassification


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


@patch('vulcanlab.simple_conversion.parse_classify.get_markdown_for_work')
def test_get_markdown_from_citation_success(mock_get_markdown):
    """Test successful markdown retrieval from Citation API."""
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.citation_id = 123
    mock_session = MagicMock()
    mock_get_markdown.return_value = "# Test Markdown\n\nContent here."

    result = get_markdown_from_citation(mock_work, mock_session)

    assert result == "# Test Markdown\n\nContent here."
    mock_get_markdown.assert_called_once_with(1, mock_session)


@patch('vulcanlab.simple_conversion.parse_classify.get_markdown_for_work')
def test_get_markdown_from_citation_no_citation(mock_get_markdown):
    """Test error when work has no citation."""
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.citation_id = None
    mock_session = MagicMock()

    with pytest.raises(ValueError, match="has no citation"):
        get_markdown_from_citation(mock_work, mock_session)


@patch('vulcanlab.simple_conversion.parse_classify.get_markdown_for_work')
def test_get_markdown_from_citation_no_markdown(mock_get_markdown):
    """Test error when markdown not available."""
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.citation_id = 123
    mock_session = MagicMock()
    mock_get_markdown.return_value = None

    with pytest.raises(ValueError, match="No markdown available"):
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

    token_count, classification = parse_and_classify_standalone(1)

    assert token_count == 12000
    assert classification == 'small'
```

**File**: `tests/unit/test_simple_parse_classify_cli.py` (NEW)

```python
"""Unit tests for parse & classify CLI tool."""

import pytest
from unittest.mock import patch, MagicMock
import sys

from vulcanlab.cli.simple_parse_classify import main


@patch('vulcanlab.cli.simple_parse_classify.parse_and_classify_standalone')
@patch('sys.argv', ['simple_parse_classify.py', '--work-id', '123'])
def test_cli_success(mock_parse, capsys):
    """Test CLI with successful execution."""
    mock_parse.return_value = (15000, 'small')

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert 'Work ID:        123' in captured.out
    assert 'Token Count:    15,000' in captured.out
    assert 'Classification: small' in captured.out


@patch('vulcanlab.cli.simple_parse_classify.parse_and_classify_standalone')
@patch('sys.argv', ['simple_parse_classify.py', '--work-id', '456'])
def test_cli_large_document(mock_parse, capsys):
    """Test CLI with large document classification."""
    mock_parse.return_value = (25000, 'large')

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert 'Classification: large' in captured.out


@patch('vulcanlab.cli.simple_parse_classify.parse_and_classify_standalone')
@patch('sys.argv', ['simple_parse_classify.py', '--work-id', '999'])
def test_cli_work_not_found(mock_parse, capsys):
    """Test CLI with non-existent work."""
    mock_parse.side_effect = ValueError("Work 999 not found")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert 'Validation error' in captured.err or 'Work 999 not found' in captured.err


@patch('vulcanlab.cli.simple_parse_classify.parse_and_classify_standalone')
@patch('sys.argv', ['simple_parse_classify.py', '--work-id', '123'])
def test_cli_unexpected_error(mock_parse, capsys):
    """Test CLI with unexpected error."""
    mock_parse.side_effect = Exception("Database connection failed")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2


@patch('sys.argv', ['simple_parse_classify.py'])
def test_cli_missing_work_id():
    """Test CLI without required --work-id argument."""
    with pytest.raises(SystemExit) as exc_info:
        main()

    # argparse exits with code 2 for missing required arguments
    assert exc_info.value.code == 2


@patch('vulcanlab.cli.simple_parse_classify.parse_and_classify_standalone')
@patch('sys.argv', ['simple_parse_classify.py', '--work-id', '123', '--verbose'])
def test_cli_verbose_mode(mock_parse):
    """Test CLI with verbose logging enabled."""
    mock_parse.return_value = (10000, 'small')

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    # Verbose mode sets log level to DEBUG (tested by no exceptions)
```

## Manual Test Plan

### Setup
1. Ensure database is initialized with T01 schema
2. Create a test Work record with converted markdown
3. Ensure `vulcanlab.config.json` has `conversion.token_threshold` set (from T02)
4. Install dependencies: `pip install tiktoken`

### Test Cases

#### TC1: Parse Small Document
**Steps**:
1. Create Work with ~5,000 token markdown via Citation API
2. Run CLI: `python -m vulcanlab.cli.simple_parse_classify --work-id 1`
3. Verify output shows "Classification: small"
4. Query database: `SELECT * FROM parsed_markdown WHERE work_id = 1`
5. Verify `classification = 'small'` and `token_count ≈ 5000`
6. Check Work.processing_status has correct keys

**Expected**: Small document classified correctly, record saved

#### TC2: Parse Large Document
**Steps**:
1. Create Work with ~25,000 token markdown
2. Run CLI: `python -m vulcanlab.cli.simple_parse_classify --work-id 2`
3. Verify output shows "Classification: large"
4. Query database: verify `classification = 'large'`, `token_count ≈ 25000`

**Expected**: Large document classified correctly

#### TC3: Token Counting Accuracy
**Steps**:
1. Create Work with known markdown (e.g., 100 words)
2. Run parse & classify
3. Manually count tokens using OpenAI tokenizer: https://platform.openai.com/tokenizer
4. Compare CLI output with manual count

**Expected**: Token counts match within 5% margin

#### TC4: Threshold Boundary
**Steps**:
1. Set `conversion.token_threshold = 10000` in config
2. Create Work with exactly 10,000 tokens
3. Run parse & classify
4. Verify classification is LARGE (threshold is inclusive upper bound)

**Expected**: Document at threshold classified as LARGE

#### TC5: Content Compression
**Steps**:
1. Create Work with >1MB markdown content
2. Run parse & classify
3. Query database: `SELECT pg_column_size(content) FROM parsed_markdown WHERE work_id = X`
4. Verify stored size is smaller than original

**Expected**: Large content is compressed automatically

#### TC6: Work Not Found Error
**Steps**:
1. Run CLI: `python -m vulcanlab.cli.simple_parse_classify --work-id 99999`
2. Verify error message about work not found
3. Verify exit code is 1

**Expected**: Graceful error handling

#### TC7: Work Not Converted Yet
**Steps**:
1. Create Work without `citation_id` set
2. Run parse & classify on that work
3. Verify error about work not converted

**Expected**: Validation prevents processing unconverted works

#### TC8: Verbose Mode
**Steps**:
1. Run CLI with `-v` flag: `python -m vulcanlab.cli.simple_parse_classify --work-id 1 -v`
2. Verify detailed debug logging appears
3. Verify shows token counting details

**Expected**: Verbose mode provides detailed logging

## Dependencies

- **External**: `tiktoken` (for token counting)
- **Internal**: T01 (ParsedMarkdown model), T02 (config system), Citation API
- **Testing**: pytest, pytest-mock

## Assumptions

1. Citation API provides `get_markdown_for_work(work_id, session)` function
2. Work records have `citation_id` set after conversion
3. Tiktoken `cl100k_base` encoding matches OpenAI's token counting
4. 1 token ≈ 0.75 words (for fallback estimate)
5. Compression threshold of 1MB is sufficient for most documents

## Notes

- This is a **backend-only** ticket
- CLI tool is standalone and functional (not just for testing)
- All tests use mocks - no database or file I/O
- Token counting uses same encoding as OpenAI (cl100k_base)
- Fallback token counting provides rough estimate if tiktoken fails
- Processing status tracks classification for later steps
- Module follows existing patterns from citation and conversion modules

## Definition of Done

- [ ] All code implemented as specified
- [ ] All unit tests pass (16 tests total)
- [ ] Manual test plan executed and passed
- [ ] CLI tool runs standalone with `--help` working
- [ ] No database access in unit tests (mocks only)
- [ ] Code follows existing project patterns
- [ ] Token counting matches OpenAI tokenizer
- [ ] Compression works for large documents (>1MB)
- [ ] Processing status correctly updated in Work record
