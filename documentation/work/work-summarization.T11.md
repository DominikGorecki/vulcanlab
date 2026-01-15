# Ticket: work-summarization.T11 - Summarize API Router

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create FastAPI router for summarization endpoints
* Expose trigger, status, nodes, derive, and list endpoints
* Register router in main.py with /api/v1 prefix

## Phase

* APIs

## Scope

### In scope

* src/vulcanlab_api/routers/summarize.py router
* POST /api/v1/summarize/{work_id} - trigger summarization
* GET /api/v1/summarize/{work_id}/status - get summarization status
* GET /api/v1/summarize/{work_id}/nodes - get summary nodes
* POST /api/v1/summarize/{work_id}/derive - generate derived output
* GET /api/v1/summarize/{work_id}/summaries - get all derived outputs
* GET /api/v1/summarize/works - list works with summaries
* DELETE /api/v1/summarize/{work_id} - delete summaries (for re-summarize)
* Pydantic request/response models
* Register router in main.py

### Out of scope

* Settings endpoints (T12)
* Core summarization logic (implemented in T04-T09)
* Frontend (T13-T16)

## Dependencies

* Depends on: T03 (models), T08 (orchestrator), T09 (compile)
* Unblocks: T13, T14, T15, T16

## Implementation plan

1. Create src/vulcanlab_api/routers/summarize.py
2. Define Pydantic response models:
   - `SummarizationTriggerResponse(status: str, message: str)`
   - `SummarizationStatusResponse(status: str, total_nodes: int, completed_nodes: int, error: str | None)`
   - `SummaryNodeResponse` with all fields from SummaryNode model
   - `SummaryNodesResponse(nodes: list[SummaryNodeResponse])`
   - `DeriveRequest(type: Literal['abstract', 'outline', 'key_concepts', 'chapter_summaries'])`
   - `DeriveResponse(summary_id: int, type: str, content: dict, line_references: list)`
   - `WorkSummaryResponse` with all fields
   - `SummarizedWorkResponse(work_id: int, title: str, node_count: int, summaries: list[str])`
   - `SummarizedWorksResponse(works: list[SummarizedWorkResponse])`
3. Implement POST /summarize/{work_id}:
   - Validate work exists
   - Check if already summarized (return status if so, unless force=true query param)
   - Call orchestrator.summarize_work
   - Return trigger response
4. Implement GET /summarize/{work_id}/status:
   - Call orchestrator.get_summarization_status
   - Return status response or 404
5. Implement GET /summarize/{work_id}/nodes:
   - Query summary_nodes for work
   - Return list response
6. Implement POST /summarize/{work_id}/derive:
   - Validate type in request body
   - Check summary_nodes exist
   - Call compile.generate_derived_output
   - Return derive response
7. Implement GET /summarize/{work_id}/summaries:
   - Query work_summaries for work
   - Return list response
8. Implement GET /summarize/works:
   - Query works that have summary_nodes
   - Include node counts and available summary types
   - Return list response
9. Implement DELETE /summarize/{work_id}:
   - Call orchestrator.delete_existing_summaries
   - Return success response
10. Register router in main.py: `app.include_router(summarize_router, prefix="/api/v1/summarize")`
* Patterns to apply:
  * API versioning: /api/v1 prefix in main.py
  * Thin API layer: delegate to core module
  * Global exception handling (don't wrap in try/except)
  * Session from dependency injection
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * POST /summarize/{work_id} returns 404 for non-existent work
  * POST /summarize/{work_id} triggers summarization for valid work
  * POST /summarize/{work_id} with force=true regenerates
  * GET /summarize/{work_id}/status returns correct progress
  * GET /summarize/{work_id}/status returns 404 for unsummarized work
  * GET /summarize/{work_id}/nodes returns all nodes
  * GET /summarize/{work_id}/nodes returns empty list for unsummarized work
  * POST /summarize/{work_id}/derive validates type parameter
  * POST /summarize/{work_id}/derive returns 400 if no summary_nodes
  * GET /summarize/{work_id}/summaries returns derived outputs
  * GET /summarize/works returns works with summaries
  * DELETE /summarize/{work_id} removes summaries
* Suggested locations:
  * tests/unit/api/routers/test_summarize.py
* Mocking/fakes needed:
  * Mock orchestrator functions
  * Mock compile functions
  * Mock database session
  * Use FastAPI TestClient

## Acceptance criteria (checklist)

* [ ] All endpoints implemented per spec
* [ ] Router registered with /api/v1/summarize prefix
* [ ] Pydantic models validate request/response data
* [ ] Work existence validated before operations
* [ ] 404 returned for non-existent resources
* [ ] 400 returned for invalid requests (bad type, no nodes)
* [ ] Force regeneration supported via query parameter
* [ ] Thin API layer - logic delegated to core module
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Start API server
  2. POST /api/v1/summarize/{work_id} for a work with chunks
  3. GET /api/v1/summarize/{work_id}/status to check progress
  4. GET /api/v1/summarize/{work_id}/nodes after completion
  5. POST /api/v1/summarize/{work_id}/derive with {"type": "outline"}
  6. GET /api/v1/summarize/works to see in list
* Expected results:
  * Summarization triggers and completes
  * Status shows progress
  * Nodes returned after completion
  * Derived output generated and returned

## Notes

* Requirements covered: R12 (trigger), R13 (list), R14 (derive), R17 (re-summarize via DELETE + POST)
* The trigger endpoint is synchronous per R15 - consider adding streaming progress later
* Force parameter enables re-summarization without separate DELETE call
* Consider rate limiting for trigger endpoint to prevent abuse
* Error responses should use standard FastAPI HTTPException
