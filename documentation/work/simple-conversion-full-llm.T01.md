# Ticket: simple-conversion-full-llm.T01 - Backend Config, API, and Frontend Toggle

## Source
- Spec: documentation/work/simple-conversion-full-llm.spec.md
- Patterns: documentation/patterns.md

## Goal
- Add complete UI toggle for "Simple Conversion - Full LLM Calls" in Settings page
- Implement backend config storage in vulcanlab.config.json
- Expose config via API endpoint
- Enable users to toggle between full and light model tiers

## Scope
### In scope
- Backend: Add get_use_full_model() and set_use_full_model() to conversion_config.py
- Backend: Update /api/conversion/settings endpoint (GET/PUT) to include use_full_model
- Frontend: Add toggle UI in ConversionTab below "Advanced Conversion"
- Frontend: Display warning when enabling
- Frontend: Persist state via API
- Unit tests for all layers (config, API, UI)

### Out of scope
- Simple conversion module updates (T02, T03)
- Integration tests with real LLM calls
- Cost estimation or tracking

## Dependencies
- Depends on: none
- Unblocks: T02, T03

## Implementation plan

### Part 1: Backend Config Functions
1. Open src/vulcanlab/config/conversion_config.py
2. Add constant: `DEFAULT_USE_FULL_MODEL = False`
3. Implement get_use_full_model() function:
   - Load config using load_config()
   - Navigate to conversion.use_full_model
   - Validate it's a boolean, warn and return default if not
   - Return default if missing
4. Implement set_use_full_model(enabled: bool) function:
   - Validate enabled is boolean (raise ValueError if not)
   - Load config
   - Create conversion section if missing
   - Set conversion.use_full_model = enabled
   - Save config
   - Log the change
5. Follow exact pattern from get_advanced_mode_enabled/set_advanced_mode_enabled

### Part 2: API Endpoint Update
1. Locate the API router file handling /api/conversion/settings
   - Likely in src/vulcanlab_api/routers/
2. Find the ConversionSettingsData schema (TypedDict or Pydantic model)
3. Add use_full_model: bool field to schema
4. In GET endpoint handler:
   - Import get_use_full_model from vulcanlab.config.conversion_config
   - Call get_use_full_model() and include in response
5. In PUT endpoint handler:
   - Accept use_full_model from request body (optional field for backward compat)
   - Import set_use_full_model from vulcanlab.config.conversion_config
   - If use_full_model is provided in request, call set_use_full_model()
   - Handle alongside existing token_threshold and advanced_mode_enabled updates
6. Ensure proper error handling and logging

### Part 3: Frontend Toggle UI
1. Open vulcanlab_ui/src/components/settings/conversion-tab.tsx
2. Update ConversionSettingsData interface to include use_full_model: boolean
3. Add state: const [fullLLMMode, setFullLLMMode] = useState<boolean>(false)
4. Add state for saving: const [savingFullLLM, setSavingFullLLM] = useState<boolean>(false)
5. Add state for success feedback: const [fullLLMSaveSuccess, setFullLLMSaveSuccess] = useState<boolean>(false)
6. In loadSettings(), read use_full_model from response and setFullLLMMode(data.use_full_model ?? false)
7. Create handleFullLLMToggleChange() handler (copy pattern from handleToggleChange for advancedMode):
   - Show warning message when enabling (checked === true)
   - Call API PUT with use_full_model: checked
   - Handle success/error states
   - Update state on success
8. Add UI section after the "Advanced Conversion" toggle section (around line 188):
   - Add border separator
   - Add Switch component with id="full-llm-mode"
   - Add Label "Simple Conversion - Full LLM Calls"
   - Add help text explaining it uses full models instead of light
   - Add warning text when enabled
9. Follow exact pattern from advancedMode toggle (lines 165-188)

Patterns to apply:
- Core Module Independence - Backend config has no FastAPI imports
- API Layer (Thin) - API orchestrates, calls core module functions
- Dual Configuration System - Store in vulcanlab.config.json
- Frontend Component Structure - Use existing Shadcn/Radix Switch component
- Client Components - ConversionTab is already "use client" for interactivity

Deviations (if any):
- None

## Unit tests (required)

### Backend Config Tests (conversion_config.py)
- Add tests for:
  - get_use_full_model() returns False when field is missing
  - get_use_full_model() returns False when config file doesn't exist
  - get_use_full_model() returns True when set to true
  - get_use_full_model() returns False and logs warning when value is non-boolean
  - set_use_full_model() creates conversion section if missing
  - set_use_full_model() updates existing value correctly
  - set_use_full_model() raises ValueError when passed non-boolean
  - set_use_full_model() logs the config change
- Suggested locations:
  - tests/unit/test_conversion_config.py (create if doesn't exist, or add to existing)
- Mocking/fakes needed:
  - Mock get_config_path() to use temporary test config file
  - Mock logger to verify logging calls

### API Tests
- Add tests for:
  - GET /api/conversion/settings includes use_full_model field (default false)
  - GET returns correct use_full_model value when set to true
  - PUT /api/conversion/settings accepts use_full_model field
  - PUT saves use_full_model correctly via set_use_full_model()
  - PUT works when use_full_model is omitted (backward compat)
  - PUT works when only use_full_model is provided (other fields unchanged)
  - PUT validates use_full_model is boolean type
- Suggested locations:
  - tests/unit/test_conversion_settings_api.py (create if doesn't exist)
- Mocking/fakes needed:
  - Mock get_use_full_model(), set_use_full_model()
  - Mock get_token_threshold(), set_token_threshold()
  - Mock get_advanced_mode_enabled(), set_advanced_mode_enabled()
  - Use FastAPI TestClient for endpoint testing

### Frontend Tests
- Add tests for:
  - Toggle renders with correct label and help text
  - Toggle is initially unchecked (false)
  - Toggle loads state from API on mount
  - Clicking toggle calls API with correct payload
  - Warning message displays when enabling
  - Success message displays after successful save
  - Error message displays on API failure
  - Toggle state updates after successful save
  - Toggle disabled state while saving
- Suggested locations:
  - vulcanlab_ui/src/components/settings/__tests__/conversion-tab.test.tsx
- Mocking/fakes needed:
  - Mock fetch for API calls (GET and PUT /api/conversion/settings)
  - Mock responses for success and error cases

## Acceptance criteria (checklist)
### Backend Config
- [ ] DEFAULT_USE_FULL_MODEL = False constant added
- [ ] get_use_full_model() function implemented
- [ ] set_use_full_model() function implemented
- [ ] Functions follow same pattern as advanced_mode_enabled functions
- [ ] Invalid values fall back to default (False)
- [ ] Missing config file returns default (False)
- [ ] Boolean type validation in setter raises ValueError
- [ ] Config changes are logged

### API
- [ ] ConversionSettingsData schema includes use_full_model: bool
- [ ] GET /api/conversion/settings returns use_full_model field
- [ ] GET returns default False when not configured
- [ ] GET returns correct value when configured
- [ ] PUT /api/conversion/settings accepts use_full_model
- [ ] PUT calls set_use_full_model() with provided value
- [ ] PUT handles missing use_full_model gracefully (backward compat)
- [ ] PUT validates boolean type for use_full_model

### Frontend
- [ ] New toggle appears in Settings > Conversion tab
- [ ] Toggle positioned below "Advanced Conversion" toggle
- [ ] Label reads "Simple Conversion - Full LLM Calls"
- [ ] Help text explains it controls model tier (full vs light)
- [ ] Warning displays when enabling: "Enabling full LLM mode will use more expensive and slower models. This may increase processing time and costs."
- [ ] Toggle saves to API on change
- [ ] Loading spinner shows while saving
- [ ] Success message shows after save
- [ ] Error message shows on failure
- [ ] State persists across page reloads

### All Layers
- [ ] All unit tests pass
- [ ] No breaking changes to existing API behavior

## Manual verification

### Backend Config
- Steps:
  1. Delete vulcanlab.config.json (or backup)
  2. Run Python REPL: `from vulcanlab.config.conversion_config import get_use_full_model; print(get_use_full_model())`
  3. Verify returns False
  4. Run: `from vulcanlab.config.conversion_config import set_use_full_model; set_use_full_model(True)`
  5. Check vulcanlab.config.json file created with conversion.use_full_model = true
  6. Run get_use_full_model() again, verify returns True
  7. Try set_use_full_model("invalid"), verify raises ValueError
- Expected results:
  - Default returns False when config missing
  - Setter creates config structure
  - Getter reads correct value
  - Type validation works

### API
- Steps:
  1. Start API server
  2. GET /api/conversion/settings
  3. Verify response includes "use_full_model": false
  4. PUT /api/conversion/settings with body: {"use_full_model": true, "token_threshold": 15000, "advanced_mode_enabled": false}
  5. Verify 200 response
  6. Check vulcanlab.config.json, verify use_full_model is true
  7. GET /api/conversion/settings again
  8. Verify response includes "use_full_model": true
  9. PUT with invalid type: {"use_full_model": "invalid"}
  10. Verify 400/422 error response
- Expected results:
  - GET returns all three fields including use_full_model
  - PUT successfully saves use_full_model
  - Type validation works
  - Backward compatibility maintained

### Frontend
- Steps:
  1. Start frontend and backend servers
  2. Navigate to Settings page
  3. Click Conversion tab
  4. Verify new toggle appears below "Advanced Conversion"
  5. Verify toggle is initially unchecked
  6. Click toggle to enable
  7. Verify warning message appears
  8. Verify loading state shows briefly
  9. Verify success message appears
  10. Reload page
  11. Verify toggle is still checked (state persisted)
  12. Open browser DevTools Network tab
  13. Toggle off and on, verify PUT requests sent
  14. Simulate API error (stop backend), toggle and verify error message
- Expected results:
  - Toggle UI works correctly
  - Warning displays when enabling
  - State persists via API
  - Error handling works
  - UI matches existing toggle patterns

## Notes
- Backend config: Follow exact pattern from lines 109-153 in conversion_config.py (advanced_mode_enabled functions)
- API: Look for existing conversion settings endpoint - may be in src/vulcanlab_api/routers/conversion.py or similar
- Frontend: Follow exact pattern from advancedMode toggle implementation in ConversionTab.tsx (lines 98-130 for handler, lines 165-188 for UI)
- Use same success/error message pattern with AlertCircle and CheckCircleIcon
- Warning message should be informative but not alarming
- Help text should clarify relationship to token threshold: "Controls which model is used for LLM calls. Does not affect small vs. large document classification (token threshold)."
- Consider adding data-testid attributes for easier testing
- This ticket provides the first vertical slice - after completion, users can toggle the setting and see it persist, validating the core workflow before model selection is implemented
