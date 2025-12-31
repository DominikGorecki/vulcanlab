# Ticket: eval-prompt-answer-pair-improvements.T02 - Update Answer-Pair Table Delete Behavior

## Source

* Spec: documentation/work/eval-prompt-answer-pair-improvements.spec.md
* Patterns: documentation/patterns.md

## Goal

* Change delete action in AnswersTable to delete entire answer-pair instead of just evaluation
* Update confirmation dialog to clearly communicate that both answer and evaluation will be deleted
* Enable users to properly remove answer-pairs from experiments

## Scope

### In scope

* Modify delete handler in AnswersTable component to call `DELETE /api/v1/eval/answers/{answer_id}`
* Update ConfirmDialog text to specify "delete answer and evaluation"
* Remove conditional logic that only shows delete button for evaluated answers
* Update state management to refresh table after answer deletion
* Add "View Details" button to actions column (eye icon, navigates to detail page)

### Out of scope

* Answer detail page itself (T03)
* Backend endpoints (T01)
* Evaluation overwrite functionality (T04)
* Changes to PasteResultDialog

## Dependencies

* Depends on: T01 (requires DELETE endpoint)
* Unblocks: T03 (provides navigation to detail page)

## Implementation plan

1. Open `vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/page.tsx`

2. Update AnswersTable component delete handler:
   - Change `handleDeleteEvaluation()` to `handleDeleteAnswer(answerId: number)`
   - Update fetch call from `DELETE /api/v1/eval/evaluations/{evaluationId}` to `DELETE /api/v1/eval/answers/{answerId}`
   - Remove evaluation_id logic, use answer.id directly
   - Update state variables: remove `deletingEvalId`, use `deletingAnswerId`

3. Update ConfirmDialog for deletion:
   - Change title from "Delete Evaluation" to "Delete Answer Pair"
   - Change description to: "Are you sure you want to delete this answer pair? This will permanently delete the answer and any associated evaluation. This action cannot be undone."
   - Change confirmLabel to "Delete Answer Pair"

4. Update delete button visibility:
   - Remove condition `{answer.has_evaluation && answer.evaluation_id && (...)}`
   - Show delete button for all answers, not just evaluated ones

5. Add "View Details" button to actions column:
   - Import Eye icon from lucide-react
   - Add new button before delete button: variant="ghost", size="sm"
   - Button text: "View Details" with Eye icon
   - onClick navigates to `/eval/${experimentId}/prompts/${promptId}/answers/${answer.id}`
   - Use Next.js router for navigation

6. Update toast messages:
   - Change success message to: "Answer pair deleted" / "The answer pair has been deleted successfully"
   - Update error messages to reflect answer deletion

### Patterns to apply

* Page Lifecycle Pattern: Table already uses usePageData hook, refetch after deletion
* Component Library: Use existing ConfirmDialog, Button components
* Props-In, Events-Out: Pass onEvaluationChange callback to trigger refetch
* Theme Awareness: Use Tailwind semantic classes for new button

### Deviations (if any)

* None

## Unit tests (required)

* Add tests for:
  * `test_delete_button_shown_for_all_answers()`: Verify delete button appears for both evaluated and unevaluated answers
  * `test_delete_calls_answer_endpoint()`: Mock fetch, click delete, verify DELETE /api/v1/eval/answers/{id} called
  * `test_delete_confirmation_shows_correct_text()`: Verify dialog shows "delete answer and evaluation" message
  * `test_view_details_navigates_correctly()`: Click View Details, verify navigation to answer detail page
  * `test_table_refreshes_after_deletion()`: Mock delete success, verify refetch called

* Suggested locations:
  * `vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/__tests__/page.test.tsx`
  * Or create new file: `vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/__tests__/answers-table.test.tsx`

* Mocking/fakes needed:
  * Mock `fetch` API for DELETE endpoint
  * Mock Next.js `useRouter` for navigation
  * Mock `useToast` hook
  * Mock answer data with both evaluated and unevaluated items

## Acceptance criteria (checklist)

- [ ] Delete button appears for all answer-pairs, not just evaluated ones
- [ ] Clicking delete button shows confirmation dialog with updated text
- [ ] Confirmation dialog mentions "delete answer and evaluation"
- [ ] Delete action calls `DELETE /api/v1/eval/answers/{answer_id}` endpoint
- [ ] Successful deletion shows toast: "Answer pair deleted"
- [ ] Table refreshes after deletion (answer disappears from list)
- [ ] "View Details" button added to each row with Eye icon
- [ ] Clicking "View Details" navigates to `/eval/[id]/prompts/[promptId]/answers/[answerId]`
- [ ] Error handling shows appropriate toast for failed deletions
- [ ] All unit tests pass

## Manual verification

* Steps:
  1. Navigate to `/eval/[id]/prompts/[promptId]` page with multiple answer-pairs
  2. Verify delete button (trash icon) appears for all answers (evaluated and unevaluated)
  3. Verify "View Details" button appears for all answers
  4. Click delete button on unevaluated answer-pair
  5. Verify confirmation dialog shows "Delete Answer Pair" title and mentions deleting "answer and evaluation"
  6. Confirm deletion and verify answer disappears from table
  7. Check database to confirm answer was deleted
  8. Click delete button on evaluated answer-pair
  9. Confirm deletion and verify both answer and evaluation removed from database
  10. Click "View Details" button on any answer
  11. Verify navigation to detail page (will show 404 or loading in T02, working in T03)

* Expected results:
  * All answers show both delete and view details buttons
  * Delete confirmation clearly states both answer and evaluation will be deleted
  * Deleted answers disappear from table immediately
  * Database confirms cascade deletion of evaluations
  * View Details button navigates to correct route
  * No console errors or infinite rendering loops

## Notes

* Requirements covered: R1, R4 (partial - adds View Details button)
* The existing ConfirmDialog component already supports variant="destructive" for delete actions
* Navigation to answer detail page will be implemented in T03
* Current code at line 103-130 in page.tsx needs modification
* The onEvaluationChange callback name is still appropriate (triggers table refresh regardless of what changed)
