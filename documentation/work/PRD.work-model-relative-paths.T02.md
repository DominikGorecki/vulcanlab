COMPLETE

# T02: Database migration script to convert absolute paths to filenames

## Context

- **PRD:** [PRD.work-model-relative-paths.md](PRD.work-model-relative-paths.md)
- **PRD Section:** Section 5.1 FR4 (Database Migration Script)
- **Business Value:** Converts all existing Work records from absolute paths to relative filenames, enabling database portability across environments without path conflicts.

## Outcome

Migration script `015_convert_paths_to_filenames.py` is created and tested. When executed, it successfully converts all `markdown_path` fields and `files[*]["path"]` entries from absolute paths to filenames (e.g., `"D:\psychRAG_data\output\file.pdf"` → `"file.pdf"`). Migration is idempotent and handles both Windows and Linux path separators.

## Scope

### In scope:
- Create Python migration script `migrations/015_convert_paths_to_filenames.py`
- Extract filename from `markdown_path` field for all Work records
- Extract filename from all `files[file_key]["path"]` entries in the `files` JSON field
- Handle both Windows (`\`) and Linux (`/`) path separators
- Handle NULL values gracefully (skip, log warning)
- Make migration idempotent (safe to run multiple times)
- Use SQLAlchemy session management following existing migration patterns (see `migrations/010_refactor_heading_breadcrumbs.py`)
- Provide progress updates and summary statistics

### Out of scope:
- Rollback/downgrade migration (per user requirements)
- Converting the deprecated `source_path` field
- Validating that extracted filenames exist on filesystem
- Pure SQL migration (too complex for regex handling of JSON fields)

## Implementation plan

### Backend

#### Migration Script Structure
**File:** `migrations/015_convert_paths_to_filenames.py`

Follow the pattern from `010_refactor_heading_breadcrumbs.py`:
- Use `sqlalchemy.text()` for queries
- Process in batches for large datasets
- Commit after each batch
- Print progress updates
- Provide summary statistics

#### Key Functions

**1. Filename Extraction Function:**
```python
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
```

**2. JSON Path Extraction Function:**
```python
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
```

**3. Main Upgrade Function:**
```python
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
```

#### Idempotency Considerations
- The migration compares extracted filename with current value
- If already a filename (no separator found), no update occurs
- Safe to run multiple times - will only update absolute paths

#### Error Handling
- NULL `markdown_path` and `files` values are logged but don't cause failures
- Invalid JSON in `files` field will raise exception (intentional - indicates data corruption)
- Transaction commits per batch - partial success on large datasets

### Frontend
Not applicable - backend-only ticket.

### Other / cross-cutting

- **Dependency on T01:** While the migration doesn't use PathResolver directly, T01 should be complete first for validation/testing purposes
- **Backup recommendation:** Document that users should backup database before running migration
- **Testing strategy:** Test on isolated database copy first, validate a sample of records manually

## Unit tests

**Test file:** `tests/unit/test_migration_015.py` (create new file)

Use pytest framework following existing repo patterns.

### Test cases for helper functions:

1. **test_extract_filename_windows_path**
   - Input: `"D:\\psychRAG_data\\output\\file.pdf"`
   - Assert returns `"file.pdf"`

2. **test_extract_filename_linux_path**
   - Input: `"/home/user/vulcanData/output/file.pdf"`
   - Assert returns `"file.pdf"`

3. **test_extract_filename_mixed_separators**
   - Input: `"D:/data\\output/file.pdf"` (mixed separators)
   - Assert returns `"file.pdf"` (uses last separator)

4. **test_extract_filename_already_filename**
   - Input: `"file.pdf"`
   - Assert returns `"file.pdf"` (unchanged)

5. **test_extract_filename_null**
   - Input: `None`
   - Assert returns `None`

6. **test_extract_filename_empty**
   - Input: `""`
   - Assert returns `""`

7. **test_extract_paths_from_files_json_single_entry**
   - Input: `{"sanitized": {"path": "/full/path/file.md", "hash": "abc123"}}`
   - Assert returns `{"sanitized": {"path": "file.md", "hash": "abc123"}}`
   - Assert hash preserved

8. **test_extract_paths_from_files_json_multiple_entries**
   - Input: Multiple file types with paths
   - Assert all paths converted, other fields preserved

9. **test_extract_paths_from_files_json_already_filenames**
   - Input: `{"sanitized": {"path": "file.md", "hash": "abc"}}`
   - Assert returns same (idempotent)

10. **test_extract_paths_from_files_json_null**
    - Input: `None`
    - Assert returns `None`

11. **test_extract_paths_from_files_json_empty_dict**
    - Input: `{}`
    - Assert returns `{}`

12. **test_extract_paths_from_files_json_missing_path_key**
    - Input: `{"sanitized": {"hash": "abc123"}}` (no path key)
    - Assert returns unchanged (doesn't fail)

### Integration test (requires test database):

13. **test_migration_015_integration**
    - Create test Work records with absolute paths
    - Run `upgrade(connection)` function
    - Query updated records
    - Assert `markdown_path` converted to filename
    - Assert `files[*]["path"]` converted to filenames
    - Assert hash values preserved

14. **test_migration_015_idempotent**
    - Run migration once
    - Capture state
    - Run migration again
    - Assert state unchanged (idempotent)

## Dependencies and sequencing

### Dependencies:
- **T01 (soft dependency):** PathResolver should be implemented for validation purposes, but migration doesn't directly use it

### Blocks:
- None - can be merged independently
- **Deployment sequencing:** Should run AFTER T03-T06 code updates are deployed (so code expects filenames, not absolute paths)

### Rollout notes:
1. Deploy T01 + T03-T06 code changes first
2. Test migration on database backup/copy
3. Run migration on production database during maintenance window
4. Validate sample records manually
5. Monitor application for path resolution issues

## Manual test plan

**Prerequisites:**
- Database with Work records containing absolute paths
- Database backup created

**Test steps:**

1. **Pre-migration validation:**
   - Query sample Work records: `SELECT id, markdown_path, files FROM works LIMIT 5`
   - Verify absolute paths present (e.g., paths contain `/` or `\`)
   - Document 3-5 work IDs for later comparison

2. **Run migration:**
   - Execute migration: `python migrations/015_convert_paths_to_filenames.py` (or via migration runner)
   - Observe progress output
   - Verify summary statistics match expected counts

3. **Post-migration validation:**
   - Query same sample Work records
   - For each record:
     - Verify `markdown_path` is now filename only (no separators)
     - Verify `files[*]["path"]` values are filenames only
     - Verify hash values unchanged in `files` JSON
   - Example validation query:
     ```sql
     SELECT id, markdown_path, files->'sanitized'->>'path' as sanitized_path
     FROM works
     WHERE id IN (1, 5, 10);
     ```

4. **Idempotency test:**
   - Run migration again
   - Verify no errors
   - Verify record values unchanged (no double-conversion)

5. **Application integration test:**
   - Start application
   - Use PathResolver to resolve paths for migrated Work records
   - Verify absolute paths constructed correctly
   - Test conversion/sanitization/chunking pipeline with migrated data

6. **Edge cases:**
   - Query works with NULL `markdown_path`: `SELECT COUNT(*) FROM works WHERE markdown_path IS NULL`
   - Verify migration handled gracefully (logged but didn't fail)
   - Query works with NULL `files`: `SELECT COUNT(*) FROM works WHERE files IS NULL`
   - Verify handled gracefully

## Clarifications and assumptions

### Assumptions:
1. **Python migration acceptable:** Pure SQL would be too complex for JSON manipulation and cross-platform path handling
2. **SQLAlchemy patterns:** Following `010_refactor_heading_breadcrumbs.py` as reference for session management and batch processing
3. **Batch size:** Using 100 (smaller than chunks migration due to JSON operations)
4. **JSON serialization:** Using `json.dumps()` to serialize updated `files` dict back to JSON for database storage
5. **No validation of file existence:** Migration converts paths but doesn't verify files exist on filesystem (out of scope)
6. **Separator priority:** When mixed separators exist, uses the LAST occurrence of either separator (most common pattern in mixed paths)

### Open questions (non-blocking):
1. Should the migration script support a `--dry-run` flag to preview changes without committing?
   - *Current assumption:* No, test on database backup instead
2. Should the migration log individual record changes to a file for audit purposes?
   - *Current assumption:* No, summary statistics sufficient

### Blocking questions:
None - all implementation details clarified.

### Before implementing:
Review this ticket and confirm the batch size (100) and progress update frequency (every 5 batches = every 500 records) are appropriate for the expected dataset size. If you have >100k works, consider increasing batch size to 500-1000.

Test the migration on a database backup before running on production data. Verify a representative sample of records manually after migration completes.
