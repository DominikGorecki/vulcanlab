"""
Convert TOC titles markdown file to structured table of contents.

This module parses a markdown file with hierarchical headings (H1, H2, etc.)
and converts it to a structured TOC format.

Example (as library):
    from vulcanlab.sanitization.toc_titles2toc import parse_toc_titles

    # Parse TOC from markdown headings
    toc = parse_toc_titles("document_toc_titles.md")
"""

import re
from pathlib import Path

from pydantic import BaseModel


class TOCEntry(BaseModel):
    """A single table of contents entry with heading level."""

    level: int  # 1 for H1, 2 for H2, 3 for H3, etc.
    title: str


class TableOfContents(BaseModel):
    """Table of contents extracted from the document."""

    entries: list[TOCEntry]


def parse_toc_titles(
    markdown_path: str | Path,
) -> TableOfContents:
    """
    Parse a markdown file with headings into a structured TOC.

    Args:
        markdown_path: Path to the markdown file with TOC headings.

    Returns:
        TableOfContents with parsed entries.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a markdown file.
    """
    markdown_path = Path(markdown_path)

    if not markdown_path.exists():
        raise FileNotFoundError(f"File not found: {markdown_path}")

    if markdown_path.suffix.lower() != ".md":
        raise ValueError(f"Expected Markdown file (.md), got: {markdown_path.suffix}")

    content = markdown_path.read_text(encoding="utf-8")

    # Parse markdown headings
    entries = []
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    for match in heading_pattern.finditer(content):
        level = len(match.group(1))
        title = match.group(2).strip()
        entries.append(TOCEntry(level=level, title=title))

    return TableOfContents(entries=entries)
