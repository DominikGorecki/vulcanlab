# Ticket: markdown-import-export.T12 - Error Handling and Edge Cases

## Source
- Spec: documentation/work/markdown-import-export.spec.md
- Patterns: documentation/patterns.md

## Goal
- Comprehensive error handling for all failure scenarios
- User-friendly error messages in UI
- Graceful degradation when operations fail
- Edge case handling (empty files, invalid markdown, etc.)

## Scope
### In scope
- Error handling for file I/O failures (permissions, disk full, etc.)
- Handling of empty or invalid markdown files
- YAML frontmatter parsing errors
- Database transaction rollback on failures
- User-friendly error messages in UI
- Retry mechanisms where appropriate
- Edge cases: very large files, unicode filenames, etc.

### Out of scope
- Automatic recovery from all errors
- Detailed error reporting to external monitoring systems
- Advanced retry logic with exponential backoff
- Partial import/export (all-or-nothing approach)

## Dependencies
- Depends on: T02, T07, T08
- Unblocks: none (completes error handling)

## Implementation plan
1. Add comprehensive error handling to export_work():
   - Wrap file write in try/except
   - Handle disk full errors (OSError with errno.ENOSPC)
   - Handle permission errors (PermissionError)
   - Handle invalid filename errors
   - Rollback any partial writes on failure
   - Log all errors with full context
   - Return specific error messages (not generic "export failed")
2. Add comprehensive error handling to import functions:
   - Wrap all database operations in try/except
   - Use session.rollback() on any failure
   - Handle file read errors (missing file, permissions, encoding)
   - Handle YAML parsing errors in extract_metadata()
   - Handle empty file edge case (file size = 0)
   - Handle chunking failures (invalid markdown structure)
   - Handle sanitization failures (LLM errors, timeouts)
   - Log all errors with full context
3. Add edge case handling:
   - Empty markdown files: reject with clear message
   - Very large files (> 10MB): warn but allow (log warning)
   - Invalid UTF-8 encoding: attempt to decode with fallback encoding
   - Unicode filenames: ensure proper handling on all platforms
   - Markdown without any headers: handle chunking gracefully
   - Files with only frontmatter (no content): reject with message
4. Update API error responses:
   - Use appropriate HTTP status codes (400, 404, 500)
   - Return structured error responses with:
     - error: string (error type/code)
     - message: string (user-friendly message)
     - detail: string (optional, technical details)
   - Don't expose internal paths or stack traces to API clients
5. Update frontend error handling:
   - Parse API error responses correctly
   - Display user-friendly error messages in modals
   - Add retry button where appropriate (transient failures)
   - Add "contact support" message for unexpected errors
   - Log errors to browser console for debugging
6. Add transaction management:
   - Ensure all import operations use database transactions
   - Rollback on any failure (Work creation, chunk creation, etc.)
   - Don't leave partial records in database
7. Patterns to apply:
   - Global exception handler: Let API middleware catch unhandled exceptions
   - Specific exceptions: Raise specific exceptions (ValueError, FileNotFoundError)
   - Transaction management: Use session.begin() and session.rollback()
   - Error logging: Log with appropriate level (ERROR, WARNING)
   - User-friendly messages: Don't expose internal details
- Deviations (if any): none

## Unit tests (required)
- Add tests for:
  - export_work() handles disk full error
  - export_work() handles permission denied error
  - export_work() handles invalid filename error
  - import functions rollback transaction on failure
  - import handles file not found error
  - import handles file permission error
  - import handles invalid UTF-8 encoding
  - import handles empty file (0 bytes)
  - import handles very large file (10MB+)
  - import handles YAML parsing errors
  - import handles markdown without headers
  - import handles file with only frontmatter
  - API returns structured error responses
  - Frontend displays error messages correctly
  - Frontend retry button works
- Suggested locations:
  - tests/unit/test_markdown_export_errors.py
  - tests/unit/test_markdown_import_errors.py
  - tests/unit/test_markdown_api_errors.py
  - Extend existing test files with error test cases
- Mocking/fakes needed:
  - Mock file I/O to simulate errors
  - Mock database session to simulate transaction errors
  - Mock sanitization functions to simulate LLM errors
  - Mock chunking functions to simulate failures

## Acceptance criteria (checklist)
- [ ] Export handles file write errors gracefully
- [ ] Export returns specific error messages for different failure types
- [ ] Import rolls back database transaction on any failure
- [ ] Import handles file read errors with clear messages
- [ ] Empty files rejected with user-friendly message
- [ ] Large files (> 10MB) trigger warning log but proceed
- [ ] Invalid UTF-8 encoding handled with fallback
- [ ] YAML parsing errors handled gracefully
- [ ] Markdown without headers chunks successfully
- [ ] Files with only frontmatter rejected
- [ ] API returns structured error responses
- [ ] Frontend displays error messages in modals
- [ ] Retry buttons appear for transient errors
- [ ] No partial records left in database on failure
- [ ] All errors logged with full context
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Attempt to export work when exports folder is read-only
  2. Verify permission error displayed
  3. Import empty file (0 bytes)
  4. Verify rejection with clear message
  5. Import file with invalid UTF-8 characters
  6. Verify file imported successfully (with fallback encoding)
  7. Import large file (> 10MB)
  8. Verify warning logged but import succeeds
  9. Import file with invalid YAML frontmatter
  10. Verify metadata form shown without pre-population
  11. Import file with only frontmatter, no content
  12. Verify rejection with message
  13. Simulate database failure during import
  14. Verify no partial Work record left in DB
  15. Check logs for all error scenarios
- Expected results:
  - All errors handled gracefully without crashes
  - User sees clear, actionable error messages
  - No partial state in database
  - Comprehensive error logs for debugging

## Notes
- File size limit of 10MB is soft limit (warn but allow) for now
- UTF-8 fallback encodings: try latin-1 or cp1252 before failing
- Empty file is 0 bytes; file with only whitespace should be rejected too
- Very long filenames may cause issues on some filesystems; consider truncating
- Disk full errors are rare but critical; consider monitoring
- Permission errors may indicate configuration issues; add to troubleshooting guide
- Transaction rollback is critical to avoid orphaned records
- Frontend should distinguish between permanent failures (show error) and transient (show retry)
- Consider adding a "detailed error log" section in UI for advanced users (dev mode)
- Some errors are user errors (empty file) vs system errors (disk full); message accordingly
