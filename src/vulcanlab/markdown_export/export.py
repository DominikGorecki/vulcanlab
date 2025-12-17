"""Core export logic for markdown files.

This module provides functions to export work markdown to files with YAML frontmatter.
"""

import logging
import re
from pathlib import Path
from typing import Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from vulcanlab.config import load_config
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.data.models.enums import FileType
from vulcanlab.markdown_export import get_exports_dir

logger = logging.getLogger(__name__)


def generate_export_filename(title: str) -> str:
    """Generate a slugified filename from a work title.

    Args:
        title: Work title to convert to filename

    Returns:
        Slugified filename with .md extension (max 100 chars before extension)

    Examples:
        >>> generate_export_filename("The Psychology of Learning")
        'the-psychology-of-learning.md'
        >>> generate_export_filename("Cognitive Science: Theory & Practice!")
        'cognitive-science-theory-practice.md'
    """
    # Convert to lowercase
    slug = title.lower()

    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')

    # Remove special characters (keep only alphanumeric and hyphens)
    slug = re.sub(r'[^a-z0-9\-]', '', slug)

    # Replace multiple consecutive hyphens with single hyphen
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    # Limit to 100 characters
    slug = slug[:100]

    # Add extension
    return f"{slug}.md"


def create_frontmatter(title: str, author: Optional[str], year: Optional[int]) -> str:
    """Generate YAML frontmatter for markdown export.

    Args:
        title: Work title
        author: Author name (optional)
        year: Publication year (optional)

    Returns:
        YAML frontmatter string with triple-dash delimiters

    Examples:
        >>> create_frontmatter("Test Book", "John Doe", 2023)
        '---\\ntitle: "Test Book"\\nauthor: "John Doe"\\nyear: 2023\\n---\\n'
    """
    lines = ["---"]

    # Always include title (quoted for YAML safety)
    lines.append(f'title: "{title}"')

    # Add author if present
    if author:
        lines.append(f'author: "{author}"')

    # Add year if present
    if year:
        lines.append(f'year: {year}')

    lines.append("---")

    return '\n'.join(lines) + '\n'


def get_markdown_source(work: Work, session: Session) -> Tuple[str, str]:
    """Retrieve markdown content from appropriate source.

    For simple conversion works (PDF/EPUB/MARKDOWN_IMPORT), retrieves from
    sanitized_markdown table in database. For advanced conversion, reads from
    output folder using work.files JSON structure.

    Args:
        work: Work object to get markdown for
        session: Database session for queries

    Returns:
        Tuple of (markdown_content, source) where source is "db" or "file"

    Raises:
        ValueError: If markdown is not available for this work
    """
    # For simple conversion, get from database
    # Check if work has sanitized markdown in DB (simple conversion)
    sanitized = session.query(SanitizedMarkdown).filter(
        SanitizedMarkdown.work_id == work.id
    ).first()

    if sanitized:
        logger.debug(f"Retrieved markdown from DB for work {work.id}")
        return (sanitized.content, "db")

    # For advanced conversion, check output folder for sanitized markdown file
    if work.files and isinstance(work.files, dict):
        sanitized_file_info = work.files.get('sanitized')

        if sanitized_file_info and isinstance(sanitized_file_info, dict):
            sanitized_filename = sanitized_file_info.get('path')

            if sanitized_filename:
                # Construct full path using output directory
                config = load_config()
                output_dir = Path(config.paths.output_dir)
                sanitized_path = output_dir / sanitized_filename

                if sanitized_path.exists():
                    try:
                        content = sanitized_path.read_text(encoding='utf-8')
                        logger.debug(f"Retrieved markdown from file for work {work.id}: {sanitized_path}")
                        return (content, "file")
                    except Exception as e:
                        logger.error(f"Failed to read sanitized markdown file {sanitized_path}: {e}")
                        raise ValueError(f"Failed to read markdown file: {e}")

    # No markdown available
    raise ValueError(f"No markdown available for work {work.id} (title: {work.title})")


def export_work(work_id: int, session: Session) -> str:
    """Export a work's markdown to the exports folder.

    Creates a markdown file with YAML frontmatter in the exports directory.
    Intelligently sources markdown from database (simple conversion) or
    output folder (advanced conversion).

    Args:
        work_id: ID of work to export
        session: Database session

    Returns:
        Export file path as string

    Raises:
        HTTPException: 404 if work not found, 400 if markdown unavailable,
                      500 if write operation fails
    """
    # Query work by ID
    work = session.query(Work).filter(Work.id == work_id).first()

    if not work:
        logger.warning(f"Work not found: {work_id}")
        raise HTTPException(status_code=404, detail=f"Work not found: {work_id}")

    # Get markdown source
    try:
        markdown_content, source = get_markdown_source(work, session)
    except ValueError as e:
        logger.error(f"Markdown unavailable for work {work_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # Generate filename
    filename = generate_export_filename(work.title)

    # Create frontmatter
    frontmatter = create_frontmatter(work.title, work.authors, work.year)

    # Combine frontmatter and content
    full_content = frontmatter + '\n' + markdown_content

    # Get exports directory
    try:
        exports_dir = get_exports_dir()
    except Exception as e:
        logger.error(f"Failed to get exports directory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to access exports directory: {e}")

    # Write file
    export_path = exports_dir / filename
    try:
        export_path.write_text(full_content, encoding='utf-8')
        logger.info(f"Exported work {work_id} to {export_path}")
    except Exception as e:
        logger.error(f"Failed to write export file {export_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to write export file: {e}")

    return str(export_path)
