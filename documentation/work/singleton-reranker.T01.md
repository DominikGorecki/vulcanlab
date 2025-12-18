# Ticket: singleton-reranker.T01 - Create Singleton Reranker Module with Caching

## Source
- Spec: documentation/work/singleton-reranker.spec.md
- Patterns: documentation/patterns.md

## Goal
- Create new `src/vulcanlab/retrieval/reranker.py` module implementing singleton pattern for BGE reranker model
- Provide `get_reranker()` function that loads model once per process and returns cached instance on subsequent calls
- Add initialization logging for observability (device, timing)

## Scope
### In scope
- Create `src/vulcanlab/retrieval/reranker.py` module
- Implement module-level cache variable `_reranker_cache`
- Implement `get_reranker()` public function returning cached (tokenizer, model, device) tuple
- Implement `_initialize_reranker()` private function with model loading logic
- Add INFO-level logging for model initialization (device, model name, timing)
- Add debug logging toggle via module constant `DEBUG_LOG_CACHE_HITS`
- Device selection logic (CUDA if available, else CPU)
- Error handling with clear exceptions on load failure
- Complete unit test suite for singleton behavior

### Out of scope
- Integration with `retrieve.py` (covered in T02)
- Changes to reranking algorithm
- Thread safety mechanisms
- force_reload parameter or cache invalidation

## Dependencies
- Depends on: none (foundational module)
- Unblocks: T02

## Implementation plan
- Create `src/vulcanlab/retrieval/reranker.py` file
- Add module-level cache variable: `_reranker_cache: tuple | None = None`
- Add debug toggle constant: `DEBUG_LOG_CACHE_HITS = False`
- Set up module logger: `logger = logging.getLogger(__name__)`
- Implement `_initialize_reranker()` private function:
  - Detect device: `device = "cuda" if torch.cuda.is_available() else "cpu"`
  - Record start time with `time.perf_counter()`
  - Load tokenizer: `AutoTokenizer.from_pretrained("BAAI/bge-reranker-large")`
  - Load model conditionally:
    - GPU: `AutoModelForSequenceClassification.from_pretrained(model_name, torch_dtype=torch.float16).to(device)`
    - CPU: `AutoModelForSequenceClassification.from_pretrained(model_name).to(device)`
  - Set model to eval mode: `model.eval()`
  - Calculate elapsed time
  - Log at INFO level: device, model name, initialization time
  - Return `(tokenizer, model, device)` tuple
  - Wrap in try/except to raise `RuntimeError` with context on failure
- Implement `get_reranker()` public function:
  - Check if `_reranker_cache is not None`
  - If cached: log debug message (if `DEBUG_LOG_CACHE_HITS` enabled) and return cache
  - If not cached: call `_initialize_reranker()`, store in `_reranker_cache`, return tuple
- Add module docstring explaining singleton pattern and usage
- Patterns to apply:
  - Core Module Independence: No FastAPI or framework imports, pure Python core logic
  - Singleton Pattern: Module-level cache variable matching `app_config.py` pattern (lines 96, 119-154)
  - Naming Conventions: `snake_case` for functions, private functions prefixed with `_`
  - Error Handling: Raise specific exceptions (RuntimeError) for load failures, not generic catches
- Deviations (if any):
  - None - fully compliant with patterns.md

## Unit tests (required)
- Add tests for:
  - Test `get_reranker()` first call returns valid (tokenizer, model, device) tuple with all non-None values
  - Test model is instance of `AutoModelForSequenceClassification`
  - Test tokenizer is instance of `AutoTokenizer`
  - Test device is either "cuda" or "cpu" string
  - Test subsequent calls return same cached instance (verify object identity: `get_reranker() is get_reranker()`)
  - Test singleton persists: call 3+ times, verify all return identical objects via `id()` comparison
  - Test device selection when CUDA available (mock `torch.cuda.is_available()` to return True, verify device="cuda")
  - Test device selection when CUDA unavailable (mock to return False, verify device="cpu")
  - Test error handling when model loading fails (mock `AutoModelForSequenceClassification.from_pretrained` to raise exception, verify RuntimeError raised with context)
  - Test cache isolation: modify returned model eval state, verify subsequent calls still return cached instance
  - Test debug logging toggle: set `DEBUG_LOG_CACHE_HITS=True`, verify log messages on cache hit
- Suggested locations:
  - `tests/unit/test_singleton_reranker.py` (new file)
- Mocking/fakes needed:
  - Mock `torch.cuda.is_available()` for device selection tests
  - Mock `AutoTokenizer.from_pretrained()` to return mock tokenizer
  - Mock `AutoModelForSequenceClassification.from_pretrained()` to return mock model
  - Mock `time.perf_counter()` for timing tests (optional)
  - Use `unittest.mock.patch` for patching module-level cache to reset between tests
  - Mock logger to verify INFO and DEBUG log calls

## Acceptance criteria (checklist)
- [ ] File `src/vulcanlab/retrieval/reranker.py` created
- [ ] `get_reranker()` function implemented and returns (tokenizer, model, device) tuple
- [ ] `_reranker_cache` module variable exists and caches singleton
- [ ] `DEBUG_LOG_CACHE_HITS` constant added (default False)
- [ ] First call to `get_reranker()` initializes model and logs device/timing at INFO level
- [ ] Subsequent calls return cached instance (object identity test passes)
- [ ] Device selection works: CUDA when available, CPU fallback when not
- [ ] Model uses float16 on GPU, float32 on CPU
- [ ] Model set to eval mode
- [ ] RuntimeError raised with clear message if model loading fails
- [ ] All unit tests pass (singleton behavior, caching, device selection, error handling)
- [ ] No imports of FastAPI or HTTP-related libraries (core module independence)

## Manual verification
- Steps:
  - Start Python REPL
  - Import: `from src.vulcanlab.retrieval.reranker import get_reranker`
  - Call once: `tok1, model1, dev1 = get_reranker()`
  - Verify INFO log shows model loaded with device and timing
  - Call again: `tok2, model2, dev2 = get_reranker()`
  - Check no additional INFO log (model not reloaded)
  - Verify identity: `model1 is model2` returns True
  - Verify device is "cuda" or "cpu"
- Expected results:
  - First call logs initialization (device, timing)
  - Second call silent (or debug log if enabled)
  - Same model instance returned both times
  - Model in eval mode

## Notes
- Follow singleton pattern from `app_config.py` (lines 96, 119-154) which uses `_config_cache` global variable
- Model name hardcoded: "BAAI/bge-reranker-large" (no configuration needed per spec non-goals)
- Cache persists for process lifetime (intentional, acceptable trade-off per spec)
- Use `logging.getLogger(__name__)` for module-specific logger
- Log timing with `time.perf_counter()` for precision
- No psutil or memory logging needed (spec implementation notes line 177)
- No force_reload parameter needed at this time (spec implementation notes line 178)
- Edge case: If model download fails on first run, RuntimeError should include original exception context
- The cache is global to the module but not shared across processes (each FastAPI worker has its own)
