# Ticket: manual-summarization-flow.T07 - Hardening, Logging, and Edge Cases

## Source

* Spec: documentation/work/manual-summarization-flow.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add comprehensive logging for manual summarization session lifecycle
* Improve error handling and user-facing error messages
* Handle edge cases: stale sessions, concurrent access, malformed responses
* Add session cleanup for abandoned sessions

## Scope

### In scope

* Logging for session creation, advancement, completion, and deletion
* Logging for failed response parsing with context
* Improved error messages for common failure modes
* Handle concurrent session access gracefully
* Add session staleness detection (sessions older than 7 days)
* API endpoint to clean up stale sessions (admin/maintenance)

### Out of scope

* Automated background job for cleanup (future enhancement)
* Metrics/alerting integration (future enhancement)

## Dependencies

* Depends on: T03 (session manager), T04 (wizard), T05 (resume), T06 (derived)
* Unblocks: none (final ticket)

## Implementation plan

1. Add logging to `src/vulcanlab/summarize/session_manager.py`:
   ```python
   logger = logging.getLogger(__name__)

   def create_session(...):
       logger.info(f"Creating {mode.value} summarization session for work {work_id}")
       # ... create session ...
       logger.info(f"Session created: {session.id}, {session.total_nodes} nodes selected")

   def advance_session(...):
       logger.info(f"Advancing session {session.id}: node {session.current_node_index} -> {next_index}")

   def complete_session(...):
       logger.info(f"Session {session.id} completed for work {session.work_id}")
   ```

2. Add logging to `src/vulcanlab/summarize/response_parser.py`:
   ```python
   def parse_node_response(response_text: str) -> SummaryResponse:
       try:
           # ... parse ...
       except json.JSONDecodeError as e:
           logger.warning(f"JSON parse error: {e}. Response preview: {response_text[:200]}")
           raise ValueError(f"Invalid JSON: {e.msg} at position {e.pos}")
       except KeyError as e:
           logger.warning(f"Missing required field: {e}. Response preview: {response_text[:200]}")
           raise ValueError(f"Missing required field: {e}")
   ```

3. Improve error messages in API endpoints:
   - 400 for invalid JSON: include position and preview of error
   - 400 for missing fields: list which fields are missing
   - 404 for no session: "No active summarization session for this work"
   - 409 for concurrent access: "Session is being modified by another request"

4. Add concurrency handling:
   - Use SELECT ... FOR UPDATE when advancing session
   - Return 409 Conflict if session was modified since last fetch
   - Add `version` column or use `updated_at` for optimistic locking

5. Add stale session detection:
   ```python
   def get_stale_sessions(db_session: Session, days: int = 7) -> List[SummarizationSession]:
       """Get sessions older than specified days that are still in_progress."""
       cutoff = datetime.utcnow() - timedelta(days=days)
       return db_session.query(SummarizationSession).filter(
           SummarizationSession.status == 'in_progress',
           SummarizationSession.updated_at < cutoff
       ).all()

   def cleanup_stale_sessions(db_session: Session, days: int = 7) -> int:
       """Delete stale sessions. Returns count deleted."""
   ```

6. Add cleanup endpoint (optional, admin-only):
   ```python
   @router.delete("/sessions/stale")
   async def cleanup_stale_sessions(days: int = 7, db: Session = Depends(get_db_session)):
       count = session_manager.cleanup_stale_sessions(db, days)
       return {"deleted": count}
   ```

7. Update frontend error handling:
   - ManualSummarizationWizard: show specific error messages from API
   - Add retry button for transient errors
   - Add "Start Over" option when session is corrupted

* Patterns to apply:
  * **Observability**: Log session lifecycle events with work_id and session_id
  * **Error handling**: Specific exceptions with clear messages
  * **API error responses**: Include actionable information

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Logging is called on session create/advance/complete/delete
  * parse_node_response logs warning on parse failure
  * Error messages include helpful context (field names, position)
  * get_stale_sessions returns sessions older than threshold
  * cleanup_stale_sessions deletes correct sessions
  * Concurrent session modification returns 409
  * Optimistic locking prevents race conditions

* Suggested locations:
  * `tests/unit/summarize/test_session_manager.py` (extend)
  * `tests/unit/summarize/test_response_parser.py` (extend)
  * `tests/unit/summarize/test_logging.py` (new, verify log calls)

* Mocking/fakes needed:
  * Mock logger to verify log calls
  * Mock database session with concurrent access simulation
  * Mock datetime for stale session tests

## Acceptance criteria (checklist)

* [ ] Session lifecycle events are logged with work_id and session_id
* [ ] Failed parse attempts are logged with response preview
* [ ] API error responses include actionable information
* [ ] Stale sessions (>7 days) can be identified
* [ ] Cleanup endpoint deletes stale sessions
* [ ] Concurrent modification returns 409 Conflict
* [ ] Frontend displays helpful error messages
* [ ] Unit tests pass

## Manual verification

* Steps:
  * Start manual summarization, check logs for session creation
  * Submit invalid JSON, verify error message includes position
  * Advance through nodes, check logs for each advancement
  * Complete session, check logs for completion
  * Create session, wait (or manually set updated_at to old date)
  * Call cleanup endpoint, verify stale session deleted
  * Open wizard in two browser tabs, submit in both, verify 409 on second

* Expected results:
  * Logs contain sufficient context for debugging
  * Error messages help users fix their input
  * Stale sessions are cleaned up
  * Concurrent access is handled gracefully

## Notes

* Requirements covered: Non-functional requirements for observability and reliability
* Log levels: INFO for normal lifecycle, WARNING for parse failures, ERROR for unexpected exceptions
* Consider adding request_id to log context for tracing
* The cleanup endpoint could be protected with admin auth in production
* Stale session threshold (7 days) could be configurable via settings
