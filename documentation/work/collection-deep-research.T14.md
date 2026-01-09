# Ticket: collection-deep-research.T14 - LangGraph Quality Evaluation and Refinement Nodes

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement LangGraph workflow nodes for Quality Evaluator and Refinement Coordinator
* Provide automated quality assessment and iterative refinement for weak sections
* Integrate with T07 (quality evaluation module)

## Phase

* LangGraph Automation

## Scope

### In scope

* Node implementations in src/vulcanlab/research/nodes/:
  * quality_evaluator_node.py - QualityEvaluatorNode
  * refinement_coordinator_node.py - RefinementCoordinatorNode
* QualityEvaluatorNode: evaluates citation coverage, coherence, completeness, flags weak sections
* RefinementCoordinatorNode: re-plans weak sections, triggers re-execution with adjusted parameters
* Quality thresholds for triggering refinement (citation_coverage < 0.7, etc.)
* Integration with T07 evaluate_quality and check_citation_coverage

### Out of scope

* Other workflow nodes (covered in T12-T13)
* Final report synthesis logic (handled in T15 workflow)
* Workflow graph definition (covered in T15)

## Dependencies

* Depends on: T07 (synthesizer/quality evaluator), T11 (state schema), T12-T13 (other nodes)
* Unblocks: T15 (workflow graph with conditional edges)

## Implementation plan

* Create quality_evaluator_node.py
* Implement QualityEvaluatorNode(state: ResearchState, session) -> ResearchState:
  * Get sections from state['sections']
  * Initialize quality_metrics dict
  * For each section (question_id, section_data):
    * Extract section_content, sources, metadata
    * Call evaluate_quality from T07 with section_content, sources, metadata
    * Get quality dict: {citation_coverage, source_diversity, coherence_score, completeness_score}
    * Call check_citation_coverage from T07 to get broken citations
    * Calculate overall quality score (weighted average)
    * If quality below thresholds:
      * citation_coverage < 0.7 OR
      * source_diversity < 3 OR
      * coherence_score == 'low' OR
      * broken_citations > 0
    * Add question_id to state['refinement_needed']
    * Store quality metrics in quality_metrics[question_id]
  * Store aggregate quality metrics in state['quality_metrics']
  * If state['refinement_needed'] is empty:
    * Update state['current_phase'] = 'completed'
  * Else:
    * Update state['current_phase'] = 'refinement'
  * Return updated state
* Create refinement_coordinator_node.py
* Implement RefinementCoordinatorNode(state: ResearchState, session) -> ResearchState:
  * Get refinement_needed list from state
  * Cap refinement iterations: check state for 'refinement_iteration_count' (default 0)
  * If refinement_iteration_count >= 2:
    * Log warning: "Max refinement iterations reached, proceeding with current quality"
    * Update state['current_phase'] = 'completed'
    * Return state
  * For each question_id in refinement_needed:
    * Get original sub_question from research_plan
    * Adjust parameters:
      * If citation_coverage low: increase token budget for more source material
      * If source_diversity low: fetch additional collection items
      * If coherence low: simplify sub-question or split into smaller parts
    * Update sub_question in state['research_plan'] with adjusted parameters
    * Clear section from state['sections'][question_id] to trigger re-execution
  * Clear state['refinement_needed']
  * Increment state['refinement_iteration_count']
  * Update state['current_phase'] = 'research' (loop back to QueryExecutorNode)
  * Return updated state
* Patterns to apply:
  * **Core module independence** - No FastAPI imports per patterns.md section 2
  * **Session management** - Accept session parameter explicitly per patterns.md section 2
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * QualityEvaluatorNode calls evaluate_quality for each section
  * QualityEvaluatorNode calls check_citation_coverage for each section
  * QualityEvaluatorNode adds question_id to refinement_needed when quality below threshold
  * QualityEvaluatorNode sets current_phase to 'completed' when all sections pass quality
  * QualityEvaluatorNode sets current_phase to 'refinement' when sections need refinement
  * RefinementCoordinatorNode adjusts parameters for weak sections
  * RefinementCoordinatorNode clears sections from state to trigger re-execution
  * RefinementCoordinatorNode caps refinement iterations at 2
  * RefinementCoordinatorNode sets current_phase to 'research' to loop back
  * RefinementCoordinatorNode sets current_phase to 'completed' when max iterations reached
* Suggested locations:
  * tests/unit/research/nodes/test_quality_evaluator_node.py
  * tests/unit/research/nodes/test_refinement_coordinator_node.py
* Mocking/fakes needed:
  * Mock evaluate_quality and check_citation_coverage from T07
  * Mock state with sections and quality metadata

## Acceptance criteria (checklist)

* [ ] QualityEvaluatorNode implemented in quality_evaluator_node.py
* [ ] RefinementCoordinatorNode implemented in refinement_coordinator_node.py
* [ ] QualityEvaluatorNode evaluates all sections and calculates quality metrics
* [ ] QualityEvaluatorNode uses thresholds from spec (citation_coverage < 0.7, etc.)
* [ ] QualityEvaluatorNode identifies sections needing refinement
* [ ] RefinementCoordinatorNode adjusts parameters for weak sections
* [ ] RefinementCoordinatorNode caps iterations at 2 per spec Implementation Notes
* [ ] RefinementCoordinatorNode triggers re-execution by clearing sections and resetting phase
* [ ] Unit tests pass for both nodes

## Manual verification

* Steps:
  * Create test ResearchState with 2 sections: one high quality, one low quality (citation_coverage = 0.5)
  * Call QualityEvaluatorNode(state, session)
  * Verify state['refinement_needed'] contains low-quality question_id
  * Verify state['current_phase'] == 'refinement'
  * Call RefinementCoordinatorNode(state, session)
  * Verify sub_question parameters adjusted (e.g., token budget increased)
  * Verify state['sections'] cleared for low-quality question
  * Verify state['current_phase'] == 'research' (loop back)
  * Set state['refinement_iteration_count'] = 2
  * Call RefinementCoordinatorNode again, verify sets current_phase to 'completed' (max iterations)
* Expected results:
  * Quality evaluation identifies weak sections
  * Refinement coordinator adjusts parameters and triggers re-execution
  * Refinement capped at 2 iterations

## Notes

* Requirements covered: R5 (Quality Evaluator and Refinement Coordinator nodes), quality thresholds from spec
* Quality thresholds from spec "Quality Evaluation Criteria" section
* Refinement iteration limit (2) per spec Implementation Notes to avoid infinite loops
* Conditional edge in workflow (covered in T15) routes to refinement node when refinement_needed non-empty
* Refinement adjusts parameters (token budget, source selection) based on quality issues
