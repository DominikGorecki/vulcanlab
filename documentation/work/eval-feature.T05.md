# Ticket: eval-feature.T05 - Statistical Analysis and Aggregation

## Source

* Spec: documentation/work/eval-feature.spec.md
* Patterns: documentation/patterns.md

## Goal

* Compute and display aggregate statistics for experiments
* Implement Wilcoxon signed-rank test for statistical comparison
* Fourth vertical slice: view evaluation results and statistical analysis

## Scope

### In scope

* Core logic for computing: X win rate, mean score, median score, tie percentage, harm rate
* Wilcoxon signed-rank test computation using scipy.stats
* Stats display section on experiment detail page
* Stats computed live on page load (no caching)
* Handle edge cases: no evaluations, single evaluation, multiple evaluations per prompt
* API endpoint enhancement: GET /api/v1/eval/experiments/{id} includes stats object
* Display individual evaluation results on prompt detail page

### Out of scope

* Caching or denormalization of stats
* Charts or visualizations (graphs, histograms)
* Comparison across multiple experiments
* Export of statistics to CSV/PDF
* Per-dimension statistics (focus on overall_score)

## Dependencies

* Depends on: T01 (models), T02 (experiment pages), T04 (evaluations)
* Unblocks: none (can be implemented in parallel with T06)

## Implementation plan

1. Verify scipy is in requirements (needed for Wilcoxon test)
2. Implement statistics computation in src/vulcanlab/eval/statistics.py:
   * compute_experiment_stats(session, experiment_id) -> ExperimentStats
     - Query all evaluations for experiment via joins
     - Extract overall_scores into list
     - Compute x_win_rate: count(score > 0) / count(*)
     - Compute mean_score: mean(overall_scores)
     - Compute median_score: median(overall_scores)
     - Compute tie_pct: count(score == 0) / count(*)
     - Compute harm_rate: count(score < 0) / count(*)
     - If multiple evaluations per prompt (group by prompt_id, count > 1):
       * Compute deltas within each prompt group
       * Call scipy.stats.wilcoxon(deltas) if len(deltas) > 0
       * Return p_value
     - Return ExperimentStats Pydantic model
   * Handle edge cases: return None or zero values if no evaluations
3. Create ExperimentStats Pydantic model:
   * x_win_rate: float
   * mean_score: float
   * median_score: float
   * tie_pct: float
   * harm_rate: float
   * wilcoxon_p: Optional[float]
   * evaluation_count: int
4. Update GET /api/v1/eval/experiments/{id} endpoint to include stats in response
5. Update experiment detail page (vulcanlab_ui/src/app/eval/[id]/page.tsx):
   * Add StatsCardGrid section above prompts table
   * Display StatsCard for each metric: X Win Rate (%), Mean Score, Median Score, Tie %, Harm Rate (%)
   * If wilcoxon_p is present and < 0.05, display with indicator (e.g., "Statistically significant")
   * Handle empty state: if evaluation_count == 0, show message "No evaluations yet"
6. Update prompt detail page to show individual evaluation results:
   * Add table or card list showing all evaluations for the prompt
   * Columns: created_at, overall_score, justification (truncated), action to view full details
   * "View Details" button opens modal showing all dimension scores + full justification
7. Implement "View Evaluation Details" modal:
   * Display overall_score prominently
   * List all dimensions with scores in a table
   * Display full justification text
8. Patterns to apply:
   * **SQL aggregations**: Use SQLAlchemy func.count, func.avg, func.percentile_cont for efficiency
   * **Component composition**: StatsCard, StatsCardGrid, DataTable, Dialog
   * **Performance**: Single query with joins to fetch all evaluation data, compute in Python

## Unit tests (required)

* Add tests for:
  * compute_experiment_stats() with no evaluations returns zero values
  * compute_experiment_stats() with single evaluation returns correct percentages
  * compute_experiment_stats() with multiple evaluations (all positive scores) returns 100% win rate
  * compute_experiment_stats() with mixed scores returns correct mean, median, tie_pct, harm_rate
  * compute_experiment_stats() with ties (score=0) correctly counts in tie_pct
  * compute_experiment_stats() with multiple evaluations per prompt computes Wilcoxon test
  * Wilcoxon test returns p-value when N > 1 evaluations per prompt
  * Wilcoxon test returns None when only one evaluation per prompt
  * Edge case: all scores are ties (score=0), verify mean=0, median=0, tie_pct=100%
  * Edge case: division by zero handling when evaluation_count=0
* Suggested locations:
  * tests/unit/test_eval_stats_computation.py
  * tests/unit/test_eval_wilcoxon.py
* Mocking/fakes needed:
  * Mock SQLAlchemy session with mock evaluation data
  * Mock scipy.stats.wilcoxon for deterministic testing (or use real with known data)

## Acceptance criteria (checklist)

* [ ] Experiment detail page displays StatsCardGrid with 5 metrics
* [ ] X win rate computed as P(overall_score > 0) and displayed as percentage
* [ ] Mean and median scores computed correctly and displayed
* [ ] Tie percentage computed as P(overall_score == 0) and displayed
* [ ] Harm rate computed as P(overall_score < 0) and displayed as percentage
* [ ] Wilcoxon p-value displayed when N > 1 evaluations per prompt
* [ ] Empty state shown when no evaluations exist
* [ ] Prompt detail page shows table of individual evaluations
* [ ] User can click "View Details" to see full evaluation (all dimensions + justification)
* [ ] All UI components follow library patterns and are theme-aware
* [ ] Unit tests achieve >80% coverage for statistics logic
* [ ] Stats query completes within 2 seconds for 1000 prompts (verified manually or via profiling)

## Manual verification

* Steps:
  1. Create experiment, add 5 prompts, add answers, submit evaluations with varying scores:
     - Prompt 1: overall_score = 10
     - Prompt 2: overall_score = 5
     - Prompt 3: overall_score = 0
     - Prompt 4: overall_score = -5
     - Prompt 5: overall_score = -10
  2. Navigate to experiment detail page
  3. Verify StatsCardGrid displays:
     - X Win Rate: 40% (2 out of 5 positive)
     - Mean Score: 0 (sum = 0)
     - Median Score: 0
     - Tie %: 20% (1 out of 5)
     - Harm Rate: 40% (2 out of 5 negative)
  4. Add second evaluation to Prompt 1 with overall_score = 8
  5. Refresh page, verify Wilcoxon p-value appears (if computable)
  6. Click into Prompt 1 detail page
  7. Verify table shows 2 evaluations with scores and justifications
  8. Click "View Details" on one evaluation
  9. Verify modal shows all dimension scores and full justification
* Expected results:
  * All statistics computed accurately
  * Percentages formatted correctly (e.g., 40.0% or 40%)
  * Wilcoxon test only appears when applicable
  * UI responsive and updates correctly
  * No errors or slow queries

## Notes

* Requirements covered: R9 (aggregate statistics), R10 (Wilcoxon test), R14 (dimension scores used in computation)
* The spec says "Wilcoxon signed-rank test on overall_score deltas when N > 1 on answers per prompt"
  - This means: for prompts with multiple answer pairs (each with evaluation), compute paired differences and run Wilcoxon
  - If only one evaluation per prompt across all prompts, Wilcoxon is not applicable
* Percentages should be formatted with 1 decimal place for display (e.g., 42.3%)
* Consider adding a "Last updated" timestamp for stats (e.g., "Stats as of 2025-01-15 10:30 AM")
* If stats computation is slow, consider adding a loading spinner or skeleton UI
* The spec requires stats to complete within 2 seconds for 1000 prompts; use SQL aggregations and avoid N+1 queries
* For Wilcoxon test, handle warnings (e.g., if all deltas are zero, test may not be valid)
* Display wilcoxon_p with context: "p = 0.03 (significant at α=0.05)" or similar
