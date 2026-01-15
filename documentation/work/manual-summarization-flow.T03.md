# Ticket: manual-summarization-flow.T03 - Session Manager, Response Parser, and Core APIs

## Source

* Spec: documentation/work/manual-summarization-flow.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement session manager module for session lifecycle (create, get, advance, complete, delete)
* Implement response parser module for parsing manual LLM responses
* Add API endpoints for session management and manual response submission
* Enable the first manually verifiable end-to-end path for manual summarization

## Scope

### In scope

* `src/vulcanlab/summarize/session_manager.py` with full session lifecycle
* `src/vulcanlab/summarize/response_parser.py` for JSON parsing with clear errors
* API endpoints: POST/GET/DELETE session, GET current-prompt, POST submit
* Pydantic schemas for request/response models
* Update orchestrator to support manual mode submissions

### Out of scope

* Frontend UI (T04)
* Resume detection in existing pages (T05)
* Derived output manual mode (T06)

## Dependencies

* Depends on: T01 (database model), T02 (prompt formatter)
* Unblocks: T04, T05, T06

## Implementation plan

1. Create `src/vulcanlab/summarize/session_manager.py`:
   ```python
   def create_session(work_id: int, mode: SummarizationMode, db_session: Session) -> SummarizationSession:
       """Create new summarization session, selecting nodes via node_selector."""

   def get_session(work_id: int, db_session: Session) -> Optional[SummarizationSession]:
       """Get current session for a work, or None if no active session."""

   def get_current_node_info(session: SummarizationSession, db_session: Session) -> Optional[dict]:
       """Get info about current node: chunk_id, heading_path, evidence_preview."""

   def advance_session(session: SummarizationSession, db_session: Session) -> Optional[int]:
       """Advance to next node, return next index or None if complete."""

   def complete_session(session: SummarizationSession, db_session: Session) -> None:
       """Mark session as completed."""

   def delete_session(work_id: int, db_session: Session) -> bool:
       """Delete session for a work. Returns True if deleted."""
   ```

2. Create `src/vulcanlab/summarize/response_parser.py`:
   ```python
   def parse_node_response(response_text: str) -> SummaryResponse:
       """Parse manual LLM response into SummaryResponse structure.

       Raises ValueError with clear message if parsing fails.
       """

   def extract_json_from_response(response_text: str) -> dict:
       """Extract JSON from response, handling markdown code blocks."""
   ```

3. Add Pydantic schemas to `src/vulcanlab_api/schemas/summarize.py`:
   - CreateSessionRequest: mode field
   - SessionResponse: session_id, mode, status, current_node_index, total_nodes, completed_nodes
   - CurrentPromptResponse: node_index, heading_path, evidence_preview, prompt, chunk_id
   - SubmitResponseRequest: response field
   - SubmitResponseResponse: success, next_node_index, completed, error

4. Add endpoints to `src/vulcanlab_api/routers/summarize.py`:
   - `POST /{work_id}/session` - create session
   - `GET /{work_id}/session` - get session state
   - `GET /{work_id}/session/current-prompt` - get current node prompt (uses prompt_formatter)
   - `POST /{work_id}/session/submit` - parse response, create summary_node, advance session
   - `DELETE /{work_id}/session` - delete session

5. Update orchestrator.py:
   - Add `process_manual_submission(work_id: int, response_text: str, db_session: Session)` function
   - This calls response_parser, creates summary_node, advances session

* Patterns to apply:
  * **Three-tier architecture**: Core logic in session_manager/response_parser, thin API layer
  * **Session management**: Database session passed explicitly
  * **API versioning**: All routes under /api/v1/summarize prefix
  * **Error handling**: Raise specific exceptions, let global handler catch

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * session_manager.create_session: creates session with correct initial state
  * session_manager.create_session: selects nodes using node_selector
  * session_manager.advance_session: increments current_node_index
  * session_manager.advance_session: returns None when all nodes complete
  * session_manager.delete_session: removes session from database
  * response_parser.parse_node_response: parses valid JSON into SummaryResponse
  * response_parser.parse_node_response: extracts JSON from markdown code blocks
  * response_parser.parse_node_response: raises ValueError with clear message for invalid JSON
  * response_parser.parse_node_response: raises ValueError for missing required fields

* Suggested locations:
  * `tests/unit/summarize/test_session_manager.py`
  * `tests/unit/summarize/test_response_parser.py`

* Mocking/fakes needed:
  * Mock database session
  * Mock node_selector.select_nodes_for_summarization
  * Mock prompt_formatter functions
  * Sample valid/invalid JSON responses

## Acceptance criteria (checklist)

* [ ] session_manager.py implements all lifecycle functions
* [ ] response_parser.py parses JSON with clear error messages
* [ ] All 5 API endpoints implemented and return correct schemas
* [ ] POST /session creates session and returns session_id
* [ ] GET /session/current-prompt returns formatted prompt
* [ ] POST /session/submit creates summary_node and advances session
* [ ] Invalid JSON submission returns 400 with helpful error message
* [ ] Unit tests pass for session_manager and response_parser

## Manual verification

* Steps:
  * Start API server
  * POST /api/v1/summarize/{work_id}/session with {"mode": "manual"}
  * GET /api/v1/summarize/{work_id}/session - verify session state
  * GET /api/v1/summarize/{work_id}/session/current-prompt - copy prompt
  * Use external LLM to get response
  * POST /api/v1/summarize/{work_id}/session/submit with response
  * Verify summary_node created in database
  * Repeat until session completes

* Expected results:
  * Session progresses through all nodes
  * Each submission creates a summary_node record
  * Session status changes to 'completed' after last node
  * Invalid JSON returns clear error without corrupting session

## Notes

* Requirements covered: R3, R4, R5, R7, R8, R9, R10, R11, R16
* The response_parser should reuse parsing logic from llm_summarize.py where possible
* Evidence preview in current-prompt response should be truncated (first 500 chars)
* Consider adding a utility function extractJson similar to UI's extractJson for handling markdown-wrapped JSON
