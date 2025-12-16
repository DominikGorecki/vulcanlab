# Title: Simple Conversion - Full LLM Model Toggle

## Summary
- Add a new toggle in the Settings page Conversion tab to enable/disable full LLM model usage for simple conversion pipeline
- Toggle appears below the existing "Advanced Conversion" toggle
- When enabled, all LLM calls in simple conversion use the "full" model tier instead of "light"
- Setting is stored in `vulcanlab.config.json` under `conversion.use_full_model`
- Only affects new conversion jobs started after the setting is changed
- No changes to the small vs. large document classification logic (token threshold remains separate)

## Problem / Context
- Currently, the simple conversion pipeline always uses the LIGHT model tier (ModelTier.LIGHT) for all LLM calls
- The LIGHT models (e.g., gemini-flash-lite-latest, gpt-4o-mini) are faster and cheaper but may produce lower quality results
- Users have no way to opt into using FULL models (e.g., gemini-3-pro-preview, gpt-4o) for better quality sanitization and processing
- The existing token threshold only controls whether a document is processed as SMALL (full content) or LARGE (condensed headings), not which model is used
- Users need the ability to trade off cost/speed for quality by choosing the full model tier

## Goals
- Add UI toggle in Settings > Conversion tab for "Simple Conversion - Full LLM Calls"
- Store the setting in `vulcanlab.config.json` under `conversion.use_full_model` (boolean)
- Create backend API to read/write this setting (similar to token_threshold and advanced_mode_enabled)
- Update all simple conversion LLM calls to respect this setting and use ModelTier.FULL when enabled
- Default to disabled (false) to maintain current behavior
- Show warning in UI when enabling (cost/time implications)

## Non-goals (Strict)
- Changing the small vs. large document classification logic (token threshold is independent)
- Allowing re-processing of existing work with the new setting
- Adding cost tracking or estimation features
- Performance optimization for full model calls
- Changes to the actual sanitization algorithms or logic
- Adding intermediate model tiers beyond LIGHT and FULL
- Per-step model selection (all steps use the same tier)

## Scope
### In scope
- Frontend: Add toggle switch in ConversionTab component below "Advanced Conversion"
- Frontend: Display warning when enabling the toggle
- Backend: Add `use_full_model` field to conversion_config.py
- Backend: Update API endpoint `/api/conversion/settings` to include the new field
- Backend: Update simple conversion modules to read setting and select model tier
- Unit tests for config functions and model tier selection logic
- Manual testing of toggle behavior and LLM model selection

### Out of scope
- Re-sanitization of existing work
- Cost estimation UI
- Granular per-step model selection
- Integration tests with real LLM calls
- Migration of existing data

## Requirements (Functional)
- R1: Settings page must display new toggle "Simple Conversion - Full LLM Calls" below "Advanced Conversion"
- R2: Toggle must save to backend via PUT /api/conversion/settings
- R3: Backend must store setting in `vulcanlab.config.json` under `conversion.use_full_model` (boolean)
- R4: Default value must be false (disabled)
- R5: When enabled, all simple conversion LLM calls must use ModelTier.FULL instead of ModelTier.LIGHT
- R6: When disabled, all simple conversion LLM calls must use ModelTier.LIGHT (current behavior)
- R7: Setting must only affect new conversion jobs, not existing work
- R8: UI must show warning message when user enables the toggle about potential cost/time implications
- R9: The small vs. large classification logic (based on token_threshold) must remain unchanged
- R10: API must return the current use_full_model value when loading settings

## Requirements (Non-functional)
- Performance:
  - Setting load/save operations must complete within 500ms
  - No performance impact on conversion jobs when setting is disabled
- Reliability:
  - Invalid config values must fall back to default (false)
  - Missing config field must default to false
  - Toggle state must persist across browser sessions
- Security / Privacy:
  - No sensitive data in the new configuration field
  - Standard CORS and API validation apply
- Observability:
  - Log model tier selection in simple conversion steps
  - Log config changes when use_full_model is updated

## Proposed Solution (High-level)
- Frontend: Add Switch component in ConversionTab.tsx similar to advancedMode toggle
- Frontend: Show warning dialog or inline message when enabling (using AlertCircle icon)
- Backend: Extend conversion_config.py with get_use_full_model() and set_use_full_model() functions
- Backend: Update ConversionSettingsData schema in API to include use_full_model field
- Backend: Modify simple conversion modules to call get_use_full_model() and pass appropriate ModelTier to create_langchain_chat()
- Configuration: Add "use_full_model": false to conversion section in vulcanlab.config.json

## Interfaces / APIs / Contracts

### API Endpoint: GET /api/conversion/settings
Response schema (updated):
```json
{
  "token_threshold": 15000,
  "advanced_mode_enabled": false,
  "use_full_model": false
}
```

### API Endpoint: PUT /api/conversion/settings
Request schema (updated):
```json
{
  "token_threshold": 15000,
  "advanced_mode_enabled": false,
  "use_full_model": false
}
```

### Configuration File: vulcanlab.config.json
Add to conversion section:
```json
{
  "conversion": {
    "token_threshold": 15000,
    "advanced_mode_enabled": false,
    "use_full_model": false
  }
}
```

### Backend Config Functions (conversion_config.py)
```python
def get_use_full_model() -> bool:
    """Get the use_full_model setting (defaults to False)"""

def set_use_full_model(enabled: bool) -> None:
    """Set the use_full_model setting"""
```

### Simple Conversion Modules
All modules making LLM calls must:
1. Import get_use_full_model from vulcanlab.config.conversion_config
2. Determine ModelTier based on setting:
   - If get_use_full_model() is True: use ModelTier.FULL
   - If get_use_full_model() is False: use ModelTier.LIGHT
3. Pass the selected tier to create_langchain_chat(tier=selected_tier)

Affected modules:
- src/vulcanlab/simple_conversion/sanitize_small.py
- src/vulcanlab/simple_conversion/sanitize_large.py
- src/vulcanlab/simple_conversion/chunk_simple.py (if it makes LLM calls)
- Any other simple_conversion module using LLM

## Data Model / Storage
No database schema changes required. Configuration is stored in vulcanlab.config.json file system storage.

## UX / Workflows

### User enables full LLM mode
1. User navigates to Settings > Conversion tab
2. User sees new toggle "Simple Conversion - Full LLM Calls" below "Advanced Conversion"
3. User clicks toggle to enable
4. Warning message appears: "Enabling full LLM mode will use more expensive and slower models. This may increase processing time and costs for large documents."
5. Toggle state changes to enabled
6. Backend saves setting to config file
7. Success message appears briefly
8. Future conversion jobs use full models

### User starts new conversion with full LLM enabled
1. User uploads document for simple conversion
2. Backend reads use_full_model setting (true)
3. During sanitization step, backend selects ModelTier.FULL
4. LLM calls use full model (e.g., gemini-3-pro-preview)
5. Document is processed with higher quality model
6. Results are stored normally

### User disables full LLM mode
1. User navigates to Settings > Conversion tab
2. User clicks toggle to disable
3. Toggle state changes to disabled
4. Backend saves setting to config file
5. Success message appears briefly
6. Future conversion jobs use light models (default behavior)

## Testing Plan

### Unit tests
- Test get_use_full_model() returns false when field is missing
- Test get_use_full_model() returns false when config file doesn't exist
- Test get_use_full_model() returns correct value when set
- Test set_use_full_model() creates conversion section if missing
- Test set_use_full_model() updates existing value correctly
- Test set_use_full_model() validates boolean type
- Test model tier selection logic in sanitize_small.py (mock get_use_full_model)
- Test model tier selection logic in sanitize_large.py (mock get_use_full_model)
- Test API endpoint returns use_full_model field
- Test API endpoint saves use_full_model field

### Integration tests
- Not required for this spec (out of scope per testing standards)

### Manual test plan
- [ ] Load Settings page, verify new toggle appears below "Advanced Conversion"
- [ ] Toggle is initially disabled (unchecked)
- [ ] Enable toggle, verify warning message appears
- [ ] Verify toggle saves successfully and shows success message
- [ ] Reload page, verify toggle state persists (enabled)
- [ ] Check vulcanlab.config.json file, verify "use_full_model": true
- [ ] Start new simple conversion with setting enabled
- [ ] Check logs, verify ModelTier.FULL is selected
- [ ] Verify LLM calls use full model (e.g., gemini-3-pro-preview)
- [ ] Disable toggle, verify state saves
- [ ] Start new simple conversion with setting disabled
- [ ] Check logs, verify ModelTier.LIGHT is selected
- [ ] Verify LLM calls use light model (e.g., gemini-flash-lite-latest)
- [ ] Test with missing config field, verify defaults to false
- [ ] Test invalid config value (non-boolean), verify falls back to false

## Acceptance Criteria (Checklist)
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

## Rollout / Migration Plan
Not applicable - no data migration required. Feature is additive with safe default (false).

## Risks and Alternatives

### Risks
- **Cost increase**: Users may enable full LLM mode without understanding cost implications
  - Mitigation: Clear warning message in UI when enabling
- **Performance degradation**: Full models are slower, may impact user experience
  - Mitigation: Warning message mentions increased processing time
- **Config file corruption**: Manual edits to config file could break the setting
  - Mitigation: Validation and fallback to default in get_use_full_model()
- **Confusion with token threshold**: Users may not understand the difference between token_threshold and use_full_model
  - Mitigation: Clear help text in UI explaining the distinction

### Alternatives considered
- **Per-step model selection**: Allow users to choose model tier for each step (sanitize, chunk, etc.)
  - Rejected: Too complex for initial implementation, can be added later if needed
- **Automatic model selection based on document size**: Use full model for small docs, light for large
  - Rejected: Contradicts user request for explicit control
- **Cost estimation before processing**: Show estimated cost before conversion
  - Rejected: Out of scope, complex to implement accurately
- **Environment variable instead of config file**: Store setting in .env
  - Rejected: Settings page already uses vulcanlab.config.json pattern for conversion settings

## Patterns and Standards Alignment (from documentation/patterns.md)

### Patterns applied
- **Dual Configuration System**: Using vulcanlab.config.json for app-level settings (not API config)
  - Follows pattern: conversion settings live in vulcanlab.config.json, accessed via vulcanlab.config.conversion_config
- **Core Module Independence**: All logic in src/vulcanlab, no FastAPI imports in conversion_config.py
  - Follows pattern: Core module functions remain framework-agnostic
- **API Layer (Thin)**: API endpoint orchestrates, calls core module functions
  - Follows pattern: API router calls conversion_config functions, doesn't implement logic
- **Frontend Component Structure**: Using existing Shadcn/Radix Switch component
  - Follows pattern: Reusing components from vulcanlab_ui/src/components/ui/
- **Client Components**: ConversionTab is already "use client" for interactivity
  - Follows pattern: Client component for forms and interactive elements
- **Database Session Management**: Not applicable (no DB changes)
- **Testing Strategy**: Unit tests with mocking, no real DB/LLM calls
  - Follows pattern: Unit tests in tests/unit with strict isolation

### Deviations (if any)
- None - this spec fully aligns with existing patterns

## Implementation Notes (Non-binding)
- ConversionTab.tsx already has pattern for toggle with async save (see advancedMode)
- Reuse the same UI pattern: Switch component, loading state, success message, error handling
- conversion_config.py already has get_advanced_mode_enabled/set_advanced_mode_enabled as reference
- Copy the pattern for use_full_model functions
- The API endpoint already handles multiple fields in the settings object
- Just add use_full_model to the ConversionSettingsData TypedDict/Pydantic model
- Simple conversion modules already import create_langchain_chat from vulcanlab.ai.llm_factory
- Just need to change tier parameter from hardcoded ModelTier.LIGHT to conditional
- Consider adding a helper function in conversion_config.py: get_model_tier_for_simple_conversion() that returns the appropriate ModelTier

## Open Questions
- None - all clarifications received from user
