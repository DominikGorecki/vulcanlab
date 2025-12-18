# Ticket: markdown-import-export.T01 - Core Infrastructure and FileType Enum

## Source
- Spec: documentation/work/markdown-import-export.spec.md
- Patterns: documentation/patterns.md

## Goal
- Add MARKDOWN_IMPORT FileType enum value
- Create core module directory structure for markdown import/export
- Set up basic path utilities for exports subfolder

## Scope
### In scope
- Add FileType.MARKDOWN_IMPORT to src/vulcanlab/data/models/enums.py
- Create src/vulcanlab/markdown_export/ directory with __init__.py
- Create src/vulcanlab/markdown_import/ directory with __init__.py
- Add utility function to get/create exports subfolder path from config
- Basic path validation helpers

### Out of scope
- Any API endpoints or routers
- Frontend components
- Business logic for import/export operations
- Database migrations (enum is code-only)

## Dependencies
- Depends on: none
- Unblocks: T02, T03

## Implementation plan
1. Add MARKDOWN_IMPORT value to FileType enum in src/vulcanlab/data/models/enums.py
2. Create src/vulcanlab/markdown_export/__init__.py
3. Create src/vulcanlab/markdown_import/__init__.py
4. In markdown_export/__init__.py, add function: get_exports_dir() -> Path
   - Load config using vulcanlab.config.load_config()
   - Return Path(config.paths.output_dir) / "exports"
   - Create directory if it doesn't exist
5. Add path validation helper: is_safe_path(path: Path, base_dir: Path) -> bool
   - Validates that resolved path is within base_dir (prevents directory traversal)
6. Patterns to apply:
   - Configuration: Use vulcanlab.config.load_config() for paths.output_dir
   - Core module independence: No FastAPI or HTTP imports
   - Naming: snake_case for functions and modules
- Deviations (if any): none

## Unit tests (required)
- Add tests for:
  - FileType.MARKDOWN_IMPORT enum value exists and has correct string representation
  - get_exports_dir() returns correct path from config
  - get_exports_dir() creates directory if it doesn't exist
  - is_safe_path() correctly validates paths within base directory
  - is_safe_path() rejects directory traversal attempts (../../etc/passwd)
  - is_safe_path() rejects absolute paths outside base directory
- Suggested locations:
  - tests/unit/test_markdown_export_utils.py
  - tests/unit/test_enums.py (add MARKDOWN_IMPORT test)
- Mocking/fakes needed:
  - Mock vulcanlab.config.load_config() to return test config
  - Mock Path.mkdir() for directory creation tests

## Acceptance criteria (checklist)
- [ ] FileType.MARKDOWN_IMPORT enum value exists in enums.py
- [ ] src/vulcanlab/markdown_export/ directory exists with __init__.py
- [ ] src/vulcanlab/markdown_import/ directory exists with __init__.py
- [ ] get_exports_dir() function returns Path to exports subfolder
- [ ] get_exports_dir() creates exports directory if missing
- [ ] is_safe_path() validates paths correctly
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Import FileType from vulcanlab.data.models.enums and verify MARKDOWN_IMPORT exists
  2. Call get_exports_dir() and verify it returns correct path
  3. Check that exports directory is created in output folder
  4. Test is_safe_path() with various valid and invalid paths
- Expected results:
  - FileType.MARKDOWN_IMPORT is accessible
  - Exports directory exists at {output_dir}/exports/
  - Path validation correctly accepts/rejects paths

## Notes
- This ticket establishes the foundation for all subsequent tickets
- The exports directory should be created lazily (on first access)
- Path validation is critical for security (prevents directory traversal attacks)
- No database migration needed since FileType is a Python enum, not a database enum type
