"""Unit tests for simple chunking module."""

import pytest
from unittest.mock import patch, MagicMock

from vulcanlab.simple_conversion.chunk_simple import (
    parse_headings_from_markdown,
    calculate_heading_ranges,
    extract_chunk_content,
    create_chunks_from_sanitized,
    create_chunks_standalone
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


def test_create_chunks_from_sanitized_success():
    """Test successful chunk creation from sanitized markdown."""
    # Setup mocks
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.processing_status = {}

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

    sanitized_query = MagicMock()
    sanitized_query.filter.return_value.first.return_value = mock_sanitized

    mock_session.query.side_effect = [work_query, sanitized_query]

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

    # Work exists, sanitized doesn't
    work_query = MagicMock()
    work_query.filter.return_value.first.return_value = mock_work

    sanitized_query = MagicMock()
    sanitized_query.filter.return_value.first.return_value = None

    mock_session.query.side_effect = [work_query, sanitized_query]

    with pytest.raises(ValueError, match="has not been sanitized yet"):
        create_chunks_from_sanitized(1, mock_session)


def test_create_chunks_from_sanitized_no_headings():
    """Test handling markdown with no headings."""
    mock_session = MagicMock()
    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.processing_status = {}

    # Markdown with no headings
    mock_sanitized = MagicMock()
    mock_sanitized.content = "Just plain text.\n\nNo headings here."

    work_query = MagicMock()
    work_query.filter.return_value.first.return_value = mock_work

    sanitized_query = MagicMock()
    sanitized_query.filter.return_value.first.return_value = mock_sanitized

    mock_session.query.side_effect = [work_query, sanitized_query]

    chunks = create_chunks_from_sanitized(1, mock_session)

    # Should return empty list, no error
    assert chunks == []
    assert mock_session.add.call_count == 0

    # Should still update processing status
    assert mock_work.processing_status['simple_conversion_step'] == 'chunked'
    assert mock_work.processing_status['chunk_count'] == 0


@patch('vulcanlab.simple_conversion.chunk_simple.get_session')
@patch('vulcanlab.simple_conversion.chunk_simple.create_chunks_from_sanitized')
def test_create_chunks_standalone(mock_create, mock_session):
    """Test standalone function for CLI."""
    mock_chunks = [MagicMock(), MagicMock(), MagicMock()]
    mock_create.return_value = mock_chunks

    mock_db_session = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db_session
    mock_session.return_value.__exit__.return_value = None

    result = create_chunks_standalone(1)

    assert result == 3
    mock_create.assert_called_once_with(1, mock_db_session)
