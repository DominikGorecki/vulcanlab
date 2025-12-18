# Ticket: simple-conversion-full-llm.T04 - End-to-End Testing and Documentation

## Source
- Spec: documentation/work/simple-conversion-full-llm.spec.md
- Patterns: documentation/patterns.md

## Goal
- Perform complete manual testing of the feature end-to-end
- Verify all acceptance criteria from spec
- Document any edge cases or issues found
- Update relevant documentation if needed

## Scope
### In scope
- Complete manual test plan from spec
- Test full user workflow (UI toggle -> config save -> LLM model selection)
- Test error cases and edge cases
- Verify logging and observability
- Check backward compatibility
- Document findings

### Out of scope
- Integration tests with real LLM calls (expensive, out of scope per patterns)
- Performance benchmarking
- Cost analysis

## Dependencies
- Depends on: T01, T02, T03 (all implementation tickets)
- Unblocks: None (final ticket)

## Implementation plan
1. Execute complete manual test plan from spec (lines 192-207)
2. Test additional edge cases:
   - Concurrent config changes
   - Invalid config file syntax
   - Missing LLM API keys with full model enabled
   - Browser refresh during save
   - Multiple browser tabs
3. Verify all acceptance criteria from spec (lines 209-224)
4. Check logs for proper model tier logging
5. Verify no regressions in existing simple conversion behavior
6. Test with both small and large documents
7. Document any issues found and create follow-up tickets if needed
8. Update README or user docs if toggle needs explanation

Patterns to apply:
- Testing Strategy - Manual testing for end-to-end validation
- Observability - Verify logging is clear and useful

Deviations (if any):
- None

## Unit tests (required)
- No new unit tests in this ticket
- Verify all unit tests from T01-T03 pass
- Run full test suite to check for regressions

## Acceptance criteria (checklist)
All items from spec acceptance criteria (lines 209-224):
- [ ] New toggle "Simple Conversion - Full LLM Calls" appears in Settings > Conversion tab below "Advanced Conversion"
- [ ] Toggle has clear label and help text explaining what it does
- [ ] Warning message displays when user enables the toggle
- [ ] Toggle state saves to backend via API
- [ ] Backend stores setting in vulcanlab.config.json under conversion.use_full_model
- [ ] Default value is false (disabled)
- [ ] get_use_full_model() and set_use_full_model() functions work correctly
- [ ] API endpoint /api/conversion/settings includes use_full_model field in GET and PUT
- [ ] sanitize_small.py uses ModelTier.FULL when setting is enabled
- [ ] sanitize_large.py uses ModelTier.FULL when setting is enabled
- [ ] All simple conversion LLM calls respect the setting
- [ ] Model tier selection is logged appropriately
- [ ] Unit tests pass for config functions and tier selection
- [ ] Manual tests confirm correct behavior in UI and backend
- [ ] Token threshold classification logic remains unchanged

Additional checks:
- [ ] No regressions in existing simple conversion workflows
- [ ] Error handling works correctly
- [ ] State persists across browser sessions
- [ ] Backward compatibility maintained (old configs still work)

## Manual verification
Complete spec manual test plan (lines 192-207):

Basic functionality:
- [ ] Load Settings page, verify new toggle appears below "Advanced Conversion"
- [ ] Toggle is initially disabled (unchecked)
- [ ] Enable toggle, verify warning message appears
- [ ] Verify toggle saves successfully and shows success message
- [ ] Reload page, verify toggle state persists (enabled)
- [ ] Check vulcanlab.config.json file, verify "use_full_model": true

Small document testing:
- [ ] Start new simple conversion with setting enabled
- [ ] Check logs, verify ModelTier.FULL is selected for small doc
- [ ] Verify LLM calls use full model (e.g., gemini-3-pro-preview)
- [ ] Disable toggle, verify state saves
- [ ] Start new simple conversion with setting disabled
- [ ] Check logs, verify ModelTier.LIGHT is selected for small doc
- [ ] Verify LLM calls use light model (e.g., gemini-flash-lite-latest)

Large document testing:
- [ ] Enable toggle
- [ ] Start simple conversion with large document (>15000 tokens)
- [ ] Check logs, verify ModelTier.FULL is selected for large doc
- [ ] Verify condensed heading extraction still works
- [ ] Disable toggle
- [ ] Start conversion with large document again
- [ ] Check logs, verify ModelTier.LIGHT is selected

Edge cases:
- [ ] Test with missing config field, verify defaults to false
- [ ] Test invalid config value (non-boolean), verify falls back to false
- [ ] Test with missing config file entirely
- [ ] Test rapid toggle on/off
- [ ] Test with multiple browser tabs open
- [ ] Test browser refresh during save operation

Expected results:
- All manual tests pass
- No errors in logs
- Correct model tier used in all cases
- UI provides clear feedback
- State persistence works reliably

## Notes
- This is the final validation ticket before feature is considered complete
- Take time to thoroughly test all scenarios
- Document any unexpected behavior or edge cases
- If issues found, create follow-up tickets but don't block completion unless critical
- Pay special attention to logging - it should be clear which model tier is being used
- Verify token threshold classification is completely independent (small/large still based on token count)
- Test with both OpenAI and Gemini providers if possible
- Consider testing with invalid API keys to ensure graceful error handling
