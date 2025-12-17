# Ticket: corpus-work-deletion.T04 - Error Handling and Error Modal

## Source
- Spec: documentation/work/corpus-work-deletion.spec.md
- Patterns: documentation/patterns.md

## Goal
- Display error modal when deletion fails
- Show descriptive error messages to user
- Handle network errors and API failures gracefully
- Provide clear recovery path (close modal, retry)

## Scope

### In scope
- Create ErrorModal component for deletion errors
- Add error state management to corpus page
- Handle API error responses (404, 500)
- Handle network errors (fetch failures)
- Display error details from API response
- Allow user to close error modal
- Unit tests for error handling

### Out of scope
- Retry logic or automatic recovery
- Core deletion logic (T01)
- API endpoint implementation (T02)
- Confirmation modal (T03)

## Dependencies
- Depends on: T03 (UI components and flow must exist)
- Unblocks: none (completes feature)

## Implementation plan

1. Create vulcanlab_ui/src/components/ErrorModal.tsx:
   - Use AlertDialog component from @/components/ui/alert-dialog
   - Accept props: isOpen, onClose, title, message, error (optional)
   - Display error icon (AlertCircle from lucide-react)
   - Show title and message prominently
   - Show detailed error text if provided
   - Render Close button (calls onClose)
   - Use destructive/error styling theme

2. Update vulcanlab_ui/src/app/corpus/page.tsx:
   - Add error state: const [deleteError, setDeleteError] = useState<string | null>(null)
   - Update handleDeleteConfirm to catch errors:
     - Check response.ok, parse error detail from JSON
     - Handle 404: "Work not found. It may have been already deleted."
     - Handle 500: Parse detail from response body
     - Handle network errors: "Failed to connect to server. Please try again."
     - Set deleteError state with appropriate message
   - Clear workToDelete when showing error (close confirmation modal)
   - Render ErrorModal with error state
   - Clear deleteError when modal closes

3. Improve error messages:
   - 404 Not Found: User-friendly message (work already deleted)
   - 500 Internal Server Error: Show error detail from API without file paths
   - Network error: Generic connection message
   - Unexpected errors: "An unexpected error occurred. Please try again."

4. Write unit tests in vulcanlab_ui/src/components/__tests__/ErrorModal.test.tsx

Patterns to apply:
- Component Composition: Use existing AlertDialog from Shadcn/ui
- Error Handling: Graceful degradation with user-friendly messages
- State Management: React useState for error state
- Accessibility: AlertDialog provides ARIA attributes
- TypeScript: Proper typing for error props

Deviations (if any):
- None: This follows all established patterns

## Unit tests (required)

Add tests for:
- test_error_modal_renders_title_and_message: Render with error, verify title and message displayed
- test_error_modal_shows_error_details: Pass detailed error, verify details shown
- test_error_modal_close_button_calls_onClose: Click Close, verify onClose called
- test_error_modal_not_visible_when_closed: Pass isOpen=false, verify modal not rendered
- test_error_modal_shows_alert_icon: Verify AlertCircle icon rendered
- test_page_handles_404_error: Mock fetch 404, verify error message shown
- test_page_handles_500_error: Mock fetch 500, verify error detail shown
- test_page_handles_network_error: Mock fetch to throw, verify network error message
- test_page_closes_confirm_modal_on_error: Trigger error, verify confirmation modal closed
- test_page_clears_error_on_modal_close: Close error modal, verify error state cleared

Suggested locations:
- vulcanlab_ui/src/components/__tests__/ErrorModal.test.tsx (new file)
- Add integration tests to corpus page test file for error handling flow

Mocking/fakes needed:
- Mock fetch API to return error responses
- Mock fetch API to throw network errors
- Mock work data for test scenarios
- Use React Testing Library for component tests

## Acceptance criteria (checklist)

- [ ] ErrorModal component created using AlertDialog
- [ ] Modal displays error icon, title, and message
- [ ] Modal shows detailed error text when provided
- [ ] Close button dismisses modal and clears error state
- [ ] 404 errors show user-friendly "already deleted" message
- [ ] 500 errors display error detail from API response
- [ ] Network errors show connection failure message
- [ ] File system paths are NOT exposed in error messages
- [ ] Confirmation modal closes when error occurs
- [ ] Error modal uses destructive/error styling
- [ ] All 10 unit tests written and passing
- [ ] Error handling does not break page functionality

## Manual verification

Steps:
1. Start development server
2. Navigate to corpus page
3. Mock API to return 500 error (browser DevTools or modify API)
4. Click delete icon and confirm
5. Verify error modal appears with error message
6. Verify confirmation modal is closed
7. Click Close on error modal
8. Verify error modal closes and page is still functional
9. Mock API to return 404
10. Attempt deletion
11. Verify "already deleted" message shown
12. Disconnect network (DevTools offline mode)
13. Attempt deletion
14. Verify network error message shown
15. Restore network
16. Delete successfully
17. Verify no error modal appears

Expected results:
- Error modal appears for all error scenarios
- Error messages are user-friendly and descriptive
- User can close error modal and continue using the page
- Confirmation modal closes when error occurs
- File paths and stack traces are not exposed
- Page remains functional after errors

## Notes

- Use AlertDialog instead of Dialog for error modals (semantic correctness)
- AlertCircle icon from lucide-react is standard for error states
- Consider using toast notifications for non-critical errors (future enhancement)
- Error messages should not expose internal implementation details
- Don't retry automatically; let user decide next action
- Consider logging errors to console for debugging (console.error)
- Error modal should prevent interaction with page content (modal overlay)
- Use descriptive error titles: "Deletion Failed", "Work Not Found", "Connection Error"
- Parse API error detail safely (check if response is JSON)
- Handle edge case where API returns HTML error page (check content-type)
- Consider adding error tracking/analytics in future (not in scope)
