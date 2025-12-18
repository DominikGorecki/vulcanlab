# Ticket: singleton-reranker.T02 - Integrate Singleton Reranker into Retrieve Pipeline

## Source
- Spec: documentation/work/singleton-reranker.spec.md
- Patterns: documentation/patterns.md

## Goal
- Replace `_load_reranker()` calls in `retrieve.py` with singleton `get_reranker()`
- Remove old `_load_reranker()` function from `retrieve.py`
- Verify retrieval pipeline maintains accuracy and achieves performance improvements

## Scope
### In scope
- Update `_rerank_chunks()` in `retrieve.py` to use `get_reranker()` from reranker module
- Remove `_load_reranker()` function definition from `retrieve.py`
- Add unit tests verifying integration preserves reranking behavior
- Manual performance verification (first vs subsequent queries)

### Out of scope
- Changes to reranking algorithm or scoring logic
- Changes to `retrieve()` public API
- Integration tests with real database
- Frontend changes

## Dependencies
- Depends on: T01 (reranker module must exist)
- Unblocks: none (completes feature)

## Implementation plan
- Open `src/vulcanlab/retrieval/retrieve.py`
- Add import at top of file: `from vulcanlab.retrieval.reranker import get_reranker`
- Locate `_rerank_chunks()` function (currently around line 380-432)
- Replace line 400 `tokenizer, model, device = _load_reranker()` with `tokenizer, model, device = get_reranker()`
- Locate `_load_reranker()` function definition (currently lines 359-377)
- Delete entire `_load_reranker()` function (19 lines)
- Verify no other references to `_load_reranker` exist in codebase:
  - Search: `grep -r "_load_reranker" src/` to confirm only historical removal
- Run existing unit tests for `retrieve.py` to verify no regressions
- Run manual tests to verify performance improvement
- Patterns to apply:
  - Core Module Independence: Import stays within `src/vulcanlab` (reranker is core module)
  - Database Session Pattern: Not applicable (no session changes)
  - Naming Conventions: Maintain existing `snake_case` conventions
- Deviations (if any):
  - None - fully compliant with patterns.md

## Unit tests (required)
- Add tests for:
  - Test `_rerank_chunks()` still produces valid rerank scores with singleton reranker
  - Test rerank scores identical to old implementation (regression test: compare old vs new scores for same input)
  - Test `_rerank_chunks()` calls `get_reranker()` exactly once per invocation
  - Test multiple calls to `retrieve()` in same process reuse singleton (mock `get_reranker` to count calls)
  - Test error propagation: if `get_reranker()` raises RuntimeError, `_rerank_chunks()` propagates it
  - Test device handling: verify device from `get_reranker()` used correctly in tokenizer calls
- Suggested locations:
  - `tests/unit/test_retrieve.py` (add new test cases to existing file if it exists)
  - `tests/unit/test_rerank_integration.py` (new file if retrieve.py tests don't exist)
- Mocking/fakes needed:
  - Mock `get_reranker()` to return mock tokenizer, model, device
  - Mock model inference outputs (logits) for score validation
  - Mock database session and query objects
  - Use `unittest.mock.patch` to intercept `get_reranker()` calls and verify call count

## Acceptance criteria (checklist)
- [ ] Import added: `from vulcanlab.retrieval.reranker import get_reranker`
- [ ] `_rerank_chunks()` updated to call `get_reranker()` instead of `_load_reranker()`
- [ ] `_load_reranker()` function completely removed from `retrieve.py`
- [ ] No remaining references to `_load_reranker` in codebase (grep verification)
- [ ] Existing unit tests for retrieve pipeline still pass
- [ ] New unit tests pass for integration behavior
- [ ] Manual test confirms first query initializes model (logs show initialization)
- [ ] Manual test confirms second query reuses model (no reinitialization log, 1-3s faster)
- [ ] Rerank scores match previous implementation (no accuracy regression)

## Manual verification
- Steps:
  - Ensure database has at least one query with `vector_status='vec'` (e.g., query_id=1)
  - Run retrieve in Python:
    ```python
    from vulcanlab.retrieval.retrieve import retrieve
    import time
    # First call - cold start
    start1 = time.time()
    result1 = retrieve(query_id=1, verbose=True)
    elapsed1 = time.time() - start1
    # Second call - cached reranker
    start2 = time.time()
    result2 = retrieve(query_id=1, verbose=True)
    elapsed2 = time.time() - start2
    print(f"First call: {elapsed1:.2f}s, Second call: {elapsed2:.2f}s")
    print(f"Speedup: {elapsed1 - elapsed2:.2f}s")
    ```
  - Check logs for reranker initialization message on first call only
  - Verify second call is 1-3 seconds faster
  - Compare `result1.chunks` and `result2.chunks` rerank scores (should be identical)
- Expected results:
  - First call shows INFO log: "Loaded reranker model BAAI/bge-reranker-large on [device] in [X.XX]s"
  - Second call shows no reranker initialization log
  - Second call 1-3 seconds faster than first
  - Both results have identical rerank scores for same chunks
  - No errors or warnings

## Notes
- The only call site is in `_rerank_chunks()` at line 400 (verified from spec implementation notes)
- Reranking logic unchanged - only loading mechanism changes
- Performance improvement visible in second and subsequent queries within same process
- Each FastAPI worker process has independent singleton (workers don't share memory)
- If retrieve() called with different queries, still benefits from cached model
- GPU/CPU device selection happens once on first load, persists for process
- Edge case: If process restarts, model reloads on first query (expected behavior)
- No changes to `retrieve()` function signature or return type
- No changes to RetrievalResult or RetrievedChunk dataclasses
