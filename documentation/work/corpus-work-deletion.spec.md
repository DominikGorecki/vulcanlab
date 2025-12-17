# Title: Corpus Work Deletion Feature

## Summary
- Add a delete icon to each row in the corpus works table that allows users to permanently delete a work and all associated data
- Deleting a work removes the work record, all chunks, DB entries for parsed/sanitized markdown, and files tracked in the Work.files JSON field
- Implement transactional deletion with confirmation modal and error handling
- Use cascade deletes for DB relationships and explicit file cleanup for advanced conversion artifacts

## Back/Context
- Currently, the corpus page displays works in a read-only table with no delete functionality
- Users have no UI mechanism to remove works from the corpus once they have been converted and chunked
- Works can accumulate test data, failed conversions, or unwanted content with no cleanup path
- The Work model tracks files via a JSON field (Work.files) for advanced conversion mode
- Simple conversion stores markdown in ParsedMarkdown and SanitizedMarkdown DB tables
- Chunks are already configured with cascade deletes (passive_deletes=True)

## Goals
- Add delete icon UI element to corpus works table rows
- Implement DELETE /api/v1/corpus/works/{work_id} endpoint
- Delete work record, chunks (via cascade), ParsedMarkdown entries, SanitizedMarkdown entries
- Delete files tracked in Work.files JSON field for advanced conversion mode
- Show confirmation modal with work details before deletion
- Provide clear error feedback if deletion fails

## Non-goals (Strict)
- Bulk deletion of multiple works (single work deletion only)
- Soft delete or trash/recovery functionality
- Authorization or permission checks (single-user application)
- Undo functionality after deletion
- Deletion history or audit logging
- Retry mechanisms for failed file deletions

## Scope

### In scope
- UI: Delete icon in corpus works table
- UI: Confirmation modal with work title and authors
- UI: Error modal for deletion failures
- API: DELETE /api/v1/corpus/works/{work_id} endpoint
- Core: Delete logic for work, chunks, parsed markdown, sanitized markdown
- Core: File deletion for all files tracked in Work.files JSON field
- Testing: Unit tests for deletion logic with mocked DB and file system

### Out of scope
- Bulk operations (selecting multiple works)
- Deletion from work detail page (only corpus list page)
- Advanced file cleanup strategies (orphaned file detection)
- Background job processing for deletions
- Integration tests with real database

## Requirements (Functional)

- R1: DELETE icon must appear in each row of the corpus works table next to existing columns
- R2: Clicking the delete icon must open a confirmation modal showing work title and authors
- R3: Confirmation modal must have "Cancel" and "Delete" buttons
- R4: DELETE /api/v1/corpus/works/{work_id} endpoint must return 204 on success, 404 if work not found, 500 on failure
- R5: Deletion must remove the Work record from the database
- R6: Deletion must cascade-delete all associated Chunk records
- R7: Deletion must delete all ParsedMarkdown records with matching work_id
- R8: Deletion must delete all SanitizedMarkdown records with matching work_id
- R9: Deletion must delete all files referenced in Work.files JSON field (if field exists and is not null)
- R10: File paths must be resolved relative to output_dir from vulcanlab.config.json
- R11: If any file deletion fails, the entire operation must be rolled back (DB transaction not committed)
- R12: On successful deletion, the corpus page must refresh to show updated stats and works list
- R13: On deletion error, an error modal must display the error message

## Requirements (Non-functional)

- Performance:
  - Deletion operation should complete within 5 seconds for typical work (< 100 chunks, < 20 files)
  - UI should show loading state during deletion API call

- Reliability:
  - Use database transactions to ensure atomic deletion of DB records
  - Log file deletion errors even if orphaned files are acceptable
  - Handle missing files gracefully (do not fail if file already deleted)

- Security / Privacy:
  - No authorization required (single-user application assumption)
  - Validate work_id is a positive integer
  - Do not expose file system paths in error messages to frontend

- Observability:
  - Log deletion operations with work_id and file count
  - Log individual file deletion attempts and results
  - Include error details in API response for debugging

## Proposed Solution (High-level)

- Frontend: Add Trash2 icon from lucide-react to each table row
- Frontend: Create ConfirmDeleteModal component with work details
- Frontend: Add error state and modal for displaying deletion errors
- API: Create DELETE handler in corpus router at /api/v1/corpus/works/{work_id}
- Core: Implement delete_work(work_id, session) function in src/vulcanlab/data/work_operations.py (or similar)
- Core: Query work by ID, retrieve Work.files JSON, resolve file paths using config.paths.output_dir
- Core: Delete files first, then delete DB records in transaction
- Core: If file deletion fails, raise exception to prevent DB commit
- DB: Leverage existing CASCADE constraints on chunks relationship
- DB: Explicitly delete ParsedMarkdown and SanitizedMarkdown records by work_id

## Interfaces / APIs / Contracts

### API Endpoint

**DELETE /api/v1/corpus/works/{work_id}**

Request:
- Path parameter: work_id (integer)

Response:
- 204 No Content: Deletion successful
- 404 Not Found: Work with given ID does not exist
  ```json
  {"detail": "Work not found"}
  ```
- 500 Internal Server Error: Deletion failed
  ```json
  {"detail": "Failed to delete work: [error message]"}
  ```

### Core Function Signature

```python
def delete_work(work_id: int, session: Session) -> None:
    """
    Delete a work and all associated data.

    Raises:
        ValueError: If work_id not found
        IOError: If file deletion fails
    """
```

## Data Model / Storage

### Database Deletions

- Work record (works table)
- Chunk records (chunks table, cascade via foreign key)
- ParsedMarkdown records (parsed_markdown table, cascade via foreign key)
- SanitizedMarkdown records (sanitized_markdown table, cascade via foreign key)

### File Deletions

Files referenced in Work.files JSON field:
- original_file
- hier_markdown
- style_markdown
- original_markdown
- toc_titles
- titles
- san_mapping
- sanitized
- sanitized_titles
- vec_suggestions

File path resolution:
- Base directory: config["paths"]["output_dir"] from vulcanlab.config.json
- Full path: os.path.join(output_dir, Work.files[key]["path"])

## UX / Workflows

### Happy Path
1. User navigates to corpus page
2. User sees delete icon (trash icon) at the end of each work row
3. User clicks delete icon for a specific work
4. Confirmation modal appears showing work title and authors
5. User clicks "Delete" button in modal
6. Loading spinner appears on the delete button
7. API call completes successfully
8. Modal closes automatically
9. Corpus page refreshes showing updated stats and works list (deleted work removed)

### Error Path
1. User clicks delete icon
2. Confirmation modal appears
3. User clicks "Delete" button
4. API call fails (e.g., file permission error, DB constraint violation)
5. Confirmation modal closes
6. Error modal appears with error message
7. User clicks "Close" on error modal
8. Corpus page remains unchanged (work not deleted)

## Testing Plan

### Unit tests

- test_delete_work_success: Mock session and file system, verify work deleted
- test_delete_work_cascades_chunks: Verify chunks are deleted via cascade
- test_delete_work_deletes_parsed_markdown: Verify ParsedMarkdown records deleted
- test_delete_work_deletes_sanitized_markdown: Verify SanitizedMarkdown records deleted
- test_delete_work_deletes_files: Mock file system, verify all files in Work.files deleted
- test_delete_work_not_found: Verify ValueError raised for non-existent work_id
- test_delete_work_file_deletion_fails: Mock file deletion failure, verify exception raised and transaction rolled back
- test_delete_work_missing_file_ignored: Mock missing file (FileNotFoundError), verify deletion continues
- test_delete_work_null_files_field: Verify deletion succeeds when Work.files is None
- test_api_delete_endpoint_204: Verify endpoint returns 204 on success
- test_api_delete_endpoint_404: Verify endpoint returns 404 for non-existent work
- test_api_delete_endpoint_500: Verify endpoint returns 500 on deletion error

### Integration tests

- Not required for this ticket (per patterns.md guidance)

### Manual test plan

- Create a test work via simple conversion
- Verify work appears in corpus page
- Click delete icon
- Verify confirmation modal shows correct work title and authors
- Click "Cancel" and verify modal closes without deletion
- Click delete icon again
- Click "Delete" and verify work is removed from corpus page
- Verify stats are updated correctly
- Check database to confirm work, chunks, parsed markdown, and sanitized markdown are deleted
- Create a test work via advanced conversion (if applicable)
- Delete the work and verify all files tracked in Work.files are deleted from output directory
- Manually delete a file from Work.files before deletion
- Delete the work and verify deletion succeeds (missing file ignored)
- Manually set file permissions to read-only for a file in Work.files
- Attempt deletion and verify error modal appears with descriptive message

## Acceptance Criteria (Checklist)

- [ ] Delete icon appears in each row of corpus works table
- [ ] Clicking delete icon opens confirmation modal with work title and authors
- [ ] Confirmation modal has "Cancel" and "Delete" buttons
- [ ] Clicking "Cancel" closes modal without deletion
- [ ] Clicking "Delete" calls DELETE /api/v1/corpus/works/{work_id} endpoint
- [ ] Successful deletion returns 204 status code
- [ ] Successful deletion removes work from database
- [ ] Successful deletion cascades to all chunks
- [ ] Successful deletion removes all ParsedMarkdown records
- [ ] Successful deletion removes all SanitizedMarkdown records
- [ ] Successful deletion removes all files tracked in Work.files JSON field
- [ ] Missing files during deletion do not cause failure
- [ ] File deletion failure rolls back database transaction
- [ ] Corpus page refreshes after successful deletion
- [ ] Error modal appears on deletion failure with descriptive message
- [ ] All unit tests pass
- [ ] Manual testing confirms delete functionality works end-to-end

## Rollout / Migration Plan

Not applicable (no database schema changes or data migration required)

## Risks and Alternatives

### Risks

- File deletion failure leaves orphaned files in output directory (acceptable per Q9)
- Race condition if work is being processed during deletion (mitigated by single-user assumption)
- Accidental deletion of important work (mitigated by confirmation modal)
- Large works with many files may exceed 5-second deletion timeout (unlikely with typical corpus sizes)

### Alternatives considered

- Soft delete: Add deleted_at timestamp instead of hard delete
  - Rejected: Adds complexity for single-user application; user can always re-convert if needed
- Background job deletion: Queue deletion for async processing
  - Rejected: Overkill for single-user application with small corpus sizes
- Bulk deletion: Allow selecting multiple works for deletion
  - Rejected: Out of scope per Q10; can be added in future ticket if needed
- Undo functionality: Allow reverting deletion within time window
  - Rejected: Requires soft delete or backup mechanism; unnecessary complexity

## Patterns and Standards Alignment (from documentation/patterns.md)

### Patterns applied

- **API Versioning**: Using /api/v1 prefix for new DELETE endpoint
- **Thin API Layer**: Business logic in core module (delete_work function), API layer only handles HTTP concerns
- **Session Management**: Database session passed explicitly to delete_work function
- **Error Handling**: Raising specific exceptions (ValueError, IOError) for global handler to catch
- **Configuration Separation**: Using vulcanlab.config.json for output_dir path resolution
- **Testing Isolation**: Unit tests with mocked DB sessions and file system
- **Cascade Deletes**: Leveraging existing passive_deletes=True on Chunk relationship

### Deviations (if any)

- None: This feature follows all established patterns

## Implementation Notes (Non-binding)

- Consider using Shadcn Dialog component for confirmation and error modals
- Trash2 icon from lucide-react is semantically appropriate for delete action
- File deletion should use pathlib.Path for cross-platform compatibility
- Consider logging deleted work title and ID for audit trail even though formal audit logging is out of scope
- For file deletion, use try/except around each file and collect errors rather than failing on first error
- If Work.files is None or empty, skip file deletion phase entirely
- Frontend can disable delete icon during deletion to prevent double-clicks
- Consider adding data-testid attributes to delete icon and modals for future E2E tests

## Open Questions

- Q1: Should we add a "last deleted work" indicator in the UI for immediate undo functionality?
  - Answer: No, per non-goals (undo functionality is out of scope)
- Q2: Should file deletion use os.remove or pathlib.Path.unlink?
  - Answer: Use pathlib.Path.unlink(missing_ok=True) for cleaner API and built-in missing file handling
