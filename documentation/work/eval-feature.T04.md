# Ticket: eval-feature.T04 - Evaluation Prompt Generation and Result Submission

## Source

* Spec: documentation/work/eval-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Enable users to copy generated evaluation prompts and paste JSON results
* Complete the blind evaluation workflow with reverse a/b to x/y mapping
* Third vertical slice: end-to-end evaluation workflow (copy prompt, paste result)

## Scope

### In scope

* API endpoints: GET /api/v1/eval/answers/{answerId}/eval-prompt, POST /api/v1/eval/answers/{answerId}/evaluation, DELETE /api/v1/eval/evaluations/{evalId}
* Core logic for template resolution with {prompt}, {answer_a}, {answer_b} substitutions
* Core logic for JSON parsing, validation, and reverse mapping (a/b to x/y)
* "Copy Eval Prompt" button on answer pairs table
* "Paste Result" button/modal on answer pairs table
* Copy-to-clipboard functionality
* JSON validation with clear error messages
* One evaluation per answer pair (unique constraint enforcement)
* Basic logging for evaluation creation/deletion

### Out of scope

* Template creation UI (defer to T06, use placeholder/hardcoded template for now)
* Statistical analysis (T05)
* Dimension validation against experiment configuration (defer to T06)
* Bulk evaluation submission

## Dependencies

* Depends on: T01 (models), T03 (answers)
* Unblocks: T05 (stats computation)

## Implementation plan

1. Implement template resolution in src/vulcanlab/eval/template_utils.py:
   * resolve_eval_template(template_text, prompt, answer_a, answer_b) -> str
   * Use simple string replacement or existing LangGraph-style templating if available
   * Handle missing placeholders gracefully (log warning)
2. Implement evaluation logic in src/vulcanlab/eval/evaluations.py:
   * generate_eval_prompt(session, answer_id) -> str
     - Fetch answer, prompt, experiment
     - Fetch template (hardcoded placeholder if eval_template_id is null)
     - Compute answer_a and answer_b based on is_x_mapped_to_a
     - Call resolve_eval_template()
   * submit_evaluation(session, answer_id, results: dict, overall_score: int, justification: str) -> ExperimentEvaluation
     - Validate unique constraint (one eval per answer)
     - Validate overall_score in range -10 to 10
     - Create ExperimentEvaluation record
     - Create ExperimentDimensionResult records for each dimension in results dict
     - Validate each dimension score in range -10 to 10
     - No reverse mapping needed here (results already in x/y terms from user perspective)
   * delete_evaluation(session, eval_id) -> None
   * Log creation/deletion events
3. Create Pydantic model for evaluation submission request:
   * EvaluationSubmitRequest(results: dict[str, int], overall_score: int, justification: str)
   * Add validators for score ranges
4. Add API endpoints in src/vulcanlab_api/routers/eval.py
5. Update prompt detail page (vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/page.tsx):
   * Add "Copy Eval Prompt" button/icon to each answer row in table
   * Add "Paste Result" button/icon to each answer row
   * Use navigator.clipboard.writeText() for copy functionality
   * Show success toast on copy
6. Implement "Paste Result" modal:
   * Single textarea for JSON input
   * Submit button calls POST /api/v1/eval/answers/{answerId}/evaluation
   * Parse JSON client-side first for immediate feedback
   * On success, close modal and update answer row to show "Evaluated" status
   * On error, display validation errors inline
7. Update answer row display:
   * Show status badge: "Pending" (no eval) or "Evaluated" (has eval)
   * Disable "Copy" and "Paste" buttons if evaluation already exists
   * Add delete evaluation button (trash icon) if evaluation exists
8. Add delete evaluation confirmation dialog
9. Use hardcoded placeholder template for now (T06 will integrate with template management):
   * Placeholder: "Evaluate the following answers to the prompt:\n\nPrompt: {prompt}\n\nAnswer A: {answer_a}\n\nAnswer B: {answer_b}\n\nProvide scores as JSON..."
10. Patterns to apply:
    * **Template resolution**: Reuse existing templating utilities if available, otherwise simple string.replace()
    * **JSON validation**: Use Pydantic models for type safety
    * **Component composition**: Dialog, FormField, StatusBadge, ConfirmDialog
    * **Error handling**: Raise HTTPException with clear messages for validation failures

## Unit tests (required)

* Add tests for:
  * resolve_eval_template() with valid placeholders returns correctly substituted string
  * resolve_eval_template() with missing placeholders logs warning and handles gracefully
  * generate_eval_prompt() with valid answer_id returns resolved template
  * generate_eval_prompt() correctly maps answer_x to answer_a when is_x_mapped_to_a=True
  * generate_eval_prompt() correctly maps answer_x to answer_b when is_x_mapped_to_a=False
  * submit_evaluation() with valid data creates evaluation and dimension results
  * submit_evaluation() with invalid overall_score (<-10 or >10) raises ValueError
  * submit_evaluation() with invalid dimension score raises ValueError
  * submit_evaluation() when evaluation already exists raises unique constraint error
  * submit_evaluation() creates correct number of dimension result records
  * delete_evaluation() removes evaluation (mock session)
  * Logging calls made on evaluation creation/deletion
* Suggested locations:
  * tests/unit/test_eval_template_resolution.py
  * tests/unit/test_eval_evaluations.py
  * tests/unit/test_eval_json_validation.py
* Mocking/fakes needed:
  * Mock SQLAlchemy session
  * Mock template fetching (hardcoded template string)
  * Mock logging calls

## Acceptance criteria (checklist)

* [ ] User can click "Copy Eval Prompt" and prompt copied to clipboard
* [ ] Copied prompt contains correct substitutions for {prompt}, {answer_a}, {answer_b}
* [ ] User can click "Paste Result" and see modal with textarea
* [ ] User can paste valid JSON and submit successfully
* [ ] Invalid JSON shows clear validation error message
* [ ] Scores outside -10 to 10 range rejected with error
* [ ] Second evaluation submission for same answer pair rejected (unique constraint)
* [ ] Answer row updates to "Evaluated" status after successful submission
* [ ] User can delete evaluation with confirmation dialog
* [ ] All pages follow UI component library patterns and are theme-aware
* [ ] Unit tests achieve >80% coverage for evaluation logic

## Manual verification

* Steps:
  1. Navigate to prompt detail page with answer pair from T03
  2. Click "Copy Eval Prompt" button
  3. Verify toast notification "Copied to clipboard"
  4. Paste into text editor, verify prompt contains actual prompt text and answer_a/answer_b
  5. Manually create JSON result:
     ```json
     {
       "factual_correctness": 5,
       "completeness": 3,
       "coherence": 1,
       "hallucination_risk": 0,
       "academic_response": -2,
       "overall_score": 2,
       "justification": "Answer A is moderately better on factual correctness."
     }
     ```
  6. Click "Paste Result" button, paste JSON into modal
  7. Submit, verify modal closes and row updates to "Evaluated"
  8. Attempt to paste second result for same answer, verify error message
  9. Click delete evaluation icon, confirm dialog, verify row returns to "Pending"
  10. Test with invalid JSON (missing field, wrong type, score out of range), verify error messages
* Expected results:
  * Copy-to-clipboard works in browser
  * Template substitution correct
  * JSON parsing and validation works
  * Unique constraint enforced
  * UI updates reflect evaluation state changes
  * Error messages clear and helpful

## Notes

* Requirements covered: R7 (copy eval prompt), R8 (paste results with mapping), R15 (overall_score and justification)
* Reverse mapping (a/b to x/y) happens implicitly: the JSON structure uses dimension names, which are stored denormalized in experiment_dimension_results
* The spec mentions reverse mapping, but since dimensions are stored by name (not as "a" or "b"), the mapping is transparent to this ticket
* For now, eval_template_id will be null and we use a hardcoded placeholder template
* T06 will add proper template selection and fetching
* Consider adding a "View Evaluation" button to show submitted results in a readonly modal
* Clipboard API requires HTTPS or localhost for security
* Add unit test for JSON with extra dimensions (should store all, defer validation to T06)
