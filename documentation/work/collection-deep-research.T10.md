# Ticket: collection-deep-research.T10 - Context and Result Matching API Endpoints

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement specialized API endpoints for manual wizard workflow (context assembly and result matching)
* Enable manual wizard UI to fetch context and check for matching results via API calls
* Provide session resume endpoint for both manual and automated workflows

## Phase

* APIs

## Scope

### In scope

* Additional endpoints in src/vulcanlab_api/routers/research_sessions.py:
  * POST /api/v1/research-sessions/{session_id}/context (assemble context)
  * POST /api/v1/research-sessions/{session_id}/match-results (match results)
  * POST /api/v1/research-sessions/{session_id}/resume (resume session)
* Request/response schemas for new endpoints
* Integration with T05 (result matching) and T06 (context assembly) modules

### Out of scope

* Core CRUD endpoints (covered in T09)
* LangGraph workflow trigger endpoint (covered in T17)
* Frontend integration (covered in T20-T23)

## Dependencies

* Depends on: T05 (result matcher), T06 (context assembler), T09 (core API endpoints)
* Unblocks: T21 (manual wizard Steps 2-3)

## Implementation plan

* Add Pydantic schemas to research_sessions.py:
  * AssembleContextRequest: {question_id: str, relevant_item_ids: list[int]}
  * AssembleContextResponse: {context: str, token_count: int, sources: list[dict]}
  * MatchResultsRequest: {question_id: str, question_text: str}
  * MatchResultsResponse: {matched_results: list[dict], recommended_strategy: str}
  * ResumeSessionRequest: {mode?: str} (optional mode switch)
  * ResumeSessionResponse: {session_id: int, current_phase: str, next_step: dict}
* Implement POST /api/v1/research-sessions/{session_id}/context:
  * Validate request body (question_id, relevant_item_ids)
  * Get research_session by session_id (verify exists and user authorized)
  * Load session state to check for reuse_info (if exists, use reuse workflow)
  * Call assemble_context_for_question from T06 with relevant_item_ids and reuse_info
  * Return AssembleContextResponse with context, token_count, sources
* Implement POST /api/v1/research-sessions/{session_id}/match-results:
  * Validate request body (question_text required)
  * Get research_session by session_id
  * Get collection_id from session
  * Call match_results_for_question from T05 with question_text and collection_id
  * Call recommend_reuse_strategy from T05 with matched_results
  * Return MatchResultsResponse with matched_results and recommended_strategy
* Implement POST /api/v1/research-sessions/{session_id}/resume:
  * Get research_session by session_id
  * Load current_phase and state_data from session
  * Determine next_step based on current_phase:
    * 'planning' → next_step = {step: 'result_matching', question_id: 'Q1'}
    * 'research' → next_step = {step: 'section_generation', question_id: current question}
    * 'synthesis' → next_step = {step: 'quality_evaluation'}
  * If mode parameter provided and different from session.session_type:
    * Update session.session_type (manual ↔ automated switch)
    * Log mode switch
  * Return ResumeSessionResponse with session_id, current_phase, next_step
* Add endpoints to router with proper HTTP methods and paths
* Patterns to apply:
  * **Thin API layer** - Orchestrate calls to Core Module (T05, T06) per patterns.md section 3
  * **Global exception handling** - Raise HTTPException for validation errors per patterns.md section 3.2
  * **Authorization** - Verify user owns session's collection
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * POST /api/v1/research-sessions/{session_id}/context returns context with correct token_count
  * POST /api/v1/research-sessions/{session_id}/context handles reuse workflow (uses reuse_info)
  * POST /api/v1/research-sessions/{session_id}/context handles new generation workflow
  * POST /api/v1/research-sessions/{session_id}/match-results returns matched results
  * POST /api/v1/research-sessions/{session_id}/match-results returns recommended_strategy
  * POST /api/v1/research-sessions/{session_id}/resume returns next_step based on current_phase
  * POST /api/v1/research-sessions/{session_id}/resume allows mode switch (manual → automated)
  * All endpoints enforce authorization (user owns collection)
* Suggested locations:
  * tests/unit/api/test_research_sessions_advanced.py
* Mocking/fakes needed:
  * Mock result_matcher.match_results_for_question
  * Mock context_assembler.assemble_context_for_question
  * Mock database session and research_session queries

## Acceptance criteria (checklist)

* [ ] POST /api/v1/research-sessions/{session_id}/context endpoint implemented
* [ ] Context endpoint calls T06 assemble_context_for_question correctly
* [ ] POST /api/v1/research-sessions/{session_id}/match-results endpoint implemented
* [ ] Match-results endpoint calls T05 match_results_for_question and recommend_reuse_strategy
* [ ] POST /api/v1/research-sessions/{session_id}/resume endpoint implemented
* [ ] Resume endpoint determines next_step based on current_phase
* [ ] Resume endpoint allows optional mode switch (R9)
* [ ] All endpoints enforce authorization
* [ ] Unit tests pass for all three endpoints

## Manual verification

* Steps:
  * Create research session with collection_id=1, session_type="manual"
  * POST /api/v1/research-sessions/{session_id}/match-results with question_text, verify matched results returned
  * Verify recommended_strategy in response (e.g., "exact_reuse" or "new_generation")
  * POST /api/v1/research-sessions/{session_id}/context with relevant_item_ids=[1,2,3], verify context assembled
  * Verify token_count in response is within 35K limit
  * Update session current_phase to "research"
  * POST /api/v1/research-sessions/{session_id}/resume, verify next_step indicates section_generation
  * POST /api/v1/research-sessions/{session_id}/resume with mode="automated", verify session_type updated
* Expected results:
  * Context assembled correctly with token count
  * Result matching returns recommendations
  * Resume determines correct next step
  * Mode switch works

## Notes

* Requirements covered: R7 (match results with similarity > 0.85), R8 (user approval of reuse), R9 (resume sessions)
* Context endpoint supports both new generation (relevant_item_ids) and reuse (reuse_info in session state)
* Match-results endpoint used by manual wizard Step 2 (T21)
* Context endpoint used by manual wizard Step 3 (T21)
* Resume endpoint enables pausing and resuming sessions per R9
* Mode switch in resume endpoint enables cross-mode compatibility per spec "Cross-Mode Session Compatibility"
