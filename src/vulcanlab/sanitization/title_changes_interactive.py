"""
Interactive title changes module for table-based editing.

This module provides functions to:
1. Extract ALL headings from a markdown file
2. Parse title_changes.md file
3. Merge headings with suggested changes for table display
4. Reconstruct title_changes.md from table data

Usage:
    from vulcanlab.sanitization.title_changes_interactive import get_title_changes_table_data

    # Get table data for frontend
    table_data = get_title_changes_table_data(work_id=1, source_key='original_markdown')
"""

import re
from pathlib import Path
from typing import Optional

from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from vulcanlab.utils.file_utils import compute_file_hash, get_path_resolver
from vulcanlab.sanitization.apply_title_changes import parse_title_changes
from vulcanlab.sanitization.extract_titles import HashMismatchError

# Initialize path resolver
resolver = get_path_resolver()


def extract_all_headings(markdown_path: Path) -> list[dict]:
    """
    Extract ALL heading lines (H1-H6) from a markdown file.

    Args:
        markdown_path: Path to the markdown file

    Returns:
        List of dicts with keys: line_num, heading, title
        Example: [
            {"line_num": 157, "heading": "H2", "title": "Cognitive Psychology"},
            {"line_num": 159, "heading": "H3", "title": "Introduction"},
            ...
        ]

    Raises:
        FileNotFoundError: If markdown file doesn't exist
    """
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    headings = []
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')

    content = markdown_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    for line_num, line in enumerate(lines, start=1):
        match = heading_pattern.match(line)
        if match:
            hash_marks = match.group(1)
            title_text = match.group(2).strip()
            heading_level = f"H{len(hash_marks)}"

            headings.append({
                "line_num": line_num,
                "heading": heading_level,
                "title": title_text
            })

    return headings


def parse_title_changes_file(title_changes_path: Path) -> dict[int, dict]:
    """
    Parse a .title_changes.md file into a dict keyed by line number.

    Args:
        title_changes_path: Path to the .title_changes.md file

    Returns:
        Dict mapping line_num to change info
        Example: {
            157: {"action": "H1", "title": "1 Cognitive Psychology"},
            159: {"action": "NO_CHANGE", "title": "Introduction"},
            ...
        }

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    if not title_changes_path.exists():
        raise FileNotFoundError(f"Title changes file not found: {title_changes_path}")

    # Reuse existing parse_title_changes function
    _, changes_list = parse_title_changes(title_changes_path)

    # Convert list to dict keyed by line_num for fast lookup
    changes_dict = {}
    for change in changes_list:
        changes_dict[change['line_num']] = {
            "action": change['action'],
            "title": change['title_text']
        }

    return changes_dict


def get_title_changes_table_data(
    work_id: int,
    source_key: str = "original_markdown",
    force: bool = False
) -> dict:
    """
    Get table data by merging ALL headings from original markdown with title_changes.

    This is the main function for the GET endpoint. It:
    1. Loads work from database
    2. Extracts all headings from the source markdown
    3. Parses title_changes.md (if exists)
    4. Merges headings with changes (defaults to NO_CHANGE for unchanged headings)

    Args:
        work_id: Database ID of the work
        source_key: Key in work.files ("original_markdown" or "sanitized")
        force: If True, skip hash validation

    Returns:
        Dict with keys:
            - work_id: int
            - source_file: str (relative path from title_changes.md)
            - rows: list[dict] with keys:
                - line_num: int
                - original_heading: str (H1-H6)
                - original_title: str
                - suggested_action: str (H1-H6 or REMOVE)
                - suggested_title: str

    Raises:
        ValueError: If work not found or files missing
        HashMismatchError: If hashes don't match (unless force=True)
        FileNotFoundError: If files don't exist on disk
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise ValueError(f"Work with ID {work_id} not found in database")

        if not work.files:
            raise ValueError(f"Work {work_id} has no files metadata")

        # Validate source_key exists
        if source_key not in work.files:
            raise ValueError(
                f"Work {work_id} does not have '{source_key}' in files metadata"
            )

        # Get source markdown file info
        markdown_info = work.files[source_key]
        markdown_path = resolver.resolve_work_path(work, source_key)
        markdown_stored_hash = markdown_info["hash"]

        # Validate markdown file exists
        if not markdown_path.exists():
            raise FileNotFoundError(
                f"Markdown file not found on disk: {markdown_path}\n"
                f"Referenced in work {work_id}, key '{source_key}'"
            )

        # Validate hash (unless force=True)
        if not force:
            markdown_current_hash = compute_file_hash(markdown_path)
            if markdown_current_hash != markdown_stored_hash:
                raise HashMismatchError(
                    stored_hash=markdown_stored_hash,
                    current_hash=markdown_current_hash
                )

        # Extract all headings from original markdown
        all_headings = extract_all_headings(markdown_path)

        # Parse title_changes file (if exists)
        title_changes_key = "title_changes" if source_key == "original_markdown" else "sanitized_title_changes"
        changes_dict = {}
        source_file = ""

        if title_changes_key in work.files:
            title_changes_info = work.files[title_changes_key]
            title_changes_path = resolver.resolve_work_path(work, title_changes_key)

            if title_changes_path.exists():
                # Validate hash (unless force=True)
                if not force:
                    changes_stored_hash = title_changes_info["hash"]
                    changes_current_hash = compute_file_hash(title_changes_path)
                    if changes_current_hash != changes_stored_hash:
                        raise HashMismatchError(
                            stored_hash=changes_stored_hash,
                            current_hash=changes_current_hash
                        )

                try:
                    source_file, _ = parse_title_changes(title_changes_path)
                    changes_dict = parse_title_changes_file(title_changes_path)
                except ValueError:
                    # If parsing fails, treat as empty changes
                    changes_dict = {}

        # If source_file wasn't extracted, use markdown filename
        if not source_file:
            source_file = f"./{markdown_path.name}"

        # Merge headings with changes
        rows = []
        for heading in all_headings:
            line_num = heading["line_num"]
            original_heading = heading["heading"]
            original_title = heading["title"]

            # Check if this line has a suggested change
            if line_num in changes_dict:
                change = changes_dict[line_num]
                suggested_action = change["action"]
                suggested_title = change["title"]
            else:
                # No change suggested - default to original
                suggested_action = original_heading
                suggested_title = original_title

            rows.append({
                "line_num": line_num,
                "original_heading": original_heading,
                "original_title": original_title,
                "suggested_action": suggested_action,
                "suggested_title": suggested_title
            })

        return {
            "work_id": work_id,
            "source_file": source_file,
            "rows": rows
        }


def reconstruct_title_changes_markdown(
    source_file: str,
    rows: list[dict]
) -> str:
    """
    Reconstruct .title_changes.md format from table data.

    Only includes rows where an actual change occurred:
    - suggested_action != original_heading OR
    - suggested_title != original_title

    Args:
        source_file: Relative path to source markdown (e.g., "./test3.md")
        rows: List of dicts with keys:
            - line_num: int
            - original_heading: str
            - original_title: str
            - suggested_action: str
            - suggested_title: str

    Returns:
        Markdown string in .title_changes.md format
    """
    # Filter rows to only include actual changes
    changed_rows = []
    for row in rows:
        has_heading_change = row["suggested_action"] != row["original_heading"]
        has_title_change = row["suggested_title"] != row["original_title"]

        if has_heading_change or has_title_change:
            changed_rows.append(row)

    # Build markdown string
    lines = [
        source_file,
        "",
        "# CHANGES TO HEADINGS",
        "```"
    ]

    # Add each change line
    for row in changed_rows:
        change_line = f"{row['line_num']} : {row['suggested_action']} : {row['suggested_title']}"
        lines.append(change_line)

    lines.append("```")
    lines.append("")  # Trailing newline

    return "\n".join(lines)
