# Ticket: work-summarization.T12 - UI: Corpus Page Summarize Action

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add "Summarize" action button to corpus page work rows
* Navigate to summarization workflow page when clicked
* Optionally add summarize button to work detail page

## Phase

* Frontend

## Scope

### In scope

* Modify `vulcanlab_ui/src/app/corpus/page.tsx` to add Summarize action
* Add navigation to `/summaries/workflow/{work_id}`
* Add visual indicator if work already has summaries

### Out of scope

* Summarization workflow page (T13)
* Summaries list page (T14)
* Summary viewer page (T15)
* Settings tab (T16)

## Dependencies

* Depends on: T10 (API exists for checking summary status)
* Unblocks: T13

## Implementation plan

1. Update `vulcanlab_ui/src/app/corpus/page.tsx`:
2. Add imports for summarization icon (e.g., `FileText` or `ListTree` from lucide-react)
3. Extend `CorpusWork` interface:
   - Add `has_summary: boolean` field (requires API update or separate fetch)
4. Add Summarize button to DataTable row actions:
   - Place next to existing delete button
   - Use appropriate icon
   - onClick navigates to `/summaries/workflow/${work.id}`
5. Optionally add visual badge if work has existing summary:
   - Small indicator in row (e.g., checkmark or "Summarized" badge)
6. Update corpus API to include summary status:
   - Option A: Extend `/corpus/works` response to include `has_summary`
   - Option B: Separate fetch to check summary status per work
   - Recommend Option A for efficiency
7. Add tooltip on Summarize button: "Generate summary for this work"
8. Handle edge cases:
   - Button disabled/hidden if work has no chunks
   - Visual feedback during navigation

* Patterns to apply:
  * **Component Composition** - Use existing button patterns
  * **useCallback** - Wrap navigation handler if needed
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Summarize button renders in each row
  * Click on Summarize button triggers navigation
  * Button navigates to correct URL with work ID
  * Summary indicator shows when `has_summary` is true
  * Summary indicator hidden when `has_summary` is false
* Suggested locations:
  * `vulcanlab_ui/src/app/corpus/__tests__/page.test.tsx` (extend existing)
* Mocking/fakes needed:
  * Mock `useRouter` for navigation testing
  * Mock fetch responses with `has_summary` field

## Acceptance criteria (checklist)

* [ ] Summarize button appears on each corpus work row
* [ ] Clicking Summarize navigates to `/summaries/workflow/{work_id}`
* [ ] Works with existing summaries show visual indicator
* [ ] Button has appropriate icon and tooltip
* [ ] Navigation works correctly
* [ ] Unit tests pass

## Manual verification

* Steps:
  * Navigate to Corpus page
  * Locate a work row
  * Click the Summarize button
  * Verify navigation to `/summaries/workflow/{work_id}`
  * If work already has summaries, verify indicator is visible
* Expected results:
  * Button visible and clickable
  * Correct page loads after click
  * Summary status accurately reflected

## Notes

* Requirements covered: R11 (UI button on corpus page)
* The `/summaries/workflow/{work_id}` page doesn't exist yet (T13)
* Consider adding summarize action to work detail page (`/corpus/[id]`) as well
* API change to include `has_summary` in corpus/works response may be a small API-side addition
