# Ticket: collection-deep-research.T11 - LangGraph State Schema and Checkpointer

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Define ResearchState TypedDict schema for LangGraph workflow state management
* Implement PostgreSQL-based checkpointer that stores state in research_sessions.state_data
* Enable workflow resumability from any node by persisting state after each node execution

## Phase

* LangGraph Automation

## Scope

### In scope

* ResearchState TypedDict in src/vulcanlab/research/state.py
* PostgreSQL checkpointer in src/vulcanlab/research/checkpointer.py
* State serialization/deserialization for JSONB storage
* Checkpointer interface compatible with LangGraph's BaseSaver

### Out of scope

* LangGraph workflow nodes (covered in T12-T14)
* Workflow graph definition (covered in T15)
* API endpoint to trigger automated research (covered in T17)
* Frontend integration (covered in T19)

## Dependencies

* Depends on: T02 (models), T03 (CRUD)
* Unblocks: T15 (LangGraph workflow graph), T16-T18 (workflow nodes)

## Implementation plan

* Create src/vulcanlab/research/state.py
* Define ResearchState TypedDict matching spec:
  * collection_id: int
  * collection_description: str
  * item_notes: list[dict]  # {item_id, note, type}
  * research_plan: dict  # {outline, sub_questions, token_budgets}
  * current_phase: str
  * sections: dict[str, dict]  # {question: {content, sources, quality}}
  * context_per_question: dict[str, list]
  * reused_sections: dict[str, dict]  # {question_id: {source_result_id, reuse_type, similarity}}
  * available_results: list[dict]  # Cache of research_result items
  * synthesis: str
  * quality_metrics: dict
  * refinement_needed: list[str]
  * thread_id: str
* Create src/vulcanlab/research/checkpointer.py
* Install langgraph dependency if not already present
* Implement PostgresSaver class implementing LangGraph's BaseSaver interface:
  * __init__(self, db_session_factory) - accepts session factory
  * put(self, thread_id, state, metadata) - save state to research_sessions.state_data
  * get(self, thread_id) - load state from research_sessions.state_data
  * list(self, thread_id_prefix) - list all states matching prefix (for debugging)
* Implement put method:
  * Get or create research_session by thread_id
  * Serialize state dict to JSONB (already JSON-serializable)
  * Update research_sessions.state_data with serialized state
  * Update research_sessions.updated_at timestamp
  * session.flush()
* Implement get method:
  * Query research_sessions by thread_id
  * Deserialize state_data JSONB to ResearchState dict
  * Return state or None if not found
* Implement list method:
  * Query research_sessions where thread_id LIKE f"{prefix}%"
  * Return list of (thread_id, state) tuples
* Add utility functions:
  * serialize_state(state: ResearchState) -> dict - handle any non-JSON-serializable objects
  * deserialize_state(state_dict: dict) -> ResearchState - reconstruct state
* Patterns to apply:
  * **Core module independence** - No FastAPI imports per patterns.md section 2
  * **Session management** - Checkpointer accepts db_session_factory, creates sessions internally (exception to patterns.md due to LangGraph interface requirements)
  * **JSONB state storage** - Per spec design for flexible schema evolution
* Deviations (if any):
  * Checkpointer creates DB sessions internally (required by LangGraph interface) - deviation from patterns.md session management, but necessary for integration

## Unit tests (required)

* Add tests for:
  * ResearchState TypedDict has all required fields
  * PostgresSaver.put saves state to research_sessions.state_data
  * PostgresSaver.get loads state from research_sessions.state_data
  * PostgresSaver.get returns None for non-existent thread_id
  * PostgresSaver.list returns all states matching thread_id prefix
  * serialize_state handles nested dicts and lists
  * deserialize_state reconstructs ResearchState correctly
  * Checkpointer updates research_sessions.updated_at on put
* Suggested locations:
  * tests/unit/research/test_state.py
  * tests/unit/research/test_checkpointer.py
* Mocking/fakes needed:
  * Mock database session factory
  * Mock research_sessions table queries

## Acceptance criteria (checklist)

* [ ] ResearchState TypedDict defined with all 13 fields from spec
* [ ] PostgresSaver class implements LangGraph BaseSaver interface
* [ ] PostgresSaver.put saves state to research_sessions.state_data JSONB column
* [ ] PostgresSaver.get loads state from database by thread_id
* [ ] PostgresSaver.list returns states matching thread_id prefix
* [ ] serialize_state and deserialize_state handle state dict correctly
* [ ] langgraph dependency added to pyproject.toml
* [ ] Unit tests pass for state schema and checkpointer

## Manual verification

* Steps:
  * Create test ResearchState dict with all fields
  * Create PostgresSaver instance with database session factory
  * Call checkpointer.put(thread_id="test_123", state=test_state)
  * Verify research_sessions row created with thread_id="test_123"
  * Verify state_data JSONB column contains serialized state
  * Call checkpointer.get(thread_id="test_123"), verify returns state
  * Call checkpointer.list(thread_id_prefix="test"), verify returns test_123 state
* Expected results:
  * State persisted to database correctly
  * State loaded from database correctly
  * Checkpointer compatible with LangGraph

## Notes

* Requirements covered: R5 (LangGraph with checkpointer), R9 (resume sessions)
* Checkpointer enables resume from any node per spec "Checkpointer Configuration" section
* state_data JSONB column in T01 designed specifically for this checkpointer
* Deviation from patterns.md session management justified: LangGraph BaseSaver interface requires internal session creation
* Thread ID format (manual_* or auto_*) enables filtering sessions by type per spec R15
