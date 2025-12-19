"""
Core operations for chunk search and deletion.

This module provides functions for lexical search of chunks with title/content
ranking, recursive descendant retrieval, and cascading deletion operations.
All functions follow the session-passing pattern and are framework-independent.
"""

import logging
from typing import List, Tuple

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from .models.chunk import Chunk

logger = logging.getLogger(__name__)


def search_chunks_lexical(
    query: str,
    page: int = 1,
    page_size: int = 25,
    headings_only: bool = False,
    session: Session = None
) -> Tuple[List[Chunk], int]:
    """
    Search chunks using lexical matching with custom title/content ranking.

    Ranks results by:
    1. Exact title match (extracted last heading equals query, case-insensitive)
    2. Partial title match (extracted last heading contains query, case-insensitive)
    3. Content match (content contains query, case-insensitive)

    Args:
        query: Search term to match against titles and content
        page: Page number (1-indexed)
        page_size: Number of results per page
        headings_only: If True, only return chunks with level H1-H5 (exclude sentence/chunk)
        session: SQLAlchemy session for database operations

    Returns:
        Tuple of (list of matching Chunk objects, total result count)

    Raises:
        ValueError: If page < 1 or page_size < 1
    """
    if page < 1:
        raise ValueError("Page must be >= 1")
    if page_size < 1:
        raise ValueError("Page size must be >= 1")
    if session is None:
        raise ValueError("Session is required")

    # Extract last heading from breadcrumbs for title matching
    # heading_breadcrumbs format: "H1 > H2 > H3"
    # We want to extract "H3" for comparison
    query_lower = query.lower()

    # Build the ranking expression
    # Priority 1: Exact title match (lowest number = highest priority)
    # Priority 2: Partial title match
    # Priority 3: Content match
    # Priority 4: No match (shouldn't happen due to WHERE clause, but for safety)

    # Extract last heading: split on " > " and take last element
    # Use func.lower for case-insensitive comparison
    last_heading = func.coalesce(
        func.nullif(
            func.split_part(Chunk.heading_breadcrumbs, ' > ', -1),
            ''
        ),
        None
    )

    rank_priority = case(
        # Exact title match (case-insensitive)
        (func.lower(last_heading) == query_lower, 1),
        # Partial title match (case-insensitive)
        (func.lower(last_heading).like(f'%{query_lower}%'), 2),
        # Content match (case-insensitive)
        (func.lower(Chunk.content).like(f'%{query_lower}%'), 3),
        else_=4
    )

    # Build WHERE clause: match in title OR content
    where_clause = (
        (Chunk.heading_breadcrumbs.ilike(f'%{query}%')) |
        (Chunk.content.ilike(f'%{query}%'))
    )

    # Add headings_only filter if requested
    if headings_only:
        where_clause = where_clause & Chunk.level.in_(['H1', 'H2', 'H3', 'H4', 'H5'])

    # Get total count
    total_count = session.query(func.count(Chunk.id)).filter(where_clause).scalar()

    # Get paginated results ordered by ranking
    offset = (page - 1) * page_size
    results = (
        session.query(Chunk)
        .filter(where_clause)
        .order_by(rank_priority, Chunk.id)  # Secondary sort by ID for consistency
        .limit(page_size)
        .offset(offset)
        .all()
    )

    return results, total_count


def get_all_descendants(chunk_id: int, session: Session) -> List[Chunk]:
    """
    Recursively retrieve all descendants of a chunk.

    This function retrieves all children, grandchildren, and deeper descendants
    of the specified chunk in a flat list. Used for preview before deletion.

    Args:
        chunk_id: ID of the parent chunk
        session: SQLAlchemy session for database operations

    Returns:
        List of all descendant Chunk objects (empty list if no descendants)

    Note:
        Returns empty list for non-existent chunk_id (not an error).
    """
    if session is None:
        raise ValueError("Session is required")

    # Query direct children
    children = session.query(Chunk).filter(Chunk.parent_id == chunk_id).all()

    if not children:
        return []

    # Recursively collect all descendants
    all_descendants = list(children)  # Start with direct children

    for child in children:
        # Recursively get descendants of each child
        child_descendants = get_all_descendants(child.id, session)
        all_descendants.extend(child_descendants)

    return all_descendants


def delete_chunk_cascade(chunk_id: int, session: Session) -> int:
    """
    Delete a chunk and all its descendants using database CASCADE.

    The actual deletion of descendants is handled by the database CASCADE
    constraint on the parent_id foreign key. This function verifies the chunk
    exists, retrieves descendants for counting, and deletes the parent chunk.

    Args:
        chunk_id: ID of the chunk to delete
        session: SQLAlchemy session for database operations

    Returns:
        Total count of chunks deleted (parent + all descendants)

    Raises:
        ValueError: If chunk_id does not exist

    Note:
        Caller is responsible for committing the transaction.
        Database CASCADE will automatically delete all descendants.
    """
    if session is None:
        raise ValueError("Session is required")

    # Verify chunk exists
    chunk = session.query(Chunk).filter(Chunk.id == chunk_id).first()
    if chunk is None:
        raise ValueError(f"Chunk with id {chunk_id} not found")

    # Get all descendants for counting (before deletion)
    descendants = get_all_descendants(chunk_id, session)
    descendant_count = len(descendants)
    total_count = 1 + descendant_count  # Parent + descendants

    # Log the deletion
    logger.info(
        f"Deleting chunk {chunk_id} with {descendant_count} descendants "
        f"(total: {total_count} chunks)"
    )

    # Delete the parent chunk
    # Database CASCADE constraint will automatically delete all descendants
    session.delete(chunk)

    # Note: Commit is handled by the caller (session management pattern)

    return total_count
