"""
Extract table of contents from markdown files.

This module provides functionality to extract table of contents
with heading hierarchy from markdown documents using LLM.

Uses lazy imports to avoid loading heavy AI dependencies until actually needed.

Example (as library):
    from vulcanlab.sanitization.extract_toc import extract_table_of_contents

    # Extract TOC
    toc = extract_table_of_contents("document.md")
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from vulcanlab.ai import LLMSettings, ModelTier

# Default number of characters to extract
EXTRACT_CHARS = 1000


class TOCEntry(BaseModel):
    """A single table of contents entry with heading level."""

    level: int  # 1 for H1, 2 for H2, 3 for H3, etc.
    title: str


class TableOfContents(BaseModel):
    """Table of contents extracted from the document."""

    entries: list[TOCEntry]


def extract_table_of_contents(
    markdown_path: str | Path,
    chars: int | None = None,
    lines: int | None = None,
    settings: "LLMSettings | None" = None,
    tier: "ModelTier | None" = None,
) -> TableOfContents:
    """
    Extract table of contents from a markdown file.

    Args:
        markdown_path: Path to the markdown file.
        chars: Number of characters to extract from the beginning (default: EXTRACT_CHARS).
        lines: Number of lines to extract from the beginning (overrides chars if specified).
        settings: Optional LLM settings, will create default if not provided.
        tier: Model tier to use (LIGHT or FULL).

    Returns:
        TableOfContents with extracted entries.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a markdown file.
    """
    markdown_path = Path(markdown_path)

    if not markdown_path.exists():
        raise FileNotFoundError(f"File not found: {markdown_path}")

    if markdown_path.suffix.lower() != ".md":
        raise ValueError(f"Expected Markdown file (.md), got: {markdown_path.suffix}")

    markdown_text = markdown_path.read_text(encoding="utf-8")

    # Determine text sample based on lines or chars
    if lines is not None:
        text_lines = markdown_text.split('\n')
        text_sample = '\n'.join(text_lines[:lines])
    else:
        if chars is None:
            chars = EXTRACT_CHARS
        text_sample = markdown_text[:chars]

    # Lazy import - only load AI module when LLM is needed
    from vulcanlab.ai import create_langchain_chat, ModelTier as MT

    if tier is None:
        tier = MT.LIGHT

    # Create LangChain chat model
    langchain_stack = create_langchain_chat(settings, tier=tier, search=False)
    chat = langchain_stack.chat

    # Create the prompt for extraction
    prompt = f"""Analyze the following text from the beginning of a document and extract the table of contents with heading levels.

For the table of contents, identify headings and their hierarchy levels:
- H1 = level 1 (main chapters)
- H2 = level 2 (sections)
- H3 = level 3 (subsections)
- etc.

Return your response in this exact JSON format:
{{
    "entries": [
        {{"level": 1, "title": "Chapter Title"}},
        {{"level": 2, "title": "Section Title"}},
        ...
    ]
}}

Text to analyze:
---
{text_sample}
---

Return only the JSON, no other text."""

    # Call the LLM
    response = chat.invoke(prompt)

    # Parse the response
    import json

    response_text = response.content
    if isinstance(response_text, list):
        response_text = response_text[0] if response_text else ""

    if isinstance(response_text, dict):
        response_text = str(response_text)

    try:
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        data = json.loads(response_text.strip())

        entries = [
            TOCEntry(level=e.get("level", 1), title=e.get("title", ""))
            for e in data.get("entries", [])
        ]

        return TableOfContents(entries=entries)

    except (json.JSONDecodeError, KeyError, TypeError):
        return TableOfContents(entries=[])
