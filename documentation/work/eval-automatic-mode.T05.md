# Ticket: eval-automatic-mode.T05 - New Eval Workflow Frontend

## Source

* Spec: documentation/work/eval-automatic-mode.spec.md
* Patterns: documentation/patterns.md

## Goal

* Replace "Add Answers" button with "New Eval" when automatic mode enabled
* Implement dialog to collect answer_x and answer_y prompts
* Show progress indicator during three-step automatic eval execution
* Handle success and error states gracefully
* Complete end-to-end automatic eval user experience

## Scope

### In scope

* Conditional rendering: "Add Answers" vs "New Eval" button based on experiment.auto_mode_enabled
* "New Eval" dialog component with three sections (main prompt read-only, answer_x textarea, answer_y textarea)
* Progress indicator with steps: "Step 1/3: Generating answer X...", "Step 2/3: Generating answer Y...", "Step 3/3: Running judge evaluation..."
* API call to POST /api/v1/eval/experiments/{experiment_id}/prompts/auto-eval
* Success toast and page refresh on completion
* Error handling with clear error messages
* Loading states during execution

### Out of scope

* Backend API endpoint (T04)
* Auto mode toggle (T03)
* LLM factory or core logic (T02, T04)
* Database schema (T01)

## Dependencies

* Depends on: T03 (auto mode toggle), T04 (backend API)
* Unblocks: none (final ticket)

## Implementation plan

1. Update vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/page.tsx:
   * Fetch experiment detail to get auto_mode_enabled flag
   * Conditionally render "Add Answers" button OR "New Eval" button based on flag
   * When auto_mode_enabled=false, show existing "Add Answers" button
   * When auto_mode_enabled=true, show "New Eval" button
2. Create vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/new-eval-dialog.tsx:
   * Dialog component with three sections
   * Section 1: "Main Prompt" - read-only textarea showing current prompt text
   * Section 2: "Answer X Prompt" - editable textarea for answer_x prompt
   * Section 3: "Answer Y Prompt" - editable textarea for answer_y prompt
   * Submit button disabled until both answer prompts filled
   * Close/Cancel button
3. Implement submit handler with progress states:
   * State machine: idle -> step1 -> step2 -> step3 -> success/error
   * Show loading overlay with current step message
   * "Step 1/3: Generating answer X..." (while API call in progress)
   * "Step 2/3: Generating answer Y..." (backend handles, but UI shows progress)
   * "Step 3/3: Running judge evaluation..." (backend handles, but UI shows progress)
   * Note: Backend executes all steps synchronously, but frontend simulates progress for better UX
4. Call POST /api/v1/eval/experiments/{experimentId}/prompts/auto-eval:
   * Request body with main_prompt_text, answer_x_prompt_text, answer_y_prompt_text
   * Handle response with evaluation_id, answer_id, prompt_group_id
   * Show success toast: "Automatic evaluation completed"
   * Refresh answers list via refetchAnswers()
   * Close dialog
5. Error handling:
   * Catch API errors and show error toast with message
   * Handle network failures gracefully
   * Reset to idle state on error
6. Patterns to apply:
   * Component composition - dialog built from shadcn primitives
   * usePageData hook with useCallback for experiment fetch
   * State management - useState for dialog open/close and progress state
   * Theme awareness - use semantic Tailwind classes
   * Props-in, events-out - dialog receives props and calls onSuccess callback
* Deviations (if any):
   * Progress indicator is simulated in frontend (backend is synchronous), but this improves UX

## Unit tests (required)

* Add tests for:
   * "New Eval" button shown when auto_mode_enabled=true
   * "Add Answers" button shown when auto_mode_enabled=false
   * Dialog opens when "New Eval" clicked
   * Submit button disabled when answer prompts empty
   * Submit button enabled when both answer prompts filled
   * Progress states update during submission
   * Success toast shown on successful eval
   * Error toast shown on API failure
   * Answers list refreshed after success
* Suggested locations:
   * tests/unit/test_new_eval_dialog.tsx (create)
   * tests/unit/test_prompt_detail_auto_mode.tsx (create)
* Mocking/fakes needed:
   * Mock fetch for experiment detail and answers
   * Mock POST /api/v1/eval/experiments/{id}/prompts/auto-eval endpoint
   * Mock useToast hook
   * Mock usePageData hook

## Acceptance criteria (checklist)

* [ ] "New Eval" button shown when auto_mode_enabled=true
* [ ] "Add Answers" button shown when auto_mode_enabled=false
* [ ] New Eval dialog component created
* [ ] Dialog shows main prompt (read-only)
* [ ] Dialog has editable textareas for answer_x and answer_y prompts
* [ ] Submit button disabled until both prompts filled
* [ ] Progress indicator shows steps 1/3, 2/3, 3/3 during execution
* [ ] API call to auto-eval endpoint on submit
* [ ] Success toast shown on completion
* [ ] Error toast shown on failure
* [ ] Answers list refreshed after success
* [ ] Manual workflow unchanged when auto mode disabled
* [ ] Unit tests pass for dialog and button rendering

## Manual verification

* Steps:
  1. Create experiment and enable automatic mode (from T03)
  2. Create a prompt via "Add Prompt" on experiment detail page
  3. Navigate to prompt detail page /eval/[id]/prompts/[promptId]
  4. Verify "New Eval" button shown instead of "Add Answers"
  5. Click "New Eval" button
  6. Verify dialog opens with three sections
  7. Verify main prompt shown read-only
  8. Fill in answer_x prompt: "Provide a concise answer"
  9. Fill in answer_y prompt: "Provide a detailed explanation"
  10. Click Submit
  11. Verify progress indicator shows "Step 1/3: Generating answer X..."
  12. Wait for completion (may take 30-90 seconds)
  13. Verify progress updates through steps 2/3 and 3/3
  14. Verify success toast: "Automatic evaluation completed"
  15. Verify dialog closes
  16. Verify answers table refreshed with new evaluation
  17. Disable automatic mode
  18. Navigate to a prompt detail page
  19. Verify "Add Answers" button shown (not "New Eval")
* Expected results:
  * Button changes based on auto mode status
  * Dialog UX intuitive and clear
  * Progress indicator provides feedback during long wait
  * Automatic eval completes successfully
  * Manual workflow still works when auto mode disabled
  * All UI states handled gracefully

## Notes

* Requirements covered: R6, R7, R8, R9, R9a, R14
* This is the final vertical slice - completes end-to-end automatic eval workflow
* Progress indicator is simulated (frontend shows steps while backend executes synchronously)
* Backend T04 handles actual three-step execution
* Manual workflow must remain unchanged when auto_mode_enabled=false
* Consider timeout handling for very slow LLM responses (show warning after 60s)
