"""
Breadcrumb generation for chunk hierarchy navigation.

This module provides breadcrumb trail generation by traversing the chunk
parent_id hierarchy upward to H1 or root.
"""

import logging
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def build_breadcrumb(chunk_id: int, session: Session) -> str:
    """
    Build breadcrumb trail by traversing chunk hierarchy to root.

    Traverses parent_id relationships upward until reaching H1 or root (parent_id=NULL).
    Returns formatted breadcrumb string with " > " separator.
    First checks if heading_breadcrumbs is already populated on the chunk.

    Args:
        chunk_id: ID of the chunk to build breadcrumb for
        session: SQLAlchemy session for database operations

    Returns:
        Breadcrumb string (e.g., "Chapter 1 > Section 1.2 > Subsection 1.2.3")
        Returns "[No heading]" for orphaned chunks or if chunk not found
    """
    if session is None:
        raise ValueError("Session is required")

    # Step 1: Check if heading_breadcrumbs is already populated
    check_query = text("SELECT heading_breadcrumbs FROM chunks WHERE id = :chunk_id")
    try:
        heading_breadcrumbs = session.execute(check_query, {"chunk_id": chunk_id}).scalar()
        if heading_breadcrumbs:
            return heading_breadcrumbs
    except Exception as e:
        logger.warning(f"Error checking heading_breadcrumbs for chunk {chunk_id}: {e}")

    # Step 2: Use recursive CTE for breadcrumb traversal if field is missing
    # We only take the FIRST LINE of content for headings and strip leading #
    query = text("""
        WITH RECURSIVE chunk_hierarchy AS (
            -- Base case: start with the target chunk
            SELECT
                id,
                parent_id,
                content,
                level,
                0 AS depth
            FROM chunks
            WHERE id = :chunk_id

            UNION ALL

            -- Recursive case: traverse up to parent
            SELECT
                c.id,
                c.parent_id,
                c.content,
                c.level,
                ch.depth + 1 AS depth
            FROM chunks c
            INNER JOIN chunk_hierarchy ch ON c.id = ch.parent_id
            WHERE ch.parent_id IS NOT NULL
        )
        SELECT content, level, depth
        FROM chunk_hierarchy
        WHERE level LIKE 'H%'  -- Only include heading levels
        ORDER BY depth DESC;  -- Root to leaf order
    """)

    try:
        result = session.execute(query, {"chunk_id": chunk_id}).fetchall()

        if not result:
            return "[No heading]"

        # Process parts: take first line and strip markdown headings (#)
        breadcrumb_parts = []
        for row in result:
            content, level, depth = row
            if not content:
                continue
            
            # Take first line
            first_line = content.splitlines()[0] if content else ""
            # Strip leading # and whitespace
            title = first_line.lstrip('#').strip()
            
            if title:
                breadcrumb_parts.append(title)

        if not breadcrumb_parts:
            return "[No heading]"

        return " > ".join(breadcrumb_parts)

    except Exception as e:
        logger.error(f"Error building breadcrumb for chunk {chunk_id}: {e}")
        return "[No heading]"
