# Ticket: markdown-import-export.T05 - Export Frontend Page (Vertical Slice)

## Source
- Spec: documentation/work/markdown-import-export.spec.md
- Patterns: documentation/patterns.md

## Goal
- Create export page UI that lists corpus works
- Implement export button functionality
- Show success/error feedback to user
- First end-to-end vertical slice for export feature

## Scope
### In scope
- Page component: vulcanlab_ui/src/app/markdown/export/page.tsx
- Export functionality: list works, trigger export, show feedback
- Reuse corpus API for work listing
- Error handling modal for export failures
- Success toast notification

### Out of scope
- Import page (covered in T08)
- Tab navigation between pages (covered in T09)
- Batch export operations
- Export history or tracking

## Dependencies
- Depends on: T02
- Unblocks: T09

## Implementation plan
1. Create vulcanlab_ui/src/app/markdown/export/page.tsx:
   - "use client" directive for client component
   - Import necessary components from shadcn/ui (Card, Table, Button, toast)
   - Define interfaces: CorpusWork (reuse from corpus page)
   - State management:
     - works: CorpusWork[]
     - loading: boolean
     - error: string | null
     - exportingWorkId: number | null (for loading state on button)
   - useEffect to fetch works on mount from /api/v1/corpus/works
   - handleExport(workId: number) async function:
     - Set exportingWorkId to workId
     - Call POST /api/v1/markdown/export/{workId}
     - On success: Show success toast with export path
     - On error: Show error modal with error message
     - Clear exportingWorkId
   - Render:
     - Page header: "Export Markdown"
     - Description: "Export corpus works as markdown files with metadata"
     - Card with Table listing works (ID, Title, Authors, Actions)
     - Export button in Actions column (shows spinner when exporting)
     - Click row to navigate to /corpus/{id} (reuse corpus behavior)
2. Create error modal component if not already exists, or reuse ErrorModal
3. Import and use toast from shadcn/ui for success notifications
4. Patterns to apply:
   - Next.js App Router: Place in app/markdown/export/page.tsx
   - Client component: Use "use client" for interactivity
   - Shadcn/Radix UI: Use existing components (Button, Card, Table, toast)
   - Error handling: Show user-friendly messages
   - Loading states: Disable button and show spinner during export
- Deviations (if any): none

## Unit tests (required)
- Add tests for:
  - Page renders with loading state initially
  - Page fetches works from API on mount
  - Works are displayed in table correctly
  - Export button calls API with correct work ID
  - Success toast appears after successful export
  - Error modal appears after failed export
  - Export button disabled during export operation
  - Row click navigates to corpus detail page
- Suggested locations:
  - vulcanlab_ui/src/app/markdown/export/__tests__/page.test.tsx
- Mocking/fakes needed:
  - Mock fetch for /api/v1/corpus/works
  - Mock fetch for /api/v1/markdown/export/{id}
  - Mock toast notifications
  - Mock useRouter from next/navigation

## Acceptance criteria (checklist)
- [ ] Export page displays all corpus works in table
- [ ] Table shows work ID, title, and authors
- [ ] Export button exists for each work
- [ ] Clicking export calls API and shows loading state
- [ ] Success toast displays export path after successful export
- [ ] Error modal displays error message on failure
- [ ] Export button disabled while export in progress
- [ ] Clicking work row navigates to corpus detail page
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Navigate to /markdown/export in browser
  2. Verify table lists all corpus works
  3. Click export button for a work
  4. Verify button shows loading spinner
  5. Verify success toast appears with export path
  6. Check exports folder for created file
  7. Export work without markdown, verify error modal
  8. Click on work row, verify navigation to corpus detail
- Expected results:
  - Works list matches corpus page
  - Export operation completes successfully
  - User feedback is clear and timely
  - Error cases handled gracefully

## Notes
- Reuse table styling from corpus page for consistency
- Export path in toast should be truncated if too long (show .../ prefix)
- Consider debouncing export button to prevent double-clicks
- Error modal should include retry button if appropriate
- Loading spinner on button should replace button text, not appear alongside
- This is the first vertical slice: user can export works end-to-end
