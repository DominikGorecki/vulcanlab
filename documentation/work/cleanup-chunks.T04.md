# Ticket: cleanup-chunks.T04 - Delete Functionality with Confirmation Modal

## Source
- Spec: documentation/work/cleanup-chunks.spec.md
- Patterns: documentation/patterns.md

## Goal
- Add delete button to each search result card with confirmation flow
- Implement confirmation modal showing all descendant chunks before deletion
- Execute deletion and update UI to remove deleted chunk from results
- Complete the feature with full end-to-end delete capability
- Add toast notifications for success/error feedback

## Scope
### In scope
- Add delete icon button (Trash2) to each result card in cleanup page
- Create confirmation modal component using Radix AlertDialog
- Fetch descendants when delete button clicked
- Display descendants list in modal with metadata (id, level, breadcrumbs)
- Show total count of chunks to be deleted in modal
- Execute DELETE request on confirmation
- Remove deleted chunk from results state without re-querying
- Show success toast after deletion
- Show error message if deletion fails
- Handle edge cases (no descendants, already deleted chunk)

### Out of scope
- Bulk deletion (multiple chunks at once)
- Undo/restore functionality
- Archive before delete
- Animation/transition effects (basic is fine)
- Optimistic UI updates (wait for API response)

## Dependencies
- Depends on: T03 (builds on existing cleanup page UI)
- Unblocks: none (completes the feature)

## Implementation plan
1. Update `vulcanlab_ui/src/app/cleanup/page.tsx`:
   - Import Trash2 icon from lucide-react
   - Import AlertDialog components from @/components/ui/alert-dialog
   - Import useToast hook or toast component (check existing pattern)
2. Add state for deletion flow:
   - useState for: selectedChunkId, descendants, deleteModalOpen, deleteLoading, deleteError
3. Add delete button to result cards:
   - Position Trash2 icon button in top-right corner or at end of metadata row
   - onClick: open modal and fetch descendants
   - Use ghost or outline variant for subtle appearance
4. Implement handleDeleteClick function:
   - Set selectedChunkId to clicked chunk's id
   - Set deleteModalOpen=true
   - Fetch descendants: GET /api/v1/chunks/{chunk_id}/descendants
   - Update descendants state with response
   - Handle fetch errors (display in modal)
5. Create confirmation modal:
   - Use Radix AlertDialog component
   - Title: "Delete Chunk"
   - Description: "This will permanently delete this chunk and all its descendants"
   - Show descendants list:
     - If descendants.length === 0: "No descendant chunks will be deleted"
     - Else: scrollable list showing id, level badge, and breadcrumbs for each descendant
     - Limit display to first 50 descendants, show "and X more..." if > 50
   - Show total count: "Total: X chunk(s) will be deleted"
   - Action buttons: Cancel (secondary) and Confirm Delete (destructive/danger variant)
6. Implement handleConfirmDelete function:
   - Set deleteLoading=true
   - Call DELETE /api/v1/chunks/{chunk_id}
   - On success:
     - Remove deleted chunk from results array using filter
     - Update pagination total if needed (decrement totalResults)
     - Close modal
     - Show success toast: "Chunk deleted successfully"
     - Reset state (selectedChunkId, descendants, deleteError)
   - On error:
     - Set deleteError state with error message
     - Display error in modal (below descendants list)
     - Keep modal open for user to retry or cancel
     - If 404 error: show "Chunk not found (may have been deleted already)"
   - Finally: set deleteLoading=false
7. Implement modal cancel handler:
   - Close modal
   - Reset state (selectedChunkId, descendants, deleteError, deleteModalOpen)
8. Add loading state to modal:
   - Show spinner while fetching descendants
   - Disable buttons while deleteLoading=true
   - Show loading text on Confirm button: "Deleting..."
9. Implement toast notifications:
   - Use existing toast system (Radix UI Toast or similar)
   - Success: "Chunk deleted successfully"
   - Error: "Failed to delete chunk: {error message}"
10. Handle edge cases:
    - Descendant fetch fails: show error in modal, disable Confirm button
    - Delete request fails: show error in modal, allow retry
    - Already deleted chunk (404): show appropriate message, close modal
11. UI polish:
    - Trash icon should have hover state (color change or opacity)
    - Modal should have proper z-index to overlay results
    - Descendant list should be scrollable if long
    - Use destructive/danger styling for Confirm Delete button (red)

- Patterns to apply:
  - **Component reuse**: Use Radix AlertDialog from existing UI components
  - **Client components**: Already "use client" from T03
  - **TailwindCSS**: Use utility classes for styling
  - **Error handling**: Display user-friendly error messages
  - **State management**: Local React state for modal and deletion flow

- Deviations (if any):
  - None: Fully aligned with patterns.md

## Unit tests (required)
- Add tests for:
  - **test_delete_button_renders**: Verify Trash2 icon button appears on each result card
  - **test_delete_button_click_opens_modal**: Click delete, verify modal opens
  - **test_delete_button_fetches_descendants**: Click delete, verify GET /descendants API called
  - **test_modal_displays_descendants**: Mock descendants response, verify list renders in modal
  - **test_modal_displays_no_descendants**: Mock empty descendants, verify "No descendants" message
  - **test_modal_displays_total_count**: Mock 3 descendants, verify "Total: 4 chunk(s)" (includes parent)
  - **test_modal_cancel_closes**: Click Cancel, verify modal closes and state resets
  - **test_modal_confirm_calls_delete_api**: Click Confirm, verify DELETE API called with chunk_id
  - **test_delete_success_removes_from_results**: Mock successful delete, verify chunk removed from results array
  - **test_delete_success_shows_toast**: Mock successful delete, verify success toast displayed
  - **test_delete_success_closes_modal**: Mock successful delete, verify modal closes
  - **test_delete_error_displays_message**: Mock delete error, verify error message shows in modal
  - **test_delete_error_keeps_modal_open**: Mock delete error, verify modal stays open
  - **test_delete_404_shows_appropriate_message**: Mock 404 response, verify "already deleted" message
  - **test_delete_loading_state**: Verify loading indicator and disabled buttons during delete
  - **test_descendants_fetch_error**: Mock fetch error, verify error displayed and Confirm disabled
  - **test_descendant_list_limit**: Mock 60 descendants, verify only 50 shown with "and 10 more..."
  - **test_delete_updates_pagination**: Mock delete, verify totalResults decremented

- Suggested locations:
  - Update `tests/unit/test_cleanup_page.tsx` (add delete functionality tests)
  - Consider separate `tests/unit/test_delete_modal.tsx` if modal becomes complex component

- Mocking/fakes needed:
  - Mock fetch for GET /descendants and DELETE endpoints
  - Mock toast notification system
  - Mock API responses (success, error, 404)
  - React Testing Library for user interaction testing

## Acceptance criteria (checklist)
- [ ] Delete icon (Trash2) appears on each search result card
- [ ] Clicking delete icon opens confirmation modal
- [ ] Modal fetches and displays descendants list
- [ ] Modal shows descendant id, level badge, and breadcrumbs for each
- [ ] Modal shows "No descendants" when list is empty
- [ ] Modal displays total count of chunks to be deleted (parent + descendants)
- [ ] Descendant list is scrollable and limits display to 50 items
- [ ] Modal has Cancel and Confirm Delete buttons
- [ ] Cancel button closes modal without action
- [ ] Confirm Delete button executes DELETE API request
- [ ] Successful deletion removes chunk from results list
- [ ] Successful deletion shows success toast notification
- [ ] Failed deletion displays error message in modal
- [ ] Failed deletion keeps modal open for retry
- [ ] 404 error shows "already deleted" message
- [ ] Loading state disables buttons and shows spinner during operations
- [ ] Deleting last result on page handles gracefully (empty results)
- [ ] Pagination total count updates after deletion
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Navigate to /cleanup page
  2. Search for chunks that have descendants
  3. Verify delete icon (trash) appears on each result
  4. Click delete icon on a chunk with children
  5. Verify modal opens with title "Delete Chunk"
  6. Verify descendants list displays with correct information
  7. Verify total count shows (e.g., "Total: 5 chunk(s) will be deleted")
  8. Click Cancel
  9. Verify modal closes and no deletion occurs
  10. Click delete icon again
  11. Click Confirm Delete
  12. Verify loading state shows ("Deleting..." button text)
  13. Verify modal closes after successful deletion
  14. Verify success toast appears
  15. Verify chunk is removed from results list
  16. Verify pagination count updated if shown
  17. Click delete on chunk with no descendants
  18. Verify modal shows "No descendant chunks will be deleted"
  19. Confirm deletion
  20. Verify successful deletion
  21. Use database viewer to verify chunks actually deleted
  22. Use database viewer to verify no orphaned chunks remain
  23. Test error case: disconnect network, try delete, verify error shown
  24. Test deleting already-deleted chunk (use browser dev tools to modify chunk_id)

- Expected results:
  - Complete delete flow works end-to-end
  - Modal provides clear warning with descendant information
  - Deletion removes chunks from database via API
  - UI updates correctly after deletion
  - Success and error states handled gracefully
  - No orphaned chunks remain in database
  - Toast notifications appear for user feedback
  - All edge cases handled appropriately

## Notes
- This ticket completes the feature, creating a full vertical slice from search to deletion
- Confirmation modal is critical for preventing accidental deletion
- Descendant list helps users understand impact before confirming
- Removing chunk from results state avoids unnecessary re-query (per spec R10)
- Toast notifications provide important user feedback for async operations
- Destructive action should use danger/destructive button styling (typically red)
- Consider showing deleted chunk's heading breadcrumbs in success toast for confirmation
- Limit descendant display to 50 to avoid modal overload, with "and X more..." indicator
- If user deletes last result on current page, consider: show empty state or auto-navigate to previous page
- Error messages should be user-friendly, not technical stack traces
- 404 handling is important since another user might delete the same chunk concurrently
- Loading states during fetch and delete prevent multiple submissions
- Test with database to verify CASCADE deletion actually works as expected
- Consider disabling all delete buttons while one deletion is in progress (optional)
- AlertDialog from Radix should handle focus trap and keyboard navigation automatically
