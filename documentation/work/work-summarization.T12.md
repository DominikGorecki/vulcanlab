# Ticket: work-summarization.T12 - Summarize Settings API Endpoints

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add API endpoints for reading and updating summarize settings
* Support salience weight and threshold configuration
* Integrate with existing settings router pattern

## Phase

* APIs

## Scope

### In scope

* GET /api/v1/settings/summarize - retrieve current settings
* PUT /api/v1/settings/summarize - update settings
* Pydantic models for settings request/response
* Validation of weight values (0-1 range, sum constraints if applicable)
* Add to existing settings router or create dedicated endpoints in summarize router

### Out of scope

* Settings UI (T13)
* Core summarization logic changes

## Dependencies

* Depends on: T03 (SummarizeSettings model)
* Unblocks: T13

## Implementation plan

1. Define Pydantic models in summarize.py or settings router:
   - `SummarizeSettingsResponse` with all settings fields
   - `SummarizeSettingsUpdateRequest` with all settings fields (optional for partial updates)
2. Implement GET /api/v1/settings/summarize:
   - Query SummarizeSettings from database (should be single row)
   - If no row exists, return defaults
   - Return settings response
3. Implement PUT /api/v1/settings/summarize:
   - Validate input values:
     - h2_top_percent: 0-100
     - threshold values: 0.0-1.0
     - weight values: 0.0-1.0
   - Upsert SummarizeSettings row
   - Return updated settings
4. Add validation logic:
   - Weights should be non-negative
   - Thresholds should be in 0-1 range
   - h2_top_percent should be 0-100
5. Consider adding reset endpoint or default values in response for UI
6. Register endpoints (either in settings router or summarize router)
* Patterns to apply:
  * API versioning: /api/v1 prefix
  * Thin API layer
  * Pydantic validation
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * GET returns default values when no settings exist
  * GET returns stored values when settings exist
  * PUT updates settings successfully
  * PUT validates h2_top_percent range (0-100)
  * PUT validates threshold range (0.0-1.0)
  * PUT validates weight range (0.0-1.0)
  * PUT rejects negative values
  * PUT handles partial updates (only some fields provided)
  * Concurrent updates don't corrupt data
* Suggested locations:
  * tests/unit/api/routers/test_summarize_settings.py
* Mocking/fakes needed:
  * Mock database session
  * Use FastAPI TestClient

## Acceptance criteria (checklist)

* [ ] GET endpoint returns current settings
* [ ] GET returns defaults when no settings row exists
* [ ] PUT updates settings in database
* [ ] PUT validates all numeric ranges
* [ ] PUT supports partial updates
* [ ] Invalid values return 400 with clear error message
* [ ] Endpoints follow /api/v1 prefix convention
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. GET /api/v1/settings/summarize - note default values
  2. PUT /api/v1/settings/summarize with {"h3_salience_threshold": 0.6}
  3. GET again - verify h3_salience_threshold updated
  4. PUT with invalid value {"h2_top_percent": 150}
  5. Verify 400 error response
* Expected results:
  * Settings retrieved and updated correctly
  * Invalid values rejected with clear message

## Notes

* Requirements covered: R4, R16
* Single settings row pattern - upsert on update
* Consider adding LLM model selection to settings if configurable per R16
* Default values should match migration defaults for consistency
* May want to add "reset to defaults" functionality
