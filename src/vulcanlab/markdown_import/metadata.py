"""
Metadata extraction from markdown files.

This module provides functions to extract YAML frontmatter metadata from
markdown files.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Metadata:
    """Metadata extracted from YAML frontmatter.

    Attributes:
        title: Work title (required)
        author: Author name(s), can be comma-separated (optional)
        year: Publication year as integer (optional)
    """
    title: str
    author: Optional[str] = None
    year: Optional[int] = None


@dataclass
class MarkdownFile:
    """Information about a markdown file in the input directory.

    Attributes:
        filename: Name of the file (e.g., "document.md")
        file_path: Full path to the file
        has_metadata: Whether YAML frontmatter was found and parsed
        metadata: Extracted metadata if available
    """
    filename: str
    file_path: str
    has_metadata: bool
    metadata: Optional[Metadata] = None


def extract_metadata(file_path: str) -> Optional[Metadata]:
    """Extract metadata from YAML frontmatter in a markdown file.

    Reads the file and parses YAML frontmatter between --- delimiters at the
    start of the file. Returns None if frontmatter is missing or invalid.

    Args:
        file_path: Path to the markdown file

    Returns:
        Metadata object if valid frontmatter found, None otherwise

    Examples:
        >>> extract_metadata("test.md")
        Metadata(title="Test Book", author="John Doe", year=2023)

        >>> extract_metadata("no-metadata.md")
        None
    """
    try:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return None

        content = path.read_text(encoding='utf-8')

        # Check if file starts with ---
        if not content.strip().startswith('---'):
            logger.debug(f"No YAML frontmatter found in {file_path}")
            return None

        # Split on --- to extract frontmatter
        parts = content.split('---', 2)

        # Need at least 3 parts: empty before first ---, frontmatter, content
        if len(parts) < 3:
            logger.debug(f"Invalid YAML frontmatter structure in {file_path}")
            return None

        frontmatter_text = parts[1].strip()

        if not frontmatter_text:
            logger.debug(f"Empty YAML frontmatter in {file_path}")
            return None

        # Parse YAML
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML frontmatter in {file_path}: {e}")
            return None

        if not isinstance(frontmatter, dict):
            logger.warning(f"YAML frontmatter is not a dictionary in {file_path}")
            return None

        # Extract required title field
        title = frontmatter.get('title')
        if not title:
            logger.debug(f"Missing 'title' field in frontmatter in {file_path}")
            return None

        if not isinstance(title, str):
            logger.warning(f"'title' field is not a string in {file_path}")
            return None

        # Extract optional fields
        author = frontmatter.get('author')
        if author is not None and not isinstance(author, str):
            logger.warning(f"'author' field is not a string in {file_path}, ignoring")
            author = None

        year = frontmatter.get('year')
        if year is not None:
            # Validate year is an integer
            if isinstance(year, int):
                # Basic sanity check for year range
                if year < 1000 or year > 9999:
                    logger.warning(f"Year {year} out of valid range in {file_path}, ignoring")
                    year = None
            else:
                logger.warning(f"'year' field is not an integer in {file_path}, ignoring")
                year = None

        logger.debug(f"Extracted metadata from {file_path}: title='{title}', author='{author}', year={year}")

        return Metadata(title=title, author=author, year=year)

    except Exception as e:
        logger.error(f"Unexpected error extracting metadata from {file_path}: {e}")
        return None


def strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from markdown content.

    If the content starts with ---, removes everything up to and including
    the closing ---. Otherwise returns content unchanged.

    Args:
        content: Markdown content that may contain frontmatter

    Returns:
        Content with frontmatter removed, leading/trailing whitespace stripped
    """
    content = content.strip()

    if not content.startswith('---'):
        return content

    # Split on ---
    parts = content.split('---', 2)

    # If we have at least 3 parts, return the content after the second ---
    if len(parts) >= 3:
        return parts[2].strip()

    # Otherwise return original content
    return content
