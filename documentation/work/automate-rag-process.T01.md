# Ticket: automate-rag-process.T01 - Backend Auto RAG Endpoint and Orchestration

## Source
- Spec: documentation/work/automate-rag-process.spec.md
- Patterns: documentation/patterns.md

## Goal
- Implement the backend orchestration endpoint POST /api/v1/rag/auto that automates the complete RAG preparation pipeline
- Execute expand_query, vectorize_query, retrieve, and consolidate_context sequentially
- Return the query_id and status on success, with detailed error information on failure

## Scope
### In scope
- New POST /api/v1/rag/auto endpoint in src/vulcanlab_api/routers/rag.py
- Pydantic request/response schemas in src/vulcanlab_api/schemas/rag_queries.py
- Sequential orchestration of expand_query -> vectorize_query -> retrieve -> consolidate_context
- Error handling that preserves partial progress (query remains in DB on failure)
- Logging for observability (start/completion of each step)
- Unit tests for endpoint logic, mocking core functions

### Out of scope
- Modifying core RAG functions (expand_query, vectorize_query, retrieve, consolidate_context)
- Frontend changes (covered in T02)
- Retry logic or sophisticated error recovery
- Background job processing or async execution
- Configuration or settings for the automation

## Dependencies
- Depends on: None (uses existing core functions)
- Unblocks: T02 (frontend implementation)

## Implementation plan
1. Add Pydantic schemas to src/vulcanlab_api/schemas/rag_queries.py:
   - AutoRAGRequest: { query: str }
   - AutoRAGResponse: { query_id: int, status: str, message: str }
   - AutoRAGErrorResponse: { detail: str, failed_step: str }

2. Add endpoint POST /rag/auto to src/vulcanlab_api/routers/rag.py:
   - Validate request body (non-empty query string)
   - Log start of automation pipeline
   - Call expand_query(query=request.query, n=3, verbose=False)
     - This creates the Query record via save_expansion_to_db
     - Capture query_id from the result
   - Call vectorize_query(query_id=query_id, verbose=False)
   - Call retrieve(query_id=query_id, config_preset=None, verbose=False)
   - Call consolidate_context(query_id=query_id, config_preset=None, verbose=False)
   - Log successful completion
   - Return AutoRAGResponse with query_id and status="ready"

3. Error handling:
   - Wrap each step in try/except to catch specific exceptions
   - On expand_query failure: raise HTTPException 400 with detail and failed_step="expansion"
   - On vectorize_query failure: raise HTTPException 500 with detail and failed_step="embeddings"
   - On retrieve failure: raise HTTPException 500 with detail and failed_step="retrieval"
   - On consolidate_context failure: raise HTTPException 500 with detail and failed_step="consolidation"
   - Do NOT delete the query on failure (partial progress persists)

4. Register the endpoint in src/vulcanlab_api/main.py:
   - Ensure the rag router is included with prefix="/api/v1/rag"
   - Verify the route is accessible at POST /api/v1/rag/auto

5. Patterns to apply:
   - API versioning: Use /api/v1 prefix via main.py router inclusion
   - Core module independence: Only call existing core functions, no business logic in endpoint
   - Session management: Core functions handle their own sessions via get_session()
   - Error handling: Raise HTTPException for client/server errors, no generic try/except wrapper
   - Thin API layer: Orchestrate only, delegate to core module

6. Deviations (if any):
   - None - implementation fully aligns with patterns.md

## Unit tests (required)
- Add tests for:
  - Successful automation: mock all 4 core functions, verify query_id returned and status="ready"
  - Empty query validation: verify 400 error on empty string
  - expand_query failure: mock expand_query to raise ValueError, verify 400 response with failed_step="expansion"
  - vectorize_query failure: mock vectorize_query to raise exception, verify 500 response with failed_step="embeddings"
  - retrieve failure: mock retrieve to raise exception, verify 500 response with failed_step="retrieval"
  - consolidate_context failure: mock consolidate_context to raise exception, verify 500 response with failed_step="consolidation"
  - Query persistence on failure: mock expand_query to succeed and vectorize_query to fail, verify query exists in DB
  - Correct function call order: verify expand_query called before vectorize_query, etc.
  - ModelTier.FULL usage: verify expand_query uses FULL tier (check via mock call args or internal function behavior)

- Suggested locations:
  - tests/unit/test_rag_auto_endpoint.py

- Mocking/fakes needed:
  - Mock expand_query from vulcanlab.retrieval
  - Mock vectorize_query from vulcanlab.retrieval
  - Mock retrieve from vulcanlab.retrieval
  - Mock consolidate_context from vulcanlab.augmentation
  - Mock get_session for database interactions if needed
  - Use pytest-mock or unittest.mock.patch

## Acceptance criteria (checklist)
- [ ] POST /api/v1/rag/auto endpoint exists and is accessible
- [ ] Endpoint accepts JSON body with query field
- [ ] Endpoint returns 400 error if query is empty or missing
- [ ] Endpoint calls expand_query, vectorize_query, retrieve, consolidate_context in order
- [ ] expand_query uses n=3 and verbose=False
- [ ] Endpoint returns { query_id, status: "ready", message } on success
- [ ] On failure, endpoint returns { detail, failed_step } with appropriate HTTP status
- [ ] Query record persists in database even if pipeline fails after expand_query
- [ ] Endpoint logs start and completion of each step
- [ ] Unit tests pass for all success and error scenarios
- [ ] Pydantic schemas are defined in rag_queries.py

## Manual verification
- Steps:
  1. Start the FastAPI server (uvicorn)
  2. Send POST request to http://localhost:8000/api/v1/rag/auto with body: { "query": "What is working memory?" }
  3. Verify response contains query_id, status="ready", and message
  4. Check database to confirm Query record exists with original_query, expanded_queries, hyde_answer, etc.
  5. Verify query status transitions through: needs_embeddings -> needs_retrieval -> needs_consolidation -> ready
  6. Send POST request with empty query: { "query": "" }
  7. Verify 400 error response
  8. Simulate failure by stopping database or corrupting data
  9. Verify error response includes detail and failed_step
  10. Check server logs to confirm each step is logged

- Expected results:
  - Success response returns valid query_id
  - Query appears in /api/v1/rag/queries list with status "ready"
  - Empty query returns 400 error
  - Failures return appropriate error messages with failed_step
  - Logs show "Starting automation", "Expanding query", "Generating embeddings", etc.

## Notes
- The endpoint should NOT use try/except Exception to wrap everything; instead catch specific exceptions from each core function
- expand_query internally uses ModelTier.FULL (verified in src/vulcanlab/retrieval/query_expansion.py:280)
- The query is created via save_expansion_to_db inside expand_query, so query_id is available after that step
- If expand_query fails, no query record exists, so raise 400 (client error - bad query text)
- If later steps fail, the query exists but is incomplete, so raise 500 (server error)
- The core functions already handle their own database sessions, so no session management is needed in the endpoint
- Consider adding a timeout or max execution time if the LLM API is slow (optional, not required for T01)
- Reference existing endpoints in src/vulcanlab_api/routers/rag.py for patterns (e.g., run_expansion at line 444)
