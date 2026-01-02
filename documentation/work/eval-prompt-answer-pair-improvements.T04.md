# Ticket: eval-prompt-answer-pair-improvements.T04 - Evaluation Overwrite Functionality

## Source

* Spec: documentation/work/eval-prompt-answer-pair-improvements.spec.md
* Patterns: documentation/patterns.md

## Goal

* Enable users to overwrite existing evaluations via paste-result dialog
* Add confirmation dialog before overwriting to prevent accidental data loss
* Support evaluation updates on answer detail page
* Maintain backward compatibility with initial paste (create new evaluation)

## Scope

### In scope

* Backend: Modify `submit_evaluation()` to support upsert mode (update if exists)
* Backend: Add `overwrite` query parameter to evaluation submission endpoint
* Frontend: Enhance PasteResultDialog to detect existing evaluation
* Frontend: Show confirmation before overwriting existing evaluation
* Frontend: Add "Paste/Overwrite Result" button to answer detail page
* Unit tests for overwrite logic (backend and frontend)

### Out of scope

* Audit logging for overwrites (explicitly excluded per spec)
* Inline editing of evaluation scores
* Bulk evaluation updates
* Version history for evaluations

## Dependencies

* Depends on: T01 (requires answer detail retrieval), T03 (detail page hosts button)
* Unblocks: none (final ticket)

## Implementation plan

1. Backend: Modify `src/vulcanlab/eval/evaluations.py`:
   - Update `submit_evaluation()` signature to accept `overwrite: bool = False` parameter
   - Add logic to check if evaluation exists for answer_id
   - If exists and overwrite=False, raise ValueError("Evaluation already exists")
   - If exists and overwrite=True, UPDATE existing evaluation instead of INSERT
   - Update dimension_results: DELETE old results, INSERT new ones (or UPSERT)
   - Log evaluation overwrites with evaluation_id
   - Ensure transaction safety (rollback on error)

2. Backend: Modify evaluation submission endpoint in `src/vulcanlab_api/routers/eval.py`:
   - Update endpoint signature: `POST /api/v1/eval/answers/{answer_id}/evaluations`
   - Add optional query parameter: `overwrite: bool = False`
   - Pass overwrite parameter to `submit_evaluation()`
   - Handle ValueError for duplicate evaluation (return 400 or 409 if overwrite=False)
   - Update endpoint documentation to describe overwrite behavior

3. Frontend: Enhance PasteResultDialog component:
   - Open `vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/paste-result-dialog.tsx`
   - Add prop: `answerId: number` and `existingEvaluation?: boolean`
   - On mount/open, check if answer already has evaluation (can pass as prop or fetch)
   - Add state for overwrite confirmation
   - If existing evaluation detected, show warning message before paste
   - Add Checkbox: "I understand this will overwrite the existing evaluation"
   - Disable paste button until checkbox checked (if overwriting)
   - Update API call to include `?overwrite=true` query param when checkbox checked

4. Frontend: Update AnswersTable to pass evaluation status:
   - Modify PasteResultDialog instantiation to include `existingEvaluation={answer.has_evaluation}`
   - Or pass answerId and let dialog fetch the status

5. Frontend: Add paste button to answer detail page (T03):
   - Import PasteResultDialog component
   - Add "Paste/Overwrite Result" button to page (near evaluation section)
   - Button appears for all answers (both evaluated and unevaluated)
   - Pass answerId and evaluation existence to PasteResultDialog
   - On success, refresh page data to show updated evaluation

6. Frontend: Add overwrite confirmation dialog:
   - Use Alert or custom dialog to warn user
   - Message: "This answer already has an evaluation. Overwriting will replace all scores and justification. Are you sure?"
   - Two-step confirmation: warning + checkbox to confirm understanding

7. Write unit tests (see Unit tests section below)

### Patterns to apply

* Three-tier Architecture: Core logic in evaluations.py, API layer in routers
* Session Management: Pass session explicitly, ensure transaction safety
* Error Handling: Raise ValueError for duplicate when overwrite=False
* Component Library: Use ConfirmDialog, Alert, Checkbox from shadcn/ui
* Props-In, Events-Out: Dialog receives props, calls onSuccess callback

### Deviations (if any)

* None

## Unit tests (required)

* Add tests for:
  * Backend:
    - `test_submit_evaluation_creates_new()`: Verify new evaluation created when none exists
    - `test_submit_evaluation_rejects_duplicate_when_no_overwrite()`: Verify ValueError raised if evaluation exists and overwrite=False
    - `test_submit_evaluation_updates_when_overwrite_true()`: Create evaluation, submit again with overwrite=True, verify UPDATE not INSERT
    - `test_submit_evaluation_overwrite_updates_dimensions()`: Verify dimension_results updated correctly
    - `test_overwrite_endpoint_with_query_param()`: Call endpoint with overwrite=true, verify success
    - `test_overwrite_endpoint_without_param_fails()`: Call endpoint without overwrite param on existing evaluation, verify error

  * Frontend:
    - `test_paste_dialog_detects_existing_evaluation()`: Mock answer with evaluation, verify warning shown
    - `test_paste_dialog_shows_checkbox_for_overwrite()`: Verify checkbox appears when evaluation exists
    - `test_paste_dialog_disables_button_until_confirmed()`: Verify paste button disabled until checkbox checked
    - `test_paste_dialog_includes_overwrite_param()`: Mock submission, verify API call includes overwrite=true
    - `test_paste_dialog_normal_flow_for_new()`: Verify normal paste works for unevaluated answers (no checkbox)
    - `test_detail_page_paste_button_present()`: Verify paste/overwrite button appears on detail page
    - `test_detail_page_refreshes_after_paste()`: Mock successful paste, verify page data refetches

* Suggested locations:
  * Backend: `tests/unit/test_eval_overwrite.py`
  * Frontend: `vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/__tests__/paste-result-dialog.test.tsx`
  * Frontend: Update `vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/answers/[answerId]/__tests__/page.test.tsx`

* Mocking/fakes needed:
  * Mock SQLAlchemy session and ORM objects for backend tests
  * Mock fetch API for frontend tests
  * Mock existing evaluation data
  * Mock toast notifications

## Acceptance criteria (checklist)

- [ ] `submit_evaluation()` accepts `overwrite` parameter
- [ ] Backend raises ValueError when evaluation exists and overwrite=False
- [ ] Backend successfully updates evaluation when overwrite=True
- [ ] Dimension results updated correctly during overwrite (old deleted, new inserted)
- [ ] Evaluation overwrite logged with evaluation_id
- [ ] Endpoint accepts `?overwrite=true` query parameter
- [ ] PasteResultDialog detects existing evaluation
- [ ] PasteResultDialog shows warning and checkbox for overwrite confirmation
- [ ] Paste button disabled until user confirms overwrite via checkbox
- [ ] API call includes `overwrite=true` when overwriting
- [ ] Answer detail page includes "Paste/Overwrite Result" button
- [ ] Detail page refreshes after successful paste/overwrite
- [ ] Normal paste flow unchanged for unevaluated answers
- [ ] All unit tests pass (at least 13 test cases)

## Manual verification

* Steps:
  1. Navigate to answer detail page for unevaluated answer
  2. Click "Paste/Overwrite Result" button
  3. Verify dialog opens WITHOUT overwrite warning (normal paste flow)
  4. Paste evaluation JSON and submit
  5. Verify evaluation appears on detail page
  6. Click "Paste/Overwrite Result" button again (now evaluated)
  7. Verify dialog shows warning message about existing evaluation
  8. Verify checkbox appears: "I understand this will overwrite..."
  9. Verify paste button disabled until checkbox checked
  10. Check checkbox and paste NEW evaluation JSON with different scores
  11. Verify success toast and page refresh
  12. Verify evaluation updated with new scores (old scores gone)
  13. Check database to confirm UPDATE not INSERT (same evaluation_id)
  14. Verify dimension_results updated correctly
  15. Test error case: attempt paste without overwrite flag on evaluated answer via API
  16. Verify appropriate error response

* Expected results:
  * Unevaluated answers use normal paste flow (no warnings)
  * Evaluated answers show overwrite warning and require confirmation
  * Checkbox must be checked to enable overwrite
  * Overwrite successfully updates evaluation and dimensions
  * No duplicate evaluation records created
  * Page data refreshes to show updated evaluation
  * Error handling works for invalid overwrite attempts
  * Transaction safety: rollback on error leaves original evaluation intact

## Notes

* Requirements covered: R7, R8
* Audit logging explicitly excluded per spec Open Questions resolution
* Overwrite is destructive: no undo functionality (confirmation mitigates risk)
* Consider adding timestamp to success toast: "Evaluation updated at HH:MM:SS"
* The existing PasteResultDialog component is at: `vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/paste-result-dialog.tsx`
* Dimension results should be replaced, not merged (delete old, insert new)
* Transaction safety critical: evaluation and dimensions must update atomically
