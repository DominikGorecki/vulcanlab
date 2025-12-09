"""Suggest heading hierarchy changes for markdown documents.

This module uses AI to analyze markdown headings and suggest corrections
based on the table of contents stored in the database.

Uses lazy imports to avoid loading heavy AI dependencies until actually needed.

Usage:
    from vulcanlab.sanitization import suggest_heading_changes
    output_path = suggest_heading_changes("path/to/document.titles.md")

Examples:
    # Basic usage - creates document.title_changes.md
    from vulcanlab.sanitization import suggest_heading_changes
    result = suggest_heading_changes("book.titles.md")

Functions:
    suggest_heading_changes(titles_file) - Analyze titles and suggest hierarchy changes
    suggest_heading_changes_from_work(work_id, source_key, use_full_model, force, verbose) - Analyze from Work by ID
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from vulcanlab.data.database import SessionLocal, get_session
from vulcanlab.data.models import Work
from vulcanlab.data.template_loader import load_template
from vulcanlab.utils import compute_file_hash
from vulcanlab.utils.file_utils import set_file_writable, set_file_readonly
from .extract_titles import HashMismatchError

# Directory for LLM logs
LLM_LOGS_DIR = Path("logs")


def _log_llm_interaction(prompt: str, response_text: str, filename_prefix: str = "suggest_heading") -> None:
    """Log LLM prompt and response to a file.

    Args:
        prompt: The prompt sent to the LLM.
        response_text: The response received from the LLM.
        filename_prefix: Prefix for the log filename.
    """
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
    """Extract text string from various LLM response formats.

    Args:
        response_content: The content from the LLM response (str, list, or dict).

    Returns:
        The extracted text as a string.
    """
    if isinstance(response_content, str):
        return response_content
    elif isinstance(response_content, list):
        # Handle list of content blocks
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
        # Handle dict response (e.g., from Gemini)
        return response_content.get('text', json.dumps(response_content))
    else:
        return str(response_content)


def suggest_heading_changes(titles_file: str | Path) -> Path:
    """Analyze titles and suggest heading hierarchy changes using AI.

    Args:
        titles_file: Path to a *.titles.md file created by extract_titles_to_file.

    Returns:
        Path to the created changes file (*.title_changes.md).

    Raises:
        FileNotFoundError: If the titles file or original document is not found.
        ValueError: If the document is not found in the database.
    """
    titles_file = Path(titles_file)

    if not titles_file.exists():
        raise FileNotFoundError(f"Titles file not found: {titles_file}")

    # Parse the titles file
    content = titles_file.read_text(encoding='utf-8')
    lines = content.splitlines()

    if not lines:
        raise ValueError(f"Titles file is empty: {titles_file}")

    # First line is the relative URI to the original file
    relative_uri = lines[0].strip()

    # Resolve the original file path
    if relative_uri.startswith('./'):
        relative_uri = relative_uri[2:]
    original_path = (titles_file.parent / relative_uri).resolve()

    if not original_path.exists():
        raise FileNotFoundError(f"Original document not found: {original_path}")

    # Extract the titles codeblock
    codeblock_match = re.search(r'```\n(.*?)\n```', content, re.DOTALL)
    if not codeblock_match:
        raise ValueError(f"No titles codeblock found in: {titles_file}")

    titles_codeblock = codeblock_match.group(1)

    # Generate SHA256 hash of the original document
    content_hash = compute_file_hash(original_path)

    # Look up the document in the database
    with SessionLocal() as session:
        work = session.query(Work).filter(Work.content_hash == content_hash).first()

        if not work:
            raise ValueError(
                f"Document not found in database. Hash: {content_hash}\n"
                f"File: {original_path}"
            )

        # Extract metadata
        toc = work.toc or []
        title = work.title or "Unknown Title"
        authors = work.authors or "Unknown Author"

    # Build the LLM prompt
    prompt = _build_prompt(title, authors, toc, titles_codeblock)

    # Lazy import - only load AI module when LLM is needed
    from vulcanlab.ai import create_langchain_chat, ModelTier

    # Call LLM with web search enabled
    langchain_stack = create_langchain_chat(
        settings=None,
        tier=ModelTier.LIGHT,
        search=True,
        temperature=0.2
    )
    chat = langchain_stack.chat

    response = chat.invoke(prompt)
    response_text = _extract_text_from_response(response.content)

    # Log the interaction
    _log_llm_interaction(prompt, response_text)

    # Parse the LLM response to extract changes
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

    # Save to output file - use output folder
    output_dir = Path.cwd() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = titles_file.stem.replace('.titles', '')
    output_path = output_dir / f"{stem}.title_changes.md"
    output_path.write_text(output_content, encoding='utf-8')

    return output_path


def _build_prompt(title: str, authors: str, toc: list, titles_codeblock: str) -> str:
    """Build the prompt for the LLM.

    This function creates the prompt for the LLM to analyze document headings
    and suggest hierarchy corrections.

    The prompt template is loaded from the database if available,
    otherwise falls back to the hardcoded default.

    Args:
        title: Document title
        authors: Document authors
        toc: Table of contents as list of dicts
        titles_codeblock: The titles content from extracted file

    Returns:
        Formatted prompt string
    """

    # Format ToC for the prompt
    toc_text = ""
    if toc:
        toc_lines = []
        for item in toc:
            level = item.get('level', 1)
            item_title = item.get('title', '')
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}Level {level}: {item_title}")
        toc_text = "\n".join(toc_lines)
    else:
        toc_text = "No table of contents available"

    # Define fallback template builder
    def get_fallback_template():
        return """You are an expert at analyzing document structure and markdown formatting.

## Task
Analyze the headings from a markdown document and assign the correct heading levels so that:
- The overall structure is consistent with the document's table of contents (ToC)
- The hierarchy is as informative as possible for chunking and context
- No meaningful heading information from the current document is lost

## Document Information
- **Title:** {title}
- **Author(s):** {authors}

## Table of Contents from Database (authoritative high-level structure)
Use this ToC as the primary guide for:
- Overall ordering of sections
- Canonical wording of titles when possible
- The *relative* depth of major parts/chapters/sections

{toc_text}

## Current Headings in Document
Each line shows: [line_number]: [current_heading]
```

{titles_codeblock}

```

## Heading Hierarchy Rules
Treat markdown heading levels as a strict outline hierarchy:

- **H1 (#)**: Main parts, chapters, or major top-level sections  
  - Usually mapped from top-level ToC entries
- **H2 (##)**: Sections within a part/chapter
- **H3 (###)**: Subsections
- **H4 (####)**: Sub-subsections (use for additional nesting; do not go deeper than H4)
- **REMOVE**: Only for non-semantic items that clearly are *not* headings  
  (e.g., page numbers, running headers/footers, repeated book title on every page, copyright notices)
- **NO_CHANGE**: Heading level is already correct, but you may still normalize the title text

The hierarchy must be *nested and consistent*:
- Do not jump levels in a way that breaks outline logic (avoid H1 → H4 with no H2/H3 in between unless structure clearly demands it)
- Preserve the reading order of the original headings; do not reorder anything

## ToC vs Current Headings (VERY IMPORTANT)
The ToC from the database may be *shallower* (fewer levels) than the actual document headings. Handle this as follows:

1. **ToC as anchor, headings add detail**
   - Use the ToC to determine:
     - Which headings are major (H1) vs subordinate (H2–H4)
     - The canonical wording of titles where there is a clear match
   - Use the current headings to *refine and deepen* the structure under those ToC entries.

2. **Do NOT discard real structure just because ToC is shallow**
   - If the ToC only has chapter-level entries but the document headings clearly contain sections/subsections:
     - Map the chapter to **H1**
     - Map its internal headings to **H2/H3/H4** while preserving their relative nesting.
   - Do **not** REMOVE a heading solely because it is missing in the ToC.

3. **Relative hierarchy preservation**
   - When aligning to the ToC, preserve the *relative* nesting of headings:
     - Example rule: if for a group of headings the original levels are (H2, H3, H4) and you determine that the first one should actually be H1 (because it matches a top-level ToC entry), then the group should become (H1, H2, H3).
   - More generally:
     - If you “promote” or “demote” one heading to align with the ToC, apply the same offset to its direct descendants so that the internal structure under it stays the same.

4. **Matching titles**
   - If a heading clearly corresponds to a ToC entry:
     - Use the ToC title text as the authoritative `title_text` (fixing capitalization, punctuation, numbering if needed).
   - If there is no clear ToC match:
     - Keep the best, cleaned-up version of the current heading text as `title_text`, and assign a level (H1–H4) based on context.

5. **Special sections**
   - Common structural sections like “Foreword”, “Preface”, “Introduction”, “Conclusion”, “Appendix”, “References”, “Bibliography”, “Glossary”, “Index” should usually be kept as headings (often H1 or H2) unless they are clearly decorative repetitions.

## Instructions
1. Use your knowledge of this work (if you recognize it) to understand its typical structure.
2. If helpful, search the web for information about this specific work's structure (e.g., canonical chapter layout).
3. Compare the ToC from the database with the current headings:
   - Use text similarity, numbering patterns (e.g., “1.”, “1.1”), and ordering to align them.
4. For **each line number** in the headings list:
   - Decide whether to assign H1, H2, H3, H4, NO_CHANGE, or REMOVE.
   - When in doubt between flattening or preserving additional structure, prefer preserving a *richer* and *consistent* hierarchy (i.e., more granularity, not less).
5. Do **not** suggest removing lower-level headings that are missing from the ToC. Instead:
   - Keep them, assign the best-fitting level (H2–H4), and maintain their relative position and nesting under the closest higher-level ToC-aligned parent.

## Output Format
Return **only** the mapping in the following format, one line **per heading line**:

[line_number] : [ACTION] : [title_text]

Where:
- `ACTION` is one of: `NO_CHANGE`, `REMOVE`, `H1`, `H2`, `H3`, `H4`
- `title_text` is:
  - The canonical title from the ToC, when there is a clear match, or
  - A cleaned-up version of the current heading text, when there is no ToC match
  - Empty only for `REMOVE`

Notes:
- Even for `NO_CHANGE`, still provide the authoritative `title_text` (which may normalize spacing/capitalization/numbering).
- Do **not** output anything other than these lines.

### Example
10 : NO_CHANGE : Introduction  
13 : H1 : Chapter 1: Getting Started  
18 : H1 : Methods  
19 : H2 : Data Collection  
20 : H3 : Survey Design  
25 : REMOVE :

Provide the complete list of mappings for **all** headings shown above."""

    # Load template from database with fallback
    template = load_template("heading_hierarchy", get_fallback_template)

    # Format template with variables
    return template.format(
        title=title,
        authors=authors,
        toc_text=toc_text,
        titles_codeblock=titles_codeblock
    )


# Old commented-out code removed
def _build_prompt_old(title: str, authors: str, toc: list, titles_codeblock: str) -> str:
    """Old version - kept for reference."""
    return f"""You are an expert at analyzing document structure and markdown formatting.

# ## Task
# Analyze the headings from a markdown document and suggest the correct heading levels based on the document's table of contents and proper hierarchical structure.

# ## Document Information
# - **Title:** {title}
# - **Author(s):** {authors}

# ## Table of Contents from Database
# {toc_text}

# ## Current Headings in Document
# Each line shows: [line_number]: [current_heading]
# ```
# {titles_codeblock}
# ```

# ## Heading Hierarchy Rules
# - **H1 (#)**: Main chapters or major sections (from ToC top-level items)
# - **H2 (##)**: Sections within chapters
# - **H3 (###)**: Subsections
# - **H4 (####)**: Sub-subsections
# - **REMOVE**: Items that should not be headings (e.g., decorative text, page numbers, running headers)
# - **NO_CHANGE**: Headings that are already correct

# ## Instructions
# 1. Use your knowledge of this work (if you recognize it) to understand its proper structure
# 2. Search the web for information about this work's structure if helpful
# 3. Compare the ToC from the database with the current headings
# 4. For each line number in the headings, determine the correct action
# 5. Don't suggest that any missing lower-level headings in the ToC to be removed from current headings just make sure they keep their relative hierarchy:
#     * If for a section H2,H3,H4, the titles matches to H1,H2 respectively then the result should be H1,H2,H3

# ## Output Format
# Return ONLY the changes in this exact format, one per line:
# [line_number] : [ACTION] : [title_text]

# Where:
# - ACTION is one of: NO_CHANGE, REMOVE, H1, H2, H3, H4
# - title_text is the correct title from the ToC (empty for REMOVE)
# - NO_CHANGE means the heading level is correct, but still include the authoritative title text

# Example:
# 10 : NO_CHANGE : Introduction
# 13 : H1 : Chapter 1: Getting Started
# 18 : H1 : Methods
# 19 : H2 : Data Collection
# 20 : H3 : Survey Design
# 25 : REMOVE :

# Provide the complete list of changes for ALL headings shown above."""


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


def build_prompt_for_work(
    work_id: int,
    source_key: str = "original_markdown",
    force: bool = False
) -> dict:
    """Build LLM prompt for suggesting heading changes without executing it.
    
    This function prepares the prompt that would be sent to the LLM, allowing
    manual execution or inspection before running.
    
    Args:
        work_id: Database ID of the work.
        source_key: Key in the files JSON ("original_markdown" or "sanitized").
        force: If True, skip hash validation and proceed anyway.
    
    Returns:
        Dict with keys:
            - prompt: The LLM prompt text
            - work_title: Title of the work
            - work_authors: Authors of the work
    
    Raises:
        ValueError: If work_id not found, source_key invalid, or files not in database.
        HashMismatchError: If file hashes don't match stored hashes (unless force=True).
        FileNotFoundError: If files referenced in database don't exist on disk.
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise ValueError(f"Work with ID {work_id} not found in database")
        
        if not work.files:
            raise ValueError(f"Work {work_id} has no files metadata")
        
        # Validate source_key
        if source_key not in ["original_markdown", "sanitized"]:
            raise ValueError(
                f"Invalid source_key: {source_key}. "
                f"Must be 'original_markdown' or 'sanitized'"
            )
        
        # Determine titles key based on source
        if source_key == "original_markdown":
            titles_key = "titles"
        else:  # sanitized
            titles_key = "sanitized_titles"
        
        # Validate both files exist in metadata
        if source_key not in work.files:
            raise ValueError(
                f"Work {work_id} does not have '{source_key}' in files metadata"
            )
        
        if titles_key not in work.files:
            raise ValueError(
                f"Work {work_id} does not have '{titles_key}' in files metadata. "
                f"Run extract_titles_from_work first."
            )
        
        # Get file info
        markdown_info = work.files[source_key]
        markdown_path = Path(markdown_info["path"])
        markdown_stored_hash = markdown_info["hash"]
        
        titles_info = work.files[titles_key]
        titles_path = Path(titles_info["path"])
        titles_stored_hash = titles_info["hash"]
        
        # Validate both files exist on disk
        if not markdown_path.exists():
            raise FileNotFoundError(
                f"Markdown file not found on disk: {markdown_path}\n"
                f"Referenced in work {work_id}, key '{source_key}'"
            )
        
        if not titles_path.exists():
            raise FileNotFoundError(
                f"Titles file not found on disk: {titles_path}\n"
                f"Referenced in work {work_id}, key '{titles_key}'"
            )
        
        # Compute current hashes and validate
        markdown_current_hash = compute_file_hash(markdown_path)
        titles_current_hash = compute_file_hash(titles_path)
        
        markdown_mismatch = markdown_current_hash != markdown_stored_hash
        titles_mismatch = titles_current_hash != titles_stored_hash
        
        if (markdown_mismatch or titles_mismatch) and not force:
            errors = []
            if markdown_mismatch:
                errors.append(
                    f"Markdown file ({source_key}):\n"
                    f"  Stored:  {markdown_stored_hash}\n"
                    f"  Current: {markdown_current_hash}"
                )
            if titles_mismatch:
                errors.append(
                    f"Titles file ({titles_key}):\n"
                    f"  Stored:  {titles_stored_hash}\n"
                    f"  Current: {titles_current_hash}"
                )
            error_msg = "File hash mismatch detected:\n" + "\n".join(errors)
            raise HashMismatchError(
                stored_hash=f"{markdown_stored_hash[:16]}... / {titles_stored_hash[:16]}...",
                current_hash=f"{markdown_current_hash[:16]}... / {titles_current_hash[:16]}..."
            )
        
        # Read titles file content
        titles_content = titles_path.read_text(encoding='utf-8')
        
        # Extract the titles codeblock
        codeblock_match = re.search(r'```\n(.*?)\n```', titles_content, re.DOTALL)
        if not codeblock_match:
            raise ValueError(f"No titles codeblock found in: {titles_path}")
        
        titles_codeblock = codeblock_match.group(1)
        
        # Get metadata from work
        title = work.title or "Unknown Title"
        authors = work.authors or "Unknown Author"
        toc = work.toc or []
        
        # Build the LLM prompt
        prompt = _build_prompt(title, authors, toc, titles_codeblock)
        
        return {
            "prompt": prompt,
            "work_title": title,
            "work_authors": authors
        }


def save_title_changes_from_response(
    work_id: int,
    source_key: str,
    llm_response: str,
    force: bool = False
) -> Path:
    """Save title changes from a manual LLM response.
    
    Takes the raw response from an LLM and processes it to create a title_changes file,
    updating the database with the new file metadata.
    
    Args:
        work_id: Database ID of the work.
        source_key: Key in the files JSON ("original_markdown" or "sanitized").
        llm_response: Raw text response from the LLM.
        force: If True, skip validation and overwrite existing files.
    
    Returns:
        Path to the created title_changes file.
    
    Raises:
        ValueError: If work_id not found, source_key invalid, or files not in database.
        FileNotFoundError: If the markdown file doesn't exist.
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise ValueError(f"Work with ID {work_id} not found in database")
        
        if not work.files:
            raise ValueError(f"Work {work_id} has no files metadata")
        
        # Validate source_key
        if source_key not in ["original_markdown", "sanitized"]:
            raise ValueError(
                f"Invalid source_key: {source_key}. "
                f"Must be 'original_markdown' or 'sanitized'"
            )
        
        # Get markdown file path to determine output path
        if source_key not in work.files:
            raise ValueError(
                f"Work {work_id} does not have '{source_key}' in files metadata"
            )
        
        markdown_info = work.files[source_key]
        markdown_path = Path(markdown_info["path"])
        
        if not markdown_path.exists():
            raise FileNotFoundError(
                f"Markdown file not found on disk: {markdown_path}"
            )
        
        # Parse the LLM response to extract changes
        changes = _parse_llm_response(llm_response)
        
        # Calculate relative path from markdown
        try:
            relative_uri = markdown_path.relative_to(markdown_path.parent)
            relative_uri_str = f"./{relative_uri.as_posix()}"
        except ValueError:
            relative_uri_str = markdown_path.as_posix()
        
        # Build output content
        output_lines = [
            relative_uri_str,
            "",
            "# CHANGES TO HEADINGS",
            "```",
            *changes,
            "```"
        ]
        output_content = "\n".join(output_lines)
        
        # Determine output path based on source
        if source_key == "original_markdown":
            output_path = markdown_path.parent / f"{markdown_path.stem}.title_changes.md"
            output_key = "title_changes"
        else:  # sanitized
            output_path = markdown_path.parent / f"{markdown_path.stem}.title_changes.md"
            output_key = "sanitized_title_changes"
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # If file exists and is read-only, make it writable
        if output_path.exists():
            try:
                set_file_writable(output_path)
            except Exception:
                pass  # Ignore errors, will fail on write if needed
        
        # Write output file
        output_path.write_text(output_content, encoding='utf-8')
        
        # Set file to read-only
        set_file_readonly(output_path)
        
        # Compute hash of new file
        output_hash = compute_file_hash(output_path)
        
        # Update work's files metadata
        updated_files = dict(work.files) if work.files else {}
        updated_files[output_key] = {
            "path": str(output_path.resolve()),
            "hash": output_hash
        }
        work.files = updated_files
        
        session.commit()
        session.refresh(work)
    
    return output_path


def suggest_heading_changes_from_work(
    work_id: int,
    source_key: str,
    use_full_model: bool = False,
    force: bool = False,
    verbose: bool = False
) -> Path:
    """Suggest heading changes for a work's markdown file using AI and update the database.

    Args:
        work_id: Database ID of the work.
        source_key: Key in the files JSON ("original_markdown" or "sanitized").
        use_full_model: If True, use ModelTier.FULL instead of ModelTier.LIGHT.
        force: If True, skip hash validation and proceed anyway.
        verbose: If True, print progress messages.

    Returns:
        Path to the created title_changes file.

    Raises:
        ValueError: If work_id not found, source_key invalid, or files not in database.
        HashMismatchError: If file hashes don't match stored hashes (unless force=True).
        FileNotFoundError: If files referenced in database don't exist on disk.
    """
    # Load work from database
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise ValueError(f"Work with ID {work_id} not found in database")

        if not work.files:
            raise ValueError(f"Work {work_id} has no files metadata")

        # Validate source_key
        if source_key not in ["original_markdown", "sanitized"]:
            raise ValueError(
                f"Invalid source_key: {source_key}. "
                f"Must be 'original_markdown' or 'sanitized'"
            )

        # Determine titles key based on source
        if source_key == "original_markdown":
            titles_key = "titles"
            output_key = "title_changes"
        else:  # sanitized
            titles_key = "sanitized_titles"
            output_key = "sanitized_title_changes"

        # Validate both files exist in metadata
        if source_key not in work.files:
            raise ValueError(
                f"Work {work_id} does not have '{source_key}' in files metadata"
            )

        if titles_key not in work.files:
            raise ValueError(
                f"Work {work_id} does not have '{titles_key}' in files metadata. "
                f"Run extract_titles_from_work first."
            )

        # Get file info
        markdown_info = work.files[source_key]
        markdown_path = Path(markdown_info["path"])
        markdown_stored_hash = markdown_info["hash"]

        titles_info = work.files[titles_key]
        titles_path = Path(titles_info["path"])
        titles_stored_hash = titles_info["hash"]

        if verbose:
            print(f"Analyzing markdown: {markdown_path}")
            print(f"Using titles from: {titles_path}")

        # Validate both files exist on disk
        if not markdown_path.exists():
            raise FileNotFoundError(
                f"Markdown file not found on disk: {markdown_path}\n"
                f"Referenced in work {work_id}, key '{source_key}'"
            )

        if not titles_path.exists():
            raise FileNotFoundError(
                f"Titles file not found on disk: {titles_path}\n"
                f"Referenced in work {work_id}, key '{titles_key}'"
            )

        # Compute current hashes and validate
        markdown_current_hash = compute_file_hash(markdown_path)
        titles_current_hash = compute_file_hash(titles_path)

        markdown_mismatch = markdown_current_hash != markdown_stored_hash
        titles_mismatch = titles_current_hash != titles_stored_hash

        if (markdown_mismatch or titles_mismatch) and not force:
            # Build detailed error message
            errors = []
            if markdown_mismatch:
                errors.append(
                    f"Markdown file ({source_key}):\n"
                    f"  Stored:  {markdown_stored_hash}\n"
                    f"  Current: {markdown_current_hash}"
                )
            if titles_mismatch:
                errors.append(
                    f"Titles file ({titles_key}):\n"
                    f"  Stored:  {titles_stored_hash}\n"
                    f"  Current: {titles_current_hash}"
                )
            error_msg = "File hash mismatch detected:\n" + "\n".join(errors)
            # Reuse HashMismatchError but customize message
            raise HashMismatchError(
                stored_hash=f"{markdown_stored_hash[:16]}... / {titles_stored_hash[:16]}...",
                current_hash=f"{markdown_current_hash[:16]}... / {titles_current_hash[:16]}..."
            )

        if force and (markdown_mismatch or titles_mismatch):
            if verbose:
                print("WARNING: Hash mismatch detected, proceeding with --force")
                if markdown_mismatch:
                    print(f"  Markdown hash changed")
                if titles_mismatch:
                    print(f"  Titles hash changed")

        # Read titles file content
        titles_content = titles_path.read_text(encoding='utf-8')

        # Extract the titles codeblock
        codeblock_match = re.search(r'```\n(.*?)\n```', titles_content, re.DOTALL)
        if not codeblock_match:
            raise ValueError(f"No titles codeblock found in: {titles_path}")

        titles_codeblock = codeblock_match.group(1)

        # Get metadata from work
        title = work.title or "Unknown Title"
        authors = work.authors or "Unknown Author"
        toc = work.toc or []

        if verbose:
            print(f"Document: {title}")
            print(f"Authors: {authors}")
            print(f"TOC entries: {len(toc)}")

        # Build the LLM prompt
        prompt = _build_prompt(title, authors, toc, titles_codeblock)

        # Lazy import - only load AI module when LLM is needed
        from vulcanlab.ai import create_langchain_chat, ModelTier

        # Call LLM with appropriate tier
        tier = ModelTier.FULL if use_full_model else ModelTier.LIGHT

        if verbose:
            print(f"Calling LLM (tier: {'FULL' if use_full_model else 'LIGHT'})...")

        langchain_stack = create_langchain_chat(
            settings=None,
            tier=tier,
            search=True,
            temperature=0.2
        )
        chat = langchain_stack.chat

        response = chat.invoke(prompt)
        response_text = _extract_text_from_response(response.content)

        # Log the interaction
        _log_llm_interaction(prompt, response_text)

        if verbose:
            print("LLM response received")

        # Parse the LLM response to extract changes
        changes = _parse_llm_response(response_text)

        # Calculate relative path from markdown to titles
        try:
            relative_uri = markdown_path.relative_to(titles_path.parent)
            relative_uri_str = f"./{relative_uri.as_posix()}"
        except ValueError:
            # Files are on different drives or can't be made relative
            relative_uri_str = markdown_path.as_posix()

        # Build output content
        output_lines = [
            relative_uri_str,
            "",
            "# CHANGES TO HEADINGS",
            "```",
            *changes,
            "```"
        ]
        output_content = "\n".join(output_lines)

        # Determine output path based on source
        if source_key == "original_markdown":
            # <file>.md -> <file>.title_changes.md
            output_path = markdown_path.parent / f"{markdown_path.stem}.title_changes.md"
        else:  # sanitized
            # <file>.sanitized.md -> <file>.sanitized.title_changes.md
            output_path = markdown_path.parent / f"{markdown_path.stem}.title_changes.md"

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write output file
        output_path.write_text(output_content, encoding='utf-8')

        if verbose:
            print(f"Title changes saved to: {output_path}")

        # Compute hash of new file
        output_hash = compute_file_hash(output_path)

        # Update work's files metadata
        # Need to create a new dict to trigger SQLAlchemy's change detection for JSON columns
        updated_files = dict(work.files) if work.files else {}
        updated_files[output_key] = {
            "path": str(output_path.resolve()),
            "hash": output_hash
        }
        work.files = updated_files

        session.commit()
        session.refresh(work)

        if verbose:
            print(f"Updated work {work_id} with '{output_key}' file metadata")

    return output_path
