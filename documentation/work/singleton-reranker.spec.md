# Title: Singleton Reranker Model for Performance Optimization

## Summary
- Convert the BGE reranker model loading from per-call to singleton pattern to eliminate redundant model initialization
- Create a dedicated reranker module (`src/vulcanlab/retrieval/reranker.py`) to encapsulate singleton logic and improve code organization
- Implement global/process-wide caching so the model loads once per process and is reused across all API requests
- Add observability logging to track model initialization, device selection, and memory usage
- Achieve near-zero overhead (< 10ms) for cached model access after initial load

## Problem / Context
- Currently, `_load_reranker()` in `retrieve.py` loads the BAAI/bge-reranker-large model from disk on every call to `retrieve()`
- This causes 1-3 seconds of latency per query due to model initialization overhead (loading weights, moving to GPU, etc.)
- The model is loaded repeatedly even though the same model instance could be reused across multiple queries
- Users experience this as slow retrieval performance, especially noticeable in interactive sessions with multiple queries
- Business impact: Poor user experience and inefficient resource utilization in production API

## Goals
- Eliminate redundant model loading by implementing singleton pattern
- Reduce per-query latency by 1-3 seconds (making cached calls nearly instant)
- Improve code organization by extracting reranker logic into dedicated module
- Maintain existing functionality and accuracy (no changes to reranking algorithm)
- Add observability for model initialization and resource usage

## Non-goals (Strict)
- Dynamic model selection or hot-swapping different reranker models
- Thread safety mechanisms (FastAPI uses process workers, not threading)
- Fallback to non-reranked results if model fails (fail fast instead)
- Configuration-based model selection (hardcoded BAAI/bge-reranker-large is sufficient)
- Distributed caching across multiple processes (each process has its own instance)

## Scope
### In scope
- Create new module `src/vulcanlab/retrieval/reranker.py`
- Implement singleton pattern using module-level cache variable
- Move `_load_reranker()` logic into new module with caching
- Refactor `retrieve.py` to use singleton reranker
- Add logging for model initialization (device, memory, timing)
- Add configurable debug logging for cache hits/misses
- Update any relevant unit tests

### Out of scope
- Changes to reranking algorithm or scoring logic
- Integration tests (unit tests only as per patterns.md)
- Thread safety locks or concurrent initialization handling
- Memory cleanup or model unloading mechanisms
- Configuration file changes (no new config parameters needed)

## Requirements (Functional)
- R1: The reranker model must load exactly once per process on first use
- R2: Subsequent calls to get the reranker must return the cached instance with < 10ms overhead
- R3: Device selection (CUDA vs CPU) must happen once during initialization based on torch.cuda.is_available()
- R4: The singleton must support the same interface as current _load_reranker() - return (tokenizer, model, device) tuple
- R5: Model initialization must use the same configuration as current implementation (BAAI/bge-reranker-large, float16 on GPU)
- R6: The module must integrate seamlessly with existing retrieve() function without changing its public API

## Requirements (Non-functional)
- Performance:
  - First call (cold start): Load model within existing timeframe (1-3 seconds is acceptable)
  - Cached calls: Return model instance in < 10ms
  - No memory leaks - single instance persists for process lifetime
- Reliability:
  - Raise clear exceptions if model fails to load (fail fast)
  - Log errors with sufficient context for debugging
  - Gracefully handle missing GPU (fallback to CPU)
- Security / Privacy:
  - Not applicable (no security-sensitive changes)
- Observability:
  - Log model initialization at INFO level (device, timing)
  - Support debug-level logging for cache hits (controlled by code variable, not always on)
  - Use existing logging patterns from the codebase

## Proposed Solution (High-level)
- Create `src/vulcanlab/retrieval/reranker.py` module with:
  - Module-level cache variable `_reranker_cache` (initially None)
  - Function `get_reranker()` that checks cache and loads model on first call
  - Private function `_initialize_reranker()` containing the actual model loading logic
  - Logging for initialization events (device, model name, timing)
- Update `retrieve.py`:
  - Replace `_load_reranker()` function call in `_rerank_chunks()` with `get_reranker()`
  - Import from new `reranker` module
  - Remove old `_load_reranker()` function
- Model initialization logic (same as current):
  - Detect CUDA availability
  - Load BAAI/bge-reranker-large tokenizer
  - Load model with float16 on GPU, float32 on CPU
  - Set model to eval mode
  - Return (tokenizer, model, device) tuple

## Interfaces / APIs / Contracts
- New public API in `reranker.py`:
  - `get_reranker() -> tuple[AutoTokenizer, AutoModelForSequenceClassification, str]`
    - Returns cached (tokenizer, model, device) tuple
    - Initializes on first call, returns cached instance on subsequent calls
    - Raises RuntimeError if model fails to load
- Internal API:
  - `_initialize_reranker() -> tuple[AutoTokenizer, AutoModelForSequenceClassification, str]`
    - Private function containing model loading logic
    - Called only by `get_reranker()` when cache is empty
- Changes to `retrieve.py`:
  - Replace `tokenizer, model, device = _load_reranker()` in `_rerank_chunks()`
  - With `tokenizer, model, device = get_reranker()` from reranker module
  - Remove `_load_reranker()` function definition

## Data Model / Storage
- Not applicable (no database or persistent storage changes)
- In-memory cache only: module-level variable `_reranker_cache`

## UX / Workflows
- User workflow unchanged - users call retrieve() API as before
- Performance improvement visible to users:
  - First query after process start: Same latency (1-3s for retrieval)
  - Subsequent queries: 1-3 seconds faster (no model loading overhead)
- No user-facing configuration changes needed

## Testing Plan
- Unit tests:
  - Test `get_reranker()` returns valid tokenizer, model, device on first call
  - Test subsequent calls return the same cached instance (verify object identity with `is`)
  - Test device selection logic (mock torch.cuda.is_available)
  - Test error handling when model loading fails
  - Test integration with `_rerank_chunks()` (ensure scores still computed correctly)
- Integration tests:
  - Not required per patterns.md (unit tests sufficient)
- Manual test plan:
  - Run retrieve() twice in same process, verify second call is faster
  - Check logs show model loaded only once
  - Test on GPU environment (if available) and CPU fallback
  - Verify memory usage stable across multiple queries (no leaks)

## Acceptance Criteria (Checklist)
- [ ] New module `src/vulcanlab/retrieval/reranker.py` created with singleton implementation
- [ ] `get_reranker()` function returns cached model instance on repeated calls
- [ ] Object identity test passes: `get_reranker() is get_reranker()` returns True
- [ ] `retrieve.py` updated to use `get_reranker()` instead of `_load_reranker()`
- [ ] Old `_load_reranker()` function removed from `retrieve.py`
- [ ] Logging outputs model initialization details (device, model name) on first load
- [ ] Debug logging variable added for cache hit tracking (default: disabled)
- [ ] Unit tests pass for singleton behavior and error handling
- [ ] Manual testing confirms 1-3 second speedup on subsequent queries
- [ ] No regression in retrieval accuracy (rerank scores unchanged)

## Rollout / Migration Plan
- No migration needed - code change only, backward compatible
- Deployment steps:
  - Deploy updated code to staging
  - Verify logs show singleton initialization
  - Run performance comparison tests (before/after)
  - Deploy to production
- Monitoring: Check application logs for initialization messages and any errors

## Risks and Alternatives
- Risks:
  - Memory persistence: Model stays in memory for process lifetime (acceptable trade-off for performance)
  - Process restart required to change models (mitigated by non-goal of dynamic model selection)
  - Slightly more complex debugging if initialization fails (mitigated by clear error logging)
- Alternatives considered:
  - Keep singleton in `retrieve.py`: Rejected in favor of better code organization in dedicated module
  - Thread-safe singleton with locks: Rejected as unnecessary for FastAPI process model
  - LRU cache decorator: Rejected because no cache eviction needed (single instance sufficient)
  - Class-based singleton: Rejected as overkill - simple module-level variable is cleaner

## Patterns and Standards Alignment (from documentation/patterns.md)
- Patterns applied:
  - Core Module Independence: New module stays in `src/vulcanlab/retrieval/`, no API/framework dependencies
  - Database Session Pattern: Not applicable (no database interaction)
  - Singleton Pattern: Following existing pattern from `app_config.py` (module-level cache variable)
  - Naming Conventions: Python `snake_case` for functions, module name `reranker.py`
- Deviations (if any):
  - None - implementation fully compliant with patterns.md

## Implementation Notes (Non-binding)
- The singleton pattern here mirrors `load_config()` in `app_config.py` (lines 119-154) which uses `_config_cache` global variable
- Consider using `logging.getLogger(__name__)` for module-specific logger
- Debug logging for cache hits can be controlled by module-level constant `DEBUG_LOG_CACHE_HITS = False`
- Model loading timing can be measured with `time.time()` or `time.perf_counter()` for logging
- The `_rerank_chunks()` function currently calls `_load_reranker()` at line 400 - this is the only call site to update
- No memory usage logging needed (keep implementation simple)
- No `force_reload` parameter needed at this time (can add later if testing requires it)

## Open Questions
- None - all questions resolved during spec review
