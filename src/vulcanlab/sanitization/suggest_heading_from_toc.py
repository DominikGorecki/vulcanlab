"""DEPRECATE
Suggest heading hierarchy changes based on TOC titles.

This module uses AI to match document headings with authoritative TOC titles
and suggest corrections for both heading levels and title text.

Uses lazy imports to avoid loading heavy AI dependencies until actually needed.

Usage:
    from vulcanlab.sanitization.suggest_heading_from_toc import suggest_heading_from_toc

    changes = suggest_heading_from_toc("book.titles.md", "book.toc_titles.md")
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

# Directory for LLM logs
LLM_LOGS_DIR = Path("logs")


def _log_llm_interaction(prompt: str, response_text: str, filename_prefix: str = "suggest_from_toc") -> None:
    """Log LLM prompt and response to a file."""
    LLM_LOGS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LLM_LOGS_DIR / f"{filename_prefix}_{timestamp}.md"

    log_content = f"""# LLM Interaction Log
**Timestamp:** {datetime.now().isoformat()}
**Type:** {filename_prefix}

## Prompt
```
{prompt}
```

## Response
```
{response_text}
```
"""
    log_file.write_text(log_content, encoding='utf-8')


def _extract_text_from_response(response_content) -> str:
    """Extract text string from various LLM response formats."""
    if isinstance(response_content, str):
        return response_content
    elif isinstance(response_content, list):
        if not response_content:
            return ""
        first_item = response_content[0]
        if isinstance(first_item, str):
            return first_item
        elif isinstance(first_item, dict):
            return first_item.get('text', str(first_item))
        else:
            return str(first_item)
    elif isinstance(response_content, dict):
        return response_content.get('text', json.dumps(response_content))
    else:
        return str(response_content)


def suggest_heading_from_toc(
    titles_file: str | Path,
    toc_titles_file: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    """
    Analyze document titles and suggest changes based on authoritative TOC titles.

    Args:
        titles_file: Path to a *.titles.md file (from extract_titles).
        toc_titles_file: Path to a *.toc_titles.md file (from pdf_bookmarks2toc).
        output_path: Optional output path. Default: <stem>.title_changes.md in output folder.

    Returns:
        Path to the created changes file.

    Raises:
        FileNotFoundError: If input files are not found.
    """
    titles_file = Path(titles_file)
    toc_titles_file = Path(toc_titles_file)

    if not titles_file.exists():
        raise FileNotFoundError(f"Titles file not found: {titles_file}")
    if not toc_titles_file.exists():
        raise FileNotFoundError(f"TOC titles file not found: {toc_titles_file}")

    # Parse the titles file
    titles_content = titles_file.read_text(encoding='utf-8')
    titles_lines = titles_content.splitlines()

    if not titles_lines:
        raise ValueError(f"Titles file is empty: {titles_file}")

    # First line is the relative URI to the original file
    relative_uri = titles_lines[0].strip()

    # Extract the titles codeblock
    codeblock_match = re.search(r'```\n(.*?)\n```', titles_content, re.DOTALL)
    if not codeblock_match:
        raise ValueError(f"No titles codeblock found in: {titles_file}")

    titles_codeblock = codeblock_match.group(1)

    # Parse the TOC titles file (markdown headings)
    toc_content = toc_titles_file.read_text(encoding='utf-8')
    toc_entries = []
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    for match in heading_pattern.finditer(toc_content):
        level = len(match.group(1))
        title = match.group(2).strip()
        toc_entries.append({"level": level, "title": title})

    # Build the LLM prompt
    prompt = _build_prompt(titles_codeblock, toc_entries)

    # Lazy import - only load AI module when LLM is needed
    from vulcanlab.ai import create_langchain_chat, ModelTier

    # Call LLM with FULL tier
    langchain_stack = create_langchain_chat(
        settings=None,
        tier=ModelTier.FULL,
        search=False,
        temperature=0.2
    )
    chat = langchain_stack.chat

    response = chat.invoke(prompt)
    response_text = _extract_text_from_response(response.content)

    # Log the interaction
    _log_llm_interaction(prompt, response_text)

    # Parse the LLM response
    changes = _parse_llm_response(response_text)

    # Build output content
    output_lines = [
        relative_uri,
        "",
        "# CHANGES TO HEADINGS",
        "```",
        *changes,
        "```"
    ]
    output_content = "\n".join(output_lines)

    # Determine output path
    if output_path is None:
        output_dir = Path.cwd() / "output"
        stem = titles_file.stem.replace('.titles', '')
        output_path = output_dir / f"{stem}.title_changes.md"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_content, encoding='utf-8')

    return output_path


def _build_prompt(titles_codeblock: str, toc_entries: list) -> str:
    """Build the prompt for the LLM."""

    # Format TOC entries for the prompt
    toc_text = ""
    if toc_entries:
        toc_lines = []
        for entry in toc_entries:
            level = entry.get('level', 1)
            title = entry.get('title', '')
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}H{level}: {title}")
        toc_text = "\n".join(toc_lines)
    else:
        toc_text = "No table of contents available"

    return f"""You are an expert at analyzing document structure and markdown formatting.

## Task
Match headings from a markdown document with the authoritative table of contents and suggest corrections for both heading levels and title text.

## Authoritative Table of Contents
These are the correct titles with their proper hierarchy levels. Use these as the source of truth for both the heading level AND the exact title text.
```
{toc_text}
```

## Current Headings in Document
Each line shows: [line_number]: [current_heading]
```
{titles_codeblock}
```

## Matching Rules
1. For each document heading, find the best matching TOC entry based on content similarity
2. The TOC entry determines BOTH the correct heading level (H1, H2, etc.) AND the correct title text
3. If a heading has no reasonable match in the TOC, mark it as REMOVE
4. Consider that document headings may have OCR errors, extra characters, or slight variations from the authoritative TOC

## Output Format
Return ONLY the changes in this exact format, one per line:
[line_number] : [ACTION] : [title_text]

Where:
- ACTION is one of: NO_CHANGE, REMOVE, H1, H2, H3, H4
- title_text is the correct title from the TOC (empty for REMOVE)
- NO_CHANGE means the heading level is correct, but still include the authoritative title text

Examples:
10 : NO_CHANGE : Introduction
13 : H1 : Chapter 1: Getting Started
18 : H2 : Overview of Methods
25 : REMOVE :

Provide changes for ALL headings shown above."""


def _parse_llm_response(response_text: str) -> list[str]:
    """Parse the LLM response to extract heading changes."""

    # Try to extract from a code block first if present
    codeblock_match = re.search(r'```(?:\w*\n)?(.*?)```', response_text, re.DOTALL)
    text_to_parse = codeblock_match.group(1) if codeblock_match else response_text

    # Parse line by line for more reliable extraction
    changes = []
    pattern = re.compile(r'^\s*(\d+)\s*:\s*(NO_CHANGE|REMOVE|H[1-4])\s*:\s*(.*)$')

    for line in text_to_parse.splitlines():
        match = pattern.match(line)
        if match:
            line_num = match.group(1)
            action = match.group(2)
            title = match.group(3).strip()
            changes.append(f"{line_num} : {action} : {title}")

    return changes
