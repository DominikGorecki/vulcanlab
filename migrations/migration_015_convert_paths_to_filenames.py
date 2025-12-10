r"""
Migration 015: Convert absolute paths to filenames.

This migration converts all Work model path fields from absolute paths to
relative filenames, enabling environment portability.

Changes:
1. Extract filename from markdown_path field
2. Extract filenames from all files[*]["path"] entries in JSON field
3. Handle both Windows (\) and Linux (/) path separators
4. Skip NULL values gracefully
5. Idempotent - safe to run multiple times
"""

import json
from sqlalchemy import text


def extract_filename(path: str) -> str:
    """
    Extract filename from absolute path, handling both Windows and Linux separators.

    Args:
        path: Absolute path (e.g., "D:\\data\\file.pdf" or "/home/user/file.pdf")

    Returns:
        Filename only (e.g., "file.pdf")

    Examples:
        extract_filename("D:\\psychRAG_data\\output\\file.pdf") -> "file.pdf"
        extract_filename("/home/user/vulcanData/output/file.pdf") -> "file.pdf"
        extract_filename("file.pdf") -> "file.pdf"  # Already a filename
    """
    if not path:
        return path

    # Handle both separators - use the last occurrence of either
    last_backslash = path.rfind('\\')
    last_forward_slash = path.rfind('/')

    separator_pos = max(last_backslash, last_forward_slash)

    if separator_pos == -1:
        # No separator found - already a filename
        return path

    return path[separator_pos + 1:]


def extract_paths_from_files_json(files_json: dict) -> dict:
    """
    Extract filenames from all 'path' keys in files JSON.

    Args:
        files_json: Work.files JSON object

    Returns:
        Updated files JSON with paths converted to filenames

    Example:
        Input: {"sanitized": {"path": "/full/path/file.md", "hash": "abc123"}}
        Output: {"sanitized": {"path": "file.md", "hash": "abc123"}}
    """
    if not files_json or not isinstance(files_json, dict):
        return files_json

    updated = {}
    for key, value in files_json.items():
        if isinstance(value, dict) and "path" in value:
            updated[key] = {**value}  # Copy dict
            updated[key]["path"] = extract_filename(value["path"])
        else:
            updated[key] = value

    return updated


def upgrade(connection):
    """Apply the migration."""
    print("Starting migration 015: Convert absolute paths to filenames")
    print("=" * 60)

    # Step 1: Get total work count
    result = connection.execute(text("SELECT COUNT(*) FROM works"))
    total_works = result.scalar()
    print(f"\nTotal works to process: {total_works}")

    # Step 2: Process works in batches
    batch_size = 100  # Smaller batch for JSON operations
    offset = 0
    works_updated = 0
    markdown_paths_updated = 0
    files_json_updated = 0
    null_markdown_paths = 0
    empty_files = 0

    print(f"\nStep 1: Processing works (batch size: {batch_size})...")

    while True:
        # Fetch batch of works
        result = connection.execute(
            text("""
                SELECT id, markdown_path, files
                FROM works
                ORDER BY id
                LIMIT :limit OFFSET :offset
            """),
            {"limit": batch_size, "offset": offset}
        )

        batch = result.fetchall()
        if not batch:
            break

        # Process each work in the batch
        for row in batch:
            work_id, markdown_path, files_json = row
            update_needed = False

            # Process markdown_path
            new_markdown_path = markdown_path
            if markdown_path:
                extracted = extract_filename(markdown_path)
                if extracted != markdown_path:
                    new_markdown_path = extracted
                    markdown_paths_updated += 1
                    update_needed = True
            else:
                null_markdown_paths += 1

            # Process files JSON
            new_files_json = files_json
            if files_json:
                updated_files = extract_paths_from_files_json(files_json)
                if updated_files != files_json:
                    new_files_json = updated_files
                    files_json_updated += 1
                    update_needed = True
            else:
                empty_files += 1

            # Update if changes detected
            if update_needed:
                connection.execute(
                    text("""
                        UPDATE works
                        SET markdown_path = :markdown_path,
                            files = :files
                        WHERE id = :id
                    """),
                    {
                        "markdown_path": new_markdown_path,
                        "files": json.dumps(new_files_json) if new_files_json else None,
                        "id": work_id
                    }
                )

            works_updated += 1

        # Commit batch
        connection.commit()

        # Progress update every 5 batches
        if works_updated % (batch_size * 5) == 0:
            print(f"  Processed {works_updated:,} / {total_works:,} works...")

        offset += batch_size

    # Summary
    print("\n" + "=" * 60)
    print("Migration 015 completed successfully!")
    print(f"\nSummary:")
    print(f"  Total works processed: {works_updated:,}")
    print(f"  markdown_path fields updated: {markdown_paths_updated:,}")
    print(f"  files JSON objects updated: {files_json_updated:,}")
    print(f"  NULL markdown_path values: {null_markdown_paths:,}")
    print(f"  NULL/empty files JSON: {empty_files:,}")
    print("=" * 60)
