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

    # Get SanitizedMarkdown (directly by work_id)
    sanitized = session.query(SanitizedMarkdown).filter(
        SanitizedMarkdown.work_id == work_id
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
        # Still update processing status even with 0 chunks
        if not work.processing_status:
            work.processing_status = {}
        work.processing_status['simple_conversion_step'] = 'chunked'
        work.processing_status['chunk_count'] = 0
        session.commit()
        return []

    # Calculate ranges
    ranges = calculate_heading_ranges(headings, total_lines)

    # Create Chunk records
    chunks = []
    for line_num, level, start_line, end_line, heading_text in ranges:
        # Extract chunk content
        chunk_content = extract_chunk_content(lines, start_line, end_line)

        # Create Chunk record (adapt to actual model schema)
        chunk = Chunk(
            work_id=work_id,
            level=f"H{level}",  # Store as "H1", "H2", etc.
            content=chunk_content,
            start_line=start_line,
            end_line=end_line,
            heading_breadcrumbs=heading_text,  # Use heading_breadcrumbs to store heading text
            vector_status="to_vec",  # Mark for vectorization
            parent_id=None,  # No parent hierarchy in simple conversion
            embedding=None  # No embedding yet
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
