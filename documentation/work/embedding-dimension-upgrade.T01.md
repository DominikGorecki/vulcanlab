# Ticket: embedding-dimension-upgrade.T01 - Update Embedding Model Configuration

## Source

* Spec: documentation/work/embedding-dimension-upgrade.spec.md
* Patterns: documentation/patterns.md

## Goal

* Update `llm_factory.py` to use `gemini-embedding-001` with `output_dimensionality=1536` for Gemini
* Update `llm_factory.py` to use `text-embedding-3-small` with `dimensions=1536` for OpenAI
* Ensure all embedding functions produce 1536-dimension vectors

## Scope

### In scope

* `create_embeddings()` function in `llm_factory.py`
* `create_embeddings_for_provider()` function in `llm_factory.py`
* Comments/docstrings referencing dimension count

### Out of scope

* SQLAlchemy model changes (T02)
* Database schema changes (T03)
* Migration script (T04)

## Dependencies

* Depends on: none
* Unblocks: T02, T03, T04

## Implementation plan

1. Open `src/vulcanlab/ai/llm_factory.py`
2. In `create_embeddings()`:
   - Change Gemini model from `"models/text-embedding-004"` to `"models/gemini-embedding-001"`
   - Add `output_dimensionality=1536` parameter to `GoogleGenerativeAIEmbeddings`
   - Change OpenAI `dimensions=768` to `dimensions=1536`
   - Update the comment from "Match database vector(768) column" to "Match database vector(1536) column"
3. In `create_embeddings_for_provider()`:
   - Same changes as step 2 for both providers
   - Update comments accordingly
4. Update any docstrings that mention "768 dimensions" to say "1536 dimensions"

* Patterns to apply:
   * Single Source of Truth - embedding dimension is defined once in the factory functions

* Deviations (if any):
   * None

## Unit tests (required)

* Add tests for:
   * `test_create_embeddings_gemini_uses_correct_model()` - verify model is `gemini-embedding-001`
   * `test_create_embeddings_gemini_uses_1536_dimensions()` - verify `output_dimensionality=1536`
   * `test_create_embeddings_openai_uses_1536_dimensions()` - verify `dimensions=1536`
   * `test_create_embeddings_for_provider_gemini_uses_correct_config()` - same checks for explicit provider
   * `test_create_embeddings_for_provider_openai_uses_correct_config()` - same checks for explicit provider

* Suggested locations:
   * `tests/unit/test_llm_factory.py` (create if not exists)

* Mocking/fakes needed:
   * Mock `GoogleGenerativeAIEmbeddings` class to capture constructor arguments
   * Mock `OpenAIEmbeddings` class to capture constructor arguments
   * Mock `LLMSettings` to provide test API keys

## Acceptance criteria (checklist)

* [ ] `create_embeddings()` with Gemini provider uses `models/gemini-embedding-001`
* [ ] `create_embeddings()` with Gemini provider passes `output_dimensionality=1536`
* [ ] `create_embeddings()` with OpenAI provider passes `dimensions=1536`
* [ ] `create_embeddings_for_provider(GEMINI)` uses correct model and dimensions
* [ ] `create_embeddings_for_provider(OPENAI)` uses correct dimensions
* [ ] Comments updated to reference 1536 dimensions
* [ ] Unit tests pass

## Manual verification

* Steps:
   * Run: `python -c "from vulcanlab.ai.llm_factory import create_embeddings; from vulcanlab.ai.config import LLMSettings, LLMProvider; s = LLMSettings(); s.provider = LLMProvider.GEMINI; e = create_embeddings(s); print(e)"`
   * Inspect the returned embeddings object to verify model configuration

* Expected results:
   * Embeddings object shows `gemini-embedding-001` model
   * No errors raised during creation

## Notes

* Requirements covered: R1, R2
* Gemini uses `output_dimensionality` parameter (not `dimensions`)
* OpenAI uses `dimensions` parameter
* The `text-embedding-3-small` model name stays the same for OpenAI; only the dimension parameter changes
