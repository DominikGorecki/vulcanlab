# Ticket: eval-automatic-mode.T04 - Automatic Eval Workflow Backend

## Source

* Spec: documentation/work/eval-automatic-mode.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement backend orchestration for automatic evaluation workflow
* Create grouped prompts (main, answer_x, answer_y) with same prompt_group_id
* Execute three LLM calls: generate answer_x, generate answer_y, run judge evaluation
* Handle transaction rollback on failure
* Enable end-to-end automatic eval via API

## Scope

### In scope

* POST /api/v1/eval/experiments/{experiment_id}/prompts/auto-eval endpoint
* Core logic function in vulcanlab.eval for orchestrating automatic eval
* Generate prompt_group_id (max + 1 per experiment)
* Create three ExperimentPrompt records
* Run answer_x and answer_y prompts using answer provider (FULL tier)
* Create ExperimentAnswer with both answers
* Run judge evaluation using judge provider (FULL tier)
* Create ExperimentEvaluation
* Transaction rollback if any step fails
* Unit tests with mocked LLM calls

### Out of scope

* UI components (T05)
* Progress indicator updates (T05)
* LLM factory changes (T02)
* Database schema (T01)
* Auto mode toggle (T03)

## Dependencies

* Depends on: T01 (schema), T02 (LLM factory), T03 (auto mode config)
* Unblocks: T05

## Implementation plan

1. Create src/vulcanlab/eval/auto_eval.py with core orchestration logic:
   * Function `execute_automatic_eval(session, experiment_id, main_prompt_text, answer_x_prompt_text, answer_y_prompt_text) -> dict`
   * Load experiment, validate auto_mode_enabled=true
   * Generate prompt_group_id: query max(prompt_group_id) for experiment and add 1 (default to 1)
   * Create three ExperimentPrompt records with same prompt_group_id
   * Get answer and judge providers from experiment
   * Use create_langchain_chat_for_provider (from T02) to create LLM instances
   * Run answer_x_prompt with answer provider, get answer_x text
   * Run answer_y_prompt with answer provider, get answer_y text
   * Create ExperimentAnswer with randomized blind mapping (existing logic)
   * Generate eval prompt using existing generate_eval_prompt
   * Run eval prompt with judge provider, parse response
   * Submit evaluation using existing submit_evaluation
   * Return evaluation_id, answer_id, prompt_group_id
2. Add POST endpoint in src/vulcanlab_api/routers/eval.py:
   * Route: POST /api/v1/eval/experiments/{experiment_id}/prompts/auto-eval
   * Request schema: main_prompt_text, answer_x_prompt_text, answer_y_prompt_text
   * Response schema: evaluation_id, answer_id, prompt_group_id
   * Call execute_automatic_eval in try/except with session
   * Rollback transaction on failure, raise HTTPException
   * Log each step for observability
3. Add logging for each LLM call with timestamps
4. Handle errors gracefully (LLM API failures, parsing errors, database errors)
5. Patterns to apply:
   * Three-tier architecture - core logic in vulcanlab.eval, thin API layer
   * Session management - pass session explicitly, commit/rollback in API layer
   * Error handling - raise specific exceptions, let global handler catch 500s
   * Transaction pattern - all-or-nothing with rollback on failure
* Deviations (if any):
   * None

## Unit tests (required)

* Add tests for:
   * execute_automatic_eval creates three prompts with same prompt_group_id
   * prompt_group_id is max + 1 for experiment
   * execute_automatic_eval calls answer provider twice (answer_x and answer_y)
   * execute_automatic_eval calls judge provider once
   * execute_automatic_eval creates ExperimentAnswer with both answers
   * execute_automatic_eval creates ExperimentEvaluation
   * execute_automatic_eval returns correct dict with IDs
   * Transaction rollback on LLM failure (no partial state)
   * Transaction rollback on database error
   * POST endpoint returns 400 if auto_mode_enabled=false
   * POST endpoint returns 404 for non-existent experiment
* Suggested locations:
   * tests/unit/test_auto_eval_workflow.py (create)
   * tests/unit/test_api_auto_eval.py (create)
* Mocking/fakes needed:
   * Mock database session and experiment queries
   * Mock create_langchain_chat_for_provider to return fake LLM
   * Mock LLM invoke calls to return fake answers and evaluations
   * Mock existing generate_eval_prompt and submit_evaluation functions

## Acceptance criteria (checklist)

* [ ] execute_automatic_eval function created in vulcanlab.eval.auto_eval
* [ ] Function generates prompt_group_id correctly (max + 1 per experiment)
* [ ] Function creates three ExperimentPrompt records
* [ ] Function uses answer provider for answer_x and answer_y generation
* [ ] Function uses judge provider for evaluation
* [ ] Function always uses FULL tier models
* [ ] Function creates ExperimentAnswer and ExperimentEvaluation
* [ ] POST endpoint created at /api/v1/eval/experiments/{experiment_id}/prompts/auto-eval
* [ ] Transaction rollback on failure (no partial state)
* [ ] Logging includes provider names, model names, and timestamps
* [ ] Unit tests pass for orchestration logic and API endpoint
* [ ] Error handling for LLM failures and database errors

## Manual verification

* Steps:
  1. Enable automatic mode on test experiment with OpenAI as answer provider
  2. Use curl or Postman to POST to /api/v1/eval/experiments/{id}/prompts/auto-eval
  3. Request body: `{"main_prompt_text": "What is 2+2?", "answer_x_prompt_text": "Answer briefly", "answer_y_prompt_text": "Answer in detail"}`
  4. Monitor logs for LLM call timestamps
  5. Query database for three prompts with same prompt_group_id
  6. Verify ExperimentAnswer created with answer_x and answer_y
  7. Verify ExperimentEvaluation created
  8. Check that prompt_group_id is sequential (1, then 2, then 3 for subsequent calls)
  9. Test failure case: disconnect database mid-request, verify rollback
  10. Verify no partial state (no orphaned prompts or answers)
* Expected results:
  * Three prompts created with same prompt_group_id
  * Answer_x and answer_y generated using OpenAI FULL model
  * Evaluation created using Gemini FULL judge model
  * All data persisted correctly
  * Rollback works on failure
  * Logs show provider names and timestamps

## Notes

* Requirements covered: R8, R9, R10, R11, R16
* Synchronous execution - user waits for all three LLM calls
* Uses existing generate_eval_prompt and submit_evaluation functions
* Blind randomization for answer mapping (existing ExperimentAnswer logic)
* prompt_group_id scoped to experiment_id
* All-or-nothing transaction ensures consistency
* Progress updates handled in T05 (frontend)
