# T05: Update chunking modules to use PathResolver

## Context

- **PRD:** [PRD.work-model-relative-paths.md](PRD.work-model-relative-paths.md)
- **PRD Section:** Section 5.1 FR3 (Update All Code References) - Chunking modules
- **Business Value:** Chunking modules now use PathResolver for all file operations, completing the path portability refactoring for the core processing pipeline.

## Outcome

All 5 chunking modules are updated to use PathResolver for resolving Work model paths. 31 code locations across chunking modules now correctly resolve filenames to absolute paths using `resolver.resolve_work_path()`. Chunking pipeline (content chunks, heading chunks, vector suggestions) works correctly with filename-only storage.

## Scope

### In scope:
- Update 5 chunking modules to use PathResolver:
  1. **content_chunking.py** (2 locations)
  2. **suggested_chunks.py** (14 locations)
  3. **chunk_headings.py** (4 locations)
  4. **vec_suggestions_interactive.py** (6 locations)
  5. **suggested_chunks_cli.py** (1 location)
- Replace all `Path(work.files[key]["path"])` with `resolver.resolve_work_path(work, key)`
- Update path storage to use direct filename assignment (`.name`)
- Ensure all chunking operations continue working correctly

### Out of scope:
- Changes to chunking business logic or algorithms
- Changes to chunk model or database schema
- Modifications to vectorization logic

## Implementation plan

### Backend

#### General Pattern (Same as T04)

**1. Add import:**
```python
from vulcanlab.utils.file_utils import get_path_resolver
```

**2. Initialize resolver:**
```python
resolver = get_path_resolver()  # Module-level
```

**3. Replace path reads:**
```python
# OLD:
sanitized_path = Path(work.files["sanitized"]["path"])

# NEW:
sanitized_path = resolver.resolve_work_path(work, "sanitized")
```

**4. Replace path writes:**
```python
# OLD:
updated_files["vec_suggestions"] = {
    "path": str(output_path.absolute()),
    "hash": hash_value
}

# NEW:
updated_files["vec_suggestions"] = {
    "path": output_path.name,
    "hash": hash_value
}
```

---

#### Module-by-Module Changes

### 1. File: `src/vulcanlab/chunking/content_chunking.py` (2 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Lines 674-675 - In `process_content_chunks_from_work()`:**
```python
# OLD:
sanitized_info = work.files["sanitized"]
sanitized_path = Path(sanitized_info["path"])

# NEW:
sanitized_path = resolver.resolve_work_path(work, "sanitized")
```

Note: This module appears to only read paths for chunking, not write them. Verify no path writes need updating.

---

### 2. File: `src/vulcanlab/chunking/suggested_chunks.py` (14 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Lines 420-421, 580-581, 687-688 - Reading sanitized paths:**
```python
# OLD:
sanitized_info = work.files["sanitized"]
sanitized_path = Path(sanitized_info["path"])

# NEW:
sanitized_path = resolver.resolve_work_path(work, "sanitized")
```

**Lines 447-448, 714-715 - Reading sanitized_titles:**
```python
# OLD:
titles_info = work.files["sanitized_titles"]
titles_path = Path(titles_info["path"])

# NEW:
titles_path = resolver.resolve_work_path(work, "sanitized_titles")
```

**Lines 631-636 - Writing vec_suggestions:**
```python
# OLD:
updated_files = dict(work.files) if work.files else {}
updated_files["vec_suggestions"] = {
    "path": str(output_path.absolute()),
    "hash": output_hash
}
work.files = updated_files

# NEW:
updated_files = dict(work.files) if work.files else {}
updated_files["vec_suggestions"] = {
    "path": output_path.name,
    "hash": output_hash
}
work.files = updated_files
```

**Lines 870-875 - Writing vec_suggestions (another function):**
```python
# OLD:
updated_files = dict(work.files) if work.files else {}
# ... (update vec_suggestions)
work.files = updated_files

# NEW:
updated_files = dict(work.files) if work.files else {}
updated_files["vec_suggestions"] = {
    "path": output_path.name,
    "hash": output_hash
}
work.files = updated_files
```

---

### 3. File: `src/vulcanlab/chunking/chunk_headings.py` (4 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Lines 153-154 - In `process_heading_chunks_from_work()`:**
```python
# OLD:
sanitized_info = work.files["sanitized"]
sanitized_path = Path(sanitized_info["path"])

# NEW:
sanitized_path = resolver.resolve_work_path(work, "sanitized")
```

**Lines 164-165 - Reading vec_suggestions:**
```python
# OLD:
vec_suggestions_info = work.files["vec_suggestions"]
vec_suggestions_path = Path(vec_suggestions_info["path"])

# NEW:
vec_suggestions_path = resolver.resolve_work_path(work, "vec_suggestions")
```

---

### 4. File: `src/vulcanlab/chunking/vec_suggestions_interactive.py` (6 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Lines 164-165 - Reading sanitized:**
```python
# OLD:
sanitized_info = work.files["sanitized"]
sanitized_path = Path(sanitized_info["path"])

# NEW:
sanitized_path = resolver.resolve_work_path(work, "sanitized")
```

**Lines 193-194 - Reading vec_suggestions:**
```python
# OLD:
vec_sugg_info = work.files["vec_suggestions"]
vec_sugg_path = Path(vec_sugg_info["path"])

# NEW:
vec_sugg_path = resolver.resolve_work_path(work, "vec_suggestions")
```

**Line 210 - Reading hash (no change needed, but document):**
```python
# This line reads hash, not path - no change needed
vec_sugg_hash = work.files["vec_suggestions"]["hash"]
```

**Lines 260-262 - Reading vec_suggestions (another location):**
```python
# OLD:
vec_sugg_info = work.files["vec_suggestions"]
vec_sugg_path = Path(vec_sugg_info["path"])

# NEW:
vec_sugg_path = resolver.resolve_work_path(work, "vec_suggestions")
```

---

### 5. File: `src/vulcanlab/chunking/suggested_chunks_cli.py` (1 location)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Line 105 - Reading sanitized path:**
```python
# OLD:
sanitized_path = work.files["sanitized"]["path"]

# NEW:
sanitized_path = resolver.resolve_work_path(work, "sanitized")
```

Note: Verify if this returns a Path object or string. If the rest of the code expects a string, use `str(resolver.resolve_work_path(...))`.

---

### Testing Strategy

For each module:
1. Ensure existing unit tests pass
2. Add tests verifying path resolution with filenames
3. Test chunking pipeline end-to-end with filename-only Work records

### Frontend
Not applicable - backend-only ticket.

### Other / cross-cutting

- **Chunk model:** No changes to Chunk model (stores work_id foreign key, not paths)
- **Vectorization:** No changes to vectorization logic (operates on chunk content, not file paths)
- **Performance:** Minimal impact from path resolution

## Unit tests

**Test files:**
- `tests/unit/test_content_chunking.py`
- `tests/unit/test_suggested_chunks.py`
- `tests/unit/test_chunk_headings.py`
- `tests/unit/test_vec_suggestions_interactive.py`
- `tests/unit/test_suggested_chunks_cli.py`

### Common test patterns:

1. **test_[module]_resolves_sanitized_path**
   - Create Work with `files = {"sanitized": {"path": "test.sanitized.md"}}`
   - Configure PathResolver with test output_dir
   - Call chunking function
   - Assert function reads from correct absolute path

2. **test_[module]_resolves_vec_suggestions_path**
   - Create Work with `files = {"vec_suggestions": {"path": "test.vec_sugg.md"}}`
   - Call chunking function
   - Assert function reads from correct absolute path

3. **test_[module]_stores_filename_only**
   - Call function that creates vec_suggestions file
   - Assert `work.files["vec_suggestions"]["path"]` is filename only

### Module-specific test cases:

**content_chunking.py:**
4. **test_process_content_chunks_from_work_resolves_path**
   - Verify content chunking reads sanitized file via resolver
5. **test_content_chunks_created_correctly**
   - Verify chunks created with correct content
   - Verify work_id foreign key set correctly

**suggested_chunks.py:**
6. **test_suggest_chunks_reads_sanitized_and_titles**
   - Verify function resolves both "sanitized" and "sanitized_titles"
7. **test_suggest_chunks_writes_vec_suggestions_filename**
   - Verify vec_suggestions path stored as filename only

**chunk_headings.py:**
8. **test_process_heading_chunks_reads_both_files**
   - Verify function resolves "sanitized" and "vec_suggestions"
9. **test_heading_chunks_created_correctly**
   - Verify heading chunks extracted correctly

**vec_suggestions_interactive.py:**
10. **test_interactive_resolves_paths**
    - Verify interactive UI resolves paths for display/editing

**suggested_chunks_cli.py:**
11. **test_cli_resolves_sanitized_path**
    - Verify CLI tool resolves path correctly

### Integration tests:

12. **test_chunking_pipeline_end_to_end**
    - Create Work with sanitized file (filename only in DB)
    - Run suggest_chunks_from_work()
    - Run process_heading_chunks_from_work()
    - Verify all chunks created correctly
    - Verify vec_suggestions stored as filename only
    - Verify all file operations succeeded

13. **test_chunking_with_missing_file**
    - Create Work with filename that doesn't exist in output_dir
    - Attempt chunking
    - Verify appropriate error (FileNotFoundError or similar)

## Dependencies and sequencing

### Dependencies:
- **T01 (required):** PathResolver must exist
- **T03, T04 (recommended):** Conversion and sanitization updated first

### Related tickets:
- **T06:** Deploy together with API updates

### Rollout notes:
- Test chunking pipeline thoroughly with filename-only Work records
- Ensure existing chunks (from pre-migration works) still accessible
- Deploy with T03, T04, T06 as a unit

## Manual test plan

**Prerequisites:**
- T01, T03, T04 completed
- Test Work record with sanitized markdown file
- Files in configured output_dir

**Test steps:**

1. **Setup test data:**
   ```python
   # Create Work with filenames only
   work.files = {
       "sanitized": {"path": "test.sanitized.md", "hash": "abc123"},
       "sanitized_titles": {"path": "test.sanitized.titles.md", "hash": "def456"}
   }
   # Place files in output_dir
   ```

2. **Test content chunking:**
   ```python
   from vulcanlab.chunking.content_chunking import process_content_chunks_from_work

   process_content_chunks_from_work(work)
   # Verify chunks created in database
   # Check: SELECT * FROM chunks WHERE work_id = [work.id]
   ```

3. **Test suggested chunks:**
   ```python
   from vulcanlab.chunking.suggested_chunks import suggest_chunks_from_work

   suggest_chunks_from_work(work)
   # Verify work.files["vec_suggestions"] created
   # Assert path is filename only: "test.sanitized.vec_sugg.md"
   # Verify file exists in output_dir
   ```

4. **Test heading chunks:**
   ```python
   from vulcanlab.chunking.chunk_headings import process_heading_chunks_from_work

   process_heading_chunks_from_work(work)
   # Verify heading chunks created
   # Check database for heading-type chunks
   ```

5. **Test interactive tools:**
   ```python
   from vulcanlab.chunking.vec_suggestions_interactive import [interactive_function]

   # Run interactive tool
   # Verify it displays/edits vec_suggestions file correctly
   ```

6. **Test CLI:**
   ```bash
   # Run suggested_chunks_cli with work_id
   python -m vulcanlab.chunking.suggested_chunks_cli --work-id [work.id]
   # Verify output shows correct file paths
   ```

7. **End-to-end pipeline test:**
   - Start with new markdown file
   - Run conversion (T03) → creates Work with filenames
   - Run sanitization (T04) → creates sanitized file, stores filename
   - Run chunking (T05) → reads sanitized, creates chunks, stores vec_suggestions filename
   - Verify all files in output_dir
   - Verify all DB paths are filenames only
   - Verify chunks created correctly

8. **Error handling:**
   - Create Work with filename that doesn't exist
   - Attempt chunking
   - Verify `FileNotFoundError` or clear error message

## Clarifications and assumptions

### Assumptions:
1. **Module-level resolver:** Using `resolver = get_path_resolver()` at module level
2. **Direct .name assignment:** Using `path.name` for storing filenames
3. **Chunk model unchanged:** Chunks reference work_id, not file paths directly
4. **File existence checks:** Existing code handles missing files appropriately
5. **CLI output:** If CLI displays paths, showing filenames is acceptable (or can construct absolute paths for display)

### Open questions (non-blocking):
1. Should CLI tools display absolute paths for user convenience?
   - *Current assumption:* Filenames are acceptable, but could add optional `--show-full-paths` flag
2. Should interactive tools resolve paths for display?
   - *Current assumption:* Yes, use resolver to show full paths in UI if helpful

### Blocking questions:
None - implementation is straightforward.

### Before implementing:
1. Review each module to confirm all path read/write locations identified
2. Test chunking pipeline with both migrated (filename) and pre-migration (absolute path) Work records during transition
3. Ensure chunk creation/deletion logic unaffected by path changes
4. Verify vectorization still works with new path handling

This ticket has 31 locations but follows a consistent pattern. Consider pairing with T04 review to ensure consistency across sanitization and chunking modules.
