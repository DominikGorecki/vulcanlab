"""
Apply title changes to markdown documents.

This module applies heading changes from a .title_changes.md file to the
original markdown document, creating a sanitized version.

Usage:
    from vulcanlab.sanitization.apply_title_changes import apply_title_changes_from_work

    # Apply changes from work ID
    output_path = apply_title_changes_from_work(work_id=1, source_key='original_markdown')

Functions:
    apply_title_changes_from_work(work_id, source_key, force, verbose) - Apply from Work by ID
    parse_title_changes(changes_file) - Parse title changes file
    preview_title_changes(changes_file, work_id) - Preview changes (legacy)
    apply_title_changes(changes_file, work_id) - Apply changes (legacy)

Exceptions:
    HashMismatchError - Raised when file hashes don't match database
"""

import re
from pathlib import Path
from typing import Optional

from vulcanlab.data.database import get_session, SessionLocal
from vulcanlab.data.models.work import Work
from vulcanlab.utils.file_utils import compute_file_hash, set_file_readonly, set_file_writable, is_file_readonly
from vulcanlab.sanitization.extract_titles import HashMismatchError


def parse_title_changes(changes_file: str | Path) -> tuple[str, list[dict]]:
    """
    Parse a .title_changes.md file.

    Args:
        changes_file: Path to the .title_changes.md file.

    Returns:
        Tuple of (relative_uri, list of change dicts).
        Each change dict has: line_num, action, title_text

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file format is invalid.
    """
    changes_file = Path(changes_file)

    if not changes_file.exists():
        raise FileNotFoundError(f"Changes file not found: {changes_file}")

    content = changes_file.read_text(encoding='utf-8')
    lines = content.splitlines()

    if not lines:
        raise ValueError(f"Changes file is empty: {changes_file}")

    # First line is the relative URI
    relative_uri = lines[0].strip()

    # Extract the changes codeblock
    codeblock_match = re.search(r'```\n(.*?)\n```', content, re.DOTALL)
    if not codeblock_match:
        raise ValueError(f"No changes codeblock found in: {changes_file}")

    changes_text = codeblock_match.group(1)

    # Parse each change line
    changes = []
    pattern = re.compile(r'^\s*(\d+)\s*:\s*(NO_CHANGE|REMOVE|H[1-4])\s*:\s*(.*?)\s*$')

    for line in changes_text.splitlines():
        match = pattern.match(line)
        if match:
            changes.append({
                'line_num': int(match.group(1)),
                'action': match.group(2),
                'title_text': match.group(3)
            })

    return relative_uri, changes


def preview_title_changes(
    changes_file: str | Path,
    work_id: int,
) -> list[dict]:
    """
    Preview title changes without applying them.

    Args:
        changes_file: Path to the .title_changes.md file.
        work_id: ID of the Work record in the database.

    Returns:
        List of preview dicts with: line_num, old_line, new_line

    Raises:
        FileNotFoundError: If files are not found.
        ValueError: If work not found or file format invalid.
    """
    changes_file = Path(changes_file)
    relative_uri, changes = parse_title_changes(changes_file)

    # Get the markdown path from the database
    with SessionLocal() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"Work with ID {work_id} not found")
        if not work.markdown_path:
            raise ValueError(f"Work {work_id} has no markdown_path")

        markdown_path = Path(work.markdown_path)

    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    # Read the original markdown
    original_content = markdown_path.read_text(encoding='utf-8')
    original_lines = original_content.splitlines()

    # Build preview
    previews = []
    for change in changes:
        line_num = change['line_num']
        action = change['action']
        title_text = change['title_text']

        if line_num < 1 or line_num > len(original_lines):
            continue

        old_line = original_lines[line_num - 1]

        if action == 'REMOVE':
            new_line = "[REMOVED]"
        elif action == 'NO_CHANGE':
            # Keep original level, but update text
            level_match = re.match(r'^(#+)\s+', old_line)
            if level_match:
                prefix = level_match.group(1)
                new_line = f"{prefix} {title_text}"
            else:
                new_line = old_line
        else:
            # H1, H2, H3, H4
            level = int(action[1])
            prefix = '#' * level
            new_line = f"{prefix} {title_text}"

        previews.append({
            'line_num': line_num,
            'old_line': old_line,
            'new_line': new_line
        })

    return previews


def apply_title_changes(
    changes_file: str | Path,
    work_id: int,
) -> Path:
    """
    Apply title changes to create a sanitized markdown file.

    Args:
        changes_file: Path to the .title_changes.md file.
        work_id: ID of the Work record in the database.

    Returns:
        Path to the created sanitized file.

    Raises:
        FileNotFoundError: If files are not found.
        ValueError: If work not found or file format invalid.
    """
    changes_file = Path(changes_file)
    relative_uri, changes = parse_title_changes(changes_file)

    # Get the markdown path from the database
    with SessionLocal() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"Work with ID {work_id} not found")
        if not work.markdown_path:
            raise ValueError(f"Work {work_id} has no markdown_path")

        markdown_path = Path(work.markdown_path)

    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    # Read the original markdown
    original_content = markdown_path.read_text(encoding='utf-8')
    original_lines = original_content.splitlines()

    # Build a map of line numbers to changes
    changes_map = {c['line_num']: c for c in changes}

    # Apply changes
    new_lines = []
    for i, line in enumerate(original_lines, start=1):
        if i in changes_map:
            change = changes_map[i]
            action = change['action']
            title_text = change['title_text']

            if action == 'REMOVE':
                # Skip this line (remove it)
                continue
            elif action == 'NO_CHANGE':
                # Keep original level, update text
                level_match = re.match(r'^(#+)\s+', line)
                if level_match:
                    prefix = level_match.group(1)
                    new_lines.append(f"{prefix} {title_text}")
                else:
                    new_lines.append(line)
            else:
                # H1, H2, H3, H4
                level = int(action[1])
                prefix = '#' * level
                new_lines.append(f"{prefix} {title_text}")
        else:
            new_lines.append(line)

    # Create sanitized file
    sanitized_path = markdown_path.with_name(
        markdown_path.stem + '.sanitized.md'
    )
    sanitized_content = '\n'.join(new_lines)
    sanitized_path.write_text(sanitized_content, encoding='utf-8')

    # Compute new hash and update database
    new_hash = compute_file_hash(sanitized_path)

    with SessionLocal() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        work.content_hash = new_hash
        work.markdown_path = str(sanitized_path.absolute())
        session.commit()

    # Set file to read-only
    set_file_readonly(sanitized_path)

    return sanitized_path


def apply_title_changes_from_work(
    work_id: int,
    source_key: str,
    force: bool = False,
    verbose: bool = False
) -> Path:
    """Apply title changes from a work's files and update the database.

    Args:
        work_id: Database ID of the work.
        source_key: Key in the files JSON ("original_markdown" or "sanitized").
        force: If True, skip hash validation and proceed anyway.
        verbose: If True, print progress messages.

    Returns:
        Path to the created sanitized file.

    Raises:
        ValueError: If work_id not found, source_key invalid, or files not in database.
        HashMismatchError: If file hashes don't match stored hashes (unless force=True).
        FileNotFoundError: If the files referenced in database don't exist on disk.
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

        # Determine which title_changes file to use
        if source_key == "original_markdown":
            markdown_key = "original_markdown"
            title_changes_key = "title_changes"
            output_key = "sanitized"
        else:  # sanitized
            markdown_key = "sanitized"
            title_changes_key = "sanitized_title_changes"
            output_key = "sanitized"  # Overwrite sanitized

        # Validate required files exist in metadata
        if markdown_key not in work.files:
            raise ValueError(
                f"Work {work_id} does not have '{markdown_key}' in files metadata"
            )

        if title_changes_key not in work.files:
            raise ValueError(
                f"Work {work_id} does not have '{title_changes_key}' in files metadata"
            )

        # Get file info
        markdown_info = work.files[markdown_key]
        markdown_path = Path(markdown_info["path"])
        markdown_stored_hash = markdown_info["hash"]

        title_changes_info = work.files[title_changes_key]
        title_changes_path = Path(title_changes_info["path"])
        title_changes_stored_hash = title_changes_info["hash"]

        if verbose:
            print(f"Markdown file: {markdown_path}")
            print(f"Title changes file: {title_changes_path}")

        # Validate files exist
        if not markdown_path.exists():
            raise FileNotFoundError(
                f"Markdown file not found on disk: {markdown_path}\n"
                f"Referenced in work {work_id}, key '{markdown_key}'"
            )

        if not title_changes_path.exists():
            raise FileNotFoundError(
                f"Title changes file not found on disk: {title_changes_path}\n"
                f"Referenced in work {work_id}, key '{title_changes_key}'"
            )

        # Compute current hashes and validate
        markdown_current_hash = compute_file_hash(markdown_path)
        title_changes_current_hash = compute_file_hash(title_changes_path)

        markdown_mismatch = markdown_current_hash != markdown_stored_hash
        title_changes_mismatch = title_changes_current_hash != title_changes_stored_hash

        if (markdown_mismatch or title_changes_mismatch) and not force:
            error_parts = []
            if markdown_mismatch:
                error_parts.append(
                    f"  {markdown_key}: stored={markdown_stored_hash}, current={markdown_current_hash}"
                )
            if title_changes_mismatch:
                error_parts.append(
                    f"  {title_changes_key}: stored={title_changes_stored_hash}, current={title_changes_current_hash}"
                )
            error_message = "File hash mismatch detected:\n" + "\n".join(error_parts)
            raise HashMismatchError(
                stored_hash="multiple",
                current_hash="multiple"
            )

        if (markdown_mismatch or title_changes_mismatch) and verbose:
            print(f"Warning: Hash mismatch detected, proceeding with --force")

        # Parse title changes
        relative_uri, changes = parse_title_changes(title_changes_path)

        # Read the markdown content
        markdown_content = markdown_path.read_text(encoding='utf-8')
        markdown_lines = markdown_content.splitlines()

        # Build a map of line numbers to changes
        changes_map = {c['line_num']: c for c in changes}

        # Apply changes
        new_lines = []
        for i, line in enumerate(markdown_lines, start=1):
            if i in changes_map:
                change = changes_map[i]
                action = change['action']
                title_text = change['title_text']

                if action == 'REMOVE':
                    # Skip this line (remove it)
                    continue
                elif action == 'NO_CHANGE':
                    # Keep original level, update text
                    level_match = re.match(r'^(#+)\s+', line)
                    if level_match:
                        prefix = level_match.group(1)
                        new_lines.append(f"{prefix} {title_text}")
                    else:
                        new_lines.append(line)
                else:
                    # H1, H2, H3, H4
                    level = int(action[1])
                    prefix = '#' * level
                    new_lines.append(f"{prefix} {title_text}")
            else:
                new_lines.append(line)

        # Determine output path
        # For original_markdown -> <file>.sanitized.md
        # For sanitized -> overwrite <file>.sanitized.md
        if source_key == "original_markdown":
            output_path = markdown_path.parent / f"{markdown_path.stem}.sanitized.md"
        else:  # sanitized - path already ends with .sanitized.md
            output_path = markdown_path

        # Check if output file exists and is read-only
        if output_path.exists():
            if verbose:
                print(f"Output file already exists: {output_path}")

            # If it's read-only, we need to make it writable to overwrite
            if is_file_readonly(output_path):
                if verbose:
                    print(f"File is read-only, making it writable for overwrite")
                set_file_writable(output_path)

        # Write sanitized content
        sanitized_content = '\n'.join(new_lines)
        output_path.write_text(sanitized_content, encoding='utf-8')

        if verbose:
            print(f"Sanitized file written: {output_path}")

        # Set file to read-only
        set_file_readonly(output_path)

        if verbose:
            print(f"File set to read-only")

        # Compute hash of sanitized file
        sanitized_hash = compute_file_hash(output_path)

        # Update work's files metadata
        # Need to create a new dict to trigger SQLAlchemy's change detection for JSON columns
        updated_files = dict(work.files) if work.files else {}
        updated_files[output_key] = {
            "path": str(output_path.resolve()),
            "hash": sanitized_hash
        }
        work.files = updated_files

        session.commit()
        session.refresh(work)

        if verbose:
            print(f"Updated work {work_id} with '{output_key}' file metadata")

    return output_path
