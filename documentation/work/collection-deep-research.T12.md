# Ticket: collection-deep-research.T12 - LangGraph Planning and Execution Nodes

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement LangGraph workflow nodes for Research Planner and Query Executor
* Provide automated research plan generation and sub-question execution with result reuse
* Integrate with T04 (planning module) and T05 (result matcher)

## Phase

* LangGraph Automation

## Scope

### In scope

* Node implementations in src/vulcanlab/research/nodes/:
  * research_planner_node.py - ResearchPlannerNode
  * query_executor_node.py - QueryExecutorNode
* ResearchPlannerNode: analyzes collection, generates plan, saves to state and database
* QueryExecutorNode: loops sub-questions, matches results, decides reuse strategy, fetches/reuses context
* Integration with T04 analyze_collection and generate_research_plan
* Integration with T05 match_results_for_question and recommend_reuse_strategy

### Out of scope

* Context assembly, synthesis, evaluation nodes (covered in T13-T14)
* Workflow graph definition (covered in T15)
* Frontend integration (covered in T19)

## Dependencies

* Depends on: T04 (planning), T05 (result matcher), T11 (state schema)
* Unblocks: T15 (workflow graph)

## Implementation plan

* Create src/vulcanlab/research/nodes/ directory
* Create research_planner_node.py
* Implement ResearchPlannerNode(state: ResearchState, session) -> ResearchState:
  * Extract collection_id from state
  * Call analyze_collection from T04 to get collection metadata and items
  * Get LLM client from vulcanlab.config
  * Call generate_research_plan from T04 with collection_data and LLM client
  * Update state:
    * state['research_plan'] = plan dict
    * state['current_phase'] = 'research'
    * state['item_notes'] = item notes from collection
  * Save plan to database using update_research_session (session_id from state)
  * Return updated state
* Create query_executor_node.py
* Implement QueryExecutorNode(state: ResearchState, session) -> ResearchState:
  * Get sub_questions from state['research_plan']['sub_questions']
  * For each sub_question:
    * Call match_results_for_question from T05 with question text and collection_id
    * If matches found (similarity > 0.85):
      * Call recommend_reuse_strategy from T05
      * Store matching info in state['reused_sections'][question_id]
      * If strategy == 'exact_reuse' or 'ensemble':
        * Fetch result content(s) and store in state['context_per_question'][question_id]
      * Else (partial or new):
        * Prepare for context assembly in next node (store relevant_item_ids)
    * Else (no matches):
      * Prepare for new generation (store relevant_item_ids from sub_question)
  * Update state['current_phase'] = 'context_assembly'
  * Return updated state
* Both nodes should be pure functions (no side effects except database updates for session state)
* Patterns to apply:
  * **Core module independence** - No FastAPI imports per patterns.md section 2
  * **Session management** - Accept session parameter explicitly per patterns.md section 2
  * **Configuration** - Use vulcanlab.config for LLM settings per patterns.md section 3.3
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * ResearchPlannerNode calls analyze_collection from T04
  * ResearchPlannerNode calls generate_research_plan from T04
  * ResearchPlannerNode updates state with research_plan and current_phase
  * ResearchPlannerNode saves plan to database
  * QueryExecutorNode loops through all sub_questions
  * QueryExecutorNode calls match_results_for_question for each question
  * QueryExecutorNode stores matching info in state['reused_sections'] when matches found
  * QueryExecutorNode prepares context for new generation when no matches found
  * QueryExecutorNode updates current_phase to 'context_assembly'
* Suggested locations:
  * tests/unit/research/nodes/test_research_planner_node.py
  * tests/unit/research/nodes/test_query_executor_node.py
* Mocking/fakes needed:
  * Mock analyze_collection and generate_research_plan from T04
  * Mock match_results_for_question and recommend_reuse_strategy from T05
  * Mock database session and update_research_session
  * Mock LLM client

## Acceptance criteria (checklist)

* [ ] ResearchPlannerNode implemented in research_planner_node.py
* [ ] QueryExecutorNode implemented in query_executor_node.py
* [ ] ResearchPlannerNode generates plan and updates state correctly
* [ ] ResearchPlannerNode saves plan to database
* [ ] QueryExecutorNode checks for matching results for each sub-question (R7)
* [ ] QueryExecutorNode stores reuse info when matches found (R8 automated workflow)
* [ ] QueryExecutorNode prepares relevant_item_ids for new generation when no matches
* [ ] Both nodes update current_phase correctly
* [ ] Unit tests pass for both nodes

## Manual verification

* Steps:
  * Create test ResearchState with collection_id=1
  * Create mock LLM that returns sample research plan JSON
  * Call ResearchPlannerNode(state, session), verify state updated with research_plan
  * Verify research_plan has 3-5 sub_questions
  * Verify current_phase updated to 'research'
  * Create collection with 2 research_result items (one matching Q1)
  * Call QueryExecutorNode(state, session), verify loops through all questions
  * Verify state['reused_sections']['Q1'] contains matching result info
  * Verify state['context_per_question']['Q2'] prepared for new generation
* Expected results:
  * Planning node generates valid research plan
  * Executor node matches results correctly
  * State updated correctly for downstream nodes

## Notes

* Requirements covered: R5 (Research Planner and Query Executor nodes), R7 (match results > 0.85), automated workflow result reuse
* QueryExecutorNode implements result reuse decision tree from spec
* Nodes are stateless functions (state in, state out) per LangGraph pattern
* Database updates for session state done within nodes for state persistence
* Similarity threshold 0.85 per R7 and spec
