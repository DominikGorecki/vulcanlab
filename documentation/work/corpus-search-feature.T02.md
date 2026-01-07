# Ticket: corpus-search-feature.T02 - Dense Vector Search Backend

## Source

* Spec: documentation/work/corpus-search-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement dense (vector) search backend using pgvector similarity
* Reuse RAG embedding model and vectorization configuration
* Add dense search API endpoint and integrate with existing search UI

## Scope

### In scope

* Core module: `src/vulcanlab/search/search_dense.py` for pgvector similarity queries
* API router: Add `GET /api/v1/search/dense` endpoint to `src/vulcanlab_api/routers/search.py`
* Query vectorization using existing RAG embedding infrastructure
* Unit tests for dense search with mock embeddings

### Out of scope

* Hybrid search with RRF fusion (T03)
* UI controls for search mode selection (T04)
* Document viewer (T05)
* Reranking or MMR diversity
* Embedding generation for new works (uses existing embeddings)

## Dependencies

* Depends on: T01
* Unblocks: T03, T04

## Implementation plan

1. Implement `src/vulcanlab/search/search_dense.py`:
   - Function `search_dense(query: str, session: Session, page: int, page_size: int, headings_only: bool, top_k: int) -> tuple[list[dict], int]`
   - Reuse embedding generation logic from `vulcanlab.retrieval.retrieve` or create shared utility
   - Generate query vector from query string using same model as RAG (check config)
   - Execute pgvector similarity query: `SELECT ... FROM chunks JOIN embeddings ON chunks.id = embeddings.chunk_id WHERE ... ORDER BY embedding <=> query_vector LIMIT top_k`
   - If `headings_only=True`, filter to `level IN ('H1', 'H2', 'H3', 'H4', 'H5')`
   - Handle missing embeddings gracefully: skip chunks without embeddings
   - JOIN with `works` table to fetch bibliographic info
   - Call `build_breadcrumb()` from T01 for each result
   - Calculate similarity score: `1 - (embedding <=> query_vector)` for display
   - Return paginated results with metadata and similarity scores
2. Add `GET /api/v1/search/dense` endpoint to `src/vulcanlab_api/routers/search.py`:
   - Same query parameters as lexical endpoint (q, page, page_size, headings_only, top_k)
   - Validate inputs
   - Call `search_dense()` from core module
   - Return JSON response matching `SearchResult` schema (reuse from T01)
   - Log search parameters at INFO level, execution time at DEBUG level
3. Update `vulcanlab_ui/src/app/search/page.tsx`:
   - Add temporary toggle or radio buttons for search mode: "Lexical" vs "Dense"
   - Update fetch logic to call `/api/v1/search/lexical` or `/api/v1/search/dense` based on selection
   - Display similarity score in result cards for dense search
   - Preserve existing UI from T01 (no major changes, just add mode toggle)
4. Add unit tests in `tests/unit/test_search_dense.py`:
   - Mock database session with chunks and embeddings
   - Mock embedding generation (return fixed query vector)
   - Test dense search returns results ordered by similarity
   - Test headings_only filter works with dense search
   - Test missing embeddings are skipped (no errors)
   - Test pagination works correctly
   - Test similarity score calculation (1 - distance)

* Patterns to apply:
  * Three-tier architecture - Core in `src/vulcanlab/search/`, API in router, UI in `vulcanlab_ui`
  * Core module independence - No FastAPI imports, session passed as argument
  * API versioning - Use `/api/v1/search/dense` prefix
  * Global exception handling - Raise HTTPException, let middleware handle
  * Reuse existing infrastructure - Use RAG embedding model and config

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Dense search with mock query vector returns results ordered by similarity
  * Dense search excludes chunks without embeddings (no crash)
  * Dense search similarity score calculated as 1 - distance
  * Headings only filter works with dense search (level IN H1-H5)
  * Dense search joins with works table and includes bibliographic metadata
  * Dense search calls breadcrumb_builder for each result
  * Pagination works correctly with dense search
  * Top-k parameter limits candidate results before pagination
  * Empty query or invalid vector raises appropriate error

* Suggested locations:
  * `tests/unit/test_search_dense.py`

* Mocking/fakes needed:
  * Mock SQLAlchemy session
  * Mock chunks table with embeddings
  * Mock works table
  * Mock embedding generation function (return fixed numpy array or list)
  * Mock pgvector distance operator (<=>)

## Acceptance criteria (checklist)

* [ ] Dense search endpoint `GET /api/v1/search/dense` returns results ordered by similarity
* [ ] Dense search reuses RAG embedding model and configuration
* [ ] Dense search skips chunks without embeddings (no errors)
* [ ] Dense search joins with works table for bibliographic info
* [ ] Dense search generates breadcrumbs using breadcrumb_builder
* [ ] Dense search respects headings_only filter
* [ ] Dense search respects pagination parameters
* [ ] Search UI includes toggle to select "Lexical" or "Dense" mode
* [ ] Dense search results display similarity score
* [ ] Unit tests pass with >80% coverage for dense search module
* [ ] Backend logs search parameters and execution time

## Manual verification

* Steps:
  1. Ensure database has embeddings for at least some chunks (run vectorization if needed)
  2. Navigate to `/search` in browser
  3. Select "Dense" search mode via toggle
  4. Enter a semantic query (e.g., "cognitive processes")
  5. Click "Search"
  6. Verify results appear ordered by semantic similarity
  7. Verify similarity scores display in result cards
  8. Check "Headings only" and search again
  9. Verify only H1-H5 chunks appear
  10. Test pagination with dense search results
  11. Check backend logs for search parameters and timing

* Expected results:
  * Dense search returns semantically relevant results
  * Results ordered by similarity score (highest first)
  * Similarity score displays in result cards
  * Breadcrumbs, bibliographic info, metadata display correctly
  * Headings only filter works with dense search
  * Pagination navigates through dense search results
  * No errors when some chunks lack embeddings
  * Logs contain dense search parameters and execution time

## Notes

* Requirements covered: R3 (dense mode only), R15, R19
* Dense search reuses embedding model from RAG retrieval (check vulcanlab.config for model name)
* Embedding generation may add latency; consider caching query vectors in future
* Similarity score formula: 1 - (embedding <=> query_vector) where <=> is cosine distance
* pgvector extension must be installed and embeddings table populated
* This ticket does NOT implement search mode UI enhancements (deferred to T04)
* Temporary mode toggle added in this ticket will be replaced with better UI in T04
* Consider using IVFFlat or HNSW index on embeddings for performance with large datasets
