# Ticket: sentence-based-chunk-search-filter.T04 - Implement Sentence Filtering in Retrieval Logic

## Source
- Spec: documentation/work/sentence-based-chunk-search-filter.spec.md
- Patterns: documentation/patterns.md

## Goal
- Update retrieve.py to filter chunks by sentence_count based on RAG config settings
- Apply filter to both dense and lexical retrieval queries
- Log filtering activity for observability

## Scope
### In scope
- Modify dense retrieval query in src/vulcanlab/retrieval/retrieve.py to add WHERE clause when filter enabled
- Modify lexical retrieval query to add WHERE clause when filter enabled
- Load min_sentence_filter_enabled and min_sentence_count from RAG config
- Exclude chunks with sentence_count=NULL when filter is enabled
- Add logging to indicate filter is active and how many chunks were filtered

### Out of scope
- Modifying RRF fusion or reranking logic
- Changing enrichment or MMR logic
- UI changes

## Dependencies
- Depends on: T01 (sentence_count column exists), T03 (config fields exist)
- Unblocks: T05 (end-to-end manual testing)

## Implementation plan
- In src/vulcanlab/retrieval/retrieve.py, locate the retrieve() function
- Load RAG config at the start of the function (use existing config loader pattern)
- Extract min_sentence_filter_enabled and min_sentence_count from config.retrieval
- Locate the dense retrieval SQL query (pgvector similarity search)
  - Add conditional WHERE clause: AND (sentence_count IS NOT NULL AND sentence_count >= :min_count) when filter enabled
  - Use parameterized query to pass min_sentence_count value
- Locate the lexical retrieval SQL query (full-text search)
  - Add same conditional WHERE clause
- Add logging before retrieval: "Sentence filter active: min_count=N" or "Sentence filter disabled"
- Add logging after retrieval: "Filtered X chunks below sentence threshold" (calculate from pre/post counts)
- Patterns to apply:
  - Core Module independence: retrieval logic in pure Python, use SQLAlchemy text() for queries
  - Database session management: session passed as argument
  - Configuration: load from RagConfig using existing loader pattern
- Deviations (if any):
  - None

## Unit tests (required)
- Add tests for:
  - Retrieval with min_sentence_filter_enabled=false returns all chunks regardless of sentence_count
  - Retrieval with min_sentence_filter_enabled=true filters chunks where sentence_count < threshold
  - Retrieval excludes chunks with sentence_count=NULL when filter enabled
  - Retrieval includes chunks with sentence_count=NULL when filter disabled
  - Dense retrieval applies filter correctly (mock query results)
  - Lexical retrieval applies filter correctly (mock query results)
  - Logging indicates filter is active and logs filtered count
  - Config with min_sentence_count=10 filters chunks with sentence_count=9
- Suggested locations:
  - tests/unit/test_retrieve.py
- Mocking/fakes needed:
  - Mock database session and query results
  - Mock RAG config loader to return test config
  - Mock chunks with various sentence_count values

## Acceptance criteria (checklist)
- [ ] Dense retrieval query filters by sentence_count when enabled
- [ ] Lexical retrieval query filters by sentence_count when enabled
- [ ] Chunks with sentence_count=NULL are excluded when filter enabled
- [ ] Filter is NOT applied when min_sentence_filter_enabled=false
- [ ] Logging indicates filter status before retrieval
- [ ] Logging shows count of filtered chunks after retrieval
- [ ] Unit tests pass for all filtering scenarios
- [ ] Parameterized queries prevent SQL injection

## Manual verification
- Steps:
  1. Create test database with chunks having various sentence_count values (3, 5, 8, 10, NULL)
  2. Create a query and run retrieval with filter disabled
  3. Verify all chunks returned (check logs and results)
  4. Enable filter with min_sentence_count=5 in RAG config
  5. Run same query again
  6. Verify only chunks with sentence_count >= 5 are returned
  7. Verify chunks with sentence_count=NULL are excluded
  8. Check logs for "Sentence filter active" message
  9. Verify log shows filtered count
- Expected results:
  - With filter disabled: all chunks returned including NULL
  - With filter enabled (min=5): only chunks with sentence_count >= 5
  - Chunks with sentence_count < 5 excluded
  - Chunks with sentence_count=NULL excluded
  - Logs clearly indicate filter status and activity

## Notes
- The spec states chunks with sentence_count=NULL should be excluded when filter is enabled (conservative approach per user answer Q2)
- Use SQL: WHERE (sentence_count IS NOT NULL AND sentence_count >= :min_count) for filtering
- Both dense and lexical queries need the same filter applied for consistency
- Index on sentence_count will be used by query planner for efficient filtering
