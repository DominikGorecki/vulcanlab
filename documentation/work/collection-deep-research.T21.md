# Ticket: collection-deep-research.T21 - Session Resume and State Persistence UI

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement UI to display in-progress sessions and enable resume functionality
* Allow users to pause manual wizard and resume later
* Restore wizard state from database on resume

## Phase

* Frontend

## Scope

### In scope

* Display in-progress sessions on collection page (status='in_progress')
* "Resume" button for each in-progress session
* Session state restoration: load research_plan, sections, context data from database
* Resume wizard at correct step based on current_phase
* Integration with API endpoints: GET /api/v1/collections/{collection_id}/research-sessions, POST /api/v1/research-sessions/{session_id}/resume

### Out of scope

* Manual wizard Steps 1-6 (covered in T18-T20)
* Report viewing (covered in T23)
* Automated research (covered in T22)

## Dependencies

* Depends on: T10 (resume endpoint), T18-T20 (wizard steps)
* Unblocks: none (enhancement to existing wizard)

## Implementation plan

* Update collection page (vulcanlab_ui/src/app/collection/[id]/page.tsx):
  * Fetch in-progress sessions on page load:
    * Call GET /api/v1/collections/{collectionId}/research-sessions
    * Filter sessions with status='in_progress'
  * Display in-progress sessions section (above "Deep Research" button):
    * Card for each in-progress session:
      * Session type (Manual or Automated)
      * Current phase (e.g., "Planning", "Research: 2/5 sections")
      * Created date
      * "Resume" button
  * "Resume" button onClick:
    * Call POST /api/v1/research-sessions/{sessionId}/resume
    * Get response: {current_phase, next_step}
    * Open DeepResearchModal with ManualResearchWizard
    * Pass sessionId to wizard for state restoration
* Update ManualResearchWizard component:
  * Accept optional sessionId prop (for resume)
  * If sessionId provided (resume mode):
    * Fetch session data: GET /api/v1/research-sessions/{sessionId}
    * Load state from response:
      * researchPlan from session.research_plan
      * Determine currentStep from session.current_phase:
        * 'planning' → Step 1
        * 'research' → Step 2 (result matching)
        * 'context_assembly' → Step 3
        * 'synthesis' → Step 5
        * 'evaluation' → Step 6
    * Fetch saved sections: GET /api/v1/research-sessions/{sessionId}/sections
    * Populate sections state
    * Set currentStep to resume at correct step
  * Else (new session):
    * Create new session via POST /api/v1/research-sessions
    * Initialize fresh state
* Add auto-save functionality to wizard:
  * After each step completion, session state already saved to database via API calls
  * Update current_phase in session after each step:
    * Step 1 complete → PUT session with current_phase='research'
    * Step 2 complete → PUT session with current_phase='context_assembly'
    * Step 3-4 complete → PUT session with current_phase='synthesis'
    * Step 5 complete → PUT session with current_phase='evaluation' (or 'completed' if skipping Step 6)
* Patterns to apply:
  * **usePageData hook** - Use for fetching sessions list per patterns.md section 4.2
  * **useCallback for fetch** - Wrap fetch functions per patterns.md section 4.1
  * **Theme awareness** - Use semantic Tailwind classes per patterns.md section 4.2
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Collection page fetches and displays in-progress sessions
  * "Resume" button calls resume endpoint
  * ManualResearchWizard loads state from sessionId when provided
  * Wizard determines correct currentStep from session.current_phase
  * Wizard populates researchPlan and sections from database
  * Wizard resumes at correct step (Step 1, 2, 3, 5, or 6)
  * Auto-save updates current_phase after each step
  * Resume works for sessions paused at different phases
* Suggested locations:
  * tests/unit/app/collection/test_session_resume.test.tsx
  * tests/unit/components/research/test_ManualResearchWizard_Resume.test.tsx
* Mocking/fakes needed:
  * Mock API calls (GET sessions, POST resume, GET session, GET sections)
  * Mock session data with various current_phase values

## Acceptance criteria (checklist)

* [ ] Collection page displays in-progress sessions (R9)
* [ ] In-progress session cards show session type, phase, created date
* [ ] "Resume" button calls resume endpoint (R9)
* [ ] ManualResearchWizard accepts sessionId prop for resume
* [ ] Wizard loads research_plan and sections from database on resume
* [ ] Wizard determines correct step from current_phase
* [ ] Wizard resumes at correct step without losing state (R9)
* [ ] Auto-save updates current_phase after each step completion
* [ ] Session can be resumed from any step (Steps 1-6)
* [ ] Unit tests pass for resume functionality

## Manual verification

* Steps:
  * Start manual research wizard, complete Step 1 (save plan)
  * Close wizard without completing (simulating pause)
  * Refresh collection page
  * Verify in-progress session displayed with phase "Research"
  * Click "Resume" button
  * Verify wizard opens at Step 2 (Result Matching)
  * Verify research_plan loaded (sub-questions displayed)
  * Complete Step 2, close wizard again
  * Resume session again
  * Verify wizard opens at Step 3 (Context Assembly)
  * Complete Steps 3-4 (save sections)
  * Close wizard
  * Resume session
  * Verify wizard opens at Step 5 (Synthesis)
  * Verify all saved sections available for synthesis
  * Complete workflow
* Expected results:
  * Sessions can be paused and resumed at any step
  * State persisted and restored correctly
  * No data loss on resume

## Notes

* Requirements covered: R9 (resume incomplete sessions), session state persistence per R6
* Auto-save after each step ensures no data loss if user closes browser
* current_phase column enables determining resume point without parsing full state_data
* Resume functionality critical for manual workflow - research may take hours or days
* In-progress sessions displayed prominently so users remember to complete them
