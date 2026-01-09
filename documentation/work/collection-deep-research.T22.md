# Ticket: collection-deep-research.T22 - Automated Research Trigger and Progress Tracking

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement UI to trigger automated research workflow
* Display progress tracking for automated sessions (current phase, sections completed)
* Show notifications when automated research completes

## Phase

* Frontend

## Scope

### In scope

* Automated research trigger from DeepResearchModal when "Start Automated" selected
* API call to POST /api/v1/research-sessions/start-automated
* Progress display component for automated sessions (current phase, section count)
* Polling or WebSocket for progress updates (polling for MVP)
* Completion notification

### Out of scope

* Manual wizard (covered in T18-T21)
* Report viewing (covered in T23)
* WebSocket real-time updates (deferred, use polling for MVP)

## Dependencies

* Depends on: T16 (automated research endpoint), T17 (modal)
* Unblocks: T23 (report viewing)

## Implementation plan

* Update DeepResearchModal component (from T17):
  * When selectedMode == 'automated':
    * Call POST /api/v1/research-sessions/start-automated with {collection_id}
    * Get response: {session_id, thread_id, status, message}
    * Close modal
    * Show toast notification: "Automated research started in background"
    * Start progress tracking for session_id
* Create AutomatedResearchProgress component:
  * Props: {sessionId: number, onComplete: () => void}
  * State: const [progress, setProgress] = useState<SessionProgress | null>(null)
  * Fetch session status on mount and poll every 5 seconds:
    * Call GET /api/v1/research-sessions/{sessionId}
    * Extract current_phase, status
    * Parse state_data to get sections completed count
    * Update progress state
  * Display progress card:
    * Session type: "Automated Research"
    * Current phase with icon (Planning ✓, Research 2/5, Synthesis ⏳)
    * Progress bar (visual indicator of completion)
    * Estimated sections: X of Y complete
  * When status == 'completed':
    * Stop polling
    * Show toast notification: "Deep research completed! View report."
    * Call onComplete callback
  * When status == 'failed':
    * Stop polling
    * Show error notification: "Research failed. Please try again."
    * Display error message from state_data
  * "Cancel" button (optional):
    * onClick: update session status to 'paused' (allows manual intervention)
* Update collection page to display automated progress:
  * Fetch in-progress automated sessions
  * Render AutomatedResearchProgress component for each automated session
  * Position below in-progress manual sessions
* Add polling utility in vulcanlab_ui/src/lib/polling.ts:
  * export function usePollSessionStatus(sessionId: number, interval: number = 5000)
  * Returns {status, current_phase, sections_completed, total_sections, error}
  * Uses useEffect with setInterval for polling
  * Cleanup interval on unmount
* Patterns to apply:
  * **usePageData or custom hook** - Use for session status polling per patterns.md section 4.2
  * **useCallback for fetch** - Wrap polling fetch in useCallback per patterns.md section 4.1
  * **Theme awareness** - Use semantic Tailwind classes per patterns.md section 4.2
  * **Component composition** - Build progress card from primitives per patterns.md section 4.2
* Deviations (if any):
  * Polling instead of WebSocket (simpler for MVP, can upgrade later)

## Unit tests (required)

* Add tests for:
  * DeepResearchModal calls start-automated endpoint when "Start Automated" selected
  * DeepResearchModal closes after starting automated research
  * Toast notification shown after starting
  * AutomatedResearchProgress fetches session status on mount
  * AutomatedResearchProgress polls every 5 seconds
  * AutomatedResearchProgress displays current phase correctly
  * AutomatedResearchProgress calculates sections completed from state_data
  * AutomatedResearchProgress shows completion notification when status='completed'
  * AutomatedResearchProgress shows error notification when status='failed'
  * AutomatedResearchProgress stops polling when status is terminal (completed or failed)
  * Polling cleanup on component unmount
* Suggested locations:
  * tests/unit/components/research/test_AutomatedResearchProgress.test.tsx
  * tests/unit/lib/test_polling.test.ts
* Mocking/fakes needed:
  * Mock API calls (POST start-automated, GET session status)
  * Mock setInterval for polling
  * Mock toast notifications

## Acceptance criteria (checklist)

* [ ] DeepResearchModal triggers automated research when "Start Automated" selected (R2, R5)
* [ ] Start-automated endpoint called with collection_id
* [ ] Modal closes and toast notification shown
* [ ] AutomatedResearchProgress component displays progress (current_phase, sections count)
* [ ] Progress updates via polling every 5 seconds
* [ ] Progress card shows visual progress bar
* [ ] Completion notification shown when status='completed'
* [ ] Error notification shown when status='failed'
* [ ] Polling stops on completion or failure
* [ ] Collection page displays automated progress for in-progress sessions
* [ ] Unit tests pass for automated trigger and progress tracking

## Manual verification

* Steps:
  * Open collection page with 5+ items
  * Click "Deep Research" button
  * Select "Automated Research"
  * Verify API called, modal closes, toast notification shown
  * Verify collection page displays automated progress card
  * Verify progress card shows "Planning" phase initially
  * Wait 5-10 seconds (mock workflow progressing quickly for testing)
  * Verify progress updates: "Planning ✓" → "Research 1/5" → "Research 2/5" → etc.
  * Verify progress bar updates
  * When workflow completes:
    * Verify progress card shows "Completed"
    * Verify toast notification: "Deep research completed!"
  * Test error case:
    * Mock workflow to fail after planning
    * Verify progress card shows error
    * Verify error notification shown
* Expected results:
  * Automated research starts correctly
  * Progress tracking works via polling
  * Notifications shown appropriately
  * UI updates reflect workflow state

## Notes

* Requirements covered: R2 (automated research option), R5 (LangGraph workflow), progress tracking per spec UX section
* Polling interval 5 seconds balances responsiveness and server load
* Progress display shows "Planning: Complete, Research: 2/5 sections" per spec UX example
* Completion notification per spec UX section: "Deep research completed! View report."
* Error handling critical: automated workflow failures should not leave user in unknown state
* Polling cleanup prevents memory leaks on component unmount
