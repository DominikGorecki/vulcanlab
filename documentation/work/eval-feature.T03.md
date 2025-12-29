# Ticket: eval-feature.T03 - Prompt Management and Answer Submission with Blind Assignment

## Source

* Spec: documentation/work/eval-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Enable users to add prompts to experiments and submit answer pairs
* Implement blind evaluation via cryptographic random a/b assignment
* Second vertical slice: add prompts and answers workflow

## Scope

### In scope

* API endpoints: POST /api/v1/eval/experiments/{id}/prompts, GET /api/v1/eval/experiments/{id}/prompts, DELETE /api/v1/eval/prompts/{promptId}, POST /api/v1/eval/prompts/{promptId}/answers, GET /api/v1/eval/prompts/{promptId}/answers
* Core logic for prompt CRUD and answer pair creation with random assignment
* Prompts table on experiment detail page
* Prompt detail page with answer pairs table
* "Add Prompt" input on experiment detail page
* "Add Answers" modal on prompt detail page
* Cryptographic random assignment (secrets module)
* Basic logging for prompt/answer creation

### Out of scope

* Evaluation prompt generation (T04)
* Result submission (T04)
* Delete individual answers (not in spec)
* Batch prompt import

## Dependencies

* Depends on: T01 (models), T02 (experiment pages)
* Unblocks: T04 (evaluation workflow)

## Implementation plan

1. Implement core logic in src/vulcanlab/eval/prompts.py:
   * create_prompt(session, experiment_id, prompt_text) -> ExperimentPrompt
   * get_prompts_by_experiment(session, experiment_id) -> List[ExperimentPrompt]
   * delete_prompt(session, prompt_id) -> None (cascade via DB)
   * Log creation/deletion events
2. Implement core logic in src/vulcanlab/eval/answers.py:
   * create_answer_pair(session, prompt_id, answer_x, answer_y) -> ExperimentAnswer
   * Use secrets.choice([True, False]) for cryptographic random is_x_mapped_to_a
   * get_answers_by_prompt(session, prompt_id) -> List[ExperimentAnswer]
   * Compute answer_a and answer_b based on mapping flag
   * Log creation events
3. Add API endpoints in src/vulcanlab_api/routers/eval.py (or separate prompts.py/answers.py routers)
4. Define Pydantic request/response models for all endpoints
5. Update experiment detail page (vulcanlab_ui/src/app/eval/[id]/page.tsx):
   * Add input field + "Add Prompt" button below metadata section
   * Add DataTable for prompts (columns: prompt_text, eval_count, created_at, delete action)
   * Click row navigates to /eval/[id]/prompts/[promptId]
   * Delete icon per row calls DELETE endpoint with ConfirmDialog
6. Create prompt detail page (vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/page.tsx):
   * StickyDetailHeader with prompt text (truncated if long) and delete button
   * Display full prompt text in a Card
   * "Add Answers" button opens modal
   * DataTable for answer pairs (columns: created_at, has_evaluation status, actions placeholder for T04)
7. Implement "Add Answers" modal:
   * Two textarea fields labeled "Answer X" and "Answer Y"
   * Submit calls POST /api/v1/eval/prompts/{promptId}/answers
   * On success, close modal and refresh answers table
8. Update experiment detail GET endpoint to include prompt_count (computed via SQL count)
9. Patterns to apply:
   * **Three-tier architecture**: Core in vulcanlab/eval/, API in vulcanlab_api/routers/eval/, UI in vulcanlab_ui
   * **Cryptographic randomness**: secrets.choice() for blind assignment
   * **Component composition**: StickyDetailHeader, DataTable, FormField, ConfirmDialog, Dialog (modal)
   * **useModal hook**: For "Add Answers" dialog

## Unit tests (required)

* Add tests for:
  * create_prompt() with valid data returns ExperimentPrompt
  * create_prompt() with empty prompt_text raises ValueError
  * get_prompts_by_experiment() returns prompts for given experiment
  * delete_prompt() removes prompt (mock session)
  * create_answer_pair() generates random is_x_mapped_to_a (test distribution over 100 calls)
  * create_answer_pair() correctly computes answer_a and answer_b based on mapping flag
  * create_answer_pair() with is_x_mapped_to_a=True maps answer_x to answer_a
  * create_answer_pair() with is_x_mapped_to_a=False maps answer_x to answer_b
  * get_answers_by_prompt() returns answers for given prompt
  * Logging calls made on prompt/answer creation and deletion
* Suggested locations:
  * tests/unit/test_eval_prompts.py
  * tests/unit/test_eval_answers.py
  * tests/unit/test_eval_random_assignment.py
* Mocking/fakes needed:
  * Mock SQLAlchemy session
  * Mock secrets.choice() for deterministic testing (use unittest.mock.patch)
  * Mock logging calls

## Acceptance criteria (checklist)

* [ ] User can add prompts to experiment via input field on experiment detail page
* [ ] Prompts appear in table on experiment detail page with eval count (0 initially)
* [ ] User can click prompt row to navigate to prompt detail page
* [ ] User can delete prompts with confirmation dialog (cascade to answers verified)
* [ ] User can click "Add Answers" button and see modal with two textareas
* [ ] User can submit answer pair and see new row in answers table
* [ ] Random assignment generates cryptographically random mapping (verified in tests)
* [ ] Answer pairs correctly map x/y to a/b based on is_x_mapped_to_a flag
* [ ] Experiment detail page shows accurate prompt count
* [ ] All pages follow UI component library patterns and are theme-aware
* [ ] Unit tests achieve >80% coverage for prompt and answer logic

## Manual verification

* Steps:
  1. Navigate to experiment detail page from T02
  2. Enter prompt text: "What is the capital of France?" and click "Add Prompt"
  3. Verify prompt appears in table with eval_count=0
  4. Click prompt row, verify navigation to prompt detail page
  5. Verify full prompt text displayed
  6. Click "Add Answers" button
  7. Enter answer_x: "The capital of France is Paris." and answer_y: "Paris is the capital of France."
  8. Submit, verify modal closes and new row appears in answers table
  9. Add second answer pair to same prompt (verify new random assignment)
  10. Click delete on prompt, verify confirmation dialog, confirm delete
  11. Verify redirect and prompt removed
* Expected results:
  * Prompts and answers created successfully
  * Tables update in real-time after actions
  * Random assignment differs between answer pairs (check DB directly if needed)
  * Delete cascades correctly (answers deleted when prompt deleted)
  * UI responsive and theme-aware

## Notes

* Requirements covered: R3 (add prompts), R4 (view prompts), R6 (add answer pairs with random assignment), R11 (delete prompts with cascade)
* eval_count for prompts computed as count of experiment_answers with has_evaluation=true (defer actual evaluation to T04)
* has_evaluation flag on answers computed as: EXISTS (SELECT 1 FROM experiment_evaluations WHERE answer_id = ...)
* Consider adding character limits or validation for prompt_text and answer fields (e.g., max 10,000 chars)
* Display truncated prompt text in table, full text on detail page
* Answer pairs table on prompt detail page should show created_at and a status badge (e.g., "Pending Evaluation" or "Evaluated")
