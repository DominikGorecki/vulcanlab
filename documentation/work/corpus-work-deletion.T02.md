# Ticket: corpus-work-deletion.T02 - DELETE API Endpoint

## Source
- Spec: documentation/work/corpus-work-deletion.spec.md
- Patterns: documentation/patterns.md

## Goal
- Expose work deletion via REST API endpoint
- Handle HTTP request/response and status codes
- Integrate with core deletion logic from T01
- Provide appropriate error responses

## Scope

### In scope
- Add DELETE /api/v1/corpus/works/{work_id} endpoint to corpus router
- Return 204 No Content on success
- Return 404 Not Found if work doesn't exist
- Return 500 Internal Server Error on deletion failure
- Validate work_id is positive integer
- Use thin API layer pattern (delegate to core module)
- Unit tests for API endpoint with mocked core function

### Out of scope
- UI components (T03)
- Core deletion logic (T01)
- Authorization checks (single-user application)

## Dependencies
- Depends on: T01 (core delete_work function)
- Unblocks: T03

## Implementation plan

1. Add DELETE endpoint to src/vulcanlab_api/routers/corpus.py:
   - Define @router.delete("/works/{work_id}", status_code=204)
   - Import delete_work from vulcanlab.data.work_operations
   - Validate work_id > 0, raise HTTPException 400 if invalid
   - Get database session using get_session()
   - Call delete_work(work_id, session) inside try/except
   - Catch ValueError -> return 404 with {"detail": "Work not found"}
   - Catch IOError -> return 500 with {"detail": "Failed to delete work: {error}"}
   - Catch generic Exception -> return 500 with generic error message
   - Return 204 No Content on success (no response body)
2. Update router registration in src/vulcanlab_api/main.py:
   - Verify corpus router is included with prefix="/api/v1/corpus"
   - If not, add: app.include_router(corpus.router, prefix="/api/v1/corpus", tags=["corpus"])
3. Write unit tests in tests/unit/test_corpus_deletion_api.py

Patterns to apply:
- API Versioning: Use /api/v1 prefix (register in main.py, not in router)
- Thin API Layer: Delegate all business logic to core module
- Session Management: Create session in API layer, pass to core function
- Error Handling: Catch specific exceptions from core, convert to HTTP exceptions
- Global Exception Handler: Let unhandled exceptions bubble to global handler

Deviations (if any):
- None: This follows all established patterns

## Unit tests (required)

Add tests for:
- test_delete_work_endpoint_success_204: Mock delete_work to succeed, verify 204 response
- test_delete_work_endpoint_not_found_404: Mock delete_work to raise ValueError, verify 404 response with detail
- test_delete_work_endpoint_file_error_500: Mock delete_work to raise IOError, verify 500 response with detail
- test_delete_work_endpoint_generic_error_500: Mock delete_work to raise generic Exception, verify 500 response
- test_delete_work_endpoint_invalid_work_id_negative: Call with work_id=-1, verify 400 response
- test_delete_work_endpoint_invalid_work_id_zero: Call with work_id=0, verify 400 response
- test_delete_work_endpoint_calls_core_function: Verify delete_work called with correct work_id and session
- test_delete_work_endpoint_session_passed: Verify session from get_session() is passed to delete_work

Suggested locations:
- tests/unit/test_corpus_deletion_api.py (new file)

Mocking/fakes needed:
- Mock vulcanlab.data.work_operations.delete_work function
- Mock vulcanlab.data.database.get_session to return mock session
- Use FastAPI TestClient for making HTTP requests
- Mock session context manager (__enter__, __exit__)

## Acceptance criteria (checklist)

- [ ] DELETE endpoint added at /api/v1/corpus/works/{work_id}
- [ ] Endpoint returns 204 No Content on success
- [ ] Endpoint returns 404 with detail message when work not found
- [ ] Endpoint returns 500 with error details when deletion fails
- [ ] Endpoint validates work_id > 0 and returns 400 for invalid IDs
- [ ] Endpoint delegates to delete_work core function
- [ ] Router registered in main.py with /api/v1/corpus prefix
- [ ] All 8 unit tests written and passing
- [ ] Tests use mocked core function (no real deletion)
- [ ] API layer contains no business logic

## Manual verification

Steps:
1. Review code in src/vulcanlab_api/routers/corpus.py
2. Review router registration in src/vulcanlab_api/main.py
3. Run pytest tests/unit/test_corpus_deletion_api.py -v
4. Verify all tests pass
5. Start the FastAPI server locally
6. Use curl or Postman to test DELETE /api/v1/corpus/works/999
7. Verify appropriate error response for non-existent work

Expected results:
- All unit tests pass
- Endpoint returns correct status codes
- Error messages are descriptive but don't expose file system paths
- API layer is thin with no business logic

## Notes

- Reference existing corpus router endpoints for consistent error handling
- Use FastAPI's HTTPException for HTTP errors
- Don't expose internal file paths or stack traces in error responses
- Session lifecycle managed by get_session() context manager
- Status code 204 has no response body (return Response(status_code=204) or use status_code parameter)
- Validate work_id in endpoint, not in core function (separation of concerns)
- Consider adding OpenAPI documentation with response_description for clarity
- Error detail format should match existing corpus endpoint patterns
- Use pytest.mark.asyncio for async endpoint tests if needed
