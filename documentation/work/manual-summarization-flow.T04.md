# Ticket: manual-summarization-flow.T04 - Mode Selection Dialog and Manual Wizard UI

## Source

* Spec: documentation/work/manual-summarization-flow.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create SummarizeModeDialog component for manual/automatic mode selection
* Create ManualSummarizationWizard page for step-by-step node processing
* Update Corpus detail page to use mode dialog instead of direct summarization trigger
* Enable the first complete user-facing manual summarization flow

## Scope

### In scope

* `components/summarize/summarize-mode-dialog.tsx` - modal with mode selection
* `app/summarize/manual/[work_id]/page.tsx` - wizard page
* Update `app/corpus/[id]/page.tsx` to show mode dialog on Summarize click
* Copy-to-clipboard functionality with success feedback
* Progress indicator (node X of Y)
* Response textarea with submit button

### Out of scope

* Resume detection on other pages (T05)
* Manual derived outputs (T06)
* Error logging/observability (T07)

## Dependencies

* Depends on: T03 (API endpoints)
* Unblocks: T05, T06

## Implementation plan

1. Create `vulcanlab_ui/src/components/summarize/summarize-mode-dialog.tsx`:
   ```tsx
   interface SummarizeModeDialogProps {
     open: boolean;
     onOpenChange: (open: boolean) => void;
     workId: string;
     onAutomatic: () => void;  // Triggers existing flow
   }
   ```
   - Modal with two cards: "Manual" and "Automatic"
   - Brief description of each mode
   - "Start" button that either triggers automatic flow or redirects to wizard
   - Use existing Dialog component from ui/

2. Create `vulcanlab_ui/src/app/summarize/manual/[work_id]/page.tsx`:
   - Use usePageData hook with useCallback-wrapped fetch (per patterns.md)
   - Fetch session state and current prompt on load
   - Display components:
     - StickyDetailHeader with title "Manual Summarization" and back button
     - Progress card: "Node {current} of {total}" with progress bar
     - Current node info card: heading path, evidence preview (truncated)
     - Prompt card with ScrollArea and "Copy Prompt" button
     - Response textarea with FormField wrapper
     - Submit button with loading state
   - On submit: POST to /session/submit, refetch on success
   - On completion: redirect to /summarize/{work_id}

3. Add copy-to-clipboard utility (or reuse from lib/clipboard.ts):
   - Success toast feedback
   - Error handling for clipboard API failures

4. Update `vulcanlab_ui/src/app/corpus/[id]/page.tsx`:
   - Replace direct handleSummarize call with dialog open
   - Add SummarizeModeDialog to page
   - Wire onAutomatic to existing handleSummarize function
   - Keep existing re-summarize and view summary buttons

5. Add loading and error states:
   - PageLoadingState while fetching prompt
   - PageErrorState for API failures
   - Inline error display for submission failures (don't navigate away)

* Patterns to apply:
  * **UI Page Lifecycle**: usePageData hook with useCallback-wrapped fetch
  * **Component Composition**: Props-in, events-out pattern
  * **Forms**: react-hook-form with FormField wrapper
  * **Theme Awareness**: Use Tailwind semantic classes

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * SummarizeModeDialog renders with both mode options
  * SummarizeModeDialog calls onAutomatic when Automatic selected
  * SummarizeModeDialog redirects to wizard when Manual selected
  * ManualSummarizationWizard displays progress correctly
  * ManualSummarizationWizard copy button calls clipboard API
  * ManualSummarizationWizard submit button disabled when textarea empty
  * ManualSummarizationWizard shows error state on API failure
  * ManualSummarizationWizard redirects on session completion

* Suggested locations:
  * `vulcanlab_ui/src/components/summarize/__tests__/summarize-mode-dialog.test.tsx`
  * `vulcanlab_ui/src/app/summarize/manual/[work_id]/__tests__/page.test.tsx`

* Mocking/fakes needed:
  * Mock fetch API for session and prompt endpoints
  * Mock navigator.clipboard.writeText
  * Mock useRouter for navigation assertions
  * Mock useToast for toast assertions

## Acceptance criteria (checklist)

* [ ] Clicking "Summarize" on Corpus page opens mode selection dialog
* [ ] Selecting "Automatic" triggers existing automated flow unchanged
* [ ] Selecting "Manual" redirects to /summarize/manual/{work_id}
* [ ] Wizard shows progress indicator with current/total nodes
* [ ] Wizard displays heading path and evidence preview for current node
* [ ] Copy Prompt button copies to clipboard with success feedback
* [ ] Paste response and submit advances to next node
* [ ] Completion redirects to summary detail page
* [ ] Error states display without crashing
* [ ] Unit tests pass for dialog and wizard

## Manual verification

* Steps:
  * Navigate to Corpus, click on a work
  * Click "Summarize" button
  * Verify mode selection dialog appears with Manual/Automatic options
  * Select "Manual", verify redirect to wizard page
  * Verify progress shows "Node 1 of N"
  * Click "Copy Prompt", verify clipboard contains prompt
  * Paste prompt into external LLM, get response
  * Paste response into textarea, click Submit
  * Verify progress advances to "Node 2 of N"
  * Complete all nodes, verify redirect to summary detail page

* Expected results:
  * Full manual flow completes successfully
  * UI is responsive and shows appropriate loading states
  * Copy functionality works across browsers
  * Invalid JSON shows inline error, doesn't crash

## Notes

* Requirements covered: R1, R2, R3, R4, R5, R7, R12
* Reuse patterns from simple-conversion manual page and ManualResearchWizard
* Evidence preview should be truncated to ~500 chars with "..." suffix
* Consider adding keyboard shortcut for copy (Ctrl/Cmd+C when prompt focused)
* The wizard page should handle browser refresh (refetches session state)
