# Ticket: collection-deep-research.T09 - Research Session API Endpoints (Core CRUD)

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement FastAPI router with core CRUD endpoints for research sessions, sections, and reports
* Provide HTTP interface for session lifecycle management (create, retrieve, update, list)
* Enable both manual wizard and automated workflow to persist session state via API

## Phase

* APIs

## Scope

### In scope

* FastAPI router src/vulcanlab_api/routers/research_sessions.py with /api/v1/research-sessions prefix
* Endpoints:
  * POST /api/v1/research-sessions (create session)
  * GET /api/v1/research-sessions/{session_id} (retrieve session)
  * PUT /api/v1/research-sessions/{session_id} (update session)
  * GET /api/v1/collections/{collection_id}/research-sessions (list sessions)
  * POST /api/v1/research-sessions/{session_id}/sections (save section)
  * GET /api/v1/research-sessions/{session_id}/sections (list sections)
  * POST /api/v1/research-sessions/{session_id}/report (save report)
  * GET /api/v1/research-sessions/{session_id}/report (retrieve report)
* Request/response schemas (Pydantic models)
* Authorization checks (session scoped to collection owner)

### Out of scope

* Context assembly endpoint (covered in T14)
* Result matching endpoint (covered in T14)
* Resume endpoint (covered in T14)
* LangGraph workflow trigger (covered in T17)
* Frontend integration (covered in T19-T24)

## Dependencies

* Depends on: T03 (CRUD functions)
* Unblocks: T19 (UI components), T20 (manual wizard)

## Implementation plan

* Create src/vulcanlab_api/routers/research_sessions.py
* Define Pydantic schemas:
  * CreateResearchSessionRequest: {collection_id: int, session_type: str}
  * ResearchSessionResponse: {session_id, collection_id, session_type, thread_id, current_phase, research_plan, state_data, status, created_at, updated_at, completed_at}
  * UpdateResearchSessionRequest: {current_phase?, research_plan?, state_data?, status?}
  * CreateResearchSectionRequest: {question_id, question_text, section_content?, context_data?, matching_results?, metadata?, reuse_info?}
  * ResearchSectionResponse: {section_id, question_id, question_text, section_content, metadata, quality_status}
  * CreateResearchReportRequest: {report_content, executive_summary?, quality_evaluation?, metadata?}
  * ResearchReportResponse: {report_id, session_id, report_content, executive_summary, quality_evaluation, metadata, created_at}
* Implement POST /api/v1/research-sessions:
  * Validate request body (collection_id exists, session_type in ['manual', 'automated'])
  * Generate thread_id using T03 generate_thread_id utility
  * Call create_research_session from T03
  * Return ResearchSessionResponse
* Implement GET /api/v1/research-sessions/{session_id}:
  * Call get_research_session from T03
  * Verify user has permission (session.collection.owner_id == current_user_id)
  * Return ResearchSessionResponse or 404
* Implement PUT /api/v1/research-sessions/{session_id}:
  * Validate request body
  * Call update_research_session from T03
  * Return updated ResearchSessionResponse
* Implement GET /api/v1/collections/{collection_id}/research-sessions:
  * Verify user owns collection
  * Call list_research_sessions_for_collection from T03
  * Return list of ResearchSessionResponse
* Implement POST /api/v1/research-sessions/{session_id}/sections:
  * Validate request body (question_id, question_text required)
  * Call create_research_section from T03
  * Return ResearchSectionResponse
* Implement GET /api/v1/research-sessions/{session_id}/sections:
  * Call get_research_sections from T03
  * Return list of ResearchSectionResponse
* Implement POST /api/v1/research-sessions/{session_id}/report:
  * Validate request body (report_content required)
  * Call create_research_report from T03 (also marks session completed)
  * Return ResearchReportResponse
* Implement GET /api/v1/research-sessions/{session_id}/report:
  * Call get_research_report from T03
  * Return ResearchReportResponse or 404
* Add authentication/authorization dependency injection
* Add router to main.py with prefix /api/v1 per patterns.md section 3.1
* Patterns to apply:
  * **API versioning** - Prefix /api/v1 defined in main.py per patterns.md section 3.1
  * **Thin API layer** - Orchestrate calls to Core Module (T03 CRUD) per patterns.md section 3
  * **Global exception handling** - Raise HTTPException or specific errors, let global handler catch per patterns.md section 3.2
  * **Authorization** - Verify user owns collection before allowing session access per R6 security requirement
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * POST /api/v1/research-sessions creates session and returns correct response
  * POST /api/v1/research-sessions rejects invalid session_type
  * GET /api/v1/research-sessions/{session_id} returns session for authorized user
  * GET /api/v1/research-sessions/{session_id} returns 403 for unauthorized user
  * PUT /api/v1/research-sessions/{session_id} updates session fields
  * GET /api/v1/collections/{collection_id}/research-sessions returns list ordered by created_at DESC
  * POST /api/v1/research-sessions/{session_id}/sections creates section
  * GET /api/v1/research-sessions/{session_id}/sections returns all sections ordered by question_id
  * POST /api/v1/research-sessions/{session_id}/report creates report and marks session completed
  * GET /api/v1/research-sessions/{session_id}/report returns latest report
* Suggested locations:
  * tests/unit/api/test_research_sessions.py
* Mocking/fakes needed:
  * Mock database session and CRUD functions from T03
  * Mock authentication/authorization (current_user fixture)

## Acceptance criteria (checklist)

* [ ] All 8 endpoints implemented in research_sessions.py router
* [ ] Pydantic schemas defined for all requests and responses
* [ ] POST /api/v1/research-sessions generates thread_id correctly (R15)
* [ ] Authorization checks verify user owns collection (R6 security)
* [ ] POST /api/v1/research-sessions/{session_id}/report marks session completed
* [ ] Router added to main.py with /api/v1 prefix
* [ ] Unit tests pass for all endpoints with mocked CRUD and auth

## Manual verification

* Steps:
  * Start FastAPI server
  * POST /api/v1/research-sessions with {collection_id: 1, session_type: "manual"}
  * Verify 201 response with session_id and thread_id format (manual_{ts}_{random})
  * GET /api/v1/research-sessions/{session_id}, verify returns session data
  * PUT /api/v1/research-sessions/{session_id} with {current_phase: "research"}, verify update
  * POST /api/v1/research-sessions/{session_id}/sections with section data, verify created
  * GET /api/v1/research-sessions/{session_id}/sections, verify section returned
  * POST /api/v1/research-sessions/{session_id}/report with report content, verify session status becomes "completed"
  * GET /api/v1/research-sessions/{session_id}/report, verify report returned
* Expected results:
  * All endpoints work correctly
  * Authorization enforced
  * Session state persists correctly

## Notes

* Requirements covered: R6 (persist session state), R15 (thread_id format), security requirement (session scoped to owner)
* Router prefix /api/v1 per patterns.md API versioning standard
* Global exception handling per patterns.md - no try/except Exception blocks in endpoints
* Thin layer - endpoints call CRUD from T03, no business logic in API layer
