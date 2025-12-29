# Title: Eval Feature - LLM Response Comparison and Evaluation System

## Summary

* Build a standalone evaluation system for comparing two LLM-generated answers across multiple criteria using a judge LLM
* Enable users to create experiments, add test prompts, submit answer pairs (x vs y), and evaluate them blindly (randomized to a vs b)
* Store dimension-based comparison scores (-10 to +10 scale) with justifications and compute aggregate statistics
* Support customizable evaluation templates and dimensions following existing prompt template patterns
* Provide full CRUD capabilities with cascade deletion for experiments, prompts, and evaluations

## Problem / Context

* Currently, there is no systematic way within VulcanLab to compare different LLM responses or RAG configurations
* Engineers and researchers need to run controlled experiments to evaluate model performance, prompting strategies, or retrieval quality
* Manual comparison is time-consuming, inconsistent, and lacks statistical rigor
* User impact: Teams cannot make data-driven decisions about which models, prompts, or RAG approaches perform better
* Business impact: Lack of evaluation infrastructure slows down iteration cycles and prevents quantitative optimization

## Goals

* Provide a self-contained evaluation workflow: create experiment → add test prompts → submit answer pairs → evaluate blindly → view aggregated results
* Support flexible dimension-based scoring with user-defined criteria
* Enable blind evaluation through randomized answer assignment (a/b mapping)
* Compute statistical comparisons (win rates, mean/median scores, Wilcoxon signed-rank test)
* Integrate with existing prompt template system for evaluation prompt management
* Maintain complete audit trail with full deletion capabilities

## Non-goals (Strict)

* No integration with the existing corpus/works/chunks data models (eval data is standalone)
* No automated execution of LLM evaluations (users manually copy prompts and paste results)
* No batch import/export of evaluation data (manual entry only in this version)
* No version control or history tracking for experiments or templates
* No user authentication or authorization (open to all application users)
* No real-time collaboration features (concurrent editing, live updates)
* No integration with external experiment tracking platforms (MLflow, Weights & Biases, etc.)

## Scope

### In scope

* Four new UI pages: Eval home, New Experiment, Experiment detail, Experiment Prompt detail
* Database schema for experiments, prompts, answer pairs, evaluations, dimensions, and results
* Template management using existing Settings → Templates pattern
* Dimension customization per experiment (add/remove/rename scoring criteria)
* Blind evaluation workflow with random a/b assignment per answer-pair submission
* Statistical analysis: win rate, mean, median, tie percentage, harm rate, Wilcoxon signed-rank test
* Copy-to-clipboard for generated evaluation prompts (using template + answer_a/answer_b substitution)
* Paste-and-parse for JSON evaluation results with reverse mapping (a/b → x/y)
* Full cascade deletion for experiments, prompts, and individual evaluations
* Basic logging for creation events

### Out of scope

* Authentication/authorization checks
* Bulk operations (batch upload of prompts or results)
* Export to CSV/JSON/PDF
* Visualization of score distributions (charts/graphs)
* Comparison across multiple experiments
* Integration with LLM APIs for automated evaluation
* Caching or denormalization of aggregate statistics

## Requirements (Functional)

* R1: User can create a new experiment with: name, answer_x description, answer_y description, model_x name, model_y name, judge model name, eval_template selection, and custom dimensions
* R2: User can view a list of all experiments with ability to click into experiment details
* R3: User can add test prompts to an experiment via text input
* R4: User can view all prompts within an experiment in a table
* R5: User can click into a specific prompt to see its evaluations
* R6: User can add answer pairs (answer_x and answer_y) to a prompt, which are randomly assigned to answer_a or answer_b
* R7: User can copy the generated evaluation prompt (template resolved with {prompt}, {answer_a}, {answer_b} substitutions)
* R8: User can paste JSON evaluation results, which are parsed and mapped back to x/y based on stored a/b assignment
* R9: System computes and displays aggregate statistics on experiment page: X win rate P(score > 0), mean score, median score, tie percentage, harm rate P(score < 0)
* R10: System performs Wilcoxon signed-rank test on overall_score deltas when N > 1 for a prompt
* R11: User can delete experiments (cascade delete all prompts and evaluations), delete prompts (cascade delete evaluations), or delete individual evaluations
* R12: Evaluation templates can be created, edited, and selected using existing Settings → Templates UI pattern
* R13: Each experiment stores dimension configuration (list of dimension names); default dimensions are: factual_correctness, completeness, coherence, hallucination_risk, academic_response
* R14: Dimension results are integers from -10 to +10 following the scoring scale (+10 = X much better, 0 = tie, -10 = Y much better)
* R15: All evaluations include overall_score and justification fields in addition to custom dimensions

## Requirements (Non-functional)

* Performance:
  * Aggregate statistics computed live on page load; queries must complete within 2 seconds for experiments with up to 1000 prompts
  * JSON parsing for pasted results must provide immediate feedback on validation errors
* Reliability:
  * Database transactions must ensure atomicity for cascade deletions
  * Random a/b assignment must be cryptographically random (not predictable)
  * JSON schema validation must prevent partial writes on malformed eval results
* Security / Privacy:
  * No auth required (per requirements), but application assumes trusted internal users
  * Input sanitization for all text fields to prevent XSS
  * No PII or sensitive data expected in eval content
* Observability:
  * Log creation events: experiment created, prompt added, evaluation submitted
  * Log deletion events with experiment/prompt/eval IDs
  * No execution tracking or performance metrics for eval workflow

## Proposed Solution (High-level)

* Extend database schema with new tables: `experiments`, `experiment_prompts`, `experiment_answers`, `experiment_evaluations`, `experiment_dimensions`, `experiment_dimension_results`
* Create four new Next.js pages in `vulcanlab_ui/src/app/eval/`: home (list), new (form), `[id]` (experiment detail), `[id]/prompts/[promptId]` (prompt detail)
* Add API routers in `src/vulcanlab_api/routers/eval/` for CRUD operations on all entities
* Implement core logic in `src/vulcanlab/eval/` for: dimension management, random assignment, statistical computation, prompt template resolution
* Reuse existing template management UI (Settings → Templates) by adding new template type `eval_template`
* Store a/b → x/y mapping in `experiment_answers` table with random boolean flag (`is_x_mapped_to_a`)
* Compute statistics using SQL aggregations for counts/averages and Python scipy for Wilcoxon test

## Interfaces / APIs / Contracts

* `POST /api/v1/eval/experiments` - Create experiment
  * Request: `{name, description_x, description_y, model_x, model_y, judge_model, eval_template_id, dimensions: string[]}`
  * Response: `{id, ...created experiment}`
* `GET /api/v1/eval/experiments` - List all experiments
  * Response: `{experiments: [{id, name, created_at, prompt_count, eval_count}]}`
* `GET /api/v1/eval/experiments/{id}` - Get experiment details with statistics
  * Response: `{experiment: {...}, stats: {x_win_rate, mean_score, median_score, tie_pct, harm_rate, wilcoxon_p}}`
* `POST /api/v1/eval/experiments/{id}/prompts` - Add prompt to experiment
  * Request: `{prompt_text: string}`
  * Response: `{id, prompt_text, experiment_id}`
* `GET /api/v1/eval/experiments/{id}/prompts` - List prompts for experiment
  * Response: `{prompts: [{id, prompt_text, eval_count}]}`
* `POST /api/v1/eval/prompts/{promptId}/answers` - Add answer pair
  * Request: `{answer_x: string, answer_y: string}`
  * Response: `{id, is_x_mapped_to_a: bool, answer_a: string, answer_b: string}`
* `GET /api/v1/eval/prompts/{promptId}/answers` - List answer pairs for prompt
  * Response: `{answers: [{id, created_at, has_evaluation}]}`
* `GET /api/v1/eval/answers/{answerId}/eval-prompt` - Generate eval prompt
  * Response: `{prompt: string}` (resolved template with substitutions)
* `POST /api/v1/eval/answers/{answerId}/evaluation` - Submit evaluation result
  * Request: `{results: {dimension_name: score, ...}, overall_score: int, justification: string}`
  * Response: `{id, evaluation: {...}}`
* `DELETE /api/v1/eval/experiments/{id}` - Delete experiment (cascade)
* `DELETE /api/v1/eval/prompts/{promptId}` - Delete prompt (cascade)
* `DELETE /api/v1/eval/evaluations/{evalId}` - Delete single evaluation

## Data Model / Storage

**New Tables:**

* `experiments`
  * `id` (PK, UUID)
  * `name` (TEXT, NOT NULL)
  * `description_x` (TEXT)
  * `description_y` (TEXT)
  * `model_x` (TEXT)
  * `model_y` (TEXT)
  * `judge_model` (TEXT)
  * `eval_template_id` (FK to templates table, nullable if templates table doesn't enforce FK)
  * `created_at` (TIMESTAMP)
  * `updated_at` (TIMESTAMP)

* `experiment_dimensions`
  * `id` (PK, UUID)
  * `experiment_id` (FK experiments, ON DELETE CASCADE)
  * `dimension_name` (TEXT, NOT NULL)
  * `display_order` (INT)
  * Unique constraint on (experiment_id, dimension_name)

* `experiment_prompts`
  * `id` (PK, UUID)
  * `experiment_id` (FK experiments, ON DELETE CASCADE)
  * `prompt_text` (TEXT, NOT NULL)
  * `created_at` (TIMESTAMP)

* `experiment_answers`
  * `id` (PK, UUID)
  * `prompt_id` (FK experiment_prompts, ON DELETE CASCADE)
  * `answer_x` (TEXT, NOT NULL)
  * `answer_y` (TEXT, NOT NULL)
  * `is_x_mapped_to_a` (BOOLEAN, NOT NULL) -- random assignment
  * `created_at` (TIMESTAMP)

* `experiment_evaluations`
  * `id` (PK, UUID)
  * `answer_id` (FK experiment_answers, ON DELETE CASCADE)
  * `overall_score` (INT, NOT NULL, CHECK -10 to 10)
  * `justification` (TEXT)
  * `created_at` (TIMESTAMP)
  * Unique constraint on (answer_id) -- one eval per answer pair

* `experiment_dimension_results`
  * `id` (PK, UUID)
  * `evaluation_id` (FK experiment_evaluations, ON DELETE CASCADE)
  * `dimension_name` (TEXT, NOT NULL) -- denormalized from experiment_dimensions for query simplicity
  * `score` (INT, NOT NULL, CHECK -10 to 10)

**Indexes:**
* `experiment_prompts.experiment_id`
* `experiment_answers.prompt_id`
* `experiment_evaluations.answer_id`
* `experiment_dimension_results.evaluation_id`

**Migration:** Create migration script to add all tables with CASCADE constraints

## UX / Workflows

**Workflow 1: Create Experiment**
1. Navigate to /eval (new left nav link)
2. Click "New Experiment" button → /eval/new
3. Fill form: name, descriptions, model names, select eval_template from dropdown
4. Add/remove/rename dimensions in a simple list UI (text inputs with add/remove buttons)
5. Submit → redirects to /eval/{id}

**Workflow 2: Add Prompts and Evaluate**
1. On /eval/{id} page, see experiment metadata and stats (empty initially)
2. Input prompt text in field, click "Add Prompt" → prompt appears in table below
3. Click prompt row → /eval/{id}/prompts/{promptId}
4. On prompt detail page, click "Add Answers" → modal with two textareas (answer_x, answer_y)
5. Submit answers → new row appears in "Evaluations" table with "Copy Eval Prompt" button
6. Click "Copy Eval Prompt" → resolved template copied to clipboard
7. Paste into external LLM interface, get JSON response
8. Click "Paste Result" → modal with textarea, paste JSON, click submit
9. System parses JSON, maps a/b → x/y, stores results
10. Table row updates to show evaluation is complete

**Workflow 3: View Results**
1. On /eval/{id} page, stats section shows aggregated metrics
2. Stats include: X win rate (%), mean score, median score, tie %, harm rate (%), Wilcoxon p-value (if applicable)
3. Prompts table shows eval count per prompt
4. Click prompt → see individual evaluations with scores per dimension
5. Click "View All Results" (optional button) → table of all evaluations for that prompt

**Workflow 4: Delete Data**
1. On experiment page: "Delete Experiment" button (with confirmation dialog) → cascade deletes all
2. On prompts table: delete icon per row → cascade deletes evaluations
3. On prompt detail page: delete icon per evaluation row → deletes single eval

## Testing Plan

* Unit tests:
  * `test_eval_dimension_crud.py`: Create, read, update, delete dimensions for an experiment
  * `test_eval_random_assignment.py`: Verify random a/b assignment and reverse mapping
  * `test_eval_stats_computation.py`: Mock data with known scores, verify win rate, mean, median, tie %, harm rate calculations
  * `test_eval_wilcoxon.py`: Mock multiple evaluations per prompt, verify Wilcoxon signed-rank test computation
  * `test_eval_template_resolution.py`: Mock template with {prompt}, {answer_a}, {answer_b}, verify substitution
  * `test_eval_json_validation.py`: Valid and invalid JSON inputs for pasted results
  * `test_eval_cascade_delete.py`: Mock DB session, verify cascade deletes propagate correctly
* Integration tests:
  * Not required unless explicitly requested
* Manual test plan:
  * Create experiment with 3 custom dimensions, verify stored correctly
  * Add 5 prompts to experiment, verify table displays
  * Add 2 answer pairs to one prompt, verify random assignment differs
  * Copy eval prompt, verify {prompt}, {answer_a}, {answer_b} are substituted
  * Paste valid JSON result, verify scores stored and mapped correctly
  * Paste invalid JSON, verify error message shown
  * Add 10 evaluations across 5 prompts, verify stats compute correctly
  * Delete one evaluation, verify stats update
  * Delete one prompt, verify evaluations gone
  * Delete experiment, verify all related data gone
  * Verify dark/light mode theme compatibility on all pages

## Acceptance Criteria (Checklist)

* [ ] User can create a new experiment with custom dimensions via UI form
* [ ] Experiments list page shows all experiments with creation date and counts
* [ ] User can add prompts to an experiment and see them in a table
* [ ] User can add answer pairs to a prompt with blind random a/b assignment
* [ ] Copy button generates eval prompt with correct template substitutions
* [ ] Paste button accepts JSON, validates, and stores results mapped to x/y
* [ ] Experiment detail page displays: X win rate, mean score, median score, tie %, harm rate
* [ ] Wilcoxon signed-rank test p-value displayed when N > 1 evaluations per prompt
* [ ] User can delete experiments, prompts, or evaluations with cascade behavior
* [ ] Evaluation templates managed via Settings → Templates with type filter for eval_template
* [ ] All dimension scores constrained to -10 to +10 range
* [ ] overall_score and justification fields always included in eval results
* [ ] Basic logging for creation and deletion events
* [ ] All pages follow UI component library patterns (PageHeader, DataTable, FormField, etc.)
* [ ] All pages are theme-aware (dark/light mode)
* [ ] Unit tests achieve >80% coverage for core eval logic

## Rollout / Migration Plan

* Create database migration script with all new tables and indexes
* Run migration on dev environment, verify schema
* Deploy API changes (new routers) without breaking existing routes
* Deploy frontend changes (new pages accessible via /eval path)
* Add "Eval" link to left navigation in UI
* Document eval workflow in internal wiki or README
* No data migration required (new feature, no existing data)

## Risks and Alternatives

* Risks:
  * Manual copy/paste workflow prone to user error (pasting wrong JSON, mapping confusion)
  * No validation that pasted JSON matches the experiment's dimension configuration (could store extra or missing dimensions)
  * Computing stats live on every page load may become slow with large datasets (mitigated by initial limit of 1000 prompts)
  * Wilcoxon test requires scipy dependency (verify already in requirements)
  * Random assignment could theoretically collide (very low probability with crypto random)
* Alternatives considered:
  * Automated LLM evaluation: Would require API key management, cost tracking, error handling → deferred to future
  * Batch import via CSV: Would require file upload, parsing, validation → deferred to future
  * Pre-configured templates in code: Less flexible for users, but simpler implementation → rejected in favor of UI management
  * Caching aggregate stats: Better performance, but adds complexity and stale data risk → deferred, start with live computation
  * Soft deletion for audit trail: More complex queries, storage overhead → rejected in favor of full deletion for simplicity

## Patterns and Standards Alignment (from documentation/patterns.md)

* Patterns applied:
  * **Three-tier architecture**: Core logic in `src/vulcanlab/eval/`, API in `src/vulcanlab_api/routers/eval/`, UI in `vulcanlab_ui/src/app/eval/`
  * **Database session management**: Pass sessions explicitly to core functions (`def compute_stats(experiment_id: int, session: Session)`)
  * **API versioning**: All routes prefixed `/api/v1/eval/`
  * **Global exception handling**: Raise HTTPException for validation errors, let global handler catch unhandled exceptions
  * **UI Page Lifecycle Pattern**: Use `usePageData` hook with `useCallback` for fetch functions to avoid infinite loops
  * **Component composition**: Use `PageHeader`, `DataTable`, `FormField`, `ConfirmDialog` for standard UI elements
  * **Theme awareness**: All UI components use Tailwind semantic classes (`text-foreground`, `bg-card`)
  * **Testing strategy**: Unit tests in `tests/unit/test_eval_*.py` with mocked DB sessions, no real DB connections
* Deviations (if any):
  * None - this feature fully aligns with existing patterns

## Implementation Notes (Non-binding)

* Reuse existing `templates` table if it supports type filtering (add `template_type` column if not present); otherwise create separate `eval_templates` table
* Use `secrets.randbelow(2)` or `secrets.choice([True, False])` for cryptographic random a/b assignment
* For Wilcoxon test: `from scipy.stats import wilcoxon; statistic, p_value = wilcoxon(deltas)`
* Template resolution can reuse existing LangGraph-style templating if available in `vulcanlab.utils` or implement simple string replacement
* Consider adding `eval_count` as computed column or query annotation for performance on prompts list
* JSON validation: Use Pydantic model for eval result schema to ensure type safety and clear error messages
* UI modals for "Add Answers" and "Paste Result": Use existing `useModal` hook and `Dialog` component from Shadcn
* Stats computation: Write SQL query using SQLAlchemy aggregates (`func.count`, `func.avg`, `func.percentile_cont`) for efficiency
* Left nav: Add new entry in `vulcanlab_ui/src/components/nav.tsx` or equivalent nav component file

## Open Questions

* Q1: Does the existing `templates` table support a `template_type` or `category` column for filtering eval templates, or should we create a separate table?
* Q2: Should dimension display_order be user-configurable via drag-and-drop UI, or is insertion order sufficient?
* Q3: For experiments with multiple evaluations per prompt (N > 1), should we display individual eval results in a sub-table or aggregated view?
* Q4: Should the "Copy Eval Prompt" button support multiple formats (plain text, JSON, markdown), or is plain text sufficient?
* Q5: Is there an existing logging utility in `vulcanlab.utils` for structured logging, or should we use Python's standard logging module?
