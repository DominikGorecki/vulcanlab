# Ticket: markdown-import-export.T07 - Import API Endpoints

## Source
- Spec: documentation/work/markdown-import-export.spec.md
- Patterns: documentation/patterns.md

## Goal
- Create API endpoints for markdown import workflow
- List available markdown files for import
- Trigger import with metadata and sanitization decision
- Return appropriate responses and errors

## Scope
### In scope
- API endpoint: GET /api/v1/markdown/files to list available files
- API endpoint: POST /api/v1/markdown/import to trigger import
- Request validation for import endpoint
- Error handling for all scenarios
- Integration with T03 and T04 core logic

### Out of scope
- Frontend UI components (covered in T08)
- Background job processing (import runs synchronously for now)
- Status page updates (covered in T10)
- Rate limiting or throttling

## Dependencies
- Depends on: T03, T04, T06
- Unblocks: T08

## Implementation plan
1. Extend src/vulcanlab_api/routers/markdown.py:
   - Add GET /files endpoint:
     - Call list_markdown_files() from markdown_import.scanner
     - For each file, call extract_metadata() to get metadata
     - Return: {"files": [{"filename": str, "file_path": str, "has_metadata": bool, "metadata": {...}}]}
     - Handle errors: 500 (filesystem errors)
   - Add POST /import endpoint:
     - Define request schema using Pydantic:
       - filename: str (required)
       - title: str (required, non-empty)
       - author: str (required, non-empty)
       - year: int (required, valid year)
       - is_sanitized: bool (required)
     - Validate request body
     - Check if file exists in input folder
     - Get database session
     - Create Metadata object from request
     - Check for duplicate using check_duplicate_work() (warning only, proceed anyway)
     - If is_sanitized=true: call import_sanitized_markdown()
     - If is_sanitized=false: call import_unsanitized_markdown()
     - Return: {"work_id": work.id, "status": "completed"}
     - Handle errors:
       - 400: Invalid metadata, missing file
       - 404: File not found
       - 500: Import/processing failed
2. Create Pydantic schemas in src/vulcanlab_api/schemas/markdown.py:
   - MarkdownFileSchema for file listing response
   - ImportRequestSchema for import request
   - ImportResponseSchema for import response
3. Patterns to apply:
   - API versioning: /api/v1/markdown prefix
   - Request validation: Use Pydantic models
   - Session management: Get session in router, pass to core functions
   - Error handling: HTTPException with appropriate status codes
   - Thin router: Business logic in core module
- Deviations (if any): none

## Unit tests (required)
- Add tests for:
  - GET /files endpoint returns list of markdown files
  - GET /files includes metadata for files with frontmatter
  - GET /files handles filesystem errors
  - POST /import validates required fields
  - POST /import rejects invalid year (non-integer, negative)
  - POST /import rejects empty title or author
  - POST /import returns 404 for non-existent file
  - POST /import calls import_sanitized_markdown when is_sanitized=true
  - POST /import calls import_unsanitized_markdown when is_sanitized=false
  - POST /import returns work_id and status on success
  - POST /import handles import errors and returns 500
  - Duplicate detection runs but doesn't block import
- Suggested locations:
  - tests/unit/test_markdown_api.py (extend or create)
- Mocking/fakes needed:
  - Mock list_markdown_files()
  - Mock extract_metadata()
  - Mock import_sanitized_markdown()
  - Mock import_unsanitized_markdown()
  - Mock check_duplicate_work()
  - Mock database session

## Acceptance criteria (checklist)
- [ ] GET /api/v1/markdown/files returns all markdown files from input folder
- [ ] Response includes has_metadata and metadata fields when available
- [ ] POST /api/v1/markdown/import accepts and validates request body
- [ ] Import endpoint validates title, author, year, and is_sanitized fields
- [ ] Import calls appropriate function based on is_sanitized flag
- [ ] Import returns work_id and status on success
- [ ] Import returns 400 for validation errors
- [ ] Import returns 404 for missing files
- [ ] Import returns 500 for processing failures
- [ ] Duplicate check runs but allows import to proceed
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Call GET /api/v1/markdown/files
  2. Verify response lists markdown files from input folder
  3. Create test markdown file with frontmatter
  4. Call GET /files again, verify metadata is included
  5. Call POST /api/v1/markdown/import with valid request (is_sanitized=true)
  6. Verify response includes work_id
  7. Check database for created work
  8. Call POST /import with is_sanitized=false
  9. Verify sanitization runs and work is created
  10. Call POST /import with invalid data, verify 400 errors
- Expected results:
  - File listing accurate and includes metadata
  - Import succeeds for both sanitized and unsanitized paths
  - Validation errors handled correctly
  - Work created in database with correct fields

## Notes
- Import runs synchronously; may need to consider async/background processing for large files
- Year validation should allow reasonable range (e.g., 1000-2100)
- Author field should be trimmed of whitespace before storing
- Consider max filename length to prevent filesystem issues
- Duplicate check should log warning but not block import per spec
- Response should indicate if duplicate was detected (add warning field to response)
