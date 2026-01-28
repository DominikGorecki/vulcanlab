# Ticket: expand-answer.T04 - UI: Expand Button and Expansions List

## Source

* Spec: documentation/work/expand-answer.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add "Expand Answer" button to result detail page
* Create Expansions list page showing all expansions with status
* Enable users to initiate expansions and view their expansion history

## Scope

### In scope

* "Expand Answer" button on result detail page (`/rag/{query_id}/results/{result_id}`)
* Modal for expansion creation with mode toggle (Automatic/Manual)
* Expansions list page at `/expansions`
* Status badges showing expansion progress
* Link from result detail page to existing expansion (if one exists)
* Navigation entry for Expansions (sidebar or discoverable location)

### Out of scope

* Expansion detail page with sections (T05)
* Section retry and manual response input (T05)
* Combined report display (T05)

## Dependencies

* Depends on: T01 (models), T03 (API endpoints)
* Unblocks: T05

## Implementation plan

1. Create expansion creation modal component:
   - `vulcanlab_ui/src/components/expansion/create-expansion-modal.tsx`
   - Mode toggle: "Automatic" (recommended) / "Manual"
   - Automatic: System runs all section LLM calls
   - Manual: User copies prompts and pastes responses
   - Confirm button calls `POST /api/v1/expansions/`
   - On success, redirect to expansion detail page
2. Add "Expand Answer" button to result detail page:
   - Locate existing result detail component
   - Add button in appropriate action area
   - Check if expansion exists via `GET /api/v1/results/{result_id}/expansion`
   - If expansion exists, show "View Expansion" link instead of "Expand Answer"
   - Button opens creation modal
3. Create Expansions list page:
   - `vulcanlab_ui/src/app/expansions/page.tsx`
   - Use `usePageData` hook with memoized fetch function
   - Fetch from `GET /api/v1/expansions/`
   - Display DataTable with columns: ID, Original Query (linked), Mode, Status, Sections, Created
   - Status badges with colors:
     - created/breakdown_pending: gray
     - breakdown_complete/sections_in_progress: blue
     - combining: yellow
     - completed: green
     - failed: red
   - Row click navigates to expansion detail
4. Add status badge component:
   - `vulcanlab_ui/src/components/expansion/expansion-status-badge.tsx`
   - Reusable across list and detail pages
5. Add navigation entry:
   - Add "Expansions" to sidebar navigation
   - Use appropriate icon
6. Handle loading/error/empty states per UI patterns

* Patterns to apply:
  * Page Lifecycle Pattern - usePageData with memoized fetch, loading/error/empty states
  * Component Composition - Props-in, events-out
  * Theme Awareness - Use Tailwind semantic classes
  * Standard Layout - PageHeader + DataTable

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `test_create_expansion_modal_renders` - modal shows mode toggle
  * `test_create_expansion_modal_submits` - calls API on confirm
  * `test_expansion_status_badge_colors` - correct color per status
  * `test_expansions_list_renders_data` - table shows expansion data
  * `test_expansions_list_empty_state` - shows empty message when no expansions
  * `test_result_detail_shows_expand_button` - button visible when no expansion
  * `test_result_detail_shows_view_link` - link visible when expansion exists

* Suggested locations:
  * `vulcanlab_ui/__tests__/components/expansion/create-expansion-modal.test.tsx`
  * `vulcanlab_ui/__tests__/components/expansion/expansion-status-badge.test.tsx`
  * `vulcanlab_ui/__tests__/app/expansions/page.test.tsx`

* Mocking/fakes needed:
  * Mock fetch responses for API calls
  * Mock router for navigation testing

## Acceptance criteria (checklist)

* [ ] "Expand Answer" button visible on result detail page
* [ ] Clicking button opens modal with Automatic/Manual toggle
* [ ] Modal submits to API and redirects to expansion detail on success
* [ ] If expansion exists for result, "View Expansion" link shown instead
* [ ] Expansions list page accessible at `/expansions`
* [ ] List shows all expansions with correct status badges
* [ ] Clicking expansion row navigates to detail page
* [ ] "Expansions" navigation entry present and functional
* [ ] Loading, error, and empty states handled correctly
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Navigate to a RAG result detail page
  2. Verify "Expand Answer" button is visible
  3. Click button, verify modal opens with mode toggle
  4. Select mode and confirm
  5. Verify redirect to expansion detail page (or error if API fails)
  6. Navigate to `/expansions`
  7. Verify list shows the created expansion with correct status
  8. Click the expansion row, verify navigation to detail

* Expected results:
  * Smooth flow from result page to expansion creation
  * Expansions list displays all expansions with status indicators
  * Navigation between list and detail works correctly

## Notes

* Requirements covered: R1 (initiate from result detail), R5 (mode toggle), R11 (dedicated Expansions view), R12 (link from result to expansion)
* Mode descriptions in modal:
  * Automatic: "System will process all sections automatically using AI"
  * Manual: "You will copy each section prompt and paste AI responses"
* The expansion detail page (T05) will show section-level details
* Status polling will be implemented in T05 for in-progress expansions
