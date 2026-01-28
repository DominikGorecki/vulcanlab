# Ticket: expand-answer.T03 - API Endpoints for Expansions

## Source

* Spec: documentation/work/expand-answer.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create FastAPI router with all expansion CRUD and operation endpoints
* Define Pydantic schemas for request/response validation
* Enable frontend to interact with expansion feature via REST API

## Scope

### In scope

* Pydantic schemas in `src/vulcanlab_api/schemas/expansions.py`
* Router `src/vulcanlab_api/routers/expansions.py` with endpoints:
  - `POST /api/v1/expansions/` - Create expansion from result_id
  - `GET /api/v1/expansions/` - List all expansions with status summary
  - `GET /api/v1/expansions/{expansion_id}` - Get expansion detail with sections
  - `POST /api/v1/expansions/{expansion_id}/breakdown` - Run initial breakdown
  - `POST /api/v1/expansions/{expansion_id}/sections/{section_id}/expand` - Run RAG pipeline for section
  - `POST /api/v1/expansions/{expansion_id}/sections/{section_id}/generate` - Run LLM generation
  - `POST /api/v1/expansions/{expansion_id}/sections/{section_id}/manual` - Save manual response
  - `POST /api/v1/expansions/{expansion_id}/combine` - Combine sections into report
  - `GET /api/v1/results/{result_id}/expansion` - Get expansion for a result
* Router registration in `main.py` under `/api/v1/expansions`
* Automatic mode orchestration with 2-concurrent parallelism
* Per-section retry capability

### Out of scope

* UI components (T04, T05)
* WebSocket/SSE progress updates (polling is sufficient per spec)

## Dependencies

* Depends on: T01 (models), T02 (core logic)
* Unblocks: T04, T05

## Implementation plan

1. Create `src/vulcanlab_api/schemas/expansions.py`:
   - `CreateExpansionRequest` (result_id, mode)
   - `CreateExpansionResponse` (expansion_id, status)
   - `ExpansionListItem` (id, result_id, mode, status, section_count, created_at)
   - `SectionSummary` (id, order, heading, summary, status, error_message)
   - `SectionDetailResponse` (full section data including RAG fields)
   - `ExpansionDetailResponse` (full expansion with sections list, combined_report)
   - `ManualResponseRequest` (response_text)
2. Create `src/vulcanlab_api/routers/expansions.py`:
   - `POST /` - Create expansion record, return expansion_id
   - `GET /` - List expansions with pagination, return ExpansionListItem[]
   - `GET /{expansion_id}` - Return ExpansionDetailResponse
   - `POST /{expansion_id}/breakdown` - Call `breakdown_answer()`, return updated expansion
   - `POST /{expansion_id}/sections/{section_id}/expand` - Call `expand_section()`
   - `POST /{expansion_id}/sections/{section_id}/generate` - Call `generate_section()`
   - `POST /{expansion_id}/sections/{section_id}/manual` - Call `save_manual_response()`
   - `POST /{expansion_id}/combine` - Call `combine_sections()`
   - `POST /{expansion_id}/run` - Automatic mode: breakdown + expand/generate all sections + combine (with 2-concurrent limit)
3. Add helper endpoint to results router or new file:
   - `GET /api/v1/results/{result_id}/expansion` - Return expansion if exists, 404 otherwise
4. Register router in `src/vulcanlab_api/main.py`:
   - `app.include_router(expansions_router, prefix="/api/v1/expansions")`
5. Implement automatic mode orchestration in `/run` endpoint:
   - Use `asyncio.Semaphore(2)` to limit concurrent section processing
   - Process expand + generate for each section
   - Handle partial failures (continue with remaining sections)
6. Write unit tests for endpoint behavior

* Patterns to apply:
  * API Versioning - All endpoints under `/api/v1/`
  * Error Handling - Use global handlers, raise HTTPException for logical errors
  * Thin API Layer - Orchestrate calls to core module, no business logic in router

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `test_create_expansion_returns_id` - verify POST creates record
  * `test_create_expansion_invalid_result` - 404 for nonexistent result
  * `test_create_expansion_duplicate` - 409 if expansion already exists for result
  * `test_list_expansions_pagination` - verify list with offset/limit
  * `test_get_expansion_detail` - verify all fields returned
  * `test_breakdown_updates_status` - verify status changes
  * `test_expand_section_success` - verify section status transitions
  * `test_generate_section_success` - verify response stored
  * `test_manual_response_success` - verify manual mode works
  * `test_combine_requires_all_complete` - 400 if sections not all completed
  * `test_run_automatic_mode` - verify full pipeline executes
  * `test_retry_failed_section` - verify retry resets status and reprocesses

* Suggested locations:
  * `tests/unit/api/routers/test_expansions.py`

* Mocking/fakes needed:
  * Mock database session
  * Mock core expansion functions (`breakdown_answer`, `expand_section`, etc.)
  * Mock LLM client

## Acceptance criteria (checklist)

* [ ] All endpoints from spec are implemented and return correct response shapes
* [ ] `POST /expansions/` creates expansion and returns ID
* [ ] `GET /expansions/` lists expansions with status summary
* [ ] `GET /expansions/{id}` returns full detail with sections
* [ ] `POST /expansions/{id}/breakdown` runs breakdown and creates sections
* [ ] Section expand/generate/manual endpoints update section state
* [ ] `POST /expansions/{id}/combine` generates final report
* [ ] `POST /expansions/{id}/run` executes full automatic pipeline with 2-concurrent limit
* [ ] `GET /results/{id}/expansion` returns expansion or 404
* [ ] Failed sections can be retried individually
* [ ] Router registered at `/api/v1/expansions`
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Start API server
  2. Use curl/httpie to test endpoints:
     - Create expansion: `POST /api/v1/expansions/` with valid result_id
     - List expansions: `GET /api/v1/expansions/`
     - Get detail: `GET /api/v1/expansions/{id}`
     - Run breakdown: `POST /api/v1/expansions/{id}/breakdown`
     - Check sections created in response
  3. Verify OpenAPI docs at `/docs` show all endpoints

* Expected results:
  * All endpoints return expected status codes and response shapes
  * Expansion and section records created in database
  * OpenAPI documentation complete

## Notes

* Requirements covered: R1 (initiate from result page via API), R4 (RAG pipeline), R5 (auto/manual toggle), R6 (2-concurrent parallelism), R7 (status tracking), R8 (retry failed), R11 (expansions accessible), R12 (result shows expansion link)
* The `/run` endpoint orchestrates automatic mode end-to-end
* Individual section endpoints enable manual mode and granular retry
* Use `asyncio.gather()` with semaphore for parallel section processing
* Return 400 for invalid state transitions (e.g., combine before all sections complete)
* DEVIATION from spec: The `metadata` column was renamed to `expansion_metadata` because SQLAlchemy reserves the name `metadata`. Use `expansion_metadata` in Pydantic schemas.
