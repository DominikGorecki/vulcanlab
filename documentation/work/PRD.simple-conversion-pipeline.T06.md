COMPLETE

# T06: Chunking Module with Refactored Dependencies

**Status**: COMPLETE
**Priority**: High
**Type**: Backend-Only
**Depends On**: T01 (Database schema), T04 (SanitizedMarkdown), T05 (SanitizedMarkdown)
**Blocks**: T07 (API endpoints), T10/T11 (Frontend workflows)

## Overview

Refactor the existing chunking module ([src/vulcanlab/chunking/chunk_headings.py](../src/vulcanlab/chunking/chunk_headings.py:1)) to work with the simple conversion pipeline. Currently it reads from files and vectorization suggestions. The new version should read directly from SanitizedMarkdown database records and create Chunk records without file dependencies. Includes standalone CLI tool.

## Acceptance Criteria

- [ ] New chunking function reads from SanitizedMarkdown DB table
- [ ] Creates Chunk records for all headings in sanitized markdown
- [ ] Uses same heading parsing logic as existing `chunk_headings.py`
- [ ] Calculates heading ranges (start_line, end_line) for each chunk
- [ ] All headings marked for VECTORIZE (no SKIP logic in simple pipeline)
- [ ] Links Chunks to Work via foreign key
- [ ] CLI tool runs standalone with `--work-id` argument
- [ ] All unit tests pass and use mocks (no database access)
- [ ] Manual test plan completed successfully

## Technical Implementation

### 1. Core Module: Simple Chunking

**File**: `src/vulcanlab/simple_conversion/chunk_simple.py` (NEW)

```python
"""
Chunking module for simple conversion pipeline.

Reads sanitized markdown from database and creates Chunk records for all
headings (H1-H5). Unlike the regular chunking module, this doesn't use
file-based vectorization suggestions - all headings are vectorized by default.
"""

import logging
import re
from typing import List, Tuple
from datetime import datetime, UTC

from sqlalchemy.orm import Session

from vulcanlab.data.models.work import Work
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.database import get_session

logger = logging.getLogger(__name__)


def parse_headings_from_markdown(content: str) -> List[Tuple[int, int, str]]:
    """
    Parse all headings from markdown content.

    Args:
        content: Markdown content

    Returns:
        List of tuples (line_num, level, heading_text)
    """
    headings = []
    lines = content.splitlines()

    for i, line in enumerate(lines, start=1):
        match = re.match(r'^(#+)\s+(.*)$', line)
        if match:
            level = len(match.group(1))
            if level <= 5:  # Only H1-H5 (skip H6)
                heading_text = match.group(2).strip()
                headings.append((i, level, heading_text))

    logger.debug(f"Parsed {len(headings)} headings (H1-H5)")
    return headings


def calculate_heading_ranges(
    headings: List[Tuple[int, int, str]],
    total_lines: int
) -> List[Tuple[int, int, int, int, str]]:
    """
    Calculate start and end lines for each heading section.

    A heading section extends from the heading line to the line before
    the next heading of equal or higher level (lower number).

    Args:
        headings: List of (line_num, level, heading_text)
        total_lines: Total number of lines in the document

    Returns:
        List of tuples (line_num, level, start_line, end_line, heading_text)
    """
    ranges = []

    for i, (line_num, level, heading_text) in enumerate(headings):
        start_line = line_num

        # Find end: next heading with same or higher level
        end_line = total_lines
        for j in range(i + 1, len(headings)):
            next_level = headings[j][1]
            if next_level <= level:
                end_line = headings[j][0] - 1
                break

        ranges.append((line_num, level, start_line, end_line, heading_text))

    logger.debug(f"Calculated ranges for {len(ranges)} heading sections")
    return ranges


def extract_chunk_content(
    markdown_lines: List[str],
    start_line: int,
    end_line: int
) -> str:
    """
    Extract content for a chunk from markdown lines.

    Args:
        markdown_lines: All lines of markdown content
        start_line: Starting line number (1-indexed)
        end_line: Ending line number (1-indexed, inclusive)

    Returns:
        Chunk content as string
    """
    # Convert to 0-indexed
    start_idx = start_line - 1
    end_idx = end_line  # end_line is inclusive, so no -1

    chunk_lines = markdown_lines[start_idx:end_idx]
    return '\n'.join(chunk_lines)


def create_chunks_from_sanitized(work_id: int, session: Session) -> List[Chunk]:
    """
    Create Chunk records from sanitized markdown.

    This function:
    1. Retrieves SanitizedMarkdown for the work
    2. Parses all headings (H1-H5)
    3. Calculates heading ranges
    4. Extracts content for each heading section
    5. Creates Chunk records
    6. Updates Work.processing_status

    Args:
        work_id: ID of the Work to process
        session: Database session

    Returns:
        List of created Chunk records

    Raises:
        ValueError: If work not found or not sanitized
    """
    # Get work
    work = session.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise ValueError(f"Work {work_id} not found")

    # Get SanitizedMarkdown
    # Need to join through ParsedMarkdown
    from vulcanlab.data.models.parsed_markdown import ParsedMarkdown

    parsed = session.query(ParsedMarkdown).filter(
        ParsedMarkdown.work_id == work_id
    ).first()

    if not parsed:
        raise ValueError(f"Work {work_id} has no ParsedMarkdown record")

    sanitized = session.query(SanitizedMarkdown).filter(
        SanitizedMarkdown.parsed_markdown_id == parsed.id
    ).first()

    if not sanitized:
        raise ValueError(f"Work {work_id} has not been sanitized yet")

    logger.info(f"Creating chunks for work {work_id}")

    # Get sanitized content (auto-decompressed by model property)
    content = sanitized.content
    lines = content.splitlines()
    total_lines = len(lines)

    # Parse headings
    headings = parse_headings_from_markdown(content)

    if not headings:
        logger.warning(f"No headings found in sanitized markdown for work {work_id}")
        return []

    # Calculate ranges
    ranges = calculate_heading_ranges(headings, total_lines)

    # Create Chunk records
    chunks = []
    for line_num, level, start_line, end_line, heading_text in ranges:
        # Extract chunk content
        chunk_content = extract_chunk_content(lines, start_line, end_line)

        # Create Chunk record
        chunk = Chunk(
            work_id=work_id,
            heading_level=level,
            heading_text=heading_text,
            start_line=start_line,
            end_line=end_line,
            content=chunk_content,
            created_at=datetime.now(UTC)
        )

        session.add(chunk)
        chunks.append(chunk)

    logger.info(f"Created {len(chunks)} chunks for work {work_id}")

    # Update Work.processing_status
    if not work.processing_status:
        work.processing_status = {}

    work.processing_status['simple_conversion_step'] = 'chunked'
    work.processing_status['chunk_count'] = len(chunks)

    session.commit()

    # Refresh all chunks to get IDs
    for chunk in chunks:
        session.refresh(chunk)

    logger.info(f"Chunking complete for work {work_id}")

    return chunks


def create_chunks_standalone(work_id: int) -> int:
    """
    Standalone version for CLI usage.

    Args:
        work_id: ID of the Work to process

    Returns:
        Number of chunks created

    Raises:
        ValueError: If validation fails
    """
    with get_session() as session:
        chunks = create_chunks_from_sanitized(work_id, session)
        return len(chunks)
```

### 2. CLI Tool

**File**: `src/vulcanlab/cli/simple_chunk.py` (NEW)

```python
#!/usr/bin/env python3
"""
Standalone CLI tool for chunking sanitized markdown.

Usage:
    python -m vulcanlab.cli.simple_chunk --work-id 123

This tool creates Chunk records from sanitized markdown, extracting all
headings (H1-H5) and their content sections.
"""

import argparse
import logging
import sys

from vulcanlab.simple_conversion.chunk_simple import create_chunks_standalone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Create chunks from sanitized markdown for simple conversion'
    )
    parser.add_argument(
        '--work-id',
        type=int,
        required=True,
        help='ID of the Work to process (must be sanitized)'
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
        logger.info(f"Creating chunks for work {args.work_id}")

        chunk_count = create_chunks_standalone(args.work_id)

        print(f"\n{'='*60}")
        print(f"Chunking Complete")
        print(f"{'='*60}")
        print(f"Work ID:       {args.work_id}")
        print(f"Chunks Created: {chunk_count}")
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

### 3. Database Model: Chunk

**File**: `src/vulcanlab/data/models/chunk.py` (ASSUMED TO EXIST)

Verify Chunk model has these fields:
- `id`: Primary key
- `work_id`: Foreign key to Work
- `heading_level`: Integer (1-5)
- `heading_text`: String
- `start_line`: Integer (1-indexed)
- `end_line`: Integer (1-indexed, inclusive)
- `content`: Text (the actual chunk content)
- `created_at`: Timestamp

If Chunk model doesn't match, document differences in implementation notes.

## Unit Tests

**File**: `tests/unit/test_chunk_simple.py` (NEW)

```python
"""Unit tests for simple chunking module."""

import pytest
from unittest.mock import patch, MagicMock

from vulcanlab.simple_conversion.chunk_simple import (
    parse_headings_from_markdown,
    calculate_heading_ranges,
    extract_chunk_content,
    create_chunks_from_sanitized
)


def test_parse_headings_simple():
    """Test parsing headings from simple markdown."""
    markdown = """
# Heading One

Some content.

## Heading Two

More content.

### Heading Three

Even more content.
"""

    headings = parse_headings_from_markdown(markdown)

    assert len(headings) == 3
    assert headings[0] == (2, 1, 'Heading One')
    assert headings[1] == (6, 2, 'Heading Two')
    assert headings[2] == (10, 3, 'Heading Three')


def test_parse_headings_all_levels():
    """Test parsing all heading levels H1-H5."""
    markdown = """
# Level 1
## Level 2
### Level 3
#### Level 4
##### Level 5
###### Level 6
"""

    headings = parse_headings_from_markdown(markdown)

    # Should only get H1-H5, not H6
    assert len(headings) == 5
    assert headings[0][1] == 1
    assert headings[4][1] == 5


def test_parse_headings_no_headings():
    """Test parsing markdown with no headings."""
    markdown = "Just some plain text.\n\nNo headings here."

    headings = parse_headings_from_markdown(markdown)

    assert len(headings) == 0


def test_calculate_heading_ranges_simple():
    """Test calculating ranges for simple heading structure."""
    headings = [
        (1, 1, 'First'),
        (5, 1, 'Second'),
        (10, 1, 'Third')
    ]
    total_lines = 15

    ranges = calculate_heading_ranges(headings, total_lines)

    assert len(ranges) == 3
    # First heading: line 1 to 4 (before second heading at line 5)
    assert ranges[0] == (1, 1, 1, 4, 'First')
    # Second heading: line 5 to 9
    assert ranges[1] == (5, 1, 5, 9, 'Second')
    # Third heading: line 10 to end
    assert ranges[2] == (10, 1, 10, 15, 'Third')


def test_calculate_heading_ranges_nested():
    """Test calculating ranges with nested headings."""
    headings = [
        (1, 1, 'Main'),
        (3, 2, 'Sub 1'),
        (6, 2, 'Sub 2'),
        (10, 1, 'Next Main')
    ]
    total_lines = 15

    ranges = calculate_heading_ranges(headings, total_lines)

    # Main heading extends until next H1 at line 10
    assert ranges[0] == (1, 1, 1, 9, 'Main')
    # Sub 1 extends until next H2 at line 6
    assert ranges[1] == (3, 2, 3, 5, 'Sub 1')
    # Sub 2 extends until next H1 at line 10
    assert ranges[2] == (6, 2, 6, 9, 'Sub 2')
    # Next Main extends to end
    assert ranges[3] == (10, 1, 10, 15, 'Next Main')


def test_extract_chunk_content():
    """Test extracting chunk content from lines."""
    lines = [
        "Line 1",
        "Line 2",
        "Line 3",
        "Line 4",
        "Line 5"
    ]

    # Extract lines 2-4 (1-indexed)
    content = extract_chunk_content(lines, 2, 4)

    assert content == "Line 2\nLine 3\nLine 4"


def test_extract_chunk_content_single_line():
    """Test extracting single line chunk."""
    lines = ["Line 1", "Line 2", "Line 3"]

    content = extract_chunk_content(lines, 2, 2)

    assert content == "Line 2"


@patch('vulcanlab.simple_conversion.chunk_simple.session')
def test_create_chunks_from_sanitized_success(mock_session):
    """Test successful chunk creation from sanitized markdown."""
    # Setup mocks
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.processing_status = {}

    mock_parsed = MagicMock()
    mock_parsed.id = 10

    sanitized_content = """# First Heading

Content for first section.

## Second Heading

Content for second section.
"""
    mock_sanitized = MagicMock()
    mock_sanitized.content = sanitized_content

    # Mock query chains
    work_query = MagicMock()
    work_query.filter.return_value.first.return_value = mock_work

    parsed_query = MagicMock()
    parsed_query.filter.return_value.first.return_value = mock_parsed

    sanitized_query = MagicMock()
    sanitized_query.filter.return_value.first.return_value = mock_sanitized

    mock_session.query.side_effect = [work_query, parsed_query, sanitized_query]

    # Execute
    chunks = create_chunks_from_sanitized(1, mock_session)

    # Verify chunks created
    assert mock_session.add.call_count == 2  # 2 headings = 2 chunks

    # Verify processing_status updated
    assert mock_work.processing_status['simple_conversion_step'] == 'chunked'
    assert mock_work.processing_status['chunk_count'] == 2

    # Verify commit called
    assert mock_session.commit.called


def test_create_chunks_from_sanitized_work_not_found():
    """Test error when work doesn't exist."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="Work 999 not found"):
        create_chunks_from_sanitized(999, mock_session)


def test_create_chunks_from_sanitized_not_sanitized():
    """Test error when work not sanitized yet."""
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1

    mock_parsed = MagicMock()
    mock_parsed.id = 10

    # Work and parsed exist, sanitized doesn't
    work_query = MagicMock()
    work_query.filter.return_value.first.return_value = mock_work

    parsed_query = MagicMock()
    parsed_query.filter.return_value.first.return_value = mock_parsed

    sanitized_query = MagicMock()
    sanitized_query.filter.return_value.first.return_value = None

    mock_session.query.side_effect = [work_query, parsed_query, sanitized_query]

    with pytest.raises(ValueError, match="has not been sanitized yet"):
        create_chunks_from_sanitized(1, mock_session)


def test_create_chunks_from_sanitized_no_headings():
    """Test handling markdown with no headings."""
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.processing_status = {}

    mock_parsed = MagicMock()
    mock_parsed.id = 10

    # Markdown with no headings
    mock_sanitized = MagicMock()
    mock_sanitized.content = "Just plain text.\n\nNo headings here."

    work_query = MagicMock()
    work_query.filter.return_value.first.return_value = mock_work

    parsed_query = MagicMock()
    parsed_query.filter.return_value.first.return_value = mock_parsed

    sanitized_query = MagicMock()
    sanitized_query.filter.return_value.first.return_value = mock_sanitized

    mock_session.query.side_effect = [work_query, parsed_query, sanitized_query]

    chunks = create_chunks_from_sanitized(1, mock_session)

    # Should return empty list, no error
    assert chunks == []
    assert mock_session.add.call_count == 0


@patch('vulcanlab.simple_conversion.chunk_simple.get_session')
@patch('vulcanlab.simple_conversion.chunk_simple.create_chunks_from_sanitized')
def test_create_chunks_standalone(mock_create, mock_session):
    """Test standalone function for CLI."""
    mock_chunks = [MagicMock(), MagicMock(), MagicMock()]
    mock_create.return_value = mock_chunks

    from vulcanlab.simple_conversion.chunk_simple import create_chunks_standalone
    result = create_chunks_standalone(1)

    assert result == 3
```

**File**: `tests/unit/test_simple_chunk_cli.py` (NEW)

```python
"""Unit tests for simple chunking CLI tool."""

import pytest
from unittest.mock import patch

from vulcanlab.cli.simple_chunk import main


@patch('vulcanlab.cli.simple_chunk.create_chunks_standalone')
@patch('sys.argv', ['simple_chunk.py', '--work-id', '123'])
def test_cli_success(mock_chunk, capsys):
    """Test CLI with successful execution."""
    mock_chunk.return_value = 8

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert 'Work ID:       123' in captured.out
    assert 'Chunks Created: 8' in captured.out


@patch('vulcanlab.cli.simple_chunk.create_chunks_standalone')
@patch('sys.argv', ['simple_chunk.py', '--work-id', '999'])
def test_cli_work_not_found(mock_chunk):
    """Test CLI with non-existent work."""
    mock_chunk.side_effect = ValueError("Work 999 not found")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


@patch('vulcanlab.cli.simple_chunk.create_chunks_standalone')
@patch('sys.argv', ['simple_chunk.py', '--work-id', '123'])
def test_cli_no_headings(mock_chunk, capsys):
    """Test CLI when no headings found."""
    mock_chunk.return_value = 0

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert 'Chunks Created: 0' in captured.out
```

## Manual Test Plan

### Setup
1. Database initialized with T01 schema
2. Create test Work with sanitized markdown (via T04 or T05)
3. Ensure Chunk model exists and matches expected schema

### Test Cases

#### TC1: Chunk Small Document
**Steps**:
1. Create and sanitize a small document with 5 headings
2. Run CLI: `python -m vulcanlab.cli.simple_chunk --work-id 1`
3. Verify CLI output shows 5 chunks created
4. Query DB: `SELECT * FROM chunks WHERE work_id = 1`
5. Verify 5 Chunk records exist
6. Check heading_level, heading_text, start_line, end_line, content fields

**Expected**: 5 chunks created with correct metadata

#### TC2: Chunk Large Document
**Steps**:
1. Create and sanitize a large document with 50 headings
2. Run chunking
3. Query DB: verify 50 Chunk records
4. Verify heading ranges don't overlap

**Expected**: All 50 headings chunked correctly

#### TC3: Nested Heading Structure
**Steps**:
1. Create markdown with nested structure:
   ```
   # H1
   ## H2
   ### H3
   ## H2
   # H1
   ```
2. Run chunking
3. Verify ranges:
   - First H1 extends until second H1
   - First H2 extends until second H2
   - H3 extends until second H2

**Expected**: Heading ranges calculated correctly for nesting

#### TC4: Heading Level Filtering
**Steps**:
1. Create markdown with H1-H6 headings
2. Run chunking
3. Query chunks
4. Verify only H1-H5 chunks created (no H6)

**Expected**: H6 headings excluded

#### TC5: Content Extraction
**Steps**:
1. Create markdown with known content under each heading
2. Run chunking
3. Query chunk content for each chunk
4. Verify content matches expected section

**Expected**: Chunk content correctly extracted

#### TC6: No Headings Edge Case
**Steps**:
1. Create sanitized markdown with no headings (plain text only)
2. Run chunking
3. Verify 0 chunks created, no error

**Expected**: Handles no-heading case gracefully

#### TC7: Processing Status Update
**Steps**:
1. Run chunking on a work
2. Query Work.processing_status
3. Verify `simple_conversion_step = 'chunked'`
4. Verify `chunk_count` matches actual chunk count

**Expected**: Processing status updated correctly

#### TC8: Work Not Sanitized Error
**Steps**:
1. Create work that's only parsed, not sanitized
2. Try to run chunking
3. Verify error about work not sanitized

**Expected**: Validation prevents chunking unsanitized works

## Dependencies

- **Internal**: T01 (Chunk model), T04/T05 (SanitizedMarkdown)
- **External**: None (uses standard library regex)
- **Testing**: pytest

## Assumptions

1. Chunk model exists with expected schema
2. SanitizedMarkdown.content property auto-decompresses content
3. All headings should be vectorized (no SKIP logic needed)
4. Heading ranges calculated same way as existing `chunk_headings.py`
5. Only H1-H5 headings are chunked (H6 ignored)

## Notes

- This is a **backend-only** ticket
- Refactored from existing `chunk_headings.py` but reads from DB instead of files
- No vectorization suggestions needed - all headings are chunked
- CLI tool is standalone and functional
- All tests use mocks - no database access
- Heading range calculation logic reused from existing module
- Content extraction uses line-based slicing

## Definition of Done

- [ ] All code implemented as specified
- [ ] All unit tests pass (12 tests total)
- [ ] Manual test plan executed and passed
- [ ] CLI tool runs standalone with `--help`
- [ ] No database access in unit tests (mocks only)
- [ ] Heading parsing works for H1-H5
- [ ] Heading ranges calculated correctly for nested structures
- [ ] Chunk content properly extracted
- [ ] Processing status updated after chunking
- [ ] Code follows existing chunking module patterns
