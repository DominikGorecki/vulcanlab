"""LLM-based full document processing for bibliography, TOC, and sanitization.

This module uses an LLM to process entire markdown documents and extract
bibliographic information, generate proper heading hierarchy, and create
a table of contents.

Uses lazy imports to avoid loading heavy AI dependencies until actually needed.

Usage:
    from vulcanlab.chunking.llm_processor import process_with_llm
    result = process_with_llm("path/to/document.md")

Examples:
    # Basic usage
    result = process_with_llm("book.md")

    # Force processing large files
    result = process_with_llm("large_book.md", force=True)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

from vulcanlab.data.database import SessionLocal

if TYPE_CHECKING:
    from vulcanlab.ai import LLMSettings, ModelTier
from vulcanlab.data.models import Work
from vulcanlab.utils import compute_file_hash, set_file_readonly


# Maximum lines before requiring force flag
MAX_LINES_DEFAULT = 2000

# Output directory for sanitized files
OUTPUT_DIR = Path("output")


class TOCEntry(BaseModel):
    """A single table of contents entry with heading level."""
    level: int
    title: str


class BibliographicInfo(BaseModel):
    """Bibliographic metadata extracted from the document."""
    title: str | None = None
    authors: list[str] = []
    year: int | None = None
    publisher: str | None = None
    isbn: str | None = None
    doi: str | None = None


class LLMProcessResult(BaseModel):
    """Result from LLM document processing."""
    bibliographic: BibliographicInfo
    sanitized_markdown: str
    toc: list[TOCEntry]


def _build_prompt(markdown_content: str) -> str:
    """Build the LLM prompt for document processing."""
    return f"""You are an expert at analyzing academic documents and extracting metadata.

## Task
Analyze the following markdown document and:
1. Extract bibliographic information
2. Rewrite the document with proper heading hierarchy
3. Generate a table of contents based on the headings

## Heading Hierarchy Rules
- **H1 (#)**: Document title (only once, at the beginning)
- **H1 (#)**: Top-level chapters or major sections
- **H2 (##)**: Sections within chapters
- **H3 (###)**: Subsections within sections

## Important Instructions
- Preserve ALL content from the original document
- Only modify the heading levels (# symbols)
- Do not add or remove any text content
- Do not change formatting other than heading levels

## Output Format
Return your response as valid JSON with this exact structure:
```json
{{
    "bibliographic": {{
        "title": "Document title or null",
        "authors": ["Author 1", "Author 2"],
        "year": 2024,
        "publisher": "Publisher name or null",
        "isbn": "ISBN or null",
        "doi": "DOI or null"
    }},
    "sanitized_markdown": "The complete rewritten markdown with corrected heading hierarchy",
    "toc": [
        {{"level": 1, "title": "Chapter Title"}},
        {{"level": 2, "title": "Section Title"}},
        {{"level": 3, "title": "Subsection Title"}}
    ]
}}
```

## Document to Process
---
{markdown_content}
---

Return only the JSON response, no additional text."""


def process_with_llm(
    input_file: str | Path,
    force: bool = False,
    verbose: bool = False,
    settings: "LLMSettings | None" = None,
    tier: "ModelTier | None" = None,
) -> LLMProcessResult:
    """
    Process a markdown document using LLM for bibliography, TOC, and sanitization.

    Args:
        input_file: Path to the input markdown file.
        force: If True, process files larger than MAX_LINES_DEFAULT.
        verbose: If True, print progress information.
        settings: Optional LLM settings.
        tier: Model tier to use (default FULL for better quality).

    Returns:
        LLMProcessResult with bibliographic info, sanitized markdown, and TOC.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is too large and force is not set.
    """
    input_path = Path(input_file).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if input_path.suffix.lower() not in ('.md', '.markdown'):
        raise ValueError(f"Input file must be a markdown file: {input_path}")

    # Read the file and check line count
    content = input_path.read_text(encoding='utf-8')
    lines = content.splitlines()
    line_count = len(lines)

    if verbose:
        print(f"Processing: {input_path}")
        print(f"Line count: {line_count}")

    if line_count > MAX_LINES_DEFAULT and not force:
        raise ValueError(
            f"File has {line_count} lines, exceeding the {MAX_LINES_DEFAULT} line limit. "
            f"Use --force flag to process large files."
        )

    # Build prompt and call LLM
    if verbose:
        print("Sending document to LLM...")

    prompt = _build_prompt(content)

    # Lazy import - only load AI module when LLM is needed
    from vulcanlab.ai import create_langchain_chat, ModelTier as MT

    if tier is None:
        tier = MT.FULL

    langchain_stack = create_langchain_chat(
        settings=settings,
        tier=tier,
        search=False,
        temperature=0.2
    )
    chat = langchain_stack.chat

    response = chat.invoke(prompt)

    # Parse response
    response_text = response.content
    if isinstance(response_text, list):
        response_text = response_text[0] if response_text else ""
    if isinstance(response_text, dict):
        response_text = json.dumps(response_text)

    # Extract JSON from response
    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        data = json.loads(response_text.strip())

        # Build result
        bib_data = data.get("bibliographic", {})
        bibliographic = BibliographicInfo(
            title=bib_data.get("title"),
            authors=bib_data.get("authors", []),
            year=bib_data.get("year"),
            publisher=bib_data.get("publisher"),
            isbn=bib_data.get("isbn"),
            doi=bib_data.get("doi"),
        )

        sanitized_markdown = data.get("sanitized_markdown", content)

        toc_data = data.get("toc", [])
        toc = [
            TOCEntry(level=e.get("level", 1), title=e.get("title", ""))
            for e in toc_data
        ]

        result = LLMProcessResult(
            bibliographic=bibliographic,
            sanitized_markdown=sanitized_markdown,
            toc=toc
        )

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        if verbose:
            print(f"Warning: Failed to parse LLM response: {e}")
        # Return minimal result with original content
        result = LLMProcessResult(
            bibliographic=BibliographicInfo(),
            sanitized_markdown=content,
            toc=[]
        )

    # Save sanitized file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sanitized_path = OUTPUT_DIR / f"{input_path.stem}.sanitized.md"
    sanitized_path.write_text(result.sanitized_markdown, encoding='utf-8')

    # Compute hash of sanitized file
    sanitized_hash = compute_file_hash(sanitized_path)

    # Set file as read-only to prevent accidental modifications
    set_file_readonly(sanitized_path)

    if verbose:
        print(f"Sanitized file saved to: {sanitized_path}")
        print(f"Set file as read-only: {sanitized_path}")

    # Create database entry
    toc_json = [{"level": e.level, "title": e.title} for e in result.toc]

    work = Work(
        title=result.bibliographic.title or input_path.stem,
        authors=", ".join(result.bibliographic.authors) if result.bibliographic.authors else None,
        year=result.bibliographic.year,
        publisher=result.bibliographic.publisher,
        isbn=result.bibliographic.isbn,
        doi=result.bibliographic.doi,
        markdown_path=str(sanitized_path.resolve()),
        toc=toc_json,
        content_hash=sanitized_hash,
    )

    with SessionLocal() as session:
        session.add(work)
        session.commit()
        work_id = work.id

    if verbose:
        print(f"Created database entry: id={work_id}")
        print(f"Title: {work.title}")
        print(f"Authors: {work.authors or 'N/A'}")
        print(f"Year: {work.year or 'N/A'}")
        print(f"TOC entries: {len(toc_json)}")

    return result
