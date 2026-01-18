"""
Dense search using pgvector similarity.

This module provides dense (vector) search functionality using pgvector's
cosine distance operator for semantic similarity.
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


def generate_query_embedding(query: str) -> List[float]:
    """
    Generate embedding vector for query text.

    Uses the same embedding model as RAG retrieval for consistency.

    Args:
        query: Query text to embed

    Returns:
        Embedding vector as list of floats

    Raises:
        RuntimeError: If embedding generation fails
    """
    # Lazy import to avoid loading heavy AI dependencies until needed
    from vulcanlab.ai.llm_factory import create_embeddings

    try:
        embeddings_model = create_embeddings()
        # embed_query returns a single embedding for the query
        embedding = embeddings_model.embed_query(query)
        return embedding
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        raise RuntimeError(f"Failed to generate query embedding: {e}")


def search_dense(
    query: str,
    session: Session,
    page: int = 1,
    page_size: int = 20,
    headings_only: bool = False,
    top_k: int = 20
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Search chunks using pgvector dense similarity.

    Uses cosine distance (<=> operator) for semantic similarity.
    Generates query embedding using same model as RAG retrieval.
    Joins with works table to include bibliographic metadata.

    Args:
        query: Search query string (will be embedded)
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
            - similarity_score: cosine similarity (1 - distance)

    Raises:
        ValueError: If page < 1, page_size < 1, or session is None
        RuntimeError: If embedding generation fails

    Examples:
        >>> results, total = search_dense("cognitive processes", session, page=1, page_size=10)
        >>> results[0]['similarity_score']
        0.87654
    """
    if page < 1:
        raise ValueError("Page must be >= 1")
    if page_size < 1:
        raise ValueError("Page size must be >= 1")
    if session is None:
        raise ValueError("Session is required")
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    logger.info(f"Dense search: query='{query}', page={page}, page_size={page_size}, headings_only={headings_only}")

    # Generate query embedding
    try:
        query_embedding = generate_query_embedding(query.strip())
    except RuntimeError as e:
        # Re-raise with context
        raise RuntimeError(f"Dense search failed: {e}")

    # Convert embedding to PostgreSQL vector literal
    embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'

    # Build WHERE clause
    where_conditions = [
        "c.embedding IS NOT NULL"  # Skip chunks without embeddings
    ]

    if headings_only:
        where_conditions.append("c.level IN ('H1', 'H2', 'H3', 'H4', 'H5')")
    else:
        where_conditions.append("c.dense_lexical_use = TRUE")

    where_clause = " AND ".join(where_conditions)

    # Count total results (limited by top_k)
    # We need to count how many results we would get from the top_k candidates
    count_query = text(f"""
        WITH top_candidates AS (
            SELECT c.id
            FROM chunks c
            WHERE {where_clause}
            ORDER BY c.embedding <=> :embedding
            LIMIT :top_k
        )
        SELECT COUNT(*) FROM top_candidates
    """)

    total_count = session.execute(
        count_query,
        {"embedding": embedding_str, "top_k": top_k}
    ).scalar()

    logger.debug(f"Dense search found {total_count} total results (limited by top_k={top_k})")

    # Calculate offset for pagination
    offset = (page - 1) * page_size

    # Main search query with similarity scoring
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
            1 - (c.embedding <=> :embedding) AS similarity_score,
            c.heading_breadcrumbs
        FROM chunks c
        INNER JOIN works w ON c.work_id = w.id
        WHERE {where_clause}
        ORDER BY c.embedding <=> :embedding, c.id
        LIMIT :limit
        OFFSET :offset
    """)

    rows = session.execute(
        search_query,
        {
            "embedding": embedding_str,
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
            "similarity_score": float(row[9]) if row[9] else 0.0
        }
        results.append(result)

    logger.debug(f"Returning {len(results)} results for page {page}")

    return results, total_count
