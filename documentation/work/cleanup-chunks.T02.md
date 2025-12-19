# Ticket: cleanup-chunks.T02 - API Endpoints for Chunk Search and Deletion

## Source
- Spec: documentation/work/cleanup-chunks.spec.md
- Patterns: documentation/patterns.md

## Goal
- Create FastAPI router with three endpoints for chunk search, deletion, and descendant preview
- Implement thin API layer that orchestrates calls to core module functions from T01
- Follow patterns.md API standards: /api/v1 versioning, global error handling, proper response models
- Add unit tests for request validation and response formatting

## Scope
### In scope
- Create FastAPI router at `src/vulcanlab_api/routers/chunks.py` (or update if exists)
- Implement `GET /api/v1/chunks/search` endpoint with pagination
- Implement `GET /api/v1/chunks/{chunk_id}/descendants` endpoint for modal preview
- Implement `DELETE /api/v1/chunks/{chunk_id}` endpoint with cascading deletion
- Pydantic response models for all endpoints
- Request validation (query parameter validation, path parameter validation)
- Database session management using existing dependency injection pattern
- Unit tests for endpoint logic (mocking core functions and database session)
- Wire router into main.py with /api/v1 prefix

### Out of scope
- Core logic implementation (already in T01)
- UI components (covered in T03-T04)
- Authentication/authorization (not required per spec)
- Rate limiting or caching
- Integration tests with real database

## Dependencies
- Depends on: T01 (requires chunk_operations functions)
- Unblocks: T03 (UI needs these endpoints)

## Implementation plan
1. Create or update `src/vulcanlab_api/routers/chunks.py`
2. Import dependencies:
   - FastAPI Router, HTTPException, Query, Path
   - Pydantic BaseModel for response schemas
   - Core functions from vulcanlab.data.chunk_operations
   - Database session dependency (existing pattern in other routers)
3. Define Pydantic response models:
   - `ChunkSearchResult`: id, content_preview, heading_breadcrumbs, level, work_id, start_line, end_line
   - `PaginationInfo`: page, page_size, total_results, has_next, has_prev
   - `ChunkSearchResponse`: results (list), pagination
   - `DescendantInfo`: id, level, heading_breadcrumbs
   - `DescendantsResponse`: descendants (list), total_count
   - `ChunkDeleteResponse`: deleted_chunk_id, descendants_deleted (list), total_deleted
4. Implement `GET /api/v1/chunks/search`:
   - Query parameters: q (str, required), page (int, default=1, min=1)
   - Validate q is not empty, raise 400 if empty
   - Call search_chunks_lexical(q, page, 25, session)
   - Truncate content to 100 characters for content_preview
   - Calculate has_next: (page * 25) < total_results
   - Calculate has_prev: page > 1
   - Return ChunkSearchResponse
   - Let global error handler catch exceptions for 500 errors
5. Implement `GET /api/v1/chunks/{chunk_id}/descendants`:
   - Path parameter: chunk_id (int)
   - Verify chunk exists, raise 404 if not found
   - Call get_all_descendants(chunk_id, session)
   - Map descendants to DescendantInfo format
   - Return DescendantsResponse with total_count
6. Implement `DELETE /api/v1/chunks/{chunk_id}`:
   - Path parameter: chunk_id (int)
   - Get all descendants first (for response)
   - Call delete_chunk_cascade(chunk_id, session)
   - Commit session transaction
   - Return ChunkDeleteResponse with deleted info
   - Catch ValueError (chunk not found) and raise 404
   - Catch SQLAlchemyError and raise 500 with generic message (let global handler log details)
7. Wire router into main.py:
   - Add `app.include_router(chunks_router, prefix="/api/v1/chunks", tags=["chunks"])`
   - Ensure prefix is defined in main.py, not in router file (per patterns.md)
8. Add logging at INFO level for successful deletions (already in core, API just passes through)

- Patterns to apply:
  - **API versioning**: Use /api/v1 prefix in main.py router inclusion
  - **Thin API layer**: Orchestrate core functions, no business logic in endpoints
  - **Global error handling**: Raise HTTPException or specific errors, let middleware handle logging
  - **Session management**: Use dependency injection for database session (existing pattern)
  - **Error handling**: Raise specific HTTPException (400, 404) for client errors, let 500 be handled globally

- Deviations (if any):
  - None: Fully aligned with patterns.md

## Unit tests (required)
- Add tests for:
  - **test_search_endpoint_success**: Mock search_chunks_lexical, verify 200 response with correct structure
  - **test_search_endpoint_empty_query**: Send empty q parameter, verify 400 Bad Request
  - **test_search_endpoint_pagination_has_next**: Mock 50 results on page 1, verify has_next=True
  - **test_search_endpoint_pagination_has_prev**: Request page 2, verify has_prev=True
  - **test_search_endpoint_pagination_first_page**: Request page 1, verify has_prev=False
  - **test_search_endpoint_content_truncation**: Mock chunk with 200 char content, verify preview is 100 chars
  - **test_search_endpoint_no_results**: Mock empty results, verify empty list with total_results=0
  - **test_descendants_endpoint_success**: Mock get_all_descendants, verify 200 response
  - **test_descendants_endpoint_chunk_not_found**: Mock chunk doesn't exist, verify 404
  - **test_descendants_endpoint_no_descendants**: Mock empty descendants list, verify total_count=0
  - **test_delete_endpoint_success**: Mock delete_chunk_cascade, verify 200 with correct count
  - **test_delete_endpoint_chunk_not_found**: Mock ValueError from core, verify 404
  - **test_delete_endpoint_returns_descendants**: Mock deletion with children, verify descendants_deleted list populated
  - **test_delete_endpoint_commits_transaction**: Verify session.commit() is called
  - **test_delete_endpoint_rollback_on_error**: Mock SQLAlchemyError, verify session.rollback() called (if explicit rollback pattern used)
  - **test_search_endpoint_default_page**: Don't send page parameter, verify defaults to page=1
  - **test_search_endpoint_invalid_page**: Send page=0 or page=-1, verify 400 or appropriate error

- Suggested locations:
  - `tests/unit/test_chunks_api.py` (new file)

- Mocking/fakes needed:
  - Mock all chunk_operations functions (search_chunks_lexical, get_all_descendants, delete_chunk_cascade)
  - Mock database session and session.commit()
  - Use FastAPI TestClient for endpoint testing
  - Mock Chunk objects for test data

## Acceptance criteria (checklist)
- [ ] Router file `src/vulcanlab_api/routers/chunks.py` created or updated
- [ ] All three endpoints implemented: GET /search, GET /{id}/descendants, DELETE /{id}
- [ ] Pydantic models defined for all request/response schemas
- [ ] Search endpoint validates query parameter and returns 400 for empty query
- [ ] Search endpoint truncates content to 100 characters in response
- [ ] Search endpoint calculates has_next and has_prev correctly
- [ ] Descendants endpoint returns 404 for non-existent chunk
- [ ] Delete endpoint returns 404 for non-existent chunk (ValueError from core)
- [ ] Delete endpoint commits transaction after successful deletion
- [ ] Delete endpoint returns list of descendants that were deleted
- [ ] Router wired into main.py with /api/v1 prefix
- [ ] All unit tests pass with mocked dependencies
- [ ] Endpoints use existing session dependency injection pattern
- [ ] Error responses follow spec format (detail field)

## Manual verification
- Steps:
  1. Run pytest on `tests/unit/test_chunks_api.py`
  2. Start FastAPI dev server: `uvicorn vulcanlab_api.main:app --reload`
  3. Open Swagger docs at http://localhost:8000/docs
  4. Verify three new endpoints appear under /api/v1/chunks
  5. Test search endpoint with query parameter in Swagger UI
  6. Test descendants endpoint with valid chunk_id
  7. Test delete endpoint (use test database or mock)

- Expected results:
  - All unit tests pass
  - Swagger UI shows all three endpoints with correct schemas
  - Search returns paginated results
  - Descendants endpoint returns list of children
  - Delete endpoint removes chunk and returns confirmation
  - 400 errors for invalid input, 404 for missing chunks

## Notes
- Use existing database session dependency pattern from other routers (likely `get_db()` or similar)
- Content truncation: `chunk.content[:100]` or use Python slice
- For has_next calculation: `(page * page_size) < total_results`
- For has_prev calculation: `page > 1`
- Session commit should be explicit in DELETE endpoint: `session.commit()`
- Consider transaction rollback on error: wrap delete in try/except, rollback on exception
- Response models ensure consistent API contract and auto-generate OpenAPI docs
- Query validation: use FastAPI `Query()` with constraints like `min_length=1`
- Path validation: use FastAPI `Path()` with constraints like `gt=0` for positive integers
- The DELETE endpoint should call get_all_descendants() BEFORE deletion to include in response
- Logging is handled at core level, API just needs to ensure errors are raised properly
