# Ticket: simplify-ui-with-simple-conversion-focus.T03 - Backend API: Simple Conversion History Endpoint

## Source
- Spec: documentation/work/simplify-ui-with-simple-conversion-focus.spec.md
- Patterns: documentation/patterns.md

## Goal
- Create GET /api/simple-conversion/history endpoint returning list of past simple conversion works
- Filter works by presence of simple_conversion_mode in processing_status JSON
- Include summary data: metadata, counts, status, error messages
- Sort results by created_at DESC (most recent first)

## Scope
### In scope
- New GET /api/simple-conversion/history endpoint in simple conversion router
- Database query filtering works with processing_status ? 'simple_conversion_mode'
- Aggregate chunk counts: total, heading chunks (H1-H5), content chunks (level ends with -chunk)
- Response includes: work_id, title, author, year, created_at, classification, mode, status, token_count, chunk_count, heading_chunk_count, content_chunk_count, error_message
- Status determination logic: complete vs failed based on processing_status fields
- Sort by created_at DESC using new index from T01
- Pydantic response model for type safety

### Out of scope
- Pagination or filtering query parameters (load all simple conversions)
- Authentication or user-specific filtering
- Modifying existing endpoints
- Frontend integration (handled in T05)

## Dependencies
- Depends on: T01 (indexes for query performance)
- Unblocks: T05 (frontend history section needs this endpoint)

## Implementation plan
1. Locate simple conversion router (likely src/vulcanlab_api/routers/simple_conversion.py)
2. Create new GET /history endpoint handler function
3. Define Pydantic response models: SimpleConversionHistoryItem and SimpleConversionHistoryResponse
4. Implement core query function in src/vulcanlab module:
   - Query works table with WHERE processing_status ? 'simple_conversion_mode'
   - Join with chunks table to aggregate counts
   - Use COUNT(*) FILTER (WHERE level IN ('H1', 'H2', 'H3', 'H4', 'H5')) for heading_chunk_count
   - Use COUNT(*) FILTER (WHERE level LIKE '%-chunk' OR level = 'chunk') for content_chunk_count
   - ORDER BY created_at DESC
5. Extract mode from processing_status->'simple_conversion_mode'
6. Determine status: failed if simple_conversion_step = 'failed' or simple_conversion_error exists, else complete
7. Extract error_message from processing_status->'simple_conversion_error' if exists
8. Pass database session explicitly to query function
9. Return list wrapped in response model
10. Add error handling for database query failures

- Patterns to apply:
  - **Thin API Layer** - Router calls core module function for business logic
  - **Explicit Session Passing** - Pass db session to query function as parameter
  - **ORM with SQLAlchemy** - Use declarative models from src/vulcanlab/data/models
  - **Global Exception Handlers** - Raise HTTPException for expected errors (empty results OK), let global handler catch db errors

- Deviations (if any):
  - None - follows established patterns for query endpoints

## Unit tests (required)
- Add tests for:
  - Query returns empty list when no simple conversion works exist
  - Query returns works with simple_conversion_mode in processing_status
  - Query excludes works without simple_conversion_mode
  - Query sorts results by created_at DESC (most recent first)
  - Chunk count aggregation correctly differentiates heading vs content chunks
  - Status determination: complete when simple_conversion_step = 'complete'
  - Status determination: failed when simple_conversion_error exists
  - Error message extracted correctly from processing_status JSON
  - Mode extracted correctly (automatic/manual) from processing_status
  - Response includes all required fields per spec
- Suggested locations:
  - tests/unit/test_simple_conversion_history_api.py (new file)
  - tests/unit/test_simple_conversion_history_query.py (core module query logic)
- Mocking/fakes needed:
  - Mock database session with fake works and chunks data
  - Mock processing_status JSON structures for various scenarios
  - No real database connections in unit tests

## Acceptance criteria (checklist)
- [ ] GET /api/simple-conversion/history endpoint exists
- [ ] Endpoint returns JSON array of simple conversion works
- [ ] Works filtered by presence of simple_conversion_mode in processing_status
- [ ] Results sorted by created_at DESC
- [ ] Each item includes all required fields: work_id, title, author, year, created_at, classification, mode, status, token_count, chunk_count, heading_chunk_count, content_chunk_count, error_message
- [ ] Heading chunk count includes only H1-H5 level chunks
- [ ] Content chunk count includes chunks with level ending in -chunk
- [ ] Status correctly identifies failed conversions
- [ ] Error message included for failed conversions
- [ ] Empty array returned when no simple conversions exist
- [ ] Unit tests cover query filtering, sorting, aggregation, and status logic

## Manual verification
- Steps:
  1. Ensure database has at least 2 simple conversion works (one success, one failed)
  2. GET /api/simple-conversion/history
  3. Verify response is JSON array sorted by created_at DESC
  4. Check first item has all required fields
  5. Verify heading_chunk_count + content_chunk_count <= chunk_count
  6. Find failed conversion in list and verify status = 'failed' and error_message is not null
  7. Create new simple conversion and verify it appears at top of list
- Expected results:
  - Response format matches spec example JSON
  - Most recent conversion appears first
  - Chunk counts accurately reflect database state
  - Failed conversions show error messages
  - Empty database returns empty array, not 404

## Notes
- The query should use the indexes created in T01 for optimal performance
- Consider using SQLAlchemy's func.count() with filter clause for aggregations
- JSON field access in SQLAlchemy: processing_status.op('?')('simple_conversion_mode') for key existence check
- Extract nested JSON values: processing_status['simple_conversion_mode'].astext for mode string
- Classification field should come from work metadata (small/large determination logic may already exist)
- Token count should be available in work record or processing_status
- Existing GET /api/simple-conversion/results/{work_id} endpoint provides full details, this endpoint provides summary list
