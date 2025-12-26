# Ticket: eval-feature.T06 - Template Integration and Dimension Management

## Source

* Spec: documentation/work/eval-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Integrate eval feature with existing prompt template system
* Enable dimension customization per experiment (add/remove/rename)
* Complete the eval feature with full template and dimension management
* Final vertical slice: full customization capabilities

## Scope

### In scope

* Template type filter: add template_type or category column to templates table (or create separate eval_templates table)
* Template selection dropdown on New Experiment form
* Template CRUD via existing Settings → Templates UI with type filter
* Dimension management UI on New Experiment form: add, remove, rename dimensions
* Default dimensions pre-populated: factual_correctness, completeness, coherence, hallucination_risk, academic_response
* Validation: pasted JSON must include all experiment dimensions (warn if extra, error if missing)
* Update template resolution in T04 to fetch from templates table
* Display dimensions on experiment detail page

### Out of scope

* Drag-and-drop reordering of dimensions (use insertion order)
* Dimension descriptions or metadata (just names)
* Template versioning or history
* Template preview or testing UI
* Dimension value constraints beyond -10 to 10 range

## Dependencies

* Depends on: T01 (models), T02 (experiment form), T04 (template resolution)
* Unblocks: none (final ticket)

## Implementation plan

1. Investigate existing templates table structure (read src/vulcanlab/data/models/prompt_template.py):
   * If template_type or category column exists, use it
   * If not, add migration to add template_type column (VARCHAR, nullable, default 'prompt')
   * Add index on template_type if adding column
2. Update template model and API to support type filtering:
   * Modify GET /api/v1/templates to accept optional type query parameter
   * Return only templates with template_type='eval_template' when filtered
3. Create default eval template in migration or seed script:
   * Name: "Default Evaluation Template"
   * Type: "eval_template"
   * Content: Full prompt with instructions, JSON schema, and placeholders for {prompt}, {answer_a}, {answer_b}
   * Example content (adapt to match LangGraph style if needed):
     ```
     You are an expert evaluator comparing two answers to a question.

     Question: {prompt}

     Answer A: {answer_a}

     Answer B: {answer_b}

     Evaluate the answers on the following dimensions. For each dimension, provide a score from -10 to 10:
     - +10 = Answer A is much better
     - +5 = Answer A is moderately better
     - +1 = Answer A is slightly better
     - 0 = No meaningful difference
     - -1 = Answer B is slightly better
     - -5 = Answer B is moderately better
     - -10 = Answer B is much better

     Provide your evaluation as JSON with the following structure:
     {
       "factual_correctness": <int>,
       "completeness": <int>,
       "coherence": <int>,
       "hallucination_risk": <int>,
       "academic_response": <int>,
       "overall_score": <int>,
       "justification": "Concise explanation referencing specific differences"
     }
     ```
4. Implement dimension management logic in src/vulcanlab/eval/dimensions.py:
   * create_dimensions(session, experiment_id, dimension_names: List[str]) -> List[ExperimentDimension]
   * get_dimensions_by_experiment(session, experiment_id) -> List[ExperimentDimension]
   * validate_evaluation_dimensions(experiment_dimensions: List[str], result_dimensions: List[str]) -> ValidationResult
     - Error if required dimensions missing
     - Warning if extra dimensions present (but allow storage)
5. Update create_experiment() in src/vulcanlab/eval/experiments.py to accept dimensions parameter and call create_dimensions()
6. Update New Experiment form (vulcanlab_ui/src/app/eval/new/page.tsx):
   * Add template selection dropdown (fetch from GET /api/v1/templates?type=eval_template)
   * Add dimension management section:
     - Display list of dimension inputs (initially 5 defaults)
     - Each row: text input for dimension name + remove button
     - "Add Dimension" button to add new row
     - Validate: no duplicate names, no empty names
   * On submit, include eval_template_id and dimensions array in request
7. Update experiment detail page to display dimensions:
   * Add Card or section showing list of dimensions for the experiment
   * Read-only display (no editing after creation)
8. Update submit_evaluation() in src/vulcanlab/eval/evaluations.py:
   * Fetch experiment dimensions before saving
   * Call validate_evaluation_dimensions()
   * If validation fails, raise HTTPException with clear error message
   * Log warning if extra dimensions present
9. Update template resolution in T04 (src/vulcanlab/eval/template_utils.py):
   * Fetch template by eval_template_id from templates table
   * If eval_template_id is null, use default template (fetch by name or hardcoded fallback)
10. Update Settings → Templates page to show template type filter (if not already present):
    * Add dropdown or tabs to filter by template type
    * Default view shows all types
11. Patterns to apply:
    * **Template management**: Reuse existing Settings → Templates patterns
    * **Form validation**: react-hook-form with custom validators for dimension uniqueness
    * **Dynamic form fields**: Add/remove dimension inputs with React state

## Unit tests (required)

* Add tests for:
  * create_dimensions() with valid names creates ExperimentDimension records
  * create_dimensions() with duplicate names raises ValueError
  * get_dimensions_by_experiment() returns dimensions in display_order
  * validate_evaluation_dimensions() with matching dimensions passes
  * validate_evaluation_dimensions() with missing required dimension returns error
  * validate_evaluation_dimensions() with extra dimensions returns warning
  * Template fetching by type returns only eval templates
  * Default template exists and contains required placeholders
  * Template resolution uses experiment's eval_template_id
  * Template resolution falls back to default if eval_template_id is null
* Suggested locations:
  * tests/unit/test_eval_dimension_crud.py
  * tests/unit/test_eval_template_integration.py
* Mocking/fakes needed:
  * Mock SQLAlchemy session
  * Mock template table queries

## Acceptance criteria (checklist)

* [ ] Templates table supports template_type filtering (column added or exists)
* [ ] Default eval template exists in database
* [ ] New Experiment form has template selection dropdown
* [ ] Dropdown shows only eval templates
* [ ] New Experiment form has dimension management UI with default 5 dimensions
* [ ] User can add and remove dimensions
* [ ] Form validates: no duplicate dimension names, no empty names
* [ ] Experiment creation saves dimensions to experiment_dimensions table
* [ ] Experiment detail page displays list of dimensions
* [ ] Evaluation submission validates dimensions against experiment configuration
* [ ] Missing required dimension rejected with clear error message
* [ ] Extra dimensions logged as warning but allowed
* [ ] Template resolution fetches from templates table using eval_template_id
* [ ] Settings → Templates page can filter by template type
* [ ] Unit tests achieve >80% coverage for dimension and template logic
* [ ] All UI components follow library patterns and are theme-aware

## Manual verification

* Steps:
  1. Navigate to Settings → Templates
  2. Create new template with type "eval_template", name "Custom Eval", content with {prompt}, {answer_a}, {answer_b}
  3. Navigate to /eval/new
  4. Verify template dropdown shows "Default Evaluation Template" and "Custom Eval"
  5. Select "Custom Eval"
  6. Verify dimension section shows 5 default dimensions
  7. Remove one dimension (e.g., "academic_response")
  8. Add new dimension: "bias_detection"
  9. Submit form, navigate to experiment detail
  10. Verify dimensions section shows 4 dimensions (factual_correctness, completeness, coherence, hallucination_risk, bias_detection)
  11. Add prompt and answer pair, click "Copy Eval Prompt"
  12. Verify prompt uses "Custom Eval" template content
  13. Paste result JSON missing "bias_detection" dimension, verify error message
  14. Paste result JSON with all required dimensions plus extra "extra_dim", verify warning logged but submission succeeds
* Expected results:
  * Template selection works correctly
  * Dimension management UI intuitive and functional
  * Validation enforces experiment dimension configuration
  * Template content correctly substituted in eval prompts
  * Errors and warnings clear and helpful

## Notes

* Requirements covered: R1 (full experiment creation with template and dimensions), R12 (template management), R13 (dimension configuration), R14 (dimension validation)
* Open Question Q1 resolved: If templates table doesn't have template_type, add it; otherwise use existing column
* Open Question Q2 resolved: Use insertion order (display_order column), no drag-and-drop UI
* Open Question Q4 resolved: Copy format is plain text (template resolution output)
* Open Question Q5 resolved: Use Python standard logging module with logger.info() and logger.warning()
* Dimension display_order can be set based on insertion order (enumerate dimensions list on creation)
* Consider adding a "Duplicate Experiment" feature in the future to copy dimensions and template settings
* Template content should include clear instructions for LLM judge on scoring scale and JSON format
* Validation should be strict on missing dimensions (hard error) but lenient on extra dimensions (warning only) to allow flexibility
