# Ticket: rag-query-manual-result-model-tracking.T02 - API Endpoints for Model Management & Result Tracking

## Source

* Spec: documentation/work/rag-query-manual-result-model-tracking.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement API endpoints for listing and creating result models
* Modify manual result endpoint to accept model selection
* Modify automatic result endpoint to capture model from config
* Return model_name in result list and detail responses

## Scope

### In scope

* New router `src/vulcanlab_api/routers/result_models.py` with endpoints:
  * `GET /api/v1/rag/result-models` - List all models
  * `POST /api/v1/rag/result-models` - Create new model
* Modify `src/vulcanlab_api/routers/rag.py` (or equivalent):
  * Update `POST /api/v1/rag/queries/{id}/augment/manual` to accept `model_id` or `new_model_name`
  * Update `POST /api/v1/rag/queries/{id}/augment/run` to capture model from config
  * Update `GET /api/v1/rag/queries/{id}/results` to return `model_name` (denormalized)
  * Update `GET /api/v1/rag/results/{id}` to return `model_name`
* Helper function to get or create model by name
* Unit tests for all new/modified endpoints

### Out of scope

* Frontend changes (covered in T03-T05)
* Database schema (covered in T01)
* Model deletion or editing endpoints (not in spec)
* Provider metadata or model configuration

## Dependencies

* Depends on: T01 (database schema and models must exist)
* Unblocks: T03, T04, T05

## Implementation plan

1. Create new router file `src/vulcanlab_api/routers/result_models.py`:
   * Define `GET /result-models` endpoint:
     - Query all ResultModel records ordered by name
     - Return JSON: `{"models": [{"id": int, "name": str, "created_at": str}, ...]}`
   * Define `POST /result-models` endpoint:
     - Accept request body: `{"name": str}`
     - Validate name is not empty (strip whitespace, check length > 0)
     - Create ResultModel record
     - Handle unique constraint violation (return 409 Conflict with message)
     - Return JSON: `{"id": int, "name": str, "created_at": str, "message": "Model created successfully"}`
   * Use dependency injection for database session (follow existing pattern in other routers)

2. Register new router in `src/vulcanlab_api/main.py`:
   * Import `result_models` router
   * Add `app.include_router(result_models.router, prefix="/api/v1/rag", tags=["result-models"])`

3. Create helper function `get_or_create_result_model(name: str, session: Session) -> ResultModel`:
   * Check if model with given name exists
   * If exists, return it
   * If not, create new ResultModel and return it
   * Handle race conditions (unique constraint violation on concurrent creates)
   * Place in `src/vulcanlab_api/routers/result_models.py` or a shared utils module

4. Modify manual result endpoint in `src/vulcanlab_api/routers/rag.py`:
   * Update request schema to include optional `model_id: Optional[int]` and `new_model_name: Optional[str]`
   * Logic:
     - If `new_model_name` provided: call `get_or_create_result_model(new_model_name, session)` to get model_id
     - Else if `model_id` provided: verify model exists, use it
     - Else: set model_id = None
   * Save Result with model_id
   * Return response including `model_name` (join or query ResultModel if model_id not None)

5. Modify automatic result endpoint in `src/vulcanlab_api/routers/rag.py`:
   * Read model name from `vulcanlab.config.json` using `load_config()` (determine exact path - likely `config.llm.model_name` or similar)
   * Call `get_or_create_result_model(model_name, session)` to get model_id
   * Save Result with model_id
   * Return response including `model_name`
   * Log model capture event for observability

6. Modify results list endpoint `GET /api/v1/rag/queries/{id}/results`:
   * Update query to LEFT JOIN `result_models` on `results.model_id`
   * Return `model_name` in each result object (use "Unspecified" if model_id is NULL or model not found)
   * Denormalize to avoid N+1 queries

7. Modify result detail endpoint `GET /api/v1/rag/results/{id}`:
   * Update query to LEFT JOIN `result_models` on `results.model_id`
   * Return `model_name` in response (use "Unspecified" if NULL)

8. Write unit tests in `tests/unit/test_result_models_api.py`:
   * Test `GET /result-models` returns all models
   * Test `POST /result-models` creates new model
   * Test `POST /result-models` with duplicate name returns 409 Conflict
   * Test `POST /result-models` with empty name returns 400 Bad Request
   * Mock database session and ResultModel queries/inserts

9. Write unit tests in `tests/unit/test_rag_augment_api.py` (or extend existing):
   * Test manual result endpoint with `model_id` saves correct model_id
   * Test manual result endpoint with `new_model_name` creates model and saves result
   * Test manual result endpoint with neither saves result with NULL model_id
   * Test automatic result endpoint captures model from config and saves result
   * Test results list endpoint returns model_name for each result
   * Test result detail endpoint returns model_name
   * Mock config loading, database session, and model creation

* Patterns to apply:
  * **Three-tier architecture**: API layer orchestrates calls to core models, does not implement business logic
  * **API Routing**: Endpoints under `/api/v1/rag/` prefix (defined in main.py)
  * **Error Handling**: Raise HTTPException for 400/404/409, let global handler catch 500s
  * **Session Management**: Database session passed via dependency injection (not created inside endpoint)
  * **Configuration**: Use `vulcanlab.config.load_config()` for app config (model name from config)

* Deviations (if any):
  * None - follows established API patterns

## Unit tests (required)

* Add tests for:
  * GET /result-models returns empty list when no models exist
  * GET /result-models returns all models ordered by name
  * POST /result-models creates model and returns 201 with model data
  * POST /result-models with duplicate name returns 409 Conflict
  * POST /result-models with empty/whitespace name returns 400 Bad Request
  * Manual result endpoint saves result with model_id when model_id provided
  * Manual result endpoint creates model and saves result when new_model_name provided
  * Manual result endpoint saves result with NULL model_id when neither provided
  * Automatic result endpoint reads model from config and saves result with model_id
  * get_or_create_result_model creates new model if not exists
  * get_or_create_result_model returns existing model if exists
  * get_or_create_result_model handles concurrent creation (unique constraint)
  * Results list endpoint denormalizes model_name correctly
  * Results list endpoint shows "Unspecified" for NULL model_id
  * Result detail endpoint shows model_name

* Suggested locations:
  * `tests/unit/test_result_models_api.py` - new file for result_models router tests
  * `tests/unit/test_rag_augment_api.py` - extend or create for augment endpoint tests

* Mocking/fakes needed:
  * Mock database session (use pytest-mock or unittest.mock)
  * Mock `vulcanlab.config.load_config()` to return test config with model name
  * Mock ResultModel and Result queries/inserts
  * Do NOT connect to real database

## Acceptance criteria (checklist)

* [ ] `GET /api/v1/rag/result-models` endpoint exists and returns all models
* [ ] `POST /api/v1/rag/result-models` endpoint exists and creates new models
* [ ] POST endpoint validates name is not empty
* [ ] POST endpoint returns 409 Conflict on duplicate model name
* [ ] `get_or_create_result_model()` helper function exists and works correctly
* [ ] Manual result endpoint accepts `model_id` and `new_model_name` parameters
* [ ] Manual result endpoint saves result with correct model_id
* [ ] Manual result endpoint creates new model when `new_model_name` provided
* [ ] Automatic result endpoint reads model from `vulcanlab.config.json`
* [ ] Automatic result endpoint calls `get_or_create_result_model()` to get model_id
* [ ] Automatic result endpoint saves result with model_id
* [ ] Results list endpoint returns `model_name` for each result
* [ ] Results list endpoint shows "Unspecified" for NULL model_id
* [ ] Result detail endpoint returns `model_name`
* [ ] All unit tests pass without connecting to real database
* [ ] Router registered in main.py with correct prefix

## Manual verification

* Steps:
  1. Start API server: `uvicorn vulcanlab_api.main:app --reload`
  2. Test GET /api/v1/rag/result-models: `curl http://localhost:8000/api/v1/rag/result-models`
  3. Test POST /api/v1/rag/result-models: `curl -X POST http://localhost:8000/api/v1/rag/result-models -H "Content-Type: application/json" -d '{"name": "gpt-4"}'`
  4. Test duplicate POST (expect 409): `curl -X POST http://localhost:8000/api/v1/rag/result-models -H "Content-Type: application/json" -d '{"name": "gpt-4"}'`
  5. Create a query and test manual result endpoint with model_id
  6. Create a query and test manual result endpoint with new_model_name
  7. Create a query and test automatic result endpoint (verify model from config is captured)
  8. Test results list endpoint and verify model_name is returned
  9. Test result detail endpoint and verify model_name is returned
  10. Run unit tests: `pytest tests/unit/test_result_models_api.py tests/unit/test_rag_augment_api.py -v`

* Expected results:
  * GET /result-models returns list of models including "Unspecified"
  * POST /result-models creates new model and returns 201
  * Duplicate POST returns 409 Conflict
  * Manual result endpoint accepts model parameters and saves correctly
  * Automatic result endpoint captures model from config
  * Results list and detail endpoints return model_name
  * All unit tests pass

## Notes

* Requirements covered: R6, R7, R8, R10 (partial - backend only), R9 (partial - backend only)
* Config path for model name: Need to determine exact path in `vulcanlab.config.json`. Likely `llm.model_name` or `generation.model`. Check existing config structure.
* Denormalization in results list is important to avoid N+1 query problem (do not query model for each result individually)
* Use LEFT JOIN to include results with NULL model_id
* "Unspecified" fallback should be consistent: if model_id is NULL, show "Unspecified" in response
* Log model selection events for manual and automatic results (per spec non-functional requirements)
* Handle race conditions in `get_or_create_result_model`: if two requests create same model concurrently, one will get unique constraint violation - catch and retry query
* Validation: Model name should not be empty or only whitespace. Trim and check length > 0 before creating.
