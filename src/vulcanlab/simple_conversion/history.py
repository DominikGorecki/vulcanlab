"""
Query functions for simple conversion history.

Provides database query logic for retrieving simple conversion work history.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from vulcanlab.data.models.work import Work
from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.parsed_markdown import ParsedMarkdown


def get_simple_conversion_history(session: Session) -> List[Dict[str, Any]]:
    """
    Query simple conversion works with summary data.

    Returns list of works that have simple_conversion_mode in processing_status,
    sorted by created_at DESC (most recent first).

    Args:
        session: Database session

    Returns:
        List of dictionaries containing work metadata and chunk counts
    """
    # Count heading chunks (H1-H5)
    heading_count = func.count(case(
        (Chunk.level.in_(['H1', 'H2', 'H3', 'H4', 'H5']), 1)
    ))

    # Count content chunks (level ends with '-chunk' or equals 'chunk')
    content_count = func.count(case(
        (Chunk.level.like('%-chunk'), 1),
        (Chunk.level == 'chunk', 1)
    ))

    # Query with aggregation
    results = (
        session.query(
            Work.id.label('work_id'),
            Work.title,
            Work.authors.label('author'),
            Work.year,
            Work.created_at,
            Work.processing_status,
            ParsedMarkdown.classification,
            ParsedMarkdown.token_count,
            func.count(Chunk.id).label('chunk_count'),
            heading_count.label('heading_chunk_count'),
            content_count.label('content_chunk_count')
        )
        .outerjoin(ParsedMarkdown, ParsedMarkdown.work_id == Work.id)
        .outerjoin(Chunk, Chunk.work_id == Work.id)
        .filter(Work.processing_status.op('?')('simple_conversion_mode'))
        .group_by(
            Work.id,
            Work.title,
            Work.authors,
            Work.year,
            Work.created_at,
            Work.processing_status,
            ParsedMarkdown.classification,
            ParsedMarkdown.token_count
        )
        .order_by(Work.created_at.desc())
        .all()
    )

    # Transform results into dictionaries
    history_items = []
    for row in results:
        ps = row.processing_status or {}

        # Extract mode
        mode = ps.get('simple_conversion_mode')

        # Determine status
        step = ps.get('simple_conversion_step', '')
        error = ps.get('simple_conversion_error') or ps.get('error_message')

        if step == 'failed' or error:
            status = 'failed'
        elif step == 'complete':
            status = 'complete'
        else:
            # Still in progress, consider as incomplete/failed for history view
            status = 'failed'

        # Extract error message
        error_message = error if error else None

        # Extract classification
        classification = None
        if row.classification:
            classification = row.classification.value if hasattr(row.classification, 'value') else str(row.classification)

        history_items.append({
            'work_id': row.work_id,
            'title': row.title,
            'author': row.author,
            'year': row.year,
            'created_at': row.created_at,
            'classification': classification,
            'mode': mode,
            'status': status,
            'token_count': row.token_count,
            'chunk_count': row.chunk_count or 0,
            'heading_chunk_count': row.heading_chunk_count or 0,
            'content_chunk_count': row.content_chunk_count or 0,
            'error_message': error_message
        })

    return history_items
