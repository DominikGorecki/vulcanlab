"""
Lexical search using PostgreSQL full-text search.

This module provides lexical (keyword) search functionality using PostgreSQL's
built-in full-text search capabilities (ts_vector, ts_query, ts_rank).
"""

import logging
from typing import List, Tuple, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from .breadcrumb_builder import build_breadcrumb

logger = logging.getLogger(__name__)


def truncate_content_words(content: str, word_limit: int = 100) -> str:
    """
    Truncate content to specified word limit.

    Args:
        content: Text to truncate
        word_limit: Maximum number of words

    Returns:
        Truncated content with ellipsis if truncated
    """
    words = content.split()
    if len(words) <= word_limit:
        return content
    return ' '.join(words[:word_limit]) + '...'


def search_lexical(
    query: str,
    session: Session,
    page: int = 1,
    page_size: int = 20,
    headings_only: bool = False,
    top_k: int = 20
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Search chunks using PostgreSQL full-text search.

    Uses to_tsvector and to_tsquery for efficient lexical matching.
    Ranks results by ts_rank for relevance scoring.
    Joins with works table to include bibliographic metadata.

    Args:
        query: Search query string (will be sanitized for ts_query)
        session: SQLAlchemy session for database operations
        page: Page number (1-indexed)
        page_size: Number of results per page (default: 20)
        headings_only: If True, only search H1-H5 chunks (default: False)
        top_k: Maximum total results to consider (default: 20)

    Returns:
        Tuple of (results list, total count)
        Each result is a dict with:
            - id: chunk ID
            - content_preview: truncated content (100 words)
            - breadcrumb: hierarchical path
            - level: chunk level (H1-H5, sentence, chunk)
            - work_id: work ID
            - work_title: work title
            - work_authors: work authors
            - work_year: publication year
            - start_line: start line number
            - end_line: end line number
            - rank_score: ts_rank relevance score

    Raises:
        ValueError: If page < 1, page_size < 1, or session is None

    Examples:
        >>> results, total = search_lexical("memory", session, page=1, page_size=10)
        >>> results[0]['breadcrumb']
        'Introduction > Cognitive Psychology > Memory Systems'
    """
    if page < 1:
        raise ValueError("Page must be >= 1")
    if page_size < 1:
        raise ValueError("Page size must be >= 1")
    if session is None:
        raise ValueError("Session is required")
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    logger.info(f"Lexical search: query='{query}', page={page}, page_size={page_size}, headings_only={headings_only}")

    # Sanitize query for ts_query (replace spaces with &)
    # This creates AND logic: "cognitive psychology" → "cognitive & psychology"
    tsquery_string = " & ".join(query.strip().split())

    # Build WHERE clause
    where_conditions = [
        "to_tsvector('english', c.content) @@ to_tsquery('english', :tsquery)"
    ]

    if headings_only:
        where_conditions.append("c.level IN ('H1', 'H2', 'H3', 'H4', 'H5')")
    else:
        where_conditions.append("c.dense_lexical_use = TRUE")

    where_clause = " AND ".join(where_conditions)

    # Count total results
    count_query = text(f"""
        SELECT COUNT(*)
        FROM chunks c
        WHERE {where_clause}
    """)

    total_count = session.execute(
        count_query,
        {"tsquery": tsquery_string}
    ).scalar()

    logger.debug(f"Lexical search found {total_count} total results")

    # Calculate offset for pagination
    offset = (page - 1) * page_size

    # Main search query with ranking
    search_query = text(f"""
        SELECT
            c.id,
            c.content,
            c.level,
            c.work_id,
            c.start_line,
            c.end_line,
            w.title AS work_title,
            w.authors AS work_authors,
            w.year AS work_year,
            ts_rank(to_tsvector('english', c.content), to_tsquery('english', :tsquery)) AS rank_score,
            c.heading_breadcrumbs
        FROM chunks c
        INNER JOIN works w ON c.work_id = w.id
        WHERE {where_clause}
        ORDER BY rank_score DESC, c.id
        LIMIT :limit
        OFFSET :offset
    """)

    rows = session.execute(
        search_query,
        {
            "tsquery": tsquery_string,
            "limit": page_size,
            "offset": offset
        }
    ).fetchall()

    # Build result dictionaries with breadcrumbs
    results = []
    for row in rows:
        chunk_id = row[0]
        content = row[1]
        heading_breadcrumbs = row[10]

        # Generate breadcrumb: use stored field if available, fallback to builder
        if heading_breadcrumbs:
            breadcrumb = heading_breadcrumbs
        else:
            breadcrumb = build_breadcrumb(chunk_id, session)

        # Truncate content to 100 words
        content_preview = truncate_content_words(content, word_limit=100)

        result = {
            "id": chunk_id,
            "content_preview": content_preview,
            "breadcrumb": breadcrumb,
            "level": row[2],
            "work_id": row[3],
            "start_line": row[4],
            "end_line": row[5],
            "work_title": row[6],
            "work_authors": row[7],
            "work_year": row[8],
            "rank_score": float(row[9]) if row[9] else 0.0
        }
        results.append(result)

    logger.debug(f"Returning {len(results)} results for page {page}")

    return results, total_count
