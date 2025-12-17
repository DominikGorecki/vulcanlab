# Ticket: simple-conversion-full-llm.T02 - Update Sanitization Model Selection

## Source
- Spec: documentation/work/simple-conversion-full-llm.spec.md
- Patterns: documentation/patterns.md

## Goal
- Update both sanitize_small.py and sanitize_large.py to use ModelTier based on use_full_model config
- Replace hardcoded ModelTier.LIGHT with conditional selection
- Add logging for model tier selection in both modules

## Scope
### In scope
- Import get_use_full_model from vulcanlab.config.conversion_config in both modules
- Add model tier selection logic in sanitize_small_document()
- Add model tier selection logic in sanitize_large_document()
- Pass selected tier to create_langchain_chat() in both modules
- Log which model tier is being used for both small and large documents
- Update both sanitize_*_document() and standalone versions

### Out of scope
- Changes to sanitization algorithms or logic
- Changes to other simple conversion modules (T03)
- API or frontend changes (T01)
- Changes to token threshold classification

## Dependencies
- Depends on: T01 (config functions)
- Unblocks: T04 (end-to-end testing)

## Implementation plan

### Part 1: Update sanitize_small.py
1. Open src/vulcanlab/simple_conversion/sanitize_small.py
2. Add import at top: from vulcanlab.config.conversion_config import get_use_full_model
3. Locate the line calling create_langchain_chat() (currently line 130):
   - Current: `llm_stack = create_langchain_chat(tier=ModelTier.LIGHT, temperature=0.2)`
4. Add model tier selection logic before the LLM call:
   ```python
   # Determine model tier based on config
   use_full = get_use_full_model()
   tier = ModelTier.FULL if use_full else ModelTier.LIGHT
   logger.info(f"Using ModelTier.{tier.name} for small document sanitization (work {work_id})")
   ```
5. Update the create_langchain_chat() call to use the selected tier:
   ```python
   llm_stack = create_langchain_chat(tier=tier, temperature=0.2)
   ```

### Part 2: Update sanitize_large.py
1. Open src/vulcanlab/simple_conversion/sanitize_large.py
2. Add import at top: from vulcanlab.config.conversion_config import get_use_full_model
3. Locate the line calling create_langchain_chat() (currently line 349):
   - Current: `llm_stack = create_langchain_chat(tier=ModelTier.LIGHT, temperature=0.2)`
4. Add model tier selection logic before the LLM call:
   ```python
   # Determine model tier based on config
   use_full = get_use_full_model()
   tier = ModelTier.FULL if use_full else ModelTier.LIGHT
   logger.info(f"Using ModelTier.{tier.name} for large document sanitization (work {work_id})")
   ```
5. Update the create_langchain_chat() call to use the selected tier:
   ```python
   llm_stack = create_langchain_chat(tier=tier, temperature=0.2)
   ```

Patterns to apply:
- Core Module Independence - No framework dependencies, pure Python
- Configuration (Dual System) - Read from vulcanlab.config.json via config module
- Logging - Use existing logger for observability

Deviations (if any):
- None

## Unit tests (required)

### Tests for sanitize_small.py
- Add tests for:
  - sanitize_small_document() uses ModelTier.LIGHT when use_full_model is False
  - sanitize_small_document() uses ModelTier.FULL when use_full_model is True
  - Model tier selection is logged correctly for small docs
  - LLM call receives correct tier parameter
  - Behavior unchanged when config missing (defaults to LIGHT)
- Suggested locations:
  - tests/unit/test_sanitize_small.py (create if doesn't exist)
- Mocking/fakes needed:
  - Mock get_use_full_model() to return True/False
  - Mock create_langchain_chat() to verify tier argument
  - Mock Work, ParsedMarkdown DB queries
  - Mock session.add(), session.commit()
  - Mock logger to verify logging calls

### Tests for sanitize_large.py
- Add tests for:
  - sanitize_large_document() uses ModelTier.LIGHT when use_full_model is False
  - sanitize_large_document() uses ModelTier.FULL when use_full_model is True
  - Model tier selection is logged correctly for large docs
  - LLM call receives correct tier parameter
  - Behavior unchanged when config missing (defaults to LIGHT)
- Suggested locations:
  - tests/unit/test_sanitize_large.py (create if doesn't exist)
- Mocking/fakes needed:
  - Mock get_use_full_model() to return True/False
  - Mock create_langchain_chat() to verify tier argument
  - Mock Work, ParsedMarkdown DB queries
  - Mock extract_headings_with_context() to return test headings
  - Mock session.add(), session.commit()
  - Mock logger to verify logging calls

## Acceptance criteria (checklist)
### sanitize_small.py
- [ ] get_use_full_model imported from conversion_config
- [ ] Model tier selection logic added before LLM call
- [ ] ModelTier.LIGHT used when use_full_model is False
- [ ] ModelTier.FULL used when use_full_model is True
- [ ] Model tier selection logged with work_id
- [ ] create_langchain_chat() receives correct tier parameter
- [ ] No changes to sanitization logic or behavior (only model selection)

### sanitize_large.py
- [ ] get_use_full_model imported from conversion_config
- [ ] Model tier selection logic added before LLM call
- [ ] ModelTier.LIGHT used when use_full_model is False
- [ ] ModelTier.FULL used when use_full_model is True
- [ ] Model tier selection logged with work_id
- [ ] create_langchain_chat() receives correct tier parameter
- [ ] No changes to condensed heading logic or behavior (only model selection)

### All modules
- [ ] All unit tests pass
- [ ] Temperature parameter (0.2) unchanged
- [ ] Default to LIGHT when config missing

## Manual verification

### Small document testing
- Steps:
  1. Set use_full_model to False in vulcanlab.config.json
  2. Run small document sanitization (via CLI or API)
  3. Check logs, verify "Using ModelTier.LIGHT for small document sanitization"
  4. Verify LLM call uses light model (gemini-flash-lite-latest or gpt-4o-mini)
  5. Set use_full_model to True in config
  6. Run small document sanitization again
  7. Check logs, verify "Using ModelTier.FULL for small document sanitization"
  8. Verify LLM call uses full model (gemini-3-pro-preview or gpt-4o)
  9. Delete use_full_model from config
  10. Run sanitization, verify defaults to LIGHT
- Expected results:
  - Correct model tier selected based on config
  - Model selection logged clearly
  - Default to LIGHT when config missing
  - LLM calls use correct model

### Large document testing
- Steps:
  1. Set use_full_model to False in vulcanlab.config.json
  2. Run large document sanitization (via CLI or API)
  3. Check logs, verify "Using ModelTier.LIGHT for large document sanitization"
  4. Verify LLM call uses light model (gemini-flash-lite-latest or gpt-4o-mini)
  5. Set use_full_model to True in config
  6. Run large document sanitization again
  7. Check logs, verify "Using ModelTier.FULL for large document sanitization"
  8. Verify LLM call uses full model (gemini-3-pro-preview or gpt-4o)
  9. Delete use_full_model from config
  10. Run sanitization, verify defaults to LIGHT
- Expected results:
  - Correct model tier selected based on config
  - Model selection logged clearly
  - Default to LIGHT when config missing
  - LLM calls use correct model
  - Condensed heading extraction still works correctly

## Notes
- sanitize_small.py: Current hardcoded line is around line 130: `llm_stack = create_langchain_chat(tier=ModelTier.LIGHT, temperature=0.2)`
- sanitize_large.py: Current hardcoded line is around line 349: `llm_stack = create_langchain_chat(tier=ModelTier.LIGHT, temperature=0.2)`
- Keep temperature=0.2 unchanged in both modules
- Model tier selection should happen inside sanitize_*_document() functions, not at module level
- Ensure logging happens before LLM call so it's visible if call fails
- The actual model name (gemini-3-pro-preview, gpt-4o, etc.) is determined by llm_factory based on tier and provider from .env
- Large documents use condensed heading extraction, but full model should still improve quality of heading analysis
- Both modules follow the same pattern - implement identically
