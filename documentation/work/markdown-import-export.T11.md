# Ticket: markdown-import-export.T11 - Security and Path Validation Hardening

## Source
- Spec: documentation/work/markdown-import-export.spec.md
- Patterns: documentation/patterns.md

## Goal
- Harden security for file path operations
- Prevent directory traversal attacks in import and export
- Sanitize user-provided metadata to prevent injection
- Add logging for security-relevant operations

## Scope
### In scope
- Path validation for import file paths (restrict to input_dir)
- Path validation for export file paths (restrict to exports subfolder)
- Metadata sanitization (title, author) to prevent injection attacks
- Year validation range enforcement
- Security-focused logging
- Input validation on all API endpoints

### Out of scope
- File content scanning for malware
- Rate limiting or DDoS protection
- Authentication/authorization (assume handled at API layer)
- Encryption of stored markdown content

## Dependencies
- Depends on: T02, T07
- Unblocks: none (hardens existing implementation)

## Implementation plan
1. Enhance path validation in markdown_export/__init__.py:
   - Strengthen is_safe_path() implementation:
     - Resolve symlinks using Path.resolve()
     - Verify resolved path is within allowed base directory
     - Reject paths with .. components
     - Reject absolute paths outside base
     - Add unit tests for edge cases (symlinks, multiple .., etc.)
2. Add path validation to import operations:
   - Validate file_path in list_markdown_files() is within input_dir
   - Validate file_path in import functions is within input_dir
   - Reject any path that resolves outside input_dir
3. Add metadata sanitization in markdown_import/validation.py:
   - Create sanitize_metadata(metadata: Metadata) -> Metadata:
     - Strip title and author of leading/trailing whitespace
     - Remove control characters from title and author
     - Limit title length (e.g., max 500 chars)
     - Limit author length (e.g., max 200 chars)
     - Validate year is integer between 1000 and 2100
     - Raise ValueError if validation fails
   - Apply sanitization before Work creation
4. Update API routers to use sanitized metadata:
   - Call sanitize_metadata() in import endpoint before processing
   - Return 400 with specific error message for validation failures
5. Add security logging:
   - Log all export operations: work_id, export_path, timestamp, user (if available)
   - Log all import operations: filename, metadata, is_sanitized, timestamp
   - Log path validation failures with attempted path
   - Log metadata validation failures with sanitized values
   - Use appropriate log level (INFO for success, WARNING for validation failures)
6. Patterns to apply:
   - Defense in depth: Multiple layers of validation
   - Fail securely: Reject invalid input, don't attempt to fix
   - Logging: Audit trail for security-relevant operations
   - Input validation: Whitelist approach (allow only safe characters)
- Deviations (if any): none

## Unit tests (required)
- Add tests for:
  - is_safe_path() rejects symlinks pointing outside base dir
  - is_safe_path() rejects multiple .. traversal attempts
  - is_safe_path() rejects absolute paths outside base
  - is_safe_path() accepts valid relative paths within base
  - sanitize_metadata() strips whitespace from title and author
  - sanitize_metadata() removes control characters
  - sanitize_metadata() enforces length limits
  - sanitize_metadata() validates year range
  - sanitize_metadata() raises ValueError for invalid input
  - Import API rejects paths outside input_dir
  - Export API rejects paths outside exports folder
  - Security events are logged correctly
  - Path validation failures are logged with attempted path
- Suggested locations:
  - tests/unit/test_markdown_security.py
  - tests/unit/test_markdown_validation.py
  - Extend existing test files with security test cases
- Mocking/fakes needed:
  - Mock Path.resolve() for symlink tests
  - Mock logger to verify log messages
  - Mock file system for path validation tests

## Acceptance criteria (checklist)
- [ ] is_safe_path() rejects all directory traversal attempts
- [ ] Import operations reject paths outside input_dir
- [ ] Export operations reject paths outside exports folder
- [ ] Metadata sanitization removes dangerous characters
- [ ] Title and author length limits enforced
- [ ] Year validation enforces reasonable range (1000-2100)
- [ ] All export operations logged with work_id and path
- [ ] All import operations logged with filename and metadata
- [ ] Path validation failures logged with attempted path
- [ ] Metadata validation failures logged
- [ ] API returns 400 for validation failures with specific messages
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Attempt to export with directory traversal in work title (../../etc/passwd)
  2. Verify export fails or sanitizes path safely
  3. Attempt to import file with path outside input_dir
  4. Verify import rejected with error
  5. Import file with extremely long title (> 500 chars)
  6. Verify title truncated or rejected
  7. Import file with control characters in author field
  8. Verify control characters removed
  9. Import file with year = 9999
  10. Verify validation error
  11. Check logs for all operations
  12. Verify security events logged appropriately
- Expected results:
  - All directory traversal attempts blocked
  - Metadata sanitized correctly
  - Comprehensive audit trail in logs
  - No crashes or undefined behavior

## Notes
- Path validation critical for preventing filesystem access attacks
- Metadata sanitization prevents SQL injection (though using ORM helps) and XSS in UI
- Year range 1000-2100 is reasonable for publication dates
- Control characters include \x00-\x1F and \x7F (delete)
- Consider using library like bleach for more sophisticated sanitization (optional)
- Log messages should not include sensitive data (e.g., full file contents)
- If path validation fails, log but don't expose internal paths to API caller
- Consider adding security.md document to track security decisions and hardening measures
- Future: Add rate limiting to prevent abuse of import/export endpoints
