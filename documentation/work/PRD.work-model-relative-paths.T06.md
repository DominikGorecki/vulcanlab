COMPLETE

# T06: Update augmentation, retrieval, and API modules to use PathResolver

## Context

- **PRD:** [PRD.work-model-relative-paths.md](PRD.work-model-relative-paths.md)
- **PRD Section:** Section 5.1 FR3 (Update All Code References) - Augmentation, Retrieval, and API modules
- **Business Value:** Completes the path portability refactoring by updating all remaining modules (augmentation, retrieval) and API endpoints, ensuring the entire application stack works with filename-only storage.

## Outcome

All remaining modules and API routers are updated to use PathResolver. 44 code locations across augmentation (4), retrieval (2), and API routers (38) now correctly resolve filenames to absolute paths. All API endpoints return and accept filenames (not absolute paths), with internal resolution handled transparently.

## Scope

### In scope:
- Update augmentation module: **consolidate_context.py** (4 locations)
- Update retrieval module: **retrieve.py** (2 locations)
- Update 3 API router modules:
  - **chunking.py** (16 locations)
  - **sanitization.py** (18 locations)
  - **corpus.py** (4 locations)
- Replace all `Path(work.markdown_path)` and `Path(work.files[key]["path"])` with resolver calls
- Ensure API responses include filenames (not absolute paths)
- Ensure API request handlers accept filenames and resolve them internally

### Out of scope:
- Changes to API contracts or response schemas (filenames in responses is acceptable per requirements)
- Changes to authentication or authorization logic
- Modifications to frontend/client code (separate concern)

## Implementation plan

### Backend

#### General Pattern (Consistent with T04, T05)

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
updated_files["key"] = {"path": str(path.absolute()), "hash": hash_val}

# NEW:
updated_files["key"] = {"path": path.name, "hash": hash_val}
```

---

#### Module-by-Module Changes

### 1. File: `src/vulcanlab/augmentation/consolidate_context.py` (4 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Lines 352-354 - In `consolidate_context_for_query()` (first occurrence):**
```python
# OLD:
if work.files and "sanitized" in work.files:
    sanitized_info = work.files["sanitized"]
    sanitized_path = Path(sanitized_info["path"])

# NEW:
if work.files and "sanitized" in work.files:
    sanitized_path = resolver.resolve_work_path(work, "sanitized")
```

**Lines 439-440 - (second occurrence):**
```python
# OLD:
if work.files and "sanitized" in work.files:
    sanitized_info = work.files["sanitized"]

# NEW:
if work.files and "sanitized" in work.files:
    sanitized_path = resolver.resolve_work_path(work, "sanitized")
```

Note: Verify line 440 usage - ensure the resolved path is used for file operations.

---

### 2. File: `src/vulcanlab/retrieval/retrieve.py` (2 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Lines 274-277 - In `enrich_chunk_context()`:**
```python
# OLD:
markdown_path = Path(work.markdown_path)

# NEW:
markdown_path = resolver.resolve_work_path(work)
```

---

### 3. File: `src/vulcanlab_api/routers/chunking.py` (16 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Pattern:** This router has multiple endpoint handlers. Apply these changes consistently:

**Lines 58-62 - In `_get_file_status()` helper:**
```python
# OLD:
if work.files and file_key in work.files:
    file_info = work.files[file_key]
    file_path = Path(file_info["path"])

# NEW:
if work.files and file_key in work.files:
    file_path = resolver.resolve_work_path(work, file_key)
```

**Lines 182-183, 227-228 - Reading sanitized:**
```python
# OLD:
file_info = work.files["sanitized"]
file_path = Path(file_info["path"])

# NEW:
file_path = resolver.resolve_work_path(work, "sanitized")
```

**Lines 250-255 - Updating files:**
```python
# OLD:
updated_files = dict(work.files)
updated_files[file_key] = {"path": str(new_path), ...}
work.files = updated_files

# NEW:
updated_files = dict(work.files)
updated_files[file_key] = {"path": new_path.name, ...}
work.files = updated_files
```

**Lines 341-342, 386-387 - Reading sanitized_titles:**
```python
# OLD:
file_info = work.files["sanitized_titles"]
file_path = Path(file_info["path"])

# NEW:
file_path = resolver.resolve_work_path(work, "sanitized_titles")
```

**Lines 409-414 - Updating files (similar pattern):**
```python
# Use path.name for storing
```

**Lines 676, 685, 698, 703, 787-788, 817 - Reading/updating vec_suggestions:**
```python
# Apply same pattern: resolver.resolve_work_path(work, "vec_suggestions")
# Store as path.name when updating
```

---

### 4. File: `src/vulcanlab_api/routers/sanitization.py` (18 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Lines 85-86 - In `_get_file_status()` helper:**
```python
# OLD:
file_info = work.files[file_key]
file_path = Path(file_info["path"])

# NEW:
file_path = resolver.resolve_work_path(work, file_key)
```

**Lines 579-580, 638-639 - Reading title_changes:**
```python
# OLD:
title_changes_info = work.files["title_changes"]
title_changes_path = Path(title_changes_info["path"])

# NEW:
title_changes_path = resolver.resolve_work_path(work, "title_changes")
```

**Lines 676-681 - Updating files:**
```python
# OLD:
updated_files = dict(work.files) if work.files else {}
updated_files[key] = {"path": str(path), ...}
work.files = updated_files

# NEW:
updated_files = dict(work.files) if work.files else {}
updated_files[key] = {"path": path.name, ...}
work.files = updated_files
```

**Lines 721-722, 780-781 - Reading titles:**
```python
# OLD:
titles_info = work.files["titles"]
titles_path = Path(titles_info["path"])

# NEW:
titles_path = resolver.resolve_work_path(work, "titles")
```

**Lines 819-824 - Updating files (similar pattern)**

**Lines 994-995 - Reading title_changes:**
```python
# Same pattern: resolver.resolve_work_path(work, title_changes_key)
```

**Lines 1077, 1098, 1118-1123 - Reading original_markdown and updating files:**
```python
# Apply resolver pattern consistently
```

---

### 5. File: `src/vulcanlab_api/routers/corpus.py` (4 locations)

**Add import and resolver:**
```python
from vulcanlab.utils.file_utils import get_path_resolver

resolver = get_path_resolver()
```

**Lines 183, 251, 259, 299 - Reading sanitized path:**
```python
# OLD:
sanitized_path = work.files["sanitized"]["path"]
# or
sanitized_path = Path(work.files["sanitized"]["path"])

# NEW:
sanitized_path = resolver.resolve_work_path(work, "sanitized")
```

Note: Some lines may directly access path as string for display. If the API needs to return paths, return filenames (acceptable per requirements).

---

### API Response Considerations

**Important:** API endpoints currently may return absolute paths in responses. After this refactoring:
- Responses will include filenames only (e.g., `"file.md"` instead of `"/full/path/file.md"`)
- This is acceptable per user requirements (visual representation doesn't require full paths)
- Frontend/clients should not rely on absolute paths in API responses

**If full paths are needed for client display:**
- Option A: Accept filename-only responses (simpler)
- Option B: Add response serializers that reconstruct absolute paths for display (more complex, not required)

Current recommendation: Accept filename-only responses.

---

### Testing Strategy

For each module:
1. Update existing endpoint tests to expect filenames in responses
2. Add tests verifying path resolution works internally
3. Test error cases (missing files, NULL paths)

### Frontend
Not applicable to this ticket - frontend updates (if needed) are separate.

### Other / cross-cutting

- **API contracts:** Response schemas unchanged (still return strings in path fields), but values change from absolute paths to filenames
- **Client compatibility:** Clients should not parse or rely on path structure
- **Error handling:** API should return clear errors if PathResolver fails (InvalidFilePathError)

## Unit tests

**Test files:**
- `tests/unit/test_consolidate_context.py`
- `tests/unit/test_retrieve.py`
- `tests/api/test_chunking_routes.py`
- `tests/api/test_sanitization_routes.py`
- `tests/api/test_corpus_routes.py`

### Module-specific tests:

**consolidate_context.py:**
1. **test_consolidate_context_resolves_sanitized_path**
   - Create Work with filename in files["sanitized"]["path"]
   - Call `consolidate_context_for_query()`
   - Assert sanitized file read correctly via resolver

**retrieve.py:**
2. **test_enrich_chunk_context_resolves_markdown_path**
   - Create Work with filename in markdown_path
   - Call `enrich_chunk_context()`
   - Assert markdown file read correctly

### API endpoint tests:

**chunking.py:**
3. **test_get_sanitized_status_resolves_path**
   - GET endpoint that checks file status
   - Assert uses resolver internally
   - Assert returns filename in response

4. **test_post_vec_suggestions_stores_filename**
   - POST endpoint that creates vec_suggestions
   - Assert work.files["vec_suggestions"]["path"] stored as filename
   - Assert response includes filename (not absolute path)

5. **test_get_vec_suggestions_content_resolves_path**
   - GET endpoint that returns file content
   - Assert uses resolver to read file
   - Assert returns content correctly

**sanitization.py:**
6. **test_get_titles_status_resolves_path**
   - Similar pattern to chunking tests

7. **test_post_apply_title_changes_stores_filename**
   - POST endpoint that applies changes
   - Assert updated paths stored as filenames

8. **test_get_title_changes_content_resolves_path**
   - GET endpoint that returns title changes file
   - Assert reads via resolver

**corpus.py:**
9. **test_get_corpus_content_resolves_sanitized**
   - GET endpoint that returns corpus content
   - Assert uses resolver for sanitized path

10. **test_corpus_endpoints_return_filenames**
    - Verify API responses include filenames only

### Integration tests:

11. **test_api_pipeline_end_to_end**
    - POST new work via API
    - POST sanitization via API
    - POST chunking via API
    - GET work record via API
    - Assert all paths in response are filenames
    - Assert all operations succeeded

12. **test_api_error_handling_missing_file**
    - Create Work with filename that doesn't exist
    - GET endpoint that needs the file
    - Assert returns appropriate error (404 or 500 with clear message)

### Error handling tests:

13. **test_api_handles_null_paths**
    - Create Work with NULL markdown_path
    - Call API endpoint that needs the path
    - Assert returns 400 or 422 with clear error message

## Dependencies and sequencing

### Dependencies:
- **T01 (required):** PathResolver must exist
- **T03-T05 (required):** Core processing modules updated first

### Blocks:
- None - this is the final code update ticket

### Rollout notes:
- Deploy together with T03-T05 as a complete unit
- Test API endpoints thoroughly before deployment
- Update API documentation to reflect filename-only responses (if docs exist)
- Communicate change to frontend/client developers if needed

## Manual test plan

**Prerequisites:**
- T01-T05 completed and deployed
- Test database with Work records
- API server running

**Test steps:**

### 1. Test augmentation endpoints:

```bash
# Test consolidate context
curl -X POST http://localhost:8000/api/augmentation/consolidate \
  -H "Content-Type: application/json" \
  -d '{"work_id": 1, "query": "test query"}'

# Verify response includes context from sanitized file
```

### 2. Test retrieval endpoints:

```bash
# Test chunk enrichment
curl -X GET http://localhost:8000/api/retrieval/chunks/1/enrich

# Verify response includes enriched context from markdown_path
```

### 3. Test chunking API endpoints:

```bash
# Get work with chunking info
curl -X GET http://localhost:8000/api/works/1

# Verify response shows filenames only:
# {
#   "id": 1,
#   "markdown_path": "test.md",  # Not /full/path/test.md
#   "files": {
#     "sanitized": {"path": "test.sanitized.md", ...},
#     "vec_suggestions": {"path": "test.vec_sugg.md", ...}
#   }
# }

# Create vec_suggestions
curl -X POST http://localhost:8000/api/works/1/chunking/suggest

# Verify work.files updated with filename only

# Get vec_suggestions content
curl -X GET http://localhost:8000/api/works/1/files/vec_suggestions

# Verify content returned correctly (resolver worked)
```

### 4. Test sanitization API endpoints:

```bash
# Extract titles
curl -X POST http://localhost:8000/api/works/1/sanitization/extract-titles

# Verify work.files["titles"]["path"] is filename only

# Get titles content
curl -X GET http://localhost:8000/api/works/1/files/titles

# Verify content returned correctly

# Apply title changes
curl -X POST http://localhost:8000/api/works/1/sanitization/apply-changes

# Verify work.files["sanitized"]["path"] is filename only
```

### 5. Test corpus endpoints:

```bash
# Get corpus content
curl -X GET http://localhost:8000/api/corpus/1

# Verify sanitized content returned correctly
```

### 6. Error handling tests:

```bash
# Test with non-existent file
curl -X GET http://localhost:8000/api/works/999/files/sanitized

# Verify returns 404 or appropriate error

# Test with NULL path
# (Create test work with NULL markdown_path, then try to access it)
curl -X GET http://localhost:8000/api/works/[null_work_id]/files/markdown

# Verify returns clear error message
```

### 7. End-to-end API workflow:

```bash
# Full pipeline via API:
# 1. Create work (POST /api/works) - verify paths stored as filenames
# 2. Extract titles (POST /api/works/[id]/sanitization/extract-titles)
# 3. Apply title changes (POST /api/works/[id]/sanitization/apply-changes)
# 4. Suggest chunks (POST /api/works/[id]/chunking/suggest)
# 5. Create heading chunks (POST /api/works/[id]/chunking/process-headings)
# 6. Get work details (GET /api/works/[id])

# Verify all paths in final GET response are filenames only
# Verify all files exist in configured output_dir
```

### 8. Client compatibility test:

If a frontend/client exists:
- Test all UI workflows that display or use file paths
- Verify UI doesn't break with filename-only responses
- Update client code if it was parsing absolute paths

## Clarifications and assumptions

### Assumptions:
1. **Filename responses acceptable:** API clients don't need absolute paths in responses
2. **Internal resolution:** All file I/O operations use resolver internally, transparent to API clients
3. **Error handling:** Existing API error handling propagates InvalidFilePathError appropriately
4. **Module-level resolver:** Using cached resolver at module level for performance
5. **No API versioning needed:** This is an internal implementation change, not a breaking API contract change (responses still contain string paths, just different format)

### Open questions (non-blocking):
1. Should API responses include a base_dir field for client convenience?
   - Example: `{"files": {"sanitized": {"path": "file.md", "base_dir": "/configured/output/dir"}}}`
   - *Current assumption:* No, keep responses simple
2. Should we add API endpoints to retrieve full resolved paths?
   - *Current assumption:* No, not needed per requirements
3. Should API documentation be updated?
   - *Current assumption:* Yes, document that paths are filenames relative to configured directories

### Blocking questions:
None - implementation approach is clear.

### Before implementing:
1. Review API response schemas to identify all places where paths are returned
2. Communicate change to any API clients (frontend developers, external integrations)
3. Update API documentation (Swagger/OpenAPI specs) if they exist
4. Consider adding API versioning if breaking changes are a concern (though not required per user input)
5. Test thoroughly with existing API clients before deployment

This is the final code update ticket. After T06, the only remaining work is the database migration (T02), which should run after T03-T06 are deployed.

**Deployment order:**
1. Deploy T01 + T03-T06 together (code changes)
2. Test in production/staging
3. Run T02 migration (database changes)
4. Verify end-to-end functionality
