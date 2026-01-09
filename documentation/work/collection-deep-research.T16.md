# Ticket: collection-deep-research.T16 - Automated Research API Endpoint and Background Execution

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement API endpoint to trigger automated research workflow
* Enable background execution of LangGraph workflow using FastAPI BackgroundTasks
* Provide progress tracking and status updates for running automated sessions

## Phase

* APIs

## Scope

### In scope

* API endpoint: POST /api/v1/research-sessions/{session_id}/start-automated
* Background task execution for LangGraph workflow (T15)
* Progress tracking: update research_sessions.current_phase after each node
* Error handling and status updates (status='failed' on exception)

### Out of scope

* Manual wizard endpoints (covered in T09-T10)
* Frontend integration (covered in T19)
* Celery integration (deferred, BackgroundTasks sufficient for MVP)

## Dependencies

* Depends on: T09 (core API endpoints), T15 (workflow graph)
* Unblocks: T19 (frontend trigger for automated research)

## Implementation plan

* Add endpoint to src/vulcanlab_api/routers/research_sessions.py
* Define Pydantic schema:
  * StartAutomatedResearchRequest: {collection_id: int}
  * StartAutomatedResearchResponse: {session_id: int, thread_id: str, status: str, message: str}
* Implement POST /api/v1/research-sessions/start-automated:
  * Validate request body (collection_id)
  * Verify user owns collection (authorization)
  * Create research_session with session_type='automated' (T03)
  * Get thread_id from created session
  * Create background task: background_tasks.add_task(run_automated_research, session_id, thread_id)
  * Return StartAutomatedResearchResponse with session_id, thread_id, status='in_progress', message='Automated research started'
* Implement run_automated_research background function:
  * Accept session_id, thread_id
  * Create database session (from session factory)
  * Try:
    * Call start_automated_research from T15 with collection_id and session
    * Workflow executes in background
    * On completion: session status already updated to 'completed' by final_synthesis_node
  * Except Exception as e:
    * Log error
    * Update session status to 'failed' using update_research_session from T03
    * Store error message in state_data
  * Finally:
    * Close database session
* Add progress tracking callback:
  * After each node execution, update research_sessions.current_phase
  * Checkpointer already saves state (T11), but explicitly update current_phase column for API queries
* Patterns to apply:
  * **Thin API layer** - Orchestrate call to workflow (T15) per patterns.md section 3
  * **Global exception handling** - Let background task handle exceptions, update status per patterns.md section 3.2
  * **Background task execution** - Use FastAPI BackgroundTasks per spec Implementation Notes
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * POST /api/v1/research-sessions/start-automated creates session and returns session_id
  * POST /api/v1/research-sessions/start-automated validates collection_id
  * POST /api/v1/research-sessions/start-automated enforces authorization (user owns collection)
  * POST /api/v1/research-sessions/start-automated adds background task
  * run_automated_research calls start_automated_research from T15
  * run_automated_research updates session status to 'failed' on exception
  * run_automated_research updates current_phase during workflow execution
  * Background task closes database session after completion
* Suggested locations:
  * tests/unit/api/test_research_sessions_automated.py
* Mocking/fakes needed:
  * Mock start_automated_research from T15
  * Mock database session factory
  * Mock background_tasks.add_task

## Acceptance criteria (checklist)

* [ ] POST /api/v1/research-sessions/start-automated endpoint implemented
* [ ] Endpoint creates session with session_type='automated' (R2, R5)
* [ ] Endpoint starts background task for workflow execution
* [ ] run_automated_research function executes LangGraph workflow
* [ ] Background task updates session status to 'completed' on success
* [ ] Background task updates session status to 'failed' on exception
* [ ] Progress tracking updates current_phase during execution
* [ ] Authorization enforced (user owns collection)
* [ ] Unit tests pass for endpoint and background task

## Manual verification

* Steps:
  * Create test collection with 5 items
  * POST /api/v1/research-sessions/start-automated with {collection_id: 1}
  * Verify 201 response with session_id and status='in_progress'
  * Check database: research_sessions row created with session_type='automated'
  * Wait for background task to complete (or mock for faster testing)
  * Query GET /api/v1/research-sessions/{session_id}
  * Verify current_phase updated through workflow (planning → research → synthesis → completed)
  * Verify final status='completed'
  * Query GET /api/v1/research-sessions/{session_id}/report
  * Verify report saved with content
  * Test error case: mock LLM to fail, verify status='failed' and error logged
* Expected results:
  * Automated research starts and runs in background
  * Session status and phase updated correctly
  * Final report saved on completion
  * Errors handled gracefully

## Notes

* Requirements covered: R2 (automated research option), R5 (LangGraph orchestration), background execution
* BackgroundTasks sufficient for MVP per spec Implementation Notes (can migrate to Celery if needed)
* Progress tracking enables frontend to show "Planning: Complete, Research: 2/5 sections" per spec UX section
* Error handling critical: automated workflow should not crash server, always update session status
* Database session management in background task: create new session, close after completion
