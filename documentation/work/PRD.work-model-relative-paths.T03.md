COMPLETE

# T03: Update conversion modules to use PathResolver

## Context

- **PRD:** [PRD.work-model-relative-paths.md](PRD.work-model-relative-paths.md)
- **PRD Section:** Section 5.1 FR3 (Update All Code References) - Conversion modules
- **Business Value:** Conversion module (`new_work.py`) now stores filenames instead of absolute paths, enabling environment-portable Work records.

## Outcome

The `new_work.py` module is updated to use Work model helper methods (`set_markdown_path`, `set_file_path`) for storing paths. All file paths stored in the database are filenames only. Existing unit tests pass, and new tests validate filename-only storage.

## Scope

### In scope:
- Update `src/vulcanlab/conversions/new_work.py` to use Work model helper methods
- Modify 3 locations where paths are stored:
  - Line 130: `files_metadata[field_name]["path"]` assignment
  - Line 167: `markdown_path` assignment to Work constructor
  - Line 182: `files` assignment to Work constructor
- Ensure file discovery logic continues using absolute paths (for filesystem operations)
- Ensure stored paths are filenames only (using helper methods)
- Update or add unit tests to validate filename-only storage

### Out of scope:
- Changes to file discovery logic (still uses absolute paths for `file_path.exists()` checks)
- Changes to hash computation (still uses absolute paths)
- Modifications to other conversion modules (if any exist)

## Implementation plan

### Backend

#### File: `src/vulcanlab/conversions/new_work.py`

**Changes to make:**

**1. No imports needed** - Work model already imported, helper methods are on the Work class

**2. Update file discovery loop (lines 122-133):**

Current code stores absolute paths:
```python
files_metadata[field_name] = {
    "path": str(file_path.resolve()),
    "hash": file_hash
}
```

New approach - store filenames only:
```python
files_metadata[field_name] = {
    "path": file_path.name,  # Just filename, not full path
    "hash": file_hash
}
```

**Rationale:** File discovery still uses `file_path` (absolute Path object) for existence checks and hash computation, but only stores `file_path.name` (filename portion) in metadata dict.

**3. Update Work instantiation (lines 165-183):**

Current code:
```python
work = Work(
    title=title,
    markdown_path=str(markdown_path),
    ...
    files=files_metadata if files_metadata else None
)
```

New approach using helper method:
```python
work = Work(
    title=title,
    authors=authors,
    year=year,
    publisher=publisher,
    isbn=isbn,
    edition=edition,
    volume=volume,
    issue=issue,
    pages=pages,
    url=url,
    city=city,
    institution=institution,
    editor=editor,
    content_hash=content_hash,
    toc=toc_data,
    files=files_metadata if files_metadata else None
)

# Use helper method to set markdown_path (extracts filename)
work.set_markdown_path(str(markdown_path))
```

**Alternative approach** (simpler, recommended):
Since we're already storing just filenames in `files_metadata` (change #2), we can directly assign to `markdown_path` in constructor:

```python
work = Work(
    title=title,
    markdown_path=markdown_path.name,  # Just filename
    authors=authors,
    ...
    files=files_metadata if files_metadata else None
)
```

**Recommendation:** Use the simpler approach (direct `markdown_path.name` assignment) since:
- It's clearer and more concise
- Helper method `set_markdown_path()` is more useful when receiving full paths from external sources
- In this module, we control the path construction and can directly extract filename

#### Complete updated function structure:

```python
def create_new_work(
    # ... parameters unchanged ...
):
    # ... validation unchanged (lines 66-99) ...

    # Compute content hash - still uses full path
    content_hash = compute_file_hash(markdown_path)

    # Discover and track all related files with their hashes
    files_metadata = {}
    stem = markdown_path.stem

    # Define file discovery rules - unchanged
    file_specs = [
        ("original_file", [".pdf", ".epub", ".html"]),
        ("hier_markdown", [".hier.md"]),
        ("style_markdown", [".style.md"]),
        ("original_markdown", [".md"]),
        ("toc_titles", [".toc_titles.md"]),
        ("titles", [".titles.md"]),
        ("san_mapping", [".san_mapping.csv"]),
        ("sanitized", [".sanitized.md"]),
        ("sanitized_titles", [".sanitized.titles.md"]),
        ("vec_suggestions", [".sanitized.vec_sugg.md"]),
    ]

    # Discover files
    for field_name, extensions in file_specs:
        for ext in extensions:
            file_path = markdown_path.parent / f"{stem}{ext}"
            if file_path.exists() and file_path.is_file():
                # Compute hash using full path
                file_hash = compute_file_hash(file_path)
                # Store ONLY filename, not full path
                files_metadata[field_name] = {
                    "path": file_path.name,  # CHANGED: was str(file_path.resolve())
                    "hash": file_hash
                }
                break  # Use first match for this field

    # TOC parsing unchanged (lines 135-149)
    # ...

    # Duplicate check unchanged (lines 151-162)
    # ...

    # Create the work
    work = Work(
        title=title,
        markdown_path=markdown_path.name,  # CHANGED: was str(markdown_path)
        authors=authors,
        year=year,
        publisher=publisher,
        isbn=isbn,
        edition=edition,
        volume=volume,
        issue=issue,
        pages=pages,
        url=url,
        city=city,
        institution=institution,
        editor=editor,
        content_hash=content_hash,
        toc=toc_data,
        files=files_metadata if files_metadata else None
    )

    # Database insertion unchanged (lines 186-191)
    # ...

    return work
```

### Frontend
Not applicable - backend-only ticket.

### Other / cross-cutting

- **Backward compatibility:** This change is NOT backward compatible with code that expects `markdown_path` or `files[*]["path"]` to contain absolute paths. Ensure T03-T06 (all code updates) are deployed together.
- **Testing implications:** Existing tests that assert on full paths will need updates to expect filenames only.

## Unit tests

**Test file:** `tests/unit/test_new_work.py` (likely exists - update existing tests)

### New test cases to add:

1. **test_create_new_work_stores_filename_only_markdown_path**
   - Create temp directory with `test.md` file
   - Call `create_new_work(title="Test", markdown_path=Path("/tmp/test.md"))`
   - Assert `work.markdown_path == "test.md"` (not full path)

2. **test_create_new_work_stores_filename_only_in_files_metadata**
   - Create temp directory with `test.md`, `test.sanitized.md`, `test.pdf`
   - Call `create_new_work(...)`
   - Assert `work.files["original_file"]["path"] == "test.pdf"`
   - Assert `work.files["sanitized"]["path"] == "test.sanitized.md"`
   - Ensure NO full paths stored

3. **test_create_new_work_preserves_hashes**
   - Create temp files
   - Call `create_new_work(...)`
   - Assert `work.files[*]["hash"]` values present and non-empty
   - Hash computation should still work (uses full path during discovery)

4. **test_file_discovery_still_works_with_absolute_paths**
   - Create files in various locations
   - Call `create_new_work(...)` with absolute Path
   - Assert files discovered correctly
   - Assert stored paths are filenames only

### Existing tests to update:

Review existing tests in `tests/unit/test_new_work.py` (if it exists):
- Update assertions that check `work.markdown_path` to expect filename only
- Update assertions that check `work.files[*]["path"]` to expect filenames only
- Ensure tests still validate file discovery logic (existence checks, hash computation)

### Integration test:

5. **test_create_new_work_integration_with_path_resolver**
   - Create new work using `create_new_work()`
   - Use PathResolver to resolve stored paths back to absolute
   - Assert resolved paths point to correct files
   - This validates the full workflow: store filenames → resolve to absolute

## Dependencies and sequencing

### Dependencies:
- **T01 (required):** Work model helper methods must exist (though we're not using them in the simpler approach)
- PathResolver utility for integration testing

### Related tickets:
- **T04-T06:** Must deploy together - all code expecting absolute paths needs updating simultaneously

### Rollout notes:
- This ticket can be developed/tested independently after T01 is complete
- Must deploy with T04-T06 to avoid breaking existing code
- Database migration (T02) should run AFTER all code is deployed

## Manual test plan

**Prerequisites:**
- T01 completed and merged
- Test environment with sample files (PDF, markdown, etc.)

**Test steps:**

1. **Create new work with files:**
   ```python
   from vulcanlab.conversions.new_work import create_new_work
   from pathlib import Path

   # Prepare test files in /tmp/test_data/
   # Files: book.pdf, book.md, book.sanitized.md

   work = create_new_work(
       title="Test Book",
       markdown_path=Path("/tmp/test_data/book.md"),
       authors="Test Author",
       year=2025
   )
   ```

2. **Verify stored paths are filenames only:**
   ```python
   print(work.markdown_path)  # Should be "book.md", not "/tmp/test_data/book.md"
   print(work.files)  # Should show:
   # {
   #   "original_file": {"path": "book.pdf", "hash": "..."},
   #   "original_markdown": {"path": "book.md", "hash": "..."},
   #   "sanitized": {"path": "book.sanitized.md", "hash": "..."}
   # }
   ```

3. **Verify database storage:**
   ```sql
   SELECT id, markdown_path, files FROM works WHERE id = [work.id];
   ```
   - Confirm `markdown_path` contains filename only
   - Confirm `files` JSON contains filenames in `path` keys

4. **Verify path resolution works:**
   ```python
   from vulcanlab.utils.file_utils import get_path_resolver

   resolver = get_path_resolver()
   markdown_abs_path = resolver.resolve_work_path(work)
   print(markdown_abs_path)  # Should be Path("/home/.../output/book.md")

   sanitized_abs_path = resolver.resolve_work_path(work, "sanitized")
   print(sanitized_abs_path)  # Should be Path("/home/.../output/book.sanitized.md")
   ```

5. **Verify file discovery still works:**
   - Create files with various extensions
   - Call `create_new_work()`
   - Verify all expected files discovered and tracked in `work.files`
   - Verify hashes computed correctly

6. **Edge cases:**
   - Test with files in deeply nested directories
   - Test with files containing spaces or special characters
   - Test when optional files missing (e.g., no `.sanitized.md`)
   - Verify `work.files` still correct in each case

## Clarifications and assumptions

### Assumptions:
1. **Simpler approach preferred:** Using direct `markdown_path.name` assignment instead of `set_markdown_path()` helper since we control path construction in this module
2. **File discovery unchanged:** File existence checks and hash computation continue using absolute paths (only storage changes to filenames)
3. **No subdirectories:** Files are assumed to be in same directory as `markdown_path` (existing behavior)
4. **Hash computation:** Still uses full absolute paths (unchanged), only storage format changes
5. **Test file location:** Assuming unit tests exist at `tests/unit/test_new_work.py` - create if doesn't exist

### Open questions (non-blocking):
1. Should the module log or warn when storing filenames instead of absolute paths?
   - *Current assumption:* No, this is expected behavior after refactoring
2. Should we add a module-level constant or config flag to control path storage format?
   - *Current assumption:* No, always store filenames (no configuration needed)

### Blocking questions:
None - implementation approach is clear.

### Before implementing:
Review this ticket and confirm the "simpler approach" (direct `.name` assignment) is acceptable. If there are concerns about consistency with other modules that might use `set_markdown_path()`, we can switch to the helper method approach instead.

Ensure existing tests are identified and updated to expect filenames instead of absolute paths.
