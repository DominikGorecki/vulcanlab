# Ticket: corpus-work-deletion.T01 - Core Work Deletion Logic

## Source
- Spec: documentation/work/corpus-work-deletion.spec.md
- Patterns: documentation/patterns.md

## Goal
- Implement core business logic for deleting a work and all associated data
- Handle database record deletion with transactions
- Handle file deletion for advanced conversion mode
- Raise appropriate exceptions for error cases

## Scope

### In scope
- Create delete_work function in core module (src/vulcanlab/data/work_operations.py)
- Delete Work record from database
- Delete ParsedMarkdown records by work_id
- Delete SanitizedMarkdown records by work_id
- Delete files tracked in Work.files JSON field
- Use pathlib for file operations
- Transaction handling with explicit session management
- Unit tests with mocked DB and file system

### Out of scope
- API endpoint implementation (T02)
- UI components (T03)
- Cascade deletion of chunks (handled automatically by existing FK constraints)
- Integration tests with real database

## Dependencies
- Depends on: none
- Unblocks: T02, T03

## Implementation plan

1. Create src/vulcanlab/data/work_operations.py if it doesn't exist
2. Implement delete_work(work_id: int, session: Session) -> None function:
   - Query work by ID, raise ValueError if not found
   - Load config to get output_dir path
   - If Work.files exists and is not None:
     - Iterate through all file entries in Work.files JSON
     - Resolve full path using output_dir + Work.files[key]["path"]
     - Delete each file using pathlib.Path.unlink(missing_ok=True)
     - If any file deletion fails (non-FileNotFoundError), raise IOError
   - Query and delete all ParsedMarkdown records where work_id matches
   - Query and delete all SanitizedMarkdown records where work_id matches
   - Delete the Work record (chunks will cascade automatically)
   - Commit transaction (caller manages session lifecycle)
3. Add logging for deletion operations (work_id, file count, errors)
4. Write comprehensive unit tests in tests/unit/test_work_deletion.py

Patterns to apply:
- Session Management: Database session passed explicitly to delete_work function (no session creation inside core logic)
- Framework Independence: Core module uses no FastAPI imports, only SQLAlchemy
- Configuration Separation: Use vulcanlab.config.load_config() for output_dir path
- Error Handling: Raise specific exceptions (ValueError for not found, IOError for file errors)

Deviations (if any):
- None: This follows all established patterns

## Unit tests (required)

Add tests for:
- test_delete_work_success: Mock session and file system, verify work deleted and commit called
- test_delete_work_cascades_chunks: Verify chunks are NOT explicitly deleted (handled by CASCADE)
- test_delete_work_deletes_parsed_markdown: Mock query, verify ParsedMarkdown.delete() called
- test_delete_work_deletes_sanitized_markdown: Mock query, verify SanitizedMarkdown.delete() called
- test_delete_work_deletes_files: Mock pathlib.Path.unlink, verify all files in Work.files deleted
- test_delete_work_not_found: Query returns None, verify ValueError raised with message
- test_delete_work_file_deletion_fails: Mock unlink to raise PermissionError, verify IOError raised
- test_delete_work_missing_file_ignored: Mock unlink to raise FileNotFoundError, verify deletion continues
- test_delete_work_null_files_field: Work.files is None, verify deletion succeeds without file operations
- test_delete_work_empty_files_field: Work.files is empty dict, verify deletion succeeds
- test_delete_work_file_path_resolution: Verify correct path construction from output_dir + filename
- test_delete_work_logs_operations: Verify logging calls with work_id and file count

Suggested locations:
- tests/unit/test_work_deletion.py (new file)

Mocking/fakes needed:
- Mock SQLAlchemy session with query, filter, first, delete, commit methods
- Mock Work, ParsedMarkdown, SanitizedMarkdown models
- Mock pathlib.Path and Path.unlink method
- Mock vulcanlab.config.load_config to return test config with output_dir
- Use existing mock_helpers from tests/unit/mock_helpers.py for session mocking patterns

## Acceptance criteria (checklist)

- [ ] delete_work function created in src/vulcanlab/data/work_operations.py
- [ ] Function signature matches spec: delete_work(work_id: int, session: Session) -> None
- [ ] ValueError raised with descriptive message when work_id not found
- [ ] IOError raised when file deletion fails (except FileNotFoundError)
- [ ] ParsedMarkdown records deleted for matching work_id
- [ ] SanitizedMarkdown records deleted for matching work_id
- [ ] Work record deleted (chunks cascade via FK)
- [ ] Files in Work.files JSON field deleted using pathlib
- [ ] File paths resolved relative to config["paths"]["output_dir"]
- [ ] Missing files handled gracefully with unlink(missing_ok=True)
- [ ] Work.files = None handled without errors
- [ ] Logging includes work_id, file count, and error details
- [ ] All 12 unit tests written and passing
- [ ] Tests use mocked DB and file system (no real files or database)

## Manual verification

Steps:
1. Review the code in src/vulcanlab/data/work_operations.py
2. Run pytest tests/unit/test_work_deletion.py -v
3. Verify all tests pass
4. Check test coverage for delete_work function (should be close to 100%)
5. Review that no FastAPI or HTTP-related imports exist in core module

Expected results:
- All unit tests pass
- Code follows patterns.md guidance
- Function is framework-independent and testable
- Error messages are clear and actionable

## Notes

- Reference tests/unit/test_delete_conversion.py for similar deletion patterns
- Use tests/unit/mock_helpers.py utilities (mock_session, configure_mock_session_query)
- The existing delete_conversion function operates on IOFile model; this ticket handles Work model
- Chunks have passive_deletes=True relationship, so CASCADE is handled at DB level
- File deletion order doesn't matter since transaction rollback only affects DB
- Consider that Work.files structure is: {"key": {"path": "filename.md", "hash": "..."}}
- Only delete files that exist in Work.files; don't search filesystem for related files
- Log individual file deletion attempts for debugging
- Use Path.unlink(missing_ok=True) to avoid FileNotFoundError for already-deleted files
