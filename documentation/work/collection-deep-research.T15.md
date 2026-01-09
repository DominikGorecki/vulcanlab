# Ticket: collection-deep-research.T15 - LangGraph Workflow Graph and Orchestration

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Define LangGraph StateGraph with all 6 workflow nodes and conditional edges
* Implement workflow orchestration function to start automated research sessions
* Configure checkpointer and node sequencing per spec "LangGraph Flow"

## Phase

* LangGraph Automation

## Scope

### In scope

* StateGraph definition in src/vulcanlab/research/workflow.py
* Workflow nodes: ResearchPlannerNode, QueryExecutorNode, ContextAssemblerNode, SynthesizerNode, QualityEvaluatorNode, RefinementCoordinatorNode
* Conditional edges: quality threshold → refinement or completion
* Workflow execution function: start_automated_research(collection_id, session)
* Checkpointer integration (T11)
* Background task execution preparation (interface for FastAPI BackgroundTasks or Celery)

### Out of scope

* Individual node implementations (covered in T12-T14)
* API endpoint to trigger workflow (covered in T17)
* Final report synthesis (added as workflow step in this ticket)
* Frontend integration (covered in T19)

## Dependencies

* Depends on: T11 (checkpointer), T12-T14 (all workflow nodes)
* Unblocks: T17 (API endpoint to trigger automated research)

## Implementation plan

* Create src/vulcanlab/research/workflow.py
* Import all nodes from T12-T14:
  * ResearchPlannerNode, QueryExecutorNode, ContextAssemblerNode, SynthesizerNode, QualityEvaluatorNode, RefinementCoordinatorNode
* Import PostgresSaver from T11
* Create final_synthesis_node function:
  * Generate final report from all sections in state['sections']
  * Call synthesis prompt (from T08) with all section contents + research goal
  * Get LLM to generate executive summary, introduction, synthesis, limitations, conclusions, references
  * Save report to database using create_research_report from T03
  * Update state['synthesis'] with report content
  * Update state['current_phase'] = 'completed'
  * Return state
* Define StateGraph:
  * from langgraph.graph import StateGraph
  * graph = StateGraph(ResearchState)
  * Add nodes:
    * graph.add_node("planner", ResearchPlannerNode)
    * graph.add_node("executor", QueryExecutorNode)
    * graph.add_node("assembler", ContextAssemblerNode)
    * graph.add_node("synthesizer", SynthesizerNode)
    * graph.add_node("evaluator", QualityEvaluatorNode)
    * graph.add_node("refiner", RefinementCoordinatorNode)
    * graph.add_node("final_synthesis", final_synthesis_node)
  * Set entry point: graph.set_entry_point("planner")
  * Add edges:
    * graph.add_edge("planner", "executor")
    * graph.add_edge("executor", "assembler")
    * graph.add_edge("assembler", "synthesizer")
    * graph.add_edge("synthesizer", "evaluator")
  * Add conditional edge from evaluator:
    * def should_refine(state): return len(state.get('refinement_needed', [])) > 0
    * graph.add_conditional_edges("evaluator", should_refine, {True: "refiner", False: "final_synthesis"})
  * Add edge from refiner back to executor (loop):
    * graph.add_edge("refiner", "executor")
  * Set finish point: graph.add_edge("final_synthesis", END)
* Implement start_automated_research function:
  * Accept collection_id, session (database session)
  * Generate thread_id: f"auto_{collection_id}_{timestamp}"
  * Create research_session using T03 create_research_session with session_type='automated', thread_id
  * Initialize ResearchState with collection_id, thread_id, current_phase='planning', empty dicts
  * Create PostgresSaver checkpointer (from T11) with session factory
  * Compile graph: compiled_graph = graph.compile(checkpointer=checkpointer)
  * Invoke graph: result = compiled_graph.invoke(initial_state, config={"configurable": {"thread_id": thread_id}})
  * Return session_id, thread_id
* Add error handling:
  * Wrap graph.invoke in try/except for LLM failures, database errors
  * On error: update session status to 'failed', log error, re-raise or return error
* Patterns to apply:
  * **Core module independence** - No FastAPI imports per patterns.md section 2
  * **Session management** - Pass session explicitly per patterns.md section 2
  * **Configuration** - Use vulcanlab.config for LLM settings per patterns.md section 3.3
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * StateGraph has all 7 nodes (6 workflow + 1 final synthesis)
  * StateGraph entry point is "planner"
  * Conditional edge from "evaluator" routes to "refiner" when refinement_needed non-empty
  * Conditional edge from "evaluator" routes to "final_synthesis" when refinement_needed empty
  * Edge from "refiner" loops back to "executor"
  * start_automated_research creates session with correct thread_id format (auto_{cid}_{ts})
  * start_automated_research initializes ResearchState correctly
  * start_automated_research invokes graph and returns session_id
  * final_synthesis_node generates report and saves to database
  * Error handling updates session status to 'failed' on exception
* Suggested locations:
  * tests/unit/research/test_workflow.py
* Mocking/fakes needed:
  * Mock all workflow nodes to return updated state
  * Mock create_research_session and create_research_report from T03
  * Mock PostgresSaver checkpointer
  * Mock LLM client for final synthesis

## Acceptance criteria (checklist)

* [ ] StateGraph defined with all 6 workflow nodes + final synthesis node
* [ ] Conditional edge from evaluator routes to refiner or final_synthesis correctly
* [ ] Edge from refiner loops back to executor (enables refinement iteration)
* [ ] start_automated_research function creates session and invokes graph
* [ ] Checkpointer integrated (state saved after each node execution)
* [ ] final_synthesis_node generates report and saves to research_reports table (R13)
* [ ] Error handling updates session status to 'failed' on exception
* [ ] Unit tests pass for workflow graph and execution

## Manual verification

* Steps:
  * Create test collection with 5 items
  * Call start_automated_research(collection_id=1, session=db_session)
  * Mock all nodes to return state transitions
  * Verify graph executes nodes in order: planner → executor → assembler → synthesizer → evaluator
  * Mock evaluator to return refinement_needed=['Q1']
  * Verify conditional edge routes to refiner
  * Verify refiner loops back to executor
  * Mock evaluator to return refinement_needed=[] on second iteration
  * Verify conditional edge routes to final_synthesis
  * Verify final_synthesis_node saves report to database
  * Verify session status updated to 'completed'
* Expected results:
  * Workflow executes all nodes in correct order
  * Conditional edges work correctly
  * Refinement loop works
  * Final report saved

## Notes

* Requirements covered: R5 (LangGraph orchestration), R13 (final report synthesis), conditional edges per spec
* Workflow flow per spec "LangGraph Flow" section
* Refinement loop enables iterative quality improvement per spec
* final_synthesis_node generates report structure per R13 (executive summary, findings, synthesis, limitations, conclusions, references)
* Checkpointer enables resume from any node per R9
* Background execution prepared for T17 API endpoint integration
