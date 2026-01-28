# Ticket: expand-answer.T05 - UI: Expansion Detail Page

## Source

* Spec: documentation/work/expand-answer.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create expansion detail page showing sections, status, and combined report
* Implement section status badges and retry functionality
* Enable manual mode with prompt display and response input
* Display combined report with markdown rendering

## Scope

### In scope

* Expansion detail page at `/expansions/{id}`
* Header with expansion metadata (mode, status, original answer link)
* Sections list with status badges and progress indicators
* Section expand/collapse to show details (prompt, RAG data, response)
* Retry button for failed sections
* Manual mode: prompt display area, response textarea, save button
* Combined report display with markdown rendering
* Status polling during automatic processing
* "Run All" button to trigger automatic mode from detail page

### Out of scope

* Expansions list page (T04)
* API endpoints (T03)

## Dependencies

* Depends on: T01 (models), T03 (API endpoints), T04 (navigation and list)
* Unblocks: T06

## Implementation plan

1. Create expansion detail page:
   - `vulcanlab_ui/src/app/expansions/[id]/page.tsx`
   - Use `usePageData` with memoized fetch from `GET /api/v1/expansions/{id}`
   - Use `StickyDetailHeader` with expansion title and status badge
   - Show original answer link (to `/rag/{query_id}/results/{result_id}`)
2. Create sections list component:
   - `vulcanlab_ui/src/components/expansion/sections-list.tsx`
   - Display each section with: order number, heading, summary, status badge
   - Expandable/collapsible section details
   - Color-coded status badges per section status
3. Create section detail component:
   - `vulcanlab_ui/src/components/expansion/section-detail.tsx`
   - Show expansion_prompt (copyable)
   - Show RAG data when available (expanded_queries, hyde_answer, intent, entities)
   - Show retrieved context summary
   - Show augmented_prompt (for debugging/verification)
   - Show response_text when completed
4. Implement retry functionality:
   - "Retry" button on failed sections
   - Calls `POST /api/v1/expansions/{id}/sections/{section_id}/expand` then `/generate`
   - Updates UI on completion
5. Implement manual mode interface:
   - When section status is `ready` and mode is `manual`:
     - Show augmented_prompt in copyable text area
     - Show response textarea for user input
     - "Save Response" button calls `POST .../sections/{id}/manual`
   - When all sections completed, show "Combine" button
6. Implement combined report display:
   - `vulcanlab_ui/src/components/expansion/combined-report.tsx`
   - Render markdown using existing markdown renderer
   - Show link to original answer at top
   - Only visible when expansion status is `completed`
7. Implement status polling:
   - When expansion status is in-progress (`sections_in_progress`, `combining`)
   - Poll `GET /api/v1/expansions/{id}` every 2-3 seconds
   - Stop polling when status becomes `completed` or `failed`
   - Use `useEffect` with cleanup to manage polling interval
8. Add "Run All" button:
   - Visible when status is `breakdown_complete` or some sections pending
   - Calls `POST /api/v1/expansions/{id}/run`
   - Triggers automatic processing of remaining sections

* Patterns to apply:
  * Page Lifecycle Pattern - usePageData with loading/error states
  * Standard Layout - StickyDetailHeader + content cards
  * Theme Awareness - Tailwind semantic classes
  * Infinite Render Prevention - useCallback for fetch functions

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `test_expansion_detail_renders_header` - shows status and original link
  * `test_sections_list_renders_all_sections` - displays all sections
  * `test_section_detail_shows_prompt` - expansion_prompt visible
  * `test_section_detail_shows_response` - response visible when completed
  * `test_retry_button_visible_on_failed` - retry only on failed sections
  * `test_retry_calls_api` - clicking retry triggers API call
  * `test_manual_mode_shows_textarea` - textarea visible in manual mode
  * `test_save_response_calls_api` - save button submits response
  * `test_combined_report_renders_markdown` - markdown rendered correctly
  * `test_polling_starts_when_in_progress` - polling active during processing
  * `test_polling_stops_on_completion` - polling stops when done

* Suggested locations:
  * `vulcanlab_ui/__tests__/app/expansions/[id]/page.test.tsx`
  * `vulcanlab_ui/__tests__/components/expansion/sections-list.test.tsx`
  * `vulcanlab_ui/__tests__/components/expansion/section-detail.test.tsx`
  * `vulcanlab_ui/__tests__/components/expansion/combined-report.test.tsx`

* Mocking/fakes needed:
  * Mock fetch responses for expansion detail
  * Mock timers for polling tests
  * Mock router for navigation

## Acceptance criteria (checklist)

* [ ] Expansion detail page loads at `/expansions/{id}`
* [ ] Header shows expansion status, mode, and link to original answer
* [ ] All sections displayed with heading, summary, and status badge
* [ ] Sections expandable to show full details (prompt, RAG data, response)
* [ ] Failed sections show "Retry" button that reprocesses the section
* [ ] Manual mode shows prompt to copy and textarea to paste response
* [ ] "Save Response" button saves manual response and updates status
* [ ] "Combine" button visible when all sections complete in manual mode
* [ ] Combined report displays with proper markdown rendering
* [ ] Status polling updates UI during automatic processing
* [ ] "Run All" button triggers automatic mode for pending sections
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Create an expansion in automatic mode from result detail page
  2. Observe expansion detail page during processing
  3. Verify sections update status as they process
  4. Wait for completion, verify combined report displays
  5. Create an expansion in manual mode
  6. For each section, copy prompt, get response from external LLM, paste and save
  7. Click "Combine" after all sections complete
  8. Verify combined report displays
  9. Test retry: manually fail a section (or use test fixture), click Retry
  10. Verify section reprocesses and completes

* Expected results:
  * Automatic mode: expansion completes without user intervention
  * Manual mode: user can input responses and combine
  * Retry: failed sections can be reprocessed
  * Combined report: readable markdown with original answer link

## Notes

* Requirements covered: R5 (auto/manual modes), R7 (per-section status), R8 (retry failed), R9 (combine into report), R10 (link to original answer)
* UI should remain responsive during automatic expansion (no blocking) - use polling
* Poll interval of 2-3 seconds balances responsiveness and API load
* Section status colors:
  * pending: gray
  * expanding: blue (animated?)
  * ready: yellow
  * generating: blue (animated?)
  * completed: green
  * failed: red
* Copy button on prompts for easy external LLM use in manual mode
