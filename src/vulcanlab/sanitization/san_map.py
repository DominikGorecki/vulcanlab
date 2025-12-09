"""
Apply string mappings to sanitize markdown documents.

This module reads a CSV file with old/new string mappings and applies
them to a markdown document, updating the database with the new hash.

Usage:
    from vulcanlab.sanitization.san_map import apply_san_mapping, preview_san_mapping

    # Preview changes
    preview = preview_san_mapping("book.md", "book.san_mapping.csv")

    # Apply mappings
    output_path = apply_san_mapping("book.md", "book.san_mapping.csv", work_id=1)
"""

import csv
from pathlib import Path

from vulcanlab.data.database import SessionLocal
from vulcanlab.data.models import Work
from vulcanlab.utils import compute_file_hash, set_file_writable, set_file_readonly, is_file_readonly


def load_mappings(csv_path: str | Path) -> list[tuple[str, str]]:
    """
    Load string mappings from a CSV file.

    Args:
        csv_path: Path to the CSV file with 'old' and 'new' columns.

    Returns:
        List of (old, new) tuples.

    Raises:
        FileNotFoundError: If the CSV file doesn't exist.
        ValueError: If the CSV format is invalid.
    """
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    mappings = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        if 'old' not in reader.fieldnames or 'new' not in reader.fieldnames:
            raise ValueError("CSV must have 'old' and 'new' columns")

        for row in reader:
            old_val = str(row['old']) if row['old'] is not None else ''
            new_val = str(row['new']) if row['new'] is not None else ''
            if old_val:  # Only add if old value is not empty
                mappings.append((old_val, new_val))

    return mappings


def preview_san_mapping(
    markdown_path: str | Path,
    csv_path: str | Path,
) -> dict:
    """
    Preview string mapping replacements without applying them.

    Args:
        markdown_path: Path to the markdown file.
        csv_path: Path to the CSV mapping file.

    Returns:
        Dict with 'mappings' (list of tuples) and 'counts' (dict of old -> count).

    Raises:
        FileNotFoundError: If files are not found.
    """
    markdown_path = Path(markdown_path)
    csv_path = Path(csv_path)

    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    # Load mappings
    mappings = load_mappings(csv_path)

    # Read content
    content = markdown_path.read_text(encoding='utf-8')

    # Count occurrences
    counts = {}
    for old_val, new_val in mappings:
        count = content.count(old_val)
        if count > 0:
            counts[old_val] = count

    return {
        'mappings': mappings,
        'counts': counts,
        'total_replacements': sum(counts.values())
    }


def apply_san_mapping(
    markdown_path: str | Path,
    csv_path: str | Path,
    work_id: int,
) -> Path:
    """
    Apply string mappings to a markdown file and update the database.

    Args:
        markdown_path: Path to the markdown file.
        csv_path: Path to the CSV mapping file.
        work_id: ID of the Work record in the database.

    Returns:
        Path to the updated markdown file.

    Raises:
        FileNotFoundError: If files are not found.
        ValueError: If work not found in database.
    """
    markdown_path = Path(markdown_path)
    csv_path = Path(csv_path)

    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    # Verify work exists
    with SessionLocal() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"Work with ID {work_id} not found")

    # Load mappings
    mappings = load_mappings(csv_path)

    # Check if file is read-only and unlock if needed
    was_readonly = is_file_readonly(markdown_path)
    if was_readonly:
        set_file_writable(markdown_path)

    # Read content
    content = markdown_path.read_text(encoding='utf-8')

    # Apply all mappings
    for old_val, new_val in mappings:
        content = content.replace(old_val, new_val)

    # Write updated content
    markdown_path.write_text(content, encoding='utf-8')

    # Compute new hash
    new_hash = compute_file_hash(markdown_path)

    # Restore read-only status
    if was_readonly:
        set_file_readonly(markdown_path)

    # Update database
    with SessionLocal() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        work.content_hash = new_hash
        session.commit()

    return markdown_path
