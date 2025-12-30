# Ticket: eval-automatic-mode.T03 - Automatic Mode Toggle UI and API

## Source

* Spec: documentation/work/eval-automatic-mode.spec.md
* Patterns: documentation/patterns.md

## Goal

* Enable users to toggle automatic mode on/off on experiment detail page
* Validate API keys before enabling automatic mode
* Allow provider selection for answer generation
* Automatically set judge provider to opposite of answer provider

## Scope

### In scope

* PATCH /api/v1/eval/experiments/{experiment_id} endpoint to update auto mode settings
* API key validation logic (both OpenAI and Gemini must be present)
* UI toggle component on /eval/[id] page
* UI dialog for provider selection when enabling
* UI confirmation dialog when disabling
* Update ExperimentDetail schema to include auto mode fields
* Unit tests for API endpoint and validation logic

### Out of scope

* "New Eval" workflow (T04, T05)
* LLM factory changes (T02)
* Grouped prompt creation (T04)
* Progress indicator during eval execution (T05)

## Dependencies

* Depends on: T01 (database schema), T02 (for API key validation via LLMSettings)
* Unblocks: T04, T05

## Implementation plan

1. Update src/vulcanlab_api/schemas/eval.py:
   * Add auto_mode_enabled, auto_answer_provider, auto_judge_provider to ExperimentDetail schema
   * Create ExperimentUpdateRequest schema with auto_mode_enabled and auto_answer_provider fields
2. Create core validation function in src/vulcanlab/eval/auto_mode.py:
   * `validate_api_keys_for_auto_mode()` - checks both OpenAI and Gemini API keys via LLMSettings
   * Returns bool and error message if invalid
3. Add PATCH endpoint in src/vulcanlab_api/routers/eval.py:
   * Route: PATCH /api/v1/eval/experiments/{experiment_id}
   * Accept auto_mode_enabled and optional auto_answer_provider
   * If enabling (auto_mode_enabled=true): validate API keys, require auto_answer_provider, set auto_judge_provider to opposite
   * If disabling (auto_mode_enabled=false): set both providers to null
   * Update experiment in database
   * Return updated ExperimentDetail
4. Update vulcanlab_ui/src/app/eval/[id]/page.tsx:
   * Add toggle switch component in experiment configuration card
   * Show current auto mode status
   * When toggled on: validate API keys first, show error if missing, then show provider selection dialog
   * When toggled off: show confirmation dialog
5. Create vulcanlab_ui/src/app/eval/[id]/auto-mode-config.tsx:
   * Provider selection dialog component
   * Two radio buttons: "OpenAI" and "Gemini"
   * Explain that judge will be set to opposite
   * Submit button calls PATCH endpoint
6. Handle success/error states with toasts
7. Patterns to apply:
   * Three-tier architecture - validation in core, API in vulcanlab_api, UI in vulcanlab_ui
   * Error handling - raise HTTPException in API, use global handler
   * Session management - pass session explicitly to update function
   * usePageData hook with useCallback for data fetching
   * ConfirmDialog for destructive action (disabling auto mode)
* Deviations (if any):
   * None

## Unit tests (required)

* Add tests for:
   * validate_api_keys_for_auto_mode returns true when both keys present
   * validate_api_keys_for_auto_mode returns false when OpenAI key missing
   * validate_api_keys_for_auto_mode returns false when Gemini key missing
   * PATCH endpoint enables auto mode with valid provider selection
   * PATCH endpoint sets judge provider to opposite of answer provider (openai -> gemini, gemini -> openai)
   * PATCH endpoint returns 400 if API keys invalid
   * PATCH endpoint disables auto mode and sets providers to null
   * PATCH endpoint returns 404 for non-existent experiment
* Suggested locations:
   * tests/unit/test_auto_mode_validation.py (create)
   * tests/unit/test_eval_api_auto_mode.py (create)
* Mocking/fakes needed:
   * Mock LLMSettings to control API key presence
   * Mock database session for experiment updates
   * Mock experiment query results

## Acceptance criteria (checklist)

* [ ] ExperimentDetail schema includes auto mode fields
* [ ] validate_api_keys_for_auto_mode function created and tested
* [ ] PATCH endpoint created at /api/v1/eval/experiments/{experiment_id}
* [ ] API key validation runs before enabling auto mode
* [ ] Judge provider automatically set to opposite of answer provider
* [ ] UI toggle component added to experiment detail page
* [ ] Provider selection dialog implemented
* [ ] Confirmation dialog for disabling auto mode implemented
* [ ] Toast notifications for success and errors
* [ ] Unit tests pass for validation and API endpoint
* [ ] Manual mode behavior unchanged

## Manual verification

* Steps:
  1. Navigate to /eval/[id] for any experiment
  2. Verify toggle shows "Automatic Mode: Disabled" by default
  3. Remove one API key from .env and restart API server
  4. Try to enable automatic mode, verify error: "Both OpenAI and Gemini API keys required"
  5. Restore both API keys and restart
  6. Enable automatic mode, select "OpenAI" as answer provider
  7. Verify database shows auto_mode_enabled=true, auto_answer_provider='openai', auto_judge_provider='gemini'
  8. Refresh page, verify toggle shows "Automatic Mode: Enabled (Answer: OpenAI, Judge: Gemini)"
  9. Disable automatic mode, confirm in dialog
  10. Verify database shows auto_mode_enabled=false, providers=null
* Expected results:
  * Toggle works smoothly with proper validation
  * API key validation prevents enabling without both keys
  * Provider selection intuitive and clear
  * Judge provider automatically set correctly
  * Disabling mode preserves existing data (does not delete prompts)
  * UI shows current state accurately

## Notes

* Requirements covered: R1, R3, R4, R4a, R5, R14, R15
* This is the first vertical slice - users can toggle auto mode on/off
* API key validation uses LLMSettings from T02
* Disabling auto mode only changes flag, does not delete grouped prompts
* Existing manual workflow unchanged when auto mode disabled
