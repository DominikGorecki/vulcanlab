"""
Duplicate detection for markdown import.

This module provides functions to check for duplicate works based on title
and author before importing markdown files.
"""

import logging
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from vulcanlab.data.models.work import Work

logger = logging.getLogger(__name__)


def check_duplicate_work(
    title: str,
    author: str,
    session: Session
) -> Optional[Work]:
    """Check if a work with matching title and author already exists.

    Performs case-insensitive matching on both title and author fields.
    For the authors field, which may contain multiple comma-separated names,
    this function matches if any author name contains the search term.

    Args:
        title: Work title to search for
        author: Author name to search for
        session: Database session

    Returns:
        Matching Work object if found, None otherwise

    Examples:
        >>> work = check_duplicate_work("The Psychology of Learning", "John Doe", session)
        >>> if work:
        ...     print(f"Duplicate found: {work.id}")
    """
    # Check for empty or whitespace-only strings
    if not title or not title.strip():
        logger.warning("Empty or whitespace-only title provided to check_duplicate_work")
        return None

    if not author or not author.strip():
        logger.warning("Empty or whitespace-only author provided to check_duplicate_work")
        return None

    try:
        # Query for works with matching title and author (case-insensitive)
        # Use ILIKE for case-insensitive matching with partial author matches
        work = (
            session.query(Work)
            .filter(func.lower(Work.title) == func.lower(title))
            .filter(func.lower(Work.authors).like(f"%{author.lower()}%"))
            .first()
        )

        if work:
            logger.info(
                f"Duplicate work found: ID={work.id}, title='{work.title}', "
                f"authors='{work.authors}'"
            )
        else:
            logger.debug(f"No duplicate found for title='{title}', author='{author}'")

        return work

    except Exception as e:
        logger.error(f"Error checking for duplicate work: {e}")
        raise
