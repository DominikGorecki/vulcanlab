# Ticket: manual-summarization-flow.T05 - Session Resume and Page Integration

## Source

* Spec: documentation/work/manual-summarization-flow.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add session resume detection to Corpus detail page and Summarize list page
* Show "Resume Manual Summarization" button when in-progress session exists
* Handle re-summarization flow: delete existing session/nodes before starting fresh
* Ensure wizard page handles resume correctly (loads at current node)

## Scope

### In scope

* Update Corpus detail page to check for existing manual sessions on load
* Update Summarize list page to show resume indicator for works with in-progress sessions
* Add "Resume" button that navigates to wizard at current node
* Handle re-summarization: confirmation dialog, delete session, start fresh
* Update mode dialog to handle existing session case

### Out of scope

* Manual derived outputs (T06)
* Logging/observability (T07)

## Dependencies

* Depends on: T03 (session API), T04 (wizard page)
* Unblocks: T06, T07

## Implementation plan

1. Update `vulcanlab_ui/src/app/corpus/[id]/page.tsx`:
   - Add useEffect to check GET /api/v1/summarize/{work_id}/session on mount
   - Store session state: { exists: boolean, mode: string, status: string, progress: number }
   - If in_progress manual session exists:
     - Show "Resume Manual Summarization" button instead of "Summarize"
     - Clicking resumes wizard at current node
   - If completed session exists (automatic or manual):
     - Keep existing "View Summary" and "Re-summarize" buttons
   - Mode dialog: if session exists, show warning and confirm before creating new

2. Update `vulcanlab_ui/src/app/summarize/page.tsx`:
   - Add session status to API response for works list
   - Display indicator (badge or icon) for works with in_progress manual sessions
   - "Resume" action in table row for in_progress sessions

3. Update SummarizeModeDialog to handle existing sessions:
   ```tsx
   interface SummarizeModeDialogProps {
     // ... existing props
     existingSession?: { mode: string; status: string; progress: number };
   }
   ```
   - If existingSession with status='in_progress', show warning
   - "This will cancel the existing session. Continue?"
   - On confirm: DELETE /session, then proceed with new session

4. Update re-summarization flow:
   - DELETE /api/v1/summarize/{work_id}/session (cancel any active session)
   - DELETE /api/v1/summarize/{work_id} (delete existing nodes per existing flow)
   - Then proceed with mode selection

5. Ensure wizard page handles resume:
   - On load, fetch session state
   - If session exists, display current node (already works from T04)
   - If no session, redirect back to corpus page

* Patterns to apply:
  * **UI Page Lifecycle**: Check session status on mount with useEffect
  * **User Input**: ConfirmDialog for destructive actions
  * **Error handling**: Handle 404 from GET /session gracefully (no session exists)

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Corpus page shows "Resume" button when in_progress manual session exists
  * Corpus page shows "Summarize" button when no session exists
  * Corpus page shows "View Summary" when completed session exists
  * SummarizeModeDialog shows warning when existingSession provided
  * SummarizeModeDialog calls delete before creating new session
  * Summarize list page displays resume indicator for in_progress sessions
  * Wizard page redirects to corpus if no session exists

* Suggested locations:
  * `vulcanlab_ui/src/app/corpus/[id]/__tests__/page.test.tsx` (extend existing)
  * `vulcanlab_ui/src/app/summarize/__tests__/page.test.tsx` (extend existing)
  * `vulcanlab_ui/src/components/summarize/__tests__/summarize-mode-dialog.test.tsx` (extend)

* Mocking/fakes needed:
  * Mock GET /session to return various states (no session, in_progress, completed)
  * Mock DELETE /session
  * Mock useRouter for navigation assertions

## Acceptance criteria (checklist)

* [ ] Corpus page detects existing in_progress manual session
* [ ] "Resume Manual Summarization" button appears for in_progress sessions
* [ ] Clicking Resume navigates to wizard at current node
* [ ] Summarize list page shows indicator for works with in_progress sessions
* [ ] Mode dialog warns before canceling existing session
* [ ] Re-summarize properly deletes session before starting fresh
* [ ] Wizard page redirects if accessed with no active session
* [ ] Unit tests pass

## Manual verification

* Steps:
  * Start manual summarization on a work
  * Complete 2 of 5 nodes
  * Navigate away to Corpus list
  * Return to work detail page
  * Verify "Resume Manual Summarization" button appears
  * Click Resume, verify wizard shows "Node 3 of 5"
  * Navigate to /summarize list page
  * Verify work shows resume indicator
  * Click Re-summarize, verify confirmation dialog
  * Confirm, verify new session starts at node 1

* Expected results:
  * Session state persists across navigation
  * Resume continues from last completed node
  * Re-summarization properly resets everything
  * No orphaned sessions or corrupted state

## Notes

* Requirements covered: R10, R11, R15
* GET /session should return 404 if no session exists (not an error, just no session)
* Consider caching session check result to avoid repeated API calls
* The "in_progress" status includes both manual sessions being worked and automatic sessions that were interrupted
