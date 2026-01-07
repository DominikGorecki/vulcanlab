# Ticket: corpus-search-feature.T03 - Hybrid Search with RRF Fusion

## Source

* Spec: documentation/work/corpus-search-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement hybrid search combining lexical and dense results using RRF fusion
* Support configurable RRF parameters (k constant, top-k candidates, weights)
* Add hybrid search API endpoint

## Scope

### In scope

* Core module: `src/vulcanlab/search/search_hybrid.py` for RRF fusion logic
* API router: Add `GET /api/v1/search/hybrid` endpoint to `src/vulcanlab_api/routers/search.py`
* RRF fusion algorithm with configurable k constant and weights
* Weight normalization (weights sum to 1.0)
* Unit tests for RRF fusion with overlapping and non-overlapping result sets

### Out of scope

* UI controls for RRF parameters (T04)
* Document viewer (T05)
* Reranking beyond RRF
* MMR diversity

## Dependencies

* Depends on: T01, T02
* Unblocks: T04

## Implementation plan

1. Implement `src/vulcanlab/search/search_hybrid.py`:
   - Function `search_hybrid(query: str, session: Session, page: int, page_size: int, headings_only: bool, rrf_k: int, dense_top_k: int, lexical_top_k: int, dense_weight: float, lexical_weight: float) -> tuple[list[dict], dict, int]`
   - Normalize weights to sum to 1.0: `total = dense_weight + lexical_weight; dense_weight /= total; lexical_weight /= total`
   - Call `search_lexical()` with `top_k=lexical_top_k` to get lexical candidates
   - Call `search_dense()` with `top_k=dense_top_k` to get dense candidates
   - Assign ranks: lexical results get ranks 1..N, dense results get ranks 1..M
   - Apply RRF formula for each unique chunk_id: `score = dense_weight * (1 / (rrf_k + dense_rank)) + lexical_weight * (1 / (rrf_k + lexical_rank))`
   - If chunk appears in only one result set, use rank 999999 for missing rank
   - Sort fused results by RRF score descending
   - Apply pagination to fused results
   - Return paginated results with RRF scores, dense_rank, lexical_rank, and RRFStats metadata
2. Add `GET /api/v1/search/hybrid` endpoint to `src/vulcanlab_api/routers/search.py`:
   - Query params: q, page, page_size, headings_only, rrf_k (default 60), dense_top_k (default 20), lexical_top_k (default 20), dense_weight (default 0.5), lexical_weight (default 0.5)
   - Validate inputs: weights must be > 0, k >= 1, top_k >= 1
   - Call `search_hybrid()` from core module
   - Define `RRFStats` Pydantic model: dense_candidates, lexical_candidates, fused_count, rrf_k
   - Return JSON response with results, pagination, and rrf_stats
   - Log hybrid search parameters at INFO level, execution time at DEBUG level
3. Update `vulcanlab_ui/src/app/search/page.tsx`:
   - Add "Both (Hybrid)" option to search mode toggle (now: Lexical, Dense, Hybrid)
   - When "Hybrid" selected, call `/api/v1/search/hybrid` with default RRF params
   - Display RRF stats in results section (e.g., "Fused 45 results from 20 dense + 25 lexical candidates")
   - Show both dense_rank and lexical_rank badges in result cards for hybrid results
   - Preserve existing UI from T01 and T02
4. Add unit tests in `tests/unit/test_search_hybrid.py`:
   - Mock search_lexical and search_dense functions
   - Test RRF fusion with overlapping results (chunk appears in both sets)
   - Test RRF fusion with non-overlapping results (disjoint sets)
   - Test RRF fusion with one empty result set (lexical or dense returns no results)
   - Test weight normalization (weights sum to 1.0)
   - Test RRF score calculation matches formula
   - Test sorting by RRF score descending
   - Test pagination applied to fused results
   - Test RRFStats metadata is correct

* Patterns to apply:
  * Three-tier architecture - Core in `src/vulcanlab/search/`, API in router, UI in `vulcanlab_ui`
  * Core module independence - No FastAPI imports, session passed as argument
  * API versioning - Use `/api/v1/search/hybrid` prefix
  * Global exception handling - Raise HTTPException for invalid inputs
  * Reuse existing search functions - Call search_lexical and search_dense

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * RRF fusion with overlapping results (chunk in both lexical and dense)
  * RRF fusion with non-overlapping results (disjoint sets)
  * RRF fusion with one empty result set (lexical=[], dense=[...])
  * RRF fusion with both empty result sets returns empty list
  * Weight normalization: (0.3, 0.7) -> (0.3, 0.7), (0.6, 0.4) -> (0.6, 0.4), (1, 1) -> (0.5, 0.5)
  * RRF score calculation: chunk in both sets gets combined score, chunk in one set uses rank 999999 for other
  * Results sorted by RRF score descending
  * Pagination offset and limit applied correctly to fused results
  * RRFStats contains correct counts: dense_candidates, lexical_candidates, fused_count
  * Headings_only filter applied to both lexical and dense searches
  * RRF k parameter affects score correctly (higher k = flatter distribution)

* Suggested locations:
  * `tests/unit/test_search_hybrid.py`

* Mocking/fakes needed:
  * Mock search_lexical function to return fixed results
  * Mock search_dense function to return fixed results
  * Mock database session (indirectly via mocked search functions)

## Acceptance criteria (checklist)

* [ ] Hybrid search endpoint `GET /api/v1/search/hybrid` returns RRF-fused results
* [ ] RRF fusion combines lexical and dense results using reciprocal rank formula
* [ ] Weights are normalized to sum to 1.0
* [ ] RRF score calculated correctly: weighted sum of 1/(k + rank) for each method
* [ ] Chunks appearing in only one result set use rank 999999 for missing method
* [ ] Fused results sorted by RRF score descending
* [ ] Pagination applied to fused results
* [ ] Hybrid search respects headings_only filter (passed to both searches)
* [ ] RRFStats metadata returned: dense_candidates, lexical_candidates, fused_count, rrf_k
* [ ] Search UI includes "Hybrid" mode option
* [ ] Hybrid results display RRF stats summary
* [ ] Hybrid results show both dense_rank and lexical_rank badges
* [ ] Unit tests pass with >80% coverage for hybrid search module
* [ ] Backend logs hybrid search parameters and execution time

## Manual verification

* Steps:
  1. Navigate to `/search` in browser
  2. Select "Hybrid" search mode via toggle
  3. Enter a query (e.g., "attention mechanisms")
  4. Click "Search"
  5. Verify results appear with RRF scores
  6. Verify RRF stats display (e.g., "Fused X results from Y dense + Z lexical")
  7. Verify result cards show both dense_rank and lexical_rank badges
  8. Check backend logs for hybrid search parameters (rrf_k, weights, top-k values)
  9. Try query that returns results in both lexical and dense (check overlapping chunks)
  10. Try query that favors one method (check non-overlapping chunks)
  11. Test pagination with hybrid results
  12. Enable "Headings only" and verify filter applies to both methods

* Expected results:
  * Hybrid search returns fused results ranked by RRF score
  * RRF stats display correctly (candidate counts, fused count)
  * Result cards show both dense and lexical ranks
  * Overlapping chunks (in both sets) have higher RRF scores
  * Non-overlapping chunks (in one set) have lower RRF scores
  * Pagination navigates through fused results
  * Headings only filter excludes sentence/paragraph chunks
  * Logs contain hybrid search parameters and timing

## Notes

* Requirements covered: R4, R17, R19
* RRF formula: `score = sum(weight_i / (k + rank_i))` for each method i
* Default RRF k = 60 (from spec), but configurable via API param
* Default weights: dense=0.5, lexical=0.5 (equal weighting)
* Weight normalization ensures relative importance is preserved
* Chunks appearing in only one result set get penalty rank (999999) for missing method
* This ticket implements RRF logic but does NOT add advanced UI controls (deferred to T04)
* RRF fusion happens in-memory after fetching candidates from both searches
* Consider caching fusion results for repeated queries in future iteration
* RRFStats helps users understand how fusion worked (transparency)
