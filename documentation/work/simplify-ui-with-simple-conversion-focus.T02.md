# Ticket: simplify-ui-with-simple-conversion-focus.T02 - Backend API: Advanced Conversion Toggle Config

## Source
- Spec: documentation/work/simplify-ui-with-simple-conversion-focus.spec.md
- Patterns: documentation/patterns.md

## Goal
- Extend existing conversion settings API to include advanced_mode_enabled boolean field
- Support GET and PUT operations for the toggle state
- Store configuration in backend config system (vulcanlab.config.json or rag_config table)

## Scope
### In scope
- Extend GET /api/conversion/settings endpoint to return advanced_mode_enabled field
- Extend PUT /api/conversion/settings endpoint to accept and persist advanced_mode_enabled field
- Add advanced_mode_enabled to conversion config storage with default value false
- Validation that advanced_mode_enabled is boolean type
- Error handling for config read/write failures

### Out of scope
- Creating new API endpoints (extend existing)
- Frontend integration (handled in T04)
- Navigation visibility logic (frontend concern)
- Database schema changes (using existing config storage)

## Dependencies
- Depends on: none (independent backend work)
- Unblocks: T04 (frontend settings UI needs API)

## Implementation plan
1. Locate existing conversion settings router (likely src/vulcanlab_api/routers/)
2. Identify GET /api/conversion/settings endpoint handler
3. Locate conversion config storage mechanism (check vulcanlab.config module)
4. Add advanced_mode_enabled field to config schema/model with default false
5. Update GET endpoint to include advanced_mode_enabled in response
6. Update PUT endpoint to accept advanced_mode_enabled in request body
7. Add Pydantic model validation for boolean type on advanced_mode_enabled
8. Ensure config persistence writes to correct storage (JSON file or database)
9. Test config read/write cycle: set value, restart, verify persisted
10. Add error handling for missing or invalid config values (default to false)

- Patterns to apply:
  - **Thin API Layer** - Router orchestrates config read/write, logic stays in core module
  - **Dual Config System** - Use App Config (vulcanlab.config) not API Config (env vars)
  - **Explicit Session Passing** - Pass database session to any data access functions
  - **Global Exception Handlers** - Raise HTTPException for expected errors, let global handler catch others

- Deviations (if any):
  - None - follows established API patterns

## Unit tests (required)
- Add tests for:
  - GET endpoint returns advanced_mode_enabled field with default false
  - GET endpoint returns advanced_mode_enabled = true after being set
  - PUT endpoint successfully updates advanced_mode_enabled to true
  - PUT endpoint successfully updates advanced_mode_enabled to false
  - PUT endpoint rejects non-boolean values for advanced_mode_enabled (422 validation error)
  - PUT endpoint persists value across config reload
  - Config defaults to false if advanced_mode_enabled key is missing
  - Config read failure returns default value without crashing
- Suggested locations:
  - tests/unit/test_conversion_settings_api.py (new or extend existing)
  - tests/unit/test_conversion_config.py (if testing config module directly)
- Mocking/fakes needed:
  - Mock config file read/write operations
  - Mock database session if using rag_config table
  - No real file I/O or database connections in unit tests

## Acceptance criteria (checklist)
- [ ] GET /api/conversion/settings includes advanced_mode_enabled field in response
- [ ] Default value for advanced_mode_enabled is false
- [ ] PUT /api/conversion/settings accepts advanced_mode_enabled in request
- [ ] PUT validates advanced_mode_enabled is boolean type
- [ ] Config changes persist to storage (JSON or database)
- [ ] Config changes survive application restart
- [ ] Invalid values return 422 validation error
- [ ] Missing config key defaults to false gracefully
- [ ] Unit tests cover GET, PUT, validation, and persistence

## Manual verification
- Steps:
  1. Start application and GET /api/conversion/settings
  2. Verify response includes "advanced_mode_enabled": false
  3. PUT /api/conversion/settings with {"advanced_mode_enabled": true, ...}
  4. GET /api/conversion/settings again and verify value is true
  5. Restart application (or reload config)
  6. GET /api/conversion/settings and verify value is still true
  7. PUT with invalid value like {"advanced_mode_enabled": "yes"}
  8. Verify 422 validation error response
- Expected results:
  - Default value is false on fresh install
  - Value persists across requests and restarts
  - Validation rejects non-boolean values
  - No crashes or 500 errors on config operations

## Notes
- Check if conversion settings are stored in vulcanlab.config.json or in database rag_config table
- If using JSON file, ensure thread-safe read/write with proper locking
- If using database table, use existing session management patterns
- The response schema should match existing conversion settings format with added field
- Consider adding config migration if existing installs need the new field added automatically
- This is a purely additive change - existing config fields remain unchanged
