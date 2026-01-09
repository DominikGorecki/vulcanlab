# Ticket: collection-deep-research.T03 - Research Session CRUD Operations

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement core CRUD functions for research sessions, sections, and reports in src/vulcanlab/data
* Provide database operations that pass session explicitly (no session creation inside functions)
* Enable session creation, retrieval, update, and deletion with proper transaction handling

## Phase

* Core Modules

## Scope

### In scope

* CRUD functions in src/vulcanlab/data/research_session.py:
  * create_research_session(collection_id, session_type, thread_id, session)
  * get_research_session(session_id, session)
  * get_research_session_by_thread_id(thread_id, session)
  * update_research_session(session_id, updates_dict, session)
  * list_research_sessions_for_collection(collection_id, session)
  * create_research_section(session_id, question_id, question_text, section, **kwargs)
  * get_research_sections(session_id, session)
  * update_research_section(section_id, updates_dict, session)
  * create_research_report(session_id, report_content, session, **kwargs)
  * get_research_report(session_id, session)
* Thread ID generation utility: generate_thread_id(session_type, collection_id)
* Session state helpers: update_session_phase(session_id, phase, session)

### Out of scope

* API endpoint handlers (covered in T10-T14)
* Business logic for result matching or context assembly (covered in T05-T07)
* LangGraph checkpointer integration (covered in T15)
* Frontend integration (covered in T19-T24)

## Dependencies

* Depends on: T02 (SQLAlchemy models)
* Unblocks: T10 (API endpoints), T15 (LangGraph workflow)

## Implementation plan

* Create src/vulcanlab/data/research_session.py
* Implement create_research_session:
  * Accept collection_id, session_type, thread_id (or generate if None), session
  * Create ResearchSession instance with status='in_progress', current_phase='planning'
  * session.add(), session.flush() to get ID, return session object
* Implement get_research_session:
  * Query ResearchSession by ID, return None if not found
  * Use joinedload for sections and reports relationships
* Implement get_research_session_by_thread_id:
  * Query ResearchSession by thread_id (unique index), return None if not found
* Implement update_research_session:
  * Accept session_id, updates_dict (keys: current_phase, research_plan, state_data, status, completed_at)
  * Query session, update fields, session.flush()
* Implement list_research_sessions_for_collection:
  * Query all ResearchSession where collection_id matches, order by created_at DESC
* Implement create_research_section:
  * Accept session_id, question_id, question_text, plus optional kwargs (section_content, context_data, metadata, etc.)
  * Create ResearchSection instance, session.add()
* Implement get_research_sections:
  * Query ResearchSection where session_id matches, order by question_id
* Implement update_research_section:
  * Update section_content, metadata, quality_status, etc.
* Implement create_research_report:
  * Accept session_id, report_content, plus optional kwargs (executive_summary, quality_evaluation, metadata)
  * Create ResearchReport instance with version=1
  * Update parent session status to 'completed', set completed_at to NOW()
* Implement get_research_report:
  * Query ResearchReport where session_id matches, order by version DESC, return latest
* Implement generate_thread_id utility:
  * If session_type == 'manual': return f"manual_{timestamp}_{random_hex}"
  * If session_type == 'automated': return f"auto_{collection_id}_{timestamp}"
* Patterns to apply:
  * **Session management** - Database sessions passed explicitly per patterns.md section 2
  * **Transaction handling** - Use session.flush() for immediate ID retrieval, rely on caller for commit
* Deviations (if any):
  * None - standard CRUD pattern

## Unit tests (required)

* Add tests for:
  * create_research_session creates session with correct defaults (status, phase)
  * get_research_session retrieves session by ID
  * get_research_session_by_thread_id retrieves session by thread_id
  * update_research_session updates fields correctly (research_plan, state_data, status)
  * list_research_sessions_for_collection returns sessions for collection, ordered correctly
  * create_research_section creates section linked to session
  * get_research_sections returns sections for session, ordered by question_id
  * update_research_section updates section_content and metadata
  * create_research_report creates report and marks session completed
  * get_research_report returns latest report for session
  * generate_thread_id produces correct format for manual and automated types
  * update_session_phase updates current_phase
* Suggested locations:
  * tests/unit/data/test_research_session.py
* Mocking/fakes needed:
  * Mock SQLAlchemy session (pytest fixture with in-memory SQLite)
  * Mock Collection model instances

## Acceptance criteria (checklist)

* [ ] All 11 CRUD functions implemented in research_session.py
* [ ] All functions accept session parameter (no session creation inside)
* [ ] create_research_session returns ResearchSession object with ID
* [ ] get_research_session_by_thread_id uses index for performance
* [ ] create_research_report updates parent session status to 'completed'
* [ ] generate_thread_id produces correct format (manual_{ts}_{random}, auto_{cid}_{ts})
* [ ] All functions use session.flush() not session.commit()
* [ ] Unit tests pass for all CRUD operations
* [ ] Code follows snake_case naming per patterns.md section 7

## Manual verification

* Steps:
  * Create test collection in database
  * Call create_research_session with collection_id, verify session created
  * Call get_research_session with session_id, verify retrieval
  * Call update_research_session with research_plan dict, verify update
  * Call create_research_section multiple times, verify sections created
  * Call get_research_sections, verify all sections returned in order
  * Call create_research_report, verify report created and session marked completed
  * Call generate_thread_id for both types, verify format matches spec
* Expected results:
  * All CRUD operations work correctly
  * thread_id format matches R15 requirement
  * Session status updates correctly when report created

## Notes

* Requirements covered: R6 (session state persistence), R15 (thread_id format)
* Thread ID format enables easy filtering: manual_* vs auto_* sessions
* create_research_report auto-completes session per spec workflow requirement
* Caller (API layer) responsible for session.commit() and rollback on error per patterns.md
