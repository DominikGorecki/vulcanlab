# Ticket: corpus-work-deletion.T03 - Delete Icon and Confirmation Modal UI

## Source
- Spec: documentation/work/corpus-work-deletion.spec.md
- Patterns: documentation/patterns.md

## Goal
- Add delete icon to each row in corpus works table
- Create confirmation modal component with work details
- Handle user interaction flow (click icon, show modal, confirm/cancel)
- Integrate with DELETE API endpoint from T02

## Scope

### In scope
- Add Trash2 icon from lucide-react to corpus table rows
- Create ConfirmDeleteModal component
- Show work title and authors in confirmation modal
- Handle Cancel and Delete button clicks
- Call DELETE API endpoint on confirmation
- Show loading state during deletion
- Close modal and refresh data on success
- Unit tests for ConfirmDeleteModal component

### Out of scope
- Error modal (T04)
- API endpoint implementation (T02)
- Core deletion logic (T01)

## Dependencies
- Depends on: T02 (API endpoint must exist)
- Unblocks: T04

## Implementation plan

1. Update vulcanlab_ui/src/app/corpus/page.tsx:
   - Import Trash2 from lucide-react
   - Add new TableHead "Actions" column to header
   - Add new TableCell to each row with Trash2 icon button
   - Add state for selected work: const [workToDelete, setWorkToDelete] = useState<CorpusWork | null>(null)
   - Add state for deletion in progress: const [isDeleting, setIsDeleting] = useState(false)
   - Add handleDeleteClick function to set workToDelete
   - Add handleDeleteConfirm function to call DELETE API
   - Add handleDeleteCancel function to clear workToDelete

2. Create vulcanlab_ui/src/components/ConfirmDeleteModal.tsx:
   - Use Dialog component from @/components/ui/dialog
   - Accept props: work (title, authors), isOpen, onClose, onConfirm, isDeleting
   - Display work title and authors in modal body
   - Show warning message about permanent deletion
   - Render Cancel button (calls onClose)
   - Render Delete button (calls onConfirm, shows loading spinner if isDeleting)
   - Use destructive styling for Delete button (variant="destructive")

3. Implement handleDeleteConfirm in page.tsx:
   - Set isDeleting to true
   - Call fetch DELETE API_BASE_URL/api/v1/corpus/works/{workId}
   - On success: close modal, call fetchData() to refresh
   - On error: T04 will handle error display
   - Finally: set isDeleting to false

4. Style delete icon:
   - Use Trash2 with size={16} and className="text-muted-foreground hover:text-destructive"
   - Wrap in button with cursor-pointer
   - Stop event propagation to prevent row click navigation

5. Write unit tests in vulcanlab_ui/src/components/__tests__/ConfirmDeleteModal.test.tsx

Patterns to apply:
- Client Component: Use "use client" directive in page.tsx (already present)
- Shadcn/Radix: Use existing Dialog component from ui/dialog
- State Management: Use React useState for modal and loading state
- TypeScript: Define proper types for props and state
- TailwindCSS: Use utility classes for styling

Deviations (if any):
- None: This follows all established frontend patterns

## Unit tests (required)

Add tests for:
- test_confirm_modal_renders_work_details: Render with work, verify title and authors displayed
- test_confirm_modal_cancel_button_calls_onClose: Click Cancel, verify onClose called
- test_confirm_modal_delete_button_calls_onConfirm: Click Delete, verify onConfirm called
- test_confirm_modal_shows_loading_state: Pass isDeleting=true, verify spinner shown and button disabled
- test_confirm_modal_not_visible_when_closed: Pass isOpen=false, verify modal not rendered
- test_delete_icon_appears_in_table: Render page with works, verify Trash2 icon present
- test_delete_icon_opens_modal: Click Trash2 icon, verify modal opens with correct work
- test_delete_icon_stops_propagation: Click icon, verify row click handler not called

Suggested locations:
- vulcanlab_ui/src/components/__tests__/ConfirmDeleteModal.test.tsx (new file)
- Add tests to existing corpus page test file if it exists

Mocking/fakes needed:
- Mock fetch API for DELETE endpoint
- Mock Router from next/navigation for page tests
- Use React Testing Library (@testing-library/react)
- Mock work data fixtures

## Acceptance criteria (checklist)

- [ ] Trash2 icon appears in Actions column of corpus works table
- [ ] Clicking icon opens ConfirmDeleteModal with correct work details
- [ ] Modal displays work title and authors
- [ ] Modal has Cancel and Delete buttons
- [ ] Cancel button closes modal without calling API
- [ ] Delete button shows loading spinner when isDeleting=true
- [ ] Delete button calls DELETE /api/v1/corpus/works/{work_id} endpoint
- [ ] Successful deletion closes modal and refreshes corpus data
- [ ] Icon click does not trigger row navigation
- [ ] Icon has hover effect (color change to destructive)
- [ ] All 8 unit tests written and passing
- [ ] Component uses TypeScript with proper typing

## Manual verification

Steps:
1. Start the development server (npm run dev)
2. Navigate to http://localhost:3000/corpus
3. Verify Trash2 icon appears in each work row
4. Click a delete icon
5. Verify confirmation modal opens showing work title and authors
6. Click Cancel and verify modal closes
7. Click delete icon again
8. Click Delete button
9. Verify loading spinner appears
10. Verify modal closes after deletion
11. Verify work is removed from table
12. Verify stats are updated
13. Click delete icon without clicking row
14. Verify work detail page is NOT opened

Expected results:
- Delete icon is visible and clickable in each row
- Modal shows correct work information
- User can cancel without side effects
- Deletion triggers API call and refreshes UI
- Loading states provide feedback
- Icon click is isolated from row click

## Notes

- Reference existing Button component usage in corpus page
- Use existing Dialog component pattern from other modals in the codebase
- The Trash2 icon should be small and unobtrusive (16px)
- Consider using stopPropagation() on icon button click to prevent row navigation
- Delete button should use variant="destructive" for visual warning
- Modal should be accessible (keyboard navigation, ARIA labels)
- Consider adding data-testid attributes for easier testing
- Ensure modal backdrop click closes modal (default Dialog behavior)
- The work title may be long; consider truncation in modal if needed
- Use semantic HTML (button elements, not div with onClick)
