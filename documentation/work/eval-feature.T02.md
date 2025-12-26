# Ticket: eval-feature.T02 - Experiment CRUD and List/Detail Pages

## Source

* Spec: documentation/work/eval-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Enable users to create new experiments and view experiment list and detail pages
* First vertical slice: complete create-and-view workflow for experiments
* Implement API endpoints and UI pages following three-tier architecture

## Scope

### In scope

* API endpoints: POST /api/v1/eval/experiments, GET /api/v1/eval/experiments, GET /api/v1/eval/experiments/{id}, DELETE /api/v1/eval/experiments/{id}
* Core logic in src/vulcanlab/eval/ for experiment CRUD operations
* UI pages: /eval (list), /eval/new (create form), /eval/[id] (detail)
* Basic experiment metadata display (no stats yet, defer to T05)
* Form validation and error handling
* Left nav link to /eval
* Confirmation dialog for delete with cascade warning
* Basic logging for create/delete events

### Out of scope

* Dimension management UI (defer to T06)
* Prompt/answer/evaluation functionality (T03, T04)
* Statistical analysis (T05)
* Template selection dropdown (T06)
* Bulk operations or export

## Dependencies

* Depends on: T01 (database models)
* Unblocks: T03, T05, T06

## Implementation plan

1. Create src/vulcanlab/eval/ module with __init__.py
2. Implement core logic functions in src/vulcanlab/eval/experiments.py:
   * create_experiment(session, name, description_x, description_y, model_x, model_y, judge_model, eval_template_id=None) -> Experiment
   * get_experiments(session) -> List[Experiment]
   * get_experiment_by_id(session, experiment_id) -> Experiment
   * delete_experiment(session, experiment_id) -> None (cascade delete via DB)
3. Add basic logging using Python logging module for create/delete events
4. Create src/vulcanlab_api/routers/eval.py (or eval/ folder with experiments.py router)
5. Implement API endpoints with request/response Pydantic models
6. Add router to main.py with prefix="/api/v1/eval"
7. Create vulcanlab_ui/src/app/eval/page.tsx (list page):
   * Use usePageData hook with useCallback for fetch
   * PageHeader with "New Experiment" button
   * DataTable showing experiments (columns: name, created_at, placeholder for prompt_count/eval_count)
   * StatusBadge for experiment state (if applicable)
   * Click row to navigate to /eval/[id]
8. Create vulcanlab_ui/src/app/eval/new/page.tsx (form page):
   * FormField components for name, description_x, description_y, model_x, model_y, judge_model
   * Use react-hook-form for validation
   * Submit button calls POST /api/v1/eval/experiments
   * On success, redirect to /eval/[id]
9. Create vulcanlab_ui/src/app/eval/[id]/page.tsx (detail page):
   * StickyDetailHeader with experiment name and delete button
   * Display experiment metadata (descriptions, models)
   * Empty state for prompts (defer table to T03)
   * Placeholder for stats section (defer to T05)
   * Delete button opens ConfirmDialog with cascade warning
10. Add "Eval" link to left navigation (vulcanlab_ui/src/components/nav.tsx or equivalent)
11. Patterns to apply:
    * **Three-tier architecture**: Core logic in vulcanlab/eval/, API in vulcanlab_api/routers/eval/, UI in vulcanlab_ui/src/app/eval/
    * **Database session management**: Pass session explicitly to core functions
    * **API versioning**: /api/v1/eval/ prefix
    * **Global exception handling**: Raise HTTPException for validation errors
    * **UI Page Lifecycle Pattern**: usePageData + useCallback
    * **Component composition**: PageHeader, DataTable, FormField, ConfirmDialog, StickyDetailHeader
    * **Theme awareness**: Tailwind semantic classes

## Unit tests (required)

* Add tests for:
  * create_experiment() with valid data returns Experiment object
  * create_experiment() with missing required fields raises ValueError
  * get_experiments() returns list of experiments
  * get_experiment_by_id() with valid ID returns experiment
  * get_experiment_by_id() with invalid ID raises exception
  * delete_experiment() removes experiment (verify via mock session.delete call)
  * Logging calls made on create and delete
  * API request/response validation (Pydantic models)
* Suggested locations:
  * tests/unit/test_eval_experiments.py
  * tests/unit/test_eval_api_experiments.py
* Mocking/fakes needed:
  * Mock SQLAlchemy session
  * Mock logging calls
  * Mock HTTP client for API tests (if testing FastAPI endpoints directly)

## Acceptance criteria (checklist)

* [ ] User can navigate to /eval and see list of experiments
* [ ] User can click "New Experiment" and fill form with all required fields
* [ ] User can submit form and be redirected to experiment detail page
* [ ] User can view experiment detail page with metadata
* [ ] User can delete experiment with confirmation dialog
* [ ] Delete cascades to prompts/evaluations (verified manually in T01)
* [ ] Left nav contains "Eval" link
* [ ] All pages follow UI component library patterns
* [ ] All pages are theme-aware (dark/light mode)
* [ ] Unit tests achieve >80% coverage for core experiment logic
* [ ] Basic logging for create/delete events verified in tests

## Manual verification

* Steps:
  1. Navigate to /eval, verify empty state or existing experiments shown
  2. Click "New Experiment" button
  3. Fill form: name="Test Experiment", description_x="GPT-4 answers", description_y="Claude answers", model_x="gpt-4", model_y="claude-sonnet-3.5", judge_model="gpt-4o"
  4. Submit form, verify redirect to /eval/{id}
  5. Verify experiment detail page displays all metadata correctly
  6. Click delete button, verify confirmation dialog appears
  7. Confirm delete, verify redirect to /eval list
  8. Verify experiment removed from list
  9. Test dark/light mode toggle, verify theme changes apply
* Expected results:
  * Form validation works (required fields, error messages)
  * Success/error toasts appear appropriately
  * Navigation flows correctly
  * Delete confirmation prevents accidental deletion
  * UI is responsive and theme-aware

## Notes

* Requirements covered: R1 (create experiment - partial, dimensions deferred to T06), R2 (list experiments), R11 (delete experiment)
* Template selection dropdown deferred to T06 (eval_template_id will be null for now)
* Dimension configuration UI deferred to T06 (dimensions field not in form yet)
* Prompt count and eval count columns will show 0 until T03/T04 implemented
* Stats section on detail page will be empty placeholder until T05
* Consider adding a "last updated" timestamp display on list and detail pages
* Use existing error handling patterns from other routers (e.g., rag_config.py, templates.py)
