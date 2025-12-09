"""
Interactive vec suggestions module for table-based editing.

This module provides functions to:
1. Extract ALL headings from .sanitized.md file
2. Parse .sanitized.vec_sugg.md file
3. Merge headings with suggestions for table display
4. Reconstruct .sanitized.vec_sugg.md from table data

Usage:
    from vulcanlab.chunking.vec_suggestions_interactive import get_vec_suggestions_table_data

    # Get table data for frontend
    table_data = get_vec_suggestions_table_data(work_id=1)
"""

import re
from pathlib import Path

from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from vulcanlab.utils.file_utils import compute_file_hash
from vulcanlab.sanitization.extract_titles import HashMismatchError


def extract_all_headings_from_sanitized(sanitized_path: Path) -> list[dict]:
    """
    Extract ALL headings from .sanitized.md file.

    Args:
        sanitized_path: Path to the .sanitized.md file

    Returns:
        List of dicts with keys: line_num, heading
        Example: [
            {"line_num": 155, "heading": "# 1 Cognitive Psychology"},
            {"line_num": 157, "heading": "## 1.1 Introduction"},
            ...
        ]

    Raises:
        FileNotFoundError: If sanitized file doesn't exist
        ValueError: If no headings found in file
    """
    if not sanitized_path.exists():
        raise FileNotFoundError(f"Sanitized file not found: {sanitized_path}")

    content = sanitized_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    headings = []
    # Parse headings directly from markdown content
    # Pattern matches markdown headings: # Heading, ## Heading, etc.
    heading_pattern = re.compile(r'^(#+)\s+(.*)$')

    for i, line in enumerate(lines, start=1):
        match = heading_pattern.match(line)
        if match:
            level = len(match.group(1))
            if level <= 5:  # Only H1-H5
                heading_text = line.strip()  # Keep full heading line with markdown symbols
                headings.append({
                    "line_num": i,
                    "heading": heading_text
                })

    if not headings:
        raise ValueError(f"No headings found in sanitized file: {sanitized_path}")

    return headings


def parse_vec_suggestions_file(vec_sugg_path: Path) -> dict[int, str]:
    """
    Parse .sanitized.vec_sugg.md into dict keyed by line number.

    Args:
        vec_sugg_path: Path to the .sanitized.vec_sugg.md file

    Returns:
        Dict mapping line_num to decision (VECTORIZE or SKIP)
        Example: {
            155: "VECTORIZE",
            649: "SKIP",
            ...
        }

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not vec_sugg_path.exists():
        raise FileNotFoundError(f"Vec suggestions file not found: {vec_sugg_path}")

    content = vec_sugg_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    # Find the code block with decisions
    in_code_block = False
    decisions = {}
    line_pattern = re.compile(r'^(\d+):\s+(VECTORIZE|SKIP)$')

    for line in lines:
        if line.strip() == '```':
            in_code_block = not in_code_block
            continue

        if in_code_block:
            match = line_pattern.match(line)
            if match:
                line_num = int(match.group(1))
                decision = match.group(2)
                decisions[line_num] = decision

    return decisions


def get_vec_suggestions_table_data(
    work_id: int,
    force: bool = False
) -> dict:
    """
    Get table data by merging ALL headings from sanitized.md with vec suggestions.

    This is the main function for the GET endpoint. It:
    1. Loads work from database
    2. Extracts all headings from the .sanitized.md file
    3. Parses .sanitized.vec_sugg.md (if exists)
    4. Merges headings with decisions (defaults to VECTORIZE for unchanged headings)

    Args:
        work_id: Database ID of the work
        force: If True, skip hash validation

    Returns:
        Dict with keys:
            - work_id: int
            - rows: list[dict] with keys:
                - line_num: int
                - heading: str (full heading text with markdown symbols)
                - decision: str (VECTORIZE or SKIP)

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

        # Validate sanitized exists
        if "sanitized" not in work.files:
            raise ValueError(
                f"Work {work_id} does not have 'sanitized' in files metadata. "
                f"Please run sanitization first."
            )

        # Get sanitized file info
        sanitized_info = work.files["sanitized"]
        sanitized_path = Path(sanitized_info["path"])
        sanitized_stored_hash = sanitized_info["hash"]

        # Validate sanitized file exists
        if not sanitized_path.exists():
            raise FileNotFoundError(
                f"Sanitized file not found on disk: {sanitized_path}\n"
                f"Referenced in work {work_id}"
            )

        # Validate hash (unless force=True)
        if not force:
            sanitized_current_hash = compute_file_hash(sanitized_path)
            if sanitized_current_hash != sanitized_stored_hash:
                raise HashMismatchError(
                    stored_hash=sanitized_stored_hash,
                    current_hash=sanitized_current_hash
                )

        # Extract all headings from sanitized.md file
        all_headings = extract_all_headings_from_sanitized(sanitized_path)

        # Parse vec_sugg file (if exists) - should be .sanitized.vec_sugg.md
        decisions_dict = {}
        vec_sugg_path = None
        
        # First, try to get path from database metadata
        if "vec_suggestions" in work.files:
            vec_sugg_info = work.files["vec_suggestions"]
            vec_sugg_path = Path(vec_sugg_info["path"])
            # Resolve to absolute path in case it's relative
            if not vec_sugg_path.is_absolute():
                vec_sugg_path = vec_sugg_path.resolve()
        else:
            # If not in database, try to auto-detect based on sanitized file path
            # Pattern: <file>.sanitized.md -> <file>.sanitized.vec_sugg.md
            vec_sugg_path = sanitized_path.parent / f"{sanitized_path.stem}.vec_sugg.md"

        # Resolve path to ensure it's absolute
        if vec_sugg_path:
            vec_sugg_path = vec_sugg_path.resolve()

        if vec_sugg_path and vec_sugg_path.exists():
            # Validate hash if we have stored hash (unless force=True)
            if not force and "vec_suggestions" in work.files:
                vec_sugg_stored_hash = work.files["vec_suggestions"]["hash"]
                vec_sugg_current_hash = compute_file_hash(vec_sugg_path)
                if vec_sugg_current_hash != vec_sugg_stored_hash:
                    raise HashMismatchError(
                        stored_hash=vec_sugg_stored_hash,
                        current_hash=vec_sugg_current_hash
                    )

            try:
                decisions_dict = parse_vec_suggestions_file(vec_sugg_path)
            except ValueError:
                # If parsing fails, treat as empty decisions
                decisions_dict = {}

        # Merge headings with decisions
        rows = []
        for heading in all_headings:
            line_num = heading["line_num"]
            heading_text = heading["heading"]

            # Check if this line has a decision
            if line_num in decisions_dict:
                decision = decisions_dict[line_num]
            else:
                # No decision specified - default to VECTORIZE
                decision = "VECTORIZE"

            rows.append({
                "line_num": line_num,
                "heading": heading_text,
                "decision": decision
            })

        result = {
            "work_id": work_id,
            "rows": rows
        }
        
        # Always include vec_sugg_path if we have one (even if file doesn't exist on disk)
        # This helps the API endpoint know what path to check
        # CRITICAL: Always include path if it's in database, even if file doesn't exist
        if vec_sugg_path:
            result["vec_sugg_path"] = str(vec_sugg_path.resolve())
            if vec_sugg_path.exists():
                result["vec_sugg_hash"] = compute_file_hash(vec_sugg_path) if not force else None
            # Also include whether it was from database or auto-detected
            result["vec_sugg_from_db"] = "vec_suggestions" in work.files
        
        # If vec_suggestions is in database but we didn't set vec_sugg_path, set it now
        if "vec_suggestions" in work.files and "vec_sugg_path" not in result:
            vec_sugg_info = work.files["vec_suggestions"]
            if isinstance(vec_sugg_info, dict) and "path" in vec_sugg_info:
                result["vec_sugg_path"] = str(Path(vec_sugg_info["path"]).resolve())
                result["vec_sugg_from_db"] = True
        
        return result


def reconstruct_vec_suggestions_markdown(
    rows: list[dict]
) -> str:
    """
    Reconstruct .sanitized.vec_sugg.md format from table data.

    Saves ALL rows (matching existing file pattern, per user's Option C decision).

    Args:
        rows: List of dicts with keys:
            - line_num: int
            - heading: str
            - decision: str (VECTORIZE or SKIP)

    Returns:
        Markdown string in .sanitized.vec_sugg.md format
    """
    # Build markdown string
    lines = [
        "# CHANGES TO HEADINGS",
        "```"
    ]

    # Add all rows (save everything like the existing file does)
    for row in rows:
        decision_line = f"{row['line_num']}: {row['decision']}"
        lines.append(decision_line)

    lines.append("```")
    lines.append("")  # Trailing newline

    return "\n".join(lines)
