# T04: Update sanitization modules to use PathResolver

## Context

- **PRD:** [PRD.work-model-relative-paths.md](PRD.work-model-relative-paths.md)
- **PRD Section:** Section 5.1 FR3 (Update All Code References) - Sanitization modules
- **Business Value:** Sanitization modules now use PathResolver for all file operations, supporting environment-portable path management.

## Outcome

All 6 sanitization modules are updated to use PathResolver for resolving Work model paths. 27 code locations across sanitization modules now correctly resolve filenames to absolute paths using `resolver.resolve_work_path()`. All existing functionality works unchanged, with paths properly resolved at runtime.

## Scope

### In scope:
- Update 6 sanitization modules to use PathResolver:
  1. **apply_title_changes.py** (11 locations)
  2. **extract_titles.py** (3 locations)
  3. **suggest_heading_changes.py** (4 locations)
  4. **skip_apply.py** (2 locations)
  5. **update_content_hash.py** (3 locations)
  6. **title_changes_interactive.py** (4 locations)
- Replace all `Path(work.markdown_path)` with `resolver.resolve_work_path(work)`
- Replace all `Path(work.files[key]["path"])` with `resolver.resolve_work_path(work, key)`
- Update path storage to use Work model helper methods or direct filename assignment
- Ensure all file I/O operations continue working correctly

### Out of scope:
- Changes to sanitization business logic
- Changes to file format or content processing
- Modifications to non-path-related code

## Implementation plan

### Backend

#### General Pattern for All Modules

**1. Add import at top of each file:**
```python
from vulcanlab.utils.file_utils import get_path_resolver
```

**2. Initialize resolver (module level or in functions):**
```python
# Option A: Module-level (recommended for modules with multiple functions)
resolver = get_path_resolver()

# Option B: In each function (if module has single entry point)
def some_function():
    resolver = get_path_resolver()
    # ...
```

**3. Replace path reads:**
```python
# OLD:
markdown_path = Path(work.markdown_path)
sanitized_path = Path(work.files["sanitized"]["path"])

# NEW:
markdown_path = resolver.resolve_work_path(work)
sanitized_path = resolver.resolve_work_path(work, "sanitized")
```

**4. Replace path writes:**
```python
# OLD:
work.markdown_path = str(sanitized_path.absolute())
updated_files["sanitized"] = {"path": str(output_path.absolute()), "hash": hash_value}

# NEW:
work.markdown_path = sanitized_path.name  # Or use work.set_markdown_path(str(sanitized_path))
updated_files["sanitized"] = {"path": output_path.name, "hash": hash_value}
```

---

#### Module-by-Module Changes

### 1. File: `src/vulcanlab/sanitization/apply_title_changes.py` (11 locations)

**Add import and initialize resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()  # Module-level
```

**Line 111, 114 - In `preview_title_changes()`:**
```python
# OLD:
markdown_path = Path(work.markdown_path)

# NEW:
markdown_path = resolver.resolve_work_path(work)
```

**Line 186, 189 - In `apply_title_changes()`:**
```python
# OLD:
markdown_path = Path(work.markdown_path)

# NEW:
markdown_path = resolver.resolve_work_path(work)
```

**Line 241 - Setting markdown_path:**
```python
# OLD:
work.markdown_path = str(sanitized_path.absolute())

# NEW:
work.markdown_path = sanitized_path.name
```

**Lines 279, 300-308, 311-312, 315-316 - In `apply_title_changes_from_work()`:**

Reading files:
```python
# OLD:
markdown_info = work.files[markdown_key]
markdown_path = Path(markdown_info["path"])

title_changes_info = work.files[title_changes_key]
title_changes_path = Path(title_changes_info["path"])

# NEW:
markdown_path = resolver.resolve_work_path(work, markdown_key)
title_changes_path = resolver.resolve_work_path(work, title_changes_key)
```

**Line 436, 441 - Updating files:**
```python
# OLD:
updated_files[sanitized_key] = {
    "path": str(sanitized_path.absolute()),
    "hash": sanitized_hash
}
work.files = updated_files

# NEW:
updated_files[sanitized_key] = {
    "path": sanitized_path.name,
    "hash": sanitized_hash
}
work.files = updated_files
```

---

### 2. File: `src/vulcanlab/sanitization/extract_titles.py` (3 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Lines 305-310 - In `extract_titles_from_work()`:**
```python
# OLD:
updated_files = dict(work.files) if work.files else {}
updated_files[output_key] = {
    "path": str(output_path.absolute()),
    "hash": output_hash
}
work.files = updated_files

# NEW:
updated_files = dict(work.files) if work.files else {}
updated_files[output_key] = {
    "path": output_path.name,
    "hash": output_hash
}
work.files = updated_files
```

Note: This module appears to only write paths, not read them. Verify by checking if there are any `Path(work.files[...]["path"])` reads that need updating.

---

### 3. File: `src/vulcanlab/sanitization/suggest_heading_changes.py` (4 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Lines 677-682, 907-912 - Updating files:**
```python
# OLD:
updated_files = dict(work.files) if work.files else {}
updated_files[output_key] = {
    "path": str(output_path.absolute()),
    "hash": output_hash
}
work.files = updated_files

# NEW:
updated_files = dict(work.files) if work.files else {}
updated_files[output_key] = {
    "path": output_path.name,
    "hash": output_hash
}
work.files = updated_files
```

---

### 4. File: `src/vulcanlab/sanitization/skip_apply.py` (2 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Lines 151-156 - In `skip_apply_from_work()`:**
```python
# OLD:
updated_files = dict(work.files) if work.files else {}
# ... (modify updated_files)
work.files = updated_files

# NEW:
# If this module reads paths from work.files, add resolver.resolve_work_path() calls
# If it only updates metadata (no path reads), no changes beyond ensuring writes use .name
updated_files = dict(work.files) if work.files else {}
# ... (ensure any path writes use .name)
work.files = updated_files
```

Note: Review this module to determine if it reads paths for file operations. If yes, add path resolution.

---

### 5. File: `src/vulcanlab/sanitization/update_content_hash.py` (3 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Lines 287, 290 - In `update_content_hash_from_work()`:**
```python
# OLD:
markdown_path = Path(work.markdown_path)

# NEW:
markdown_path = resolver.resolve_work_path(work)
```

**Lines 242-247 - Updating files:**
```python
# OLD:
updated_files = dict(work.files) if work.files else {}
# ... (modify updated_files)
work.files = updated_files

# NEW:
updated_files = dict(work.files) if work.files else {}
# ... (ensure any path writes use .name)
work.files = updated_files
```

---

### 6. File: `src/vulcanlab/sanitization/title_changes_interactive.py` (4 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Lines 158-159 - Reading markdown:**
```python
# OLD:
markdown_info = work.files[source_key]
markdown_path = Path(markdown_info["path"])

# NEW:
markdown_path = resolver.resolve_work_path(work, source_key)
```

**Lines 187-188 - Reading title changes:**
```python
# OLD:
title_changes_info = work.files[title_changes_key]
title_changes_path = Path(title_changes_info["path"])

# NEW:
title_changes_path = resolver.resolve_work_path(work, title_changes_key)
```

---

### Testing Strategy

For each module:
1. Ensure existing unit tests continue to pass
2. Add integration tests that verify path resolution works correctly
3. Mock or use test config with known input_dir/output_dir paths

### Frontend
Not applicable - backend-only ticket.

### Other / cross-cutting

- **Config dependency:** All modules now depend on `vulcanlab.config.json` being properly configured
- **Error handling:** PathResolver will throw `InvalidFilePathError` if paths are NULL - existing code should handle gracefully or let exception propagate
- **Performance:** Minimal impact - config loaded once and cached

## Unit tests

**Test files:** Update existing test files for each module, or create new ones:
- `tests/unit/test_apply_title_changes.py`
- `tests/unit/test_extract_titles.py`
- `tests/unit/test_suggest_heading_changes.py`
- `tests/unit/test_skip_apply.py`
- `tests/unit/test_update_content_hash.py`
- `tests/unit/test_title_changes_interactive.py`

### Common test patterns for all modules:

1. **test_[module]_resolves_paths_correctly**
   - Create Work with filenames in `markdown_path` and `files[*]["path"]`
   - Mock or configure PathResolver with test directories
   - Call module function
   - Assert function received correct absolute paths

2. **test_[module]_stores_filenames_only**
   - Call module function that updates Work paths
   - Assert `work.markdown_path` contains filename only (no separators)
   - Assert `work.files[*]["path"]` contains filenames only

3. **test_[module]_preserves_hashes**
   - Call module function that updates files
   - Assert hash values preserved or updated correctly
   - Ensure hash computation still works

### Module-specific test cases:

**apply_title_changes.py:**
4. **test_preview_title_changes_resolves_markdown_path**
   - Verify `preview_title_changes()` uses resolver for markdown_path
5. **test_apply_title_changes_from_work_resolves_multiple_keys**
   - Verify function resolves both `markdown_key` and `title_changes_key`
6. **test_apply_title_changes_stores_sanitized_filename**
   - Verify sanitized path stored as filename only

**extract_titles.py:**
7. **test_extract_titles_from_work_stores_filename**
   - Verify output path stored as filename only

**suggest_heading_changes.py:**
8. **test_suggest_heading_changes_stores_filename**
   - Verify output path stored as filename only

**update_content_hash.py:**
9. **test_update_content_hash_resolves_markdown_path**
   - Verify function resolves markdown_path correctly for hash computation

**title_changes_interactive.py:**
10. **test_interactive_resolves_source_and_changes_paths**
    - Verify both source and title changes paths resolved

### Integration tests:

11. **test_sanitization_pipeline_end_to_end**
    - Create Work with filenames
    - Run through sanitization pipeline (extract → suggest → apply)
    - Verify all intermediate files created correctly
    - Verify all paths stored as filenames
    - Verify path resolution works at each stage

## Dependencies and sequencing

### Dependencies:
- **T01 (required):** PathResolver must be implemented
- **T03 (recommended):** Conversion module updated first for consistency

### Related tickets:
- **T05-T06:** Must deploy together with all code updates

### Rollout notes:
- Develop after T01 is complete
- Test thoroughly with both existing (absolute paths) and new (filename) data
- Deploy together with T03, T05, T06 to avoid inconsistent path handling

## Manual test plan

**Prerequisites:**
- T01 completed
- Test database with Work records
- Sample markdown files in configured output_dir

**Test steps for each module:**

1. **Setup test data:**
   - Create Work record with filenames: `markdown_path = "test.md"`, `files = {"sanitized": {"path": "test.sanitized.md"}}`
   - Place actual files in output_dir: `test.md`, `test.sanitized.md`

2. **Test apply_title_changes.py:**
   ```python
   from vulcanlab.sanitization.apply_title_changes import preview_title_changes, apply_title_changes_from_work

   # Test preview
   result = preview_title_changes(work)
   # Verify no errors, markdown_path resolved correctly

   # Test apply
   apply_title_changes_from_work(work, title_changes_key="titles")
   # Verify work.files updated with filename only
   ```

3. **Test extract_titles.py:**
   ```python
   from vulcanlab.sanitization.extract_titles import extract_titles_from_work

   extract_titles_from_work(work)
   # Verify work.files["titles"]["path"] is filename only
   ```

4. **Test suggest_heading_changes.py:**
   ```python
   from vulcanlab.sanitization.suggest_heading_changes import suggest_heading_changes

   suggest_heading_changes(work, ...)
   # Verify output path stored as filename
   ```

5. **Test update_content_hash.py:**
   ```python
   from vulcanlab.sanitization.update_content_hash import update_content_hash_from_work

   update_content_hash_from_work(work)
   # Verify markdown_path resolved for hash computation
   ```

6. **Test title_changes_interactive.py:**
   ```python
   from vulcanlab.sanitization.title_changes_interactive import [interactive_function]

   # Run interactive function
   # Verify paths resolved correctly from filenames
   ```

7. **End-to-end test:**
   - Run full sanitization pipeline on a real document
   - Verify all intermediate files created
   - Check database: all paths should be filenames only
   - Verify no errors in path resolution

8. **Error handling:**
   - Create Work with NULL markdown_path
   - Attempt to run sanitization function
   - Verify `InvalidFilePathError` raised with clear message

## Clarifications and assumptions

### Assumptions:
1. **Module-level resolver:** Using module-level `resolver = get_path_resolver()` for efficiency (called once per module import)
2. **Direct .name assignment:** Using `path.name` for storing filenames (consistent with T03)
3. **Existing tests:** Assuming unit tests exist for these modules and need updates
4. **File I/O unchanged:** File reading/writing logic unchanged, only path resolution updated
5. **Error propagation:** Letting `InvalidFilePathError` propagate to caller (existing error handling should suffice)

### Open questions (non-blocking):
1. Should sanitization modules validate that resolved paths exist before processing?
   - *Current assumption:* No, existing code already handles missing files
2. Should we add logging when paths are resolved (for debugging)?
   - *Current assumption:* No, PathResolver can add debug logging if needed

### Blocking questions:
None - implementation approach is clear.

### Before implementing:
1. Review each module to identify ALL path read/write locations (PRD provides line numbers, but verify they're comprehensive)
2. Ensure test coverage exists for each module - if not, create basic tests first
3. Consider using a feature flag to toggle between old (absolute) and new (filename) path handling during rollout, if gradual migration is needed
4. Test with both migrated (filename-only) and legacy (absolute path) Work records to ensure compatibility during transition period

This is the largest ticket (27 locations) - consider breaking into smaller chunks if needed, e.g.:
- T04a: apply_title_changes.py + extract_titles.py (14 locations)
- T04b: suggest_heading_changes.py + skip_apply.py (6 locations)
- T04c: update_content_hash.py + title_changes_interactive.py (7 locations)
