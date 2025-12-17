# Ticket: simple-conversion-full-llm.T03 - Update chunk_simple.py Model Selection (if applicable)

## Source
- Spec: documentation/work/simple-conversion-full-llm.spec.md
- Patterns: documentation/patterns.md

## Goal
- Investigate if chunk_simple.py makes LLM calls
- If yes, update to use ModelTier based on use_full_model config
- If no, document and close ticket

## Scope
### In scope
- Review chunk_simple.py for LLM calls
- If LLM calls exist, apply same pattern as T02
- If no LLM calls, document findings and mark complete
- Add unit tests if changes made

### Out of scope
- Changes to chunking logic itself
- Changes to other modules not in simple_conversion
- API or frontend changes (T01)

## Dependencies
- Depends on: T01 (config functions)
- Unblocks: None

## Implementation plan
1. Open src/vulcanlab/simple_conversion/chunk_simple.py
2. Search for imports: create_langchain_chat, create_pydantic_agent, ModelTier
3. Search for LLM invocations or AI calls
4. If LLM calls found:
   - Add import: from vulcanlab.config.conversion_config import get_use_full_model
   - Add model tier selection logic before each LLM call
   - Pass selected tier to create_langchain_chat() or equivalent
   - Add logging for model tier selection
   - Follow exact pattern from T02
5. If no LLM calls found:
   - Document in ticket comments
   - Verify chunking is rule-based or uses non-LLM methods
   - Mark ticket complete with "No changes needed"

Patterns to apply:
- Core Module Independence - No framework dependencies, pure Python
- Configuration (Dual System) - Read from vulcanlab.config.json via config module
- Logging - Use existing logger for observability

Deviations (if any):
- None

## Unit tests (required)
If LLM calls exist:
- Add tests for:
  - chunk_simple functions use ModelTier.LIGHT when use_full_model is False
  - chunk_simple functions use ModelTier.FULL when use_full_model is True
  - Model tier selection is logged correctly
  - LLM call receives correct tier parameter
  - Behavior unchanged when config missing (defaults to LIGHT)
- Suggested locations:
  - tests/unit/test_chunk_simple.py (create if doesn't exist)
- Mocking/fakes needed:
  - Mock get_use_full_model() to return True/False
  - Mock create_langchain_chat() to verify tier argument
  - Mock relevant DB queries
  - Mock logger to verify logging calls

If no LLM calls:
- No new tests required
- Verify existing tests still pass

## Acceptance criteria (checklist)
If LLM calls exist:
- [ ] get_use_full_model imported from conversion_config
- [ ] Model tier selection logic added before all LLM calls
- [ ] ModelTier.LIGHT used when use_full_model is False
- [ ] ModelTier.FULL used when use_full_model is True
- [ ] Model tier selection logged appropriately
- [ ] All unit tests pass

If no LLM calls:
- [ ] Code review confirms no LLM calls in chunk_simple.py
- [ ] Findings documented in ticket
- [ ] Existing tests still pass

## Manual verification
If LLM calls exist:
- Steps:
  1. Set use_full_model to False in vulcanlab.config.json
  2. Run simple chunking operation (via CLI or API)
  3. Check logs, verify "Using ModelTier.LIGHT" message appears
  4. Set use_full_model to True
  5. Run chunking again
  6. Check logs, verify "Using ModelTier.FULL" message appears
- Expected results:
  - Correct model tier selected based on config
  - Model selection logged clearly
  - LLM calls use correct model

If no LLM calls:
- Steps:
  1. Review chunk_simple.py code
  2. Verify no create_langchain_chat or AI calls
  3. Document approach (rule-based, heuristic, etc.)
- Expected results:
  - No changes needed
  - Chunking still works as before

## Notes
- This ticket is investigative - may result in code changes or just documentation
- Review the module carefully for any AI/LLM usage patterns
- If chunking uses suggested_chunks.py or other modules that make LLM calls, those modules may need updates too (create follow-up tickets if needed)
- The spec mentions "all LLM calls in simple conversion" so be thorough
- Check for both direct LLM calls and calls to utility functions that might invoke LLMs
