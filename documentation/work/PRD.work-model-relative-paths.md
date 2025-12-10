# PRD: Refactor Work Model Path Storage to Relative Paths

---
status: draft
owner: TODO
created: 2025-12-10
slug: work-model-relative-paths
---

## 1. Summary

Refactor the Work model's path storage from absolute paths to relative filenames, using configuration-based base directories (`input_dir` and `output_dir`) to construct absolute paths at runtime. This change reduces coupling to specific filesystem layouts, improves portability across environments (development, Docker, production), and simplifies path management throughout the processing pipeline.

## 2. Problem & Context

**Current Situation:**
- The Work model stores absolute paths in `markdown_path` and within the `files` JSON field (e.g., `files["sanitized"]["path"]`)
- These absolute paths are hardcoded to specific environments (e.g., `D:\psychRAG_data\output\file.pdf` or `/home/user/vulcanData/output/file.pdf`)
- The `source_path` field exists but is deprecated

**Pain Points:**
- Database dumps cannot be easily moved between environments without path rewriting
- Docker containers and local development use different path structures
- Path changes require database migrations
- Testing requires mocking full absolute paths

**Affected Users:**
- Developers working across multiple environments (local, WSL, Docker)
- DevOps/deployment processes that need environment portability
- Testing infrastructure

## 3. Goals & Non-Goals

### 3.1 Goals
- Store only relative filenames (no directory path) in the Work model database fields
- Use `vulcanlab.config.json` paths (`input_dir`, `output_dir`) to construct absolute paths at runtime
- Create utility functions in `file_utils.py` for path resolution with config caching
- Add property setters to Work model that automatically extract filenames from full paths
- Update all code locations (70+ references across conversion, sanitization, chunking, augmentation, retrieval, and API modules) to use the new path utilities
- Create migration script (015) to convert existing absolute paths to filenames
- Ensure NULL path values throw a custom exception

### 3.2 Non-Goals
- Maintaining the deprecated `source_path` field
- Supporting subdirectory structures (all files must be at root of `input_dir` or `output_dir`)
- Backward compatibility for external APIs expecting absolute paths (filename-only response is acceptable)
- File existence validation in utility functions (existing code handles this)

## 4. Users & Use Cases

### 4.1 User Segments
- **Primary:** Backend developers and data pipeline engineers
- **Secondary:** DevOps engineers managing deployments

### 4.2 Key Use Cases / User Stories

**UC1: Environment Portability**
- As a developer, I want to migrate database dumps between my local machine and Docker without path issues, so that I can test with production-like data locally

**UC2: Path Resolution**
- As a developer calling conversion/sanitization/chunking code, I want to access work file paths using simple helper functions that automatically resolve to the correct absolute path for my environment

**UC3: Setting Paths**
- As a developer creating/updating Work records, I want to set full absolute paths and have the model automatically store only the filename, so I don't need to manually extract filenames everywhere

**UC4: Migration**
- As a DevOps engineer, I want to run a migration script that converts all existing absolute paths to filenames, preserving data integrity

## 5. Requirements

### 5.1 Functional Requirements

**FR1: Path Utility Module**
- FR1.1: Create or extend `src/vulcanlab/utils/file_utils.py` with path resolution utilities
- FR1.2: Implement `PathResolver` class that:
  - Initializes once from `vulcanlab.config.json` at project root
  - Caches `input_dir` and `output_dir` paths
  - Provides method to resolve filenames to absolute paths based on field type
  - Throws custom `InvalidFilePathError` exception for NULL/empty filenames
- FR1.3: Path resolution logic:
  - `files["original_file"]["path"]` → uses `input_dir`
  - All other paths in `files` JSON and `markdown_path` → use `output_dir`
  - Only resolves the `"path"` key within each `files` entry

**FR2: Work Model Property Setters**
- FR2.1: Add setter for `markdown_path` that extracts filename from full path (e.g., `"/full/path/file.md"` → `"file.md"`)
- FR2.2: Ensure setters handle both absolute paths and plain filenames
- FR2.3: Use `Path(value).name` to extract filename portion

**FR3: Update All Code References**
Based on codebase analysis, update 70+ locations across:
- **Conversion modules:** `new_work.py` (3 locations)
- **Sanitization modules:** `apply_title_changes.py` (11 locations), `extract_titles.py` (3 locations), `suggest_heading_changes.py` (4 locations), `skip_apply.py` (2 locations), `update_content_hash.py` (3 locations), `title_changes_interactive.py` (4 locations)
- **Chunking modules:** `content_chunking.py` (2 locations), `suggested_chunks.py` (14 locations), `chunk_headings.py` (4 locations), `vec_suggestions_interactive.py` (6 locations), `suggested_chunks_cli.py` (1 location)
- **Augmentation modules:** `consolidate_context.py` (4 locations)
- **Retrieval modules:** `retrieve.py` (2 locations)
- **API routers:** `chunking.py` (16 locations), `sanitization.py` (18 locations), `corpus.py` (4 locations)

All locations that currently use `Path(work.markdown_path)` or `Path(work.files[key]["path"])` should be updated to use the new path resolver utility.

**FR4: Database Migration Script**
- FR4.1: Create migration `015_convert_paths_to_filenames.sql` (prefer pure SQL)
- FR4.2: If SQL regex is too complex, use Python script `015_convert_paths_to_filenames.py`
- FR4.3: Python script must:
  - Use SQLAlchemy session management following existing patterns
  - Extract filename from absolute paths (e.g., `"D:\psychRAG_data\output\file.pdf"` → `"file.pdf"`)
  - Handle both Windows (`\`) and Linux (`/`) path separators
  - Update `markdown_path` field
  - Update all `path` keys within `files` JSON field for all file types
  - Handle NULL values appropriately (skip or log)
- FR4.4: Migration should be idempotent (safe to run multiple times)

### 5.2 Non-Functional Requirements

**NFR1: Performance**
- Config caching must avoid repeated file I/O for path resolution
- Path resolution should add negligible overhead (<1ms per call)

**NFR2: Error Handling**
- Clear exception messages indicating which field/file type failed
- Custom `InvalidFilePathError` with context about the Work ID and field name

**NFR3: Maintainability**
- Centralized path logic in utility module
- Clear documentation of which fields use which base directory

## 6. UX / UI Notes

**Developer Experience:**
- Developers should import and use the path resolver utility:
  ```python
  from vulcanlab.utils.file_utils import get_path_resolver

  resolver = get_path_resolver()
  absolute_path = resolver.resolve_work_file(work, "sanitized")
  ```
- Setting paths remains intuitive:
  ```python
  work.markdown_path = "/full/path/to/file.md"  # Automatically stores "file.md"
  ```

**API Responses:**
- APIs will return filenames instead of absolute paths
- This is acceptable per user requirements (visual representation doesn't require full path)

## 7. Analytics & Success Metrics

**Success Metrics:**
- Migration successfully converts all existing paths without data loss
- All unit tests pass for path resolution utilities
- Zero regressions in conversion/sanitization/chunking pipelines
- Database can be migrated between environments without path issues

**Testing Requirements:**
- Unit tests for `PathResolver` class covering:
  - Config loading and caching
  - Correct directory selection (input vs output)
  - NULL value exception handling
  - Filename extraction from various path formats
- Unit tests for Work model property setters
- Integration test: Create Work record with full paths, verify storage as filenames, retrieve and resolve back to full paths

## 8. Dependencies & Risks

**Dependencies:**
- `vulcanlab.config.json` must exist and contain valid `paths.input_dir` and `paths.output_dir`
- All files must be stored flat (no subdirectories) in input/output directories

**Risks:**
1. **Migration complexity:** Existing database may have inconsistent path formats
   - *Mitigation:* Robust path parsing in migration script, logging of edge cases
2. **Breaking change:** Code outside identified modules may use paths
   - *Mitigation:* Comprehensive grep search before implementation, thorough testing
3. **Performance:** Path resolution called in hot loops
   - *Mitigation:* Config caching, benchmark path resolution overhead

## 9. Rollout & Milestones

**Phase 1: Implementation**
1. Create path resolver utility in `file_utils.py`
2. Add Work model property setters
3. Update all 70+ code references across modules
4. Add unit tests

**Phase 2: Migration**
1. Create and test migration script (015) in isolated database
2. Run migration on development database
3. Validate data integrity

**Phase 3: Deployment**
1. Deploy code changes
2. Run migration in production (if applicable)
3. Monitor for issues in conversion/chunking pipelines

## 10. Open Questions

None - all clarifications obtained during PRD creation phase.

---

## Appendix: Detailed Code Locations

### Conversion Modules
- **new_work.py**: Lines 129-132, 167, 182

### Sanitization Modules
- **apply_title_changes.py**: Lines 111, 114, 186, 189, 241, 279, 300-308, 311-312, 315-316, 436, 441
- **extract_titles.py**: Lines 305-310
- **suggest_heading_changes.py**: Lines 677-682, 907-912
- **skip_apply.py**: Lines 151-156
- **update_content_hash.py**: Lines 287, 290, 242-247
- **title_changes_interactive.py**: Lines 158-159, 187-188

### Chunking Modules
- **content_chunking.py**: Lines 674-675
- **suggested_chunks.py**: Lines 420-421, 447-448, 580-581, 631-636, 687-688, 714-715, 870-875
- **chunk_headings.py**: Lines 153-154, 164-165
- **vec_suggestions_interactive.py**: Lines 164-165, 193-194, 210, 260-262
- **suggested_chunks_cli.py**: Line 105

### Augmentation Modules
- **consolidate_context.py**: Lines 352-354, 439-440

### Retrieval Modules
- **retrieve.py**: Lines 274-277

### API Routers
- **chunking.py**: Lines 58-62, 182-183, 227-228, 250-255, 341-342, 386-387, 409-414, 676, 685, 698, 703, 787-788, 817
- **sanitization.py**: Lines 85-86, 579-580, 638-639, 676-681, 721-722, 780-781, 819-824, 994-995, 1077, 1098, 1118-1123
- **corpus.py**: Lines 183, 251, 259, 299
