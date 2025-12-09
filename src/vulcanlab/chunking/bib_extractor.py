""" DEPRECATING

Extract bibliographic information and table of contents from markdown.

Uses lazy imports to avoid loading heavy AI dependencies until actually needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from vulcanlab.ai import LLMSettings, ModelTier

# Configurable setting for how many characters to extract from the beginning
EXTRACT_CHARS = 1000


class TOCEntry(BaseModel):
    """A single table of contents entry with heading level."""

    level: int  # 1 for H1, 2 for H2, 3 for H3, etc.
    title: str


class TableOfContents(BaseModel):
    """Table of contents extracted from the document."""

    entries: list[TOCEntry]


class BibliographicInfo(BaseModel):
    """Bibliographic metadata extracted from the document."""

    title: str | None = None
    authors: list[str] = []
    publication_date: str | None = None
    publisher: str | None = None
    isbn: str | None = None
    edition: str | None = None


class ExtractedMetadata(BaseModel):
    """Combined metadata extraction result."""

    bibliographic: BibliographicInfo
    toc: TableOfContents


def extract_metadata(
    markdown_text: str,
    chars: int | None = None,
    lines: int | None = None,
    settings: "LLMSettings | None" = None,
    tier: "ModelTier | None" = None,
) -> ExtractedMetadata:
    """
    Extract bibliographic info and table of contents from markdown text.

    Args:
        markdown_text: The full markdown text of the document
        chars: Number of characters to extract from the beginning (default: EXTRACT_CHARS)
        lines: Number of lines to extract from the beginning (overrides chars if specified)
        settings: Optional LLM settings, will create default if not provided
        tier: Model tier to use (LIGHT or FULL, default: LIGHT)

    Returns:
        ExtractedMetadata with bibliographic info and table of contents
    """
    # Lazy import - only load AI module when this function is called
    from vulcanlab.ai import create_langchain_chat, ModelTier as MT

    if tier is None:
        tier = MT.LIGHT

    # Determine text sample based on lines or chars
    if lines is not None:
        text_lines = markdown_text.split('\n')
        text_sample = '\n'.join(text_lines[:lines])
    else:
        if chars is None:
            chars = EXTRACT_CHARS
        text_sample = markdown_text[:chars]

    # Create LangChain chat model
    langchain_stack = create_langchain_chat(settings, tier=tier, search=False)
    chat = langchain_stack.chat

    # Create the prompt for extraction
    prompt = f"""Analyze the following text from the beginning of a document and extract:

1. Bibliographic information (title, authors, publication date, publisher, ISBN, edition)
2. Table of contents with heading levels

For the table of contents, identify headings and their hierarchy levels:
- H1 = level 1 (main chapters)
- H2 = level 2 (sections)
- H3 = level 3 (subsections)
- etc.

Return your response in this exact JSON format:
{{
    "bibliographic": {{
        "title": "string or null",
        "authors": ["list of author names"],
        "publication_date": "string or null",
        "publisher": "string or null",
        "isbn": "string or null",
        "edition": "string or null"
    }},
    "toc": {{
        "entries": [
            {{"level": 1, "title": "Chapter Title"}},
            {{"level": 2, "title": "Section Title"}},
            ...
        ]
    }}
}}

If information is not found, use null for strings and empty lists for arrays.

Text to analyze:
---
{text_sample}
---

Return only the JSON, no other text."""

    # Call the LLM
    response = chat.invoke(prompt)

    # Parse the response
    import json

    # Extract JSON from response
    response_text = response.content
    if isinstance(response_text, list):
        response_text = response_text[0] if response_text else ""

    # Handle case where content is already a dict
    if isinstance(response_text, dict):
        response_text = str(response_text)

    # Try to parse JSON from the response
    try:
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        data = json.loads(response_text.strip())

        # Build the result
        bib_data = data.get("bibliographic", {})
        toc_data = data.get("toc", {})

        bibliographic = BibliographicInfo(
            title=bib_data.get("title"),
            authors=bib_data.get("authors", []),
            publication_date=bib_data.get("publication_date"),
            publisher=bib_data.get("publisher"),
            isbn=bib_data.get("isbn"),
            edition=bib_data.get("edition"),
        )

        entries = [
            TOCEntry(level=e.get("level", 1), title=e.get("title", ""))
            for e in toc_data.get("entries", [])
        ]
        toc = TableOfContents(entries=entries)

        return ExtractedMetadata(bibliographic=bibliographic, toc=toc)

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        # Return empty result on parse failure
        return ExtractedMetadata(
            bibliographic=BibliographicInfo(),
            toc=TableOfContents(entries=[])
        )
