# Ticket: work-summarization.T16 - Corpus Page Summarize Integration

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add "Summarize" button to Corpus work detail page
* Show progress during summarization
* Navigate to summary view on completion
* Handle already-summarized works

## Phase

* Frontend

## Scope

### In scope

* Add Summarize button to vulcanlab_ui/src/app/corpus/[id]/page.tsx
* Progress modal/indicator during summarization
* Status polling during summarization
* Success navigation to /summarize/[id]
* Error handling with toast notifications
* "View Summary" button if already summarized
* Re-summarize option with confirmation

### Out of scope

* Summarize list page (T14)
* Summary detail page (T15)
* Core summarization logic

## Dependencies

* Depends on: T11 (summarize API endpoints), T15 (summary detail page to navigate to)
* Unblocks: none (final frontend piece)

## Implementation plan

1. Update vulcanlab_ui/src/app/corpus/[id]/page.tsx
2. Add state for summarization:
   - isSummarizing: boolean
   - summarizationProgress: { total_nodes, completed_nodes } | null
   - hasSummary: boolean (check on load)
3. Check if work has summary on page load:
   - GET /api/v1/summarize/{work_id}/status
   - Set hasSummary based on response
4. Add button to StickyDetailHeader actions:
   - If hasSummary: "View Summary" button linking to /summarize/[id]
   - If !hasSummary: "Summarize" button
   - If hasSummary: also show "Re-summarize" as secondary action
5. Implement Summarize button handler:
   - POST /api/v1/summarize/{work_id}
   - Set isSummarizing = true
   - Start polling GET /api/v1/summarize/{work_id}/status every 2 seconds
   - Update summarizationProgress with poll results
   - On status = 'completed': navigate to /summarize/[id]
   - On status = 'failed': show error toast, stop polling
6. Create SummarizationProgressModal component:
   - Modal showing "Summarizing work..."
   - Progress bar: completed_nodes / total_nodes
   - "Processing node X of Y" text
   - Cancel button (optional - may not be supported)
7. Implement Re-summarize handler:
   - ConfirmDialog warning about data loss
   - POST /api/v1/summarize/{work_id}?force=true
   - Same progress flow as initial summarization
8. Handle edge cases:
   - Work with no chunks: show error "No content to summarize"
   - Summarization already in progress: disable button, show status
* Patterns to apply:
  * StickyDetailHeader for button placement
  * ConfirmDialog for destructive re-summarize
  * Toast notifications for success/error
  * Modal for progress display
  * Polling for async status updates
* Deviations (if any):
  * None - R15 says synchronous with progress streaming; polling simulates this

## Unit tests (required)

* Add tests for:
  * Page checks for existing summary on load
  * "View Summary" button shown when summary exists
  * "Summarize" button shown when no summary
  * Summarize button triggers POST to API
  * Progress modal displays during summarization
  * Progress updates as polling returns new status
  * Navigation to /summarize/[id] on completion
  * Error toast shown on failure
  * Re-summarize shows confirmation dialog
  * Re-summarize calls API with force=true
  * Button disabled during summarization
* Suggested locations:
  * vulcanlab_ui/src/app/corpus/[id]/__tests__/page.test.tsx (update existing)
* Mocking/fakes needed:
  * Mock fetch for API calls
  * Mock useRouter for navigation
  * Mock timers for polling

## Acceptance criteria (checklist)

* [ ] Summarize button appears on Corpus work detail page
* [ ] Button triggers summarization API call
* [ ] Progress modal shows during summarization
* [ ] Progress updates via polling
* [ ] Success navigates to summary detail page
* [ ] Error shows toast notification
* [ ] "View Summary" shown for already-summarized works
* [ ] Re-summarize with confirmation available
* [ ] Button disabled during active summarization
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Navigate to Corpus, click on a work
  2. Verify "Summarize" button in header
  3. Click Summarize
  4. Observe progress modal with updating progress
  5. On completion, verify navigation to /summarize/[id]
  6. Navigate back to Corpus work detail
  7. Verify "View Summary" button now shown
  8. Click Re-summarize, confirm, verify regeneration
* Expected results:
  * Full flow works end-to-end
  * Progress visible during operation
  * Appropriate buttons shown based on state

## Notes

* Requirements covered: R12, R15, R17
* Polling interval of 2 seconds balances responsiveness and API load
* Consider WebSocket or SSE for real-time progress in future (beyond R15 scope)
* Progress modal should not be dismissable during summarization (or warn if dismissed)
* "No content to summarize" case: works without heading-level chunks
* Button should be visually prominent - consider primary variant
