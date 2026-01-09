# Title: Collection Deep Research Feature

## Summary

* Add a "Deep Research" button to collection pages (when collection has 5+ items) that opens a modal for manual or automated research session creation
* Implement web-based manual research workflow with step-by-step wizard UI that mirrors the LangGraph flow (planning, result matching, context assembly, section generation, synthesis, quality evaluation)
* Implement LangGraph-based automated research workflow with PostgreSQL-backed checkpointer for resumability
* Create database schema (research_sessions, research_sections, research_reports tables) to persist both manual and automated research sessions
* Build API endpoints to support session CRUD, section management, and report generation
* Display list of completed research reports on collection detail page with markdown rendering

## Problem / Context

Currently, users can collect excerpts, research results, and queries into collections but lack a systematic way to synthesize comprehensive reports from their curated materials. The ChatGPT Deep Research feature demonstrates the value of orchestrated multi-step research, but VulcanLab needs a solution that:

* Leverages pre-curated collection items (excerpts, research_results, research_queries) rather than generic web search
* Provides precise source attribution to original works and chunks
* Enables both manual (human-controlled) and automated (LangGraph-orchestrated) research workflows
* Reuses existing research_result items when relevant to avoid redundant LLM generation
* Maintains full session state for resumability and iterative refinement

Users are affected by the inability to efficiently synthesize large collections into coherent reports. Business impact includes reduced research quality and slower knowledge synthesis workflows.

## Goals

* Enable users to generate comprehensive research reports from collection items through a guided workflow
* Provide both manual (step-by-step UI wizard) and automated (LangGraph) execution modes
* Implement result reuse logic to leverage existing research_result items and reduce LLM API costs
* Persist all session state to database for resumability and audit trails
* Support iterative refinement (resume in-progress sessions, regenerate sections)
* Maintain source provenance from collection items through to final report citations

## Non-goals (Strict)

* PDF export of reports (markdown only for now)
* Automated citation validation tooling (basic validation only)
* Multi-user collaboration on research sessions (single-user sessions)
* A/B testing infrastructure for different prompt templates
* Direct integration with external LLM APIs (use existing VulcanLab LLM infrastructure)
* Real-time streaming of LLM responses in manual mode
* Graph-based visualization of research dependencies

## Scope

### In scope

* Database schema for research_sessions, research_sections, research_reports
* SQLAlchemy models and CRUD operations
* API endpoints for session lifecycle, section management, report retrieval
* "Deep Research" button on collection page header (only appears when collection has 5+ items)
* Modal UI for mode selection (manual vs automated)
* Manual research wizard UI (6-step workflow: planning, result matching, context assembly, section generation, synthesis, quality evaluation)
* LangGraph state machine implementation with 6 workflow nodes
* PostgreSQL-based checkpointer for session persistence
* Result reuse logic with quality scoring and user approval (manual mode)
* Report list display on collection detail page
* Markdown rendering of final reports with citation support
* Session resume capability for incomplete manual or automated sessions

### Out of scope

* PDF export functionality
* Advanced citation validation beyond basic source matching
* Real-time collaborative editing of research sessions
* Prompt template A/B testing framework
* Custom LLM provider integrations (use existing infrastructure)
* Automated quality scoring with external model evaluation
* Export to external formats (Word, LaTeX, etc.)

## Requirements (Functional)

* R1: Collection page must display "Deep Research" button in header when collection contains 5 or more items
* R2: "Deep Research" button must open modal with two options: "Manual Research" and "Automated Research"
* R3: Manual research mode must provide 6-step wizard UI (planning, result matching, context assembly, section generation, synthesis, quality evaluation)
* R4: Each manual wizard step must allow user to copy generated prompts, paste LLM responses, and save to database
* R5: Automated research mode must use LangGraph orchestration with 6 workflow nodes (Research Planner, Query Executor, Context Assembler, Synthesizer, Quality Evaluator, Refinement Coordinator)
* R6: System must persist all session state to research_sessions, research_sections, research_reports tables
* R7: Query Executor node (and manual step 2) must check for existing research_result items matching sub-questions with similarity > 0.85
* R8: When matching results found in manual mode, user must be prompted to approve reuse (exact, partial, ensemble, or new generation)
* R9: System must support resuming incomplete research sessions (both manual and automated)
* R10: Collection detail page must display list of all completed research reports for that collection
* R11: Users must be able to view full markdown reports with inline citations
* R12: Each research section must track source attribution (collection_item_ids, result_ids, reuse metadata)
* R13: Final report must include executive summary, research questions, findings per sub-question, synthesis, limitations, and references
* R14: Quality evaluation step (manual step 6) must be optional and skippable
* R15: System must generate session thread_id in format: manual_{timestamp}_{random} or auto_{collection_id}_{timestamp}

## Requirements (Non-functional)

* Performance:
  * Manual wizard step transitions must complete within 500ms (data fetch and display)
  * Automated research session must handle 20K-40K token contexts per section without degradation
  * Result matching queries (similarity search) must complete within 2 seconds for collections up to 1000 items
  * Session resume must restore full state within 1 second

* Reliability:
  * Research session state must be persisted after each completed step (manual) or node execution (automated)
  * System must gracefully handle LLM API failures with retry logic (3 attempts with exponential backoff)
  * Database transactions must ensure atomicity of section saves and report generation
  * Checkpointer must enable recovery from any node in LangGraph workflow

* Security / Privacy:
  * Research sessions must be scoped to user permissions (only accessible to collection owner)
  * Session state data (JSONB) must not expose sensitive configuration or API keys
  * Report content must be sanitized before rendering in UI to prevent XSS

* Observability:
  * Each research session must log start time, completion time, status, and error messages
  * Automated workflow must track token usage per node and total cost
  * Manual workflow must track user actions (step completions, skips, retries)
  * Quality metrics (citation coverage, source diversity, coherence) must be stored in report metadata

## Proposed Solution (High-level)

* Extend PostgreSQL schema with three new tables: research_sessions (stores overall session state and thread_id), research_sections (stores per-sub-question content and metadata), research_reports (stores final synthesized reports)
* Create SQLAlchemy models for ResearchSession, ResearchSection, ResearchReport with appropriate relationships
* Build FastAPI router (/api/v1/research-sessions) with endpoints for CRUD operations, section management, and report retrieval
* Add "Deep Research" button to collection detail page header (conditional rendering based on item count >= 5)
* Implement modal component with mode selection UI (Manual vs Automated cards with descriptions)
* Build 6-step wizard UI for manual research using Shadcn/Radix components with react-hook-form for user input
* Implement LangGraph StateGraph with ResearchState TypedDict and 6 workflow nodes (Planner, Executor, Assembler, Synthesizer, Evaluator, Coordinator)
* Use PostgreSQL-based custom checkpointer (store state in research_sessions.state_data JSONB column)
* Implement result reuse logic in Query Executor node: compute embedding similarity between sub-questions and existing research_result queries, score quality (citation density, freshness, completeness), and recommend strategy (exact/partial/ensemble/new)
* Create report list component on collection page with markdown renderer and citation link handling
* Enable session resume by loading state from database and re-hydrating wizard or LangGraph state

## Interfaces / APIs / Contracts

* **POST /api/v1/research-sessions**
  * Request: `{collection_id: int, session_type: "manual" | "automated"}`
  * Response: `{session_id: int, thread_id: string, status: string, created_at: timestamp}`
  * Creates new research session and returns session metadata

* **GET /api/v1/research-sessions/{session_id}**
  * Response: `{session_id, collection_id, session_type, thread_id, current_phase, research_plan, state_data, status, created_at, updated_at, completed_at}`
  * Retrieves full session details including state

* **PUT /api/v1/research-sessions/{session_id}**
  * Request: `{current_phase?: string, research_plan?: object, state_data?: object, status?: string}`
  * Response: `{session_id, updated_at}`
  * Updates session state (used by both manual and automated workflows)

* **GET /api/v1/collections/{collection_id}/research-sessions**
  * Response: `{sessions: [{session_id, session_type, status, created_at, completed_at}, ...]}`
  * Lists all research sessions for a collection

* **POST /api/v1/research-sessions/{session_id}/sections**
  * Request: `{question_id: string, question_text: string, section_content?: string, context_data?: object, matching_results?: object, metadata?: object, reuse_info?: object}`
  * Response: `{section_id: int, question_id: string, created_at: timestamp}`
  * Saves a research section to database

* **GET /api/v1/research-sessions/{session_id}/sections**
  * Response: `{sections: [{section_id, question_id, question_text, section_content, metadata, quality_status}, ...]}`
  * Retrieves all sections for a session

* **POST /api/v1/research-sessions/{session_id}/report**
  * Request: `{report_content: string, executive_summary?: string, quality_evaluation?: object, metadata?: object}`
  * Response: `{report_id: int, session_id: int, created_at: timestamp}`
  * Saves final report and marks session as completed

* **GET /api/v1/research-sessions/{session_id}/report**
  * Response: `{report_id, report_content, executive_summary, quality_evaluation, metadata, created_at}`
  * Retrieves final report for a session

* **POST /api/v1/research-sessions/{session_id}/resume**
  * Request: `{mode?: "manual" | "automated"}`
  * Response: `{session_id, current_phase, next_step: object}`
  * Resumes an incomplete session (optionally switching modes)

* **POST /api/v1/research-sessions/{session_id}/context**
  * Request: `{question_id: string, relevant_item_ids: [int]}`
  * Response: `{context: string, token_count: int, sources: [{item_id, type, preview}, ...]}`
  * Assembles context for a sub-question from collection items (used by manual wizard)

* **POST /api/v1/research-sessions/{session_id}/match-results**
  * Request: `{question_id: string, question_text: string}`
  * Response: `{matched_results: [{result_id, similarity, quality_score, recommendation}, ...], recommended_strategy: string}`
  * Finds existing research_result items matching a sub-question (used by manual wizard step 2)

## Data Model / Storage

### New Tables

**research_sessions**
```sql
CREATE TABLE research_sessions (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    session_type VARCHAR(20) NOT NULL CHECK (session_type IN ('manual', 'automated')),
    thread_id VARCHAR(255) UNIQUE NOT NULL,
    current_phase VARCHAR(50),  -- 'planning', 'research', 'synthesis', 'evaluation', 'completed'
    research_plan JSONB,  -- {research_goal, key_themes, sub_questions: [{id, question, rationale, estimated_tokens, relevant_items}], synthesis_approach}
    state_data JSONB,  -- Full ResearchState object (for LangGraph checkpointer and manual wizard state)
    status VARCHAR(20) DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'failed', 'paused')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_research_sessions_collection ON research_sessions(collection_id);
CREATE INDEX idx_research_sessions_thread ON research_sessions(thread_id);
CREATE INDEX idx_research_sessions_status ON research_sessions(status);
```

**research_sections**
```sql
CREATE TABLE research_sections (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
    question_id VARCHAR(50) NOT NULL,  -- 'Q1', 'Q2', etc.
    question_text TEXT NOT NULL,
    section_content TEXT,  -- Generated markdown content
    context_data JSONB,  -- {context: string, sources: [{item_id, type, work_id, preview}], token_count: int}
    matching_results JSONB,  -- {matched_results: [{result_id, similarity, quality_score}], strategy: string}
    metadata JSONB,  -- {word_count: int, citation_count: int, source_diversity: int}
    reuse_info JSONB,  -- {source_result_ids: [int], reuse_type: string, similarity_scores: [float], original_queries: [string]}
    quality_status VARCHAR(20) DEFAULT 'pending' CHECK (quality_status IN ('pending', 'approved', 'needs_refinement')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_research_sections_session ON research_sections(session_id);
CREATE INDEX idx_research_sections_question ON research_sections(question_id);
CREATE INDEX idx_research_sections_quality ON research_sections(quality_status);
```

**research_reports**
```sql
CREATE TABLE research_reports (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
    report_content TEXT NOT NULL,  -- Full markdown report
    executive_summary TEXT,
    quality_evaluation JSONB,  -- {citation_coverage: float, source_diversity: int, coherence_score: string, completeness_score: string, identified_gaps: [string]}
    metadata JSONB,  -- {total_words: int, total_citations: int, sources_used: [int], token_usage: int}
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_research_reports_session ON research_reports(session_id);
```

### SQLAlchemy Models

* **ResearchSession**: Corresponds to research_sessions table, relationships to ResearchSection (one-to-many), ResearchReport (one-to-many), Collection (many-to-one)
* **ResearchSection**: Corresponds to research_sections table, relationship to ResearchSession (many-to-one)
* **ResearchReport**: Corresponds to research_reports table, relationship to ResearchSession (many-to-one)

### Migrations

* Migration file: `migrations/add_research_tables.sql` or Alembic revision (depending on project setup)
* Add tables, indexes, and foreign key constraints
* Ensure JSONB columns support querying and indexing where needed

## UX / Workflows

### Manual Research Workflow (6-Step Wizard)

**Step 0: Trigger**
* User navigates to `/collection/[id]` page
* If collection has >= 5 items, "Deep Research" button appears in page header (next to collection title)
* User clicks button, modal opens with mode selection

**Step 1: Mode Selection Modal**
* Modal displays two cards: "Manual Research" and "Automated Research"
* Manual card: "Step-by-step guided workflow. You control LLM interactions and paste responses."
* Automated card: "Fully automated using LangGraph. System handles all LLM calls."
* User selects "Manual Research", modal transitions to wizard

**Step 2: Planning Wizard Step**
* UI displays collection overview (name, description, item counts by type)
* "Generate Research Plan" button copies planning prompt to clipboard
* Text area for user to paste LLM response (JSON with research_goal, key_themes, sub_questions)
* "Save Plan" button validates JSON and saves to research_sessions.research_plan
* Wizard advances to Step 3

**Step 3: Result Matching (Per Sub-Question Loop)**
* UI shows current sub-question (e.g., Q1) with question text and rationale
* "Check for Matching Results" button calls API to find similar research_result items
* If matches found: Display list with similarity scores, quality assessments, and recommended strategy
* User selects strategy: "Exact Reuse", "Partial Reuse", "Ensemble", or "Generate New"
* If reuse selected: Display preview of result(s) to be reused
* "Confirm Selection" button saves matching_results to research_sections table
* Wizard advances to Step 4

**Step 4: Context Assembly**
* If "Generate New" was selected in Step 3: "Fetch Context" button calls API to assemble context from collection items
* Context preview displayed (truncated) with token count
* "Copy Context Prompt" button copies context + generation prompt to clipboard
* If "Reuse" was selected: Displays reused result(s) content instead
* User pastes into external LLM, receives section content
* Wizard advances to Step 5

**Step 5: Section Generation**
* Text area for user to paste LLM-generated section content (markdown)
* Preview pane shows rendered markdown
* "Save Section" button stores to research_sections.section_content
* Metadata extracted automatically (word count, citation count)
* If more sub-questions remain: Loop back to Step 3 for next question
* If all sections complete: Wizard advances to Step 6

**Step 6: Synthesis**
* "Fetch All Sections" button retrieves all saved sections and copies synthesis prompt to clipboard
* User pastes into external LLM, receives final report
* Text area for user to paste final report markdown
* Preview pane shows full rendered report
* "Save Report" button stores to research_reports table and marks session as completed
* Optional: "Evaluate Quality" button copies quality evaluation prompt (user can skip)

**Step 7: Completion**
* Success message: "Research report completed!"
* Link to view report on collection page
* Option to "Start New Research" or "Close"

### Automated Research Workflow (LangGraph)

**User Interaction**
* User selects "Automated Research" in mode selection modal
* Modal shows "Starting automated research..." with progress indicator
* Session starts in background, user can close modal and navigate away
* Progress updates shown on collection page (e.g., "Planning: Complete, Research: 2/5 sections")
* When complete, notification appears: "Deep research completed! View report."

**LangGraph Flow**
* Node 1 (Research Planner): Analyzes collection, generates research plan, saves to research_sessions.research_plan
* Node 2 (Query Executor): For each sub-question, checks for matching results, decides reuse strategy, fetches/reuses context
* Node 3 (Context Assembler): Consolidates context within token limits, deduplicates, maintains attribution
* Node 4 (Synthesizer): Generates section content via LLM, saves to research_sections
* Node 5 (Quality Evaluator): Checks citations, coherence, completeness; triggers refinement if needed
* Node 6 (Refinement Coordinator): Re-plans weak sections, re-executes with adjusted parameters (conditional edge)
* Final: Generates synthesis, saves to research_reports, marks session completed

### Report Viewing

* Collection detail page shows "Research Reports" section below collection items
* List displays report cards: session type (manual/automated), creation date, status, preview of executive summary
* Click report card to open full report view (modal or dedicated page)
* Report view: Markdown-rendered content with syntax highlighting for code blocks, clickable citation links back to collection items

## Work Breakdown (Ticket Seed)

### Phase 0: Foundations

* T01: Define database schema design document (tables, indexes, foreign keys, JSONB structure)
* T02: Create migration file for research_sessions, research_sections, research_reports tables
* T03: Run migrations in development environment and validate schema

### Phase 1: Data / Migrations

* T04: Create SQLAlchemy models for ResearchSession, ResearchSection, ResearchReport
* T05: Add enums for session_type, status, current_phase, quality_status
* T06: Define relationships (ResearchSession ↔ Collection, ResearchSession ↔ ResearchSection, ResearchSession ↔ ResearchReport)
* T07: Implement CRUD functions in src/vulcanlab/data for research sessions, sections, reports
* T08: Write unit tests for CRUD operations (mocked database)

### Phase 2: Core Domain / Modules

* T09: Create src/vulcanlab/research module with research_session.py, research_planner.py, result_matcher.py, context_assembler.py
* T10: Implement result matching logic: embedding similarity computation, quality scoring algorithm (citation density, freshness, completeness)
* T11: Implement context assembly logic: fetch collection items, consolidate content, apply token limits, deduplicate sources
* T12: Implement research planning logic: analyze collection description and items, generate sub-questions, estimate token budgets
* T13: Write unit tests for result matching, context assembly, research planning (mocked session, mocked LLM calls)

### Phase 3: External APIs / Integrations

* T14: Create FastAPI router src/vulcanlab_api/routers/research_sessions.py with /api/v1/research-sessions prefix
* T15: Implement POST /api/v1/research-sessions endpoint (create session)
* T16: Implement GET /api/v1/research-sessions/{session_id} endpoint (retrieve session)
* T17: Implement PUT /api/v1/research-sessions/{session_id} endpoint (update session state)
* T18: Implement GET /api/v1/collections/{collection_id}/research-sessions endpoint (list sessions)
* T19: Implement POST /api/v1/research-sessions/{session_id}/sections endpoint (save section)
* T20: Implement GET /api/v1/research-sessions/{session_id}/sections endpoint (list sections)
* T21: Implement POST /api/v1/research-sessions/{session_id}/report endpoint (save report)
* T22: Implement GET /api/v1/research-sessions/{session_id}/report endpoint (retrieve report)
* T23: Implement POST /api/v1/research-sessions/{session_id}/resume endpoint (resume session)
* T24: Implement POST /api/v1/research-sessions/{session_id}/context endpoint (assemble context for manual wizard)
* T25: Implement POST /api/v1/research-sessions/{session_id}/match-results endpoint (match results for manual wizard)
* T26: Add authentication/authorization checks (session scoped to collection owner)
* T27: Add global error handling for research session endpoints

### Phase 4: UI / Client

* T28: Add "Deep Research" button to collection detail page header (conditional on item count >= 5)
* T29: Create DeepResearchModal component with mode selection UI (Manual vs Automated cards)
* T30: Create ManualResearchWizard component with stepper UI (6 steps)
* T31: Implement Step 1 (Planning): display collection overview, copy prompt button, paste response area, save plan action
* T32: Implement Step 2 (Result Matching): display sub-question, check matches button, match results display, strategy selection, confirm action
* T33: Implement Step 3 (Context Assembly): fetch context button (if new generation), context preview, copy prompt button
* T34: Implement Step 4 (Section Generation): paste section area, markdown preview, save section action, loop to next sub-question
* T35: Implement Step 5 (Synthesis): fetch sections button, copy synthesis prompt, paste report area, preview, save report action
* T36: Implement Step 6 (Quality Evaluation - Optional): copy quality eval prompt, paste evaluation area, save or skip
* T37: Implement completion UI (success message, link to report)
* T38: Create ResearchReportList component on collection detail page
* T39: Create ResearchReportCard component with session metadata and preview
* T40: Create ResearchReportView component with markdown rendering and citation links
* T41: Add session resume UI (show in-progress sessions, "Resume" button)
* T42: Implement clipboard copy utility functions (copy to clipboard, show toast notification)
* T43: Add loading states, error handling, and validation to wizard steps
* T44: Style wizard components using TailwindCSS and Shadcn/Radix primitives

### Phase 5: LangGraph Automation

* T45: Install langgraph dependency and configure in project
* T46: Define ResearchState TypedDict schema in src/vulcanlab/research/state.py
* T47: Implement PostgreSQL-based checkpointer (store state in research_sessions.state_data)
* T48: Create LangGraph StateGraph definition in src/vulcanlab/research/workflow.py
* T49: Implement Node 1: ResearchPlannerNode (analyzes collection, generates plan, saves to DB)
* T50: Implement Node 2: QueryExecutorNode (loops sub-questions, matches results, decides reuse, fetches context)
* T51: Implement Node 3: ContextAssemblerNode (consolidates context, applies token limits, deduplicates)
* T52: Implement Node 4: SynthesizerNode (calls LLM to generate section, saves to research_sections)
* T53: Implement Node 5: QualityEvaluatorNode (validates citations, checks coherence, calculates metrics)
* T54: Implement Node 6: RefinementCoordinatorNode (re-plans weak sections, triggers re-execution)
* T55: Configure conditional edges (quality threshold → refinement or continue, all sections complete → synthesis)
* T56: Implement workflow execution function (start_automated_research) with thread_id management
* T57: Add background task execution for automated research (FastAPI BackgroundTasks or Celery)
* T58: Implement progress tracking (update research_sessions.current_phase after each node)
* T59: Add error recovery and retry logic (exponential backoff for LLM API failures)
* T60: Write integration tests for LangGraph workflow (end-to-end with test collection)

### Phase 6: Testing + Observability + Hardening

* T61: Write unit tests for all research session API endpoints (mocked database and LLM)
* T62: Write unit tests for manual wizard UI components (mocked API calls)
* T63: Write integration tests for manual research workflow (full 6-step flow with test data)
* T64: Write integration tests for automated research workflow (LangGraph execution with test collection)
* T65: Add logging for session lifecycle events (start, phase transitions, completion, errors)
* T66: Add metrics tracking (token usage per section, total cost, execution time)
* T67: Implement session cleanup (delete old failed sessions after 30 days)
* T68: Add database query optimization (indexes on frequently queried fields)
* T69: Validate result matching similarity threshold empirically (test with sample collections)
* T70: Validate token budget allocation (ensure 20K-40K range produces quality output)

### Phase 7: Rollout

* T71: Update documentation with research session feature overview and user guide
* T72: Create sample collection with 10+ items for demo/testing
* T73: Run manual research workflow on sample collection, validate output quality
* T74: Run automated research workflow on sample collection, compare with manual output
* T75: Deploy database migrations to staging environment
* T76: Deploy backend changes to staging environment
* T77: Deploy frontend changes to staging environment
* T78: Conduct user acceptance testing (UAT) with 2-3 test users
* T79: Deploy to production environment
* T80: Monitor session creation rate, completion rate, and error logs for first week

## Testing Plan

* Unit tests:
  * All CRUD functions for ResearchSession, ResearchSection, ResearchReport (mocked database)
  * Result matching logic (similarity computation, quality scoring, strategy recommendation)
  * Context assembly logic (item fetching, token counting, deduplication)
  * Research planning logic (sub-question generation, token budget allocation)
  * All API endpoint handlers (mocked database and LLM calls)
  * All LangGraph nodes (mocked state, mocked LLM calls, verify state transitions)
  * Manual wizard UI components (mocked API responses, user interactions)

* Integration tests:
  * Full manual research workflow (create session → plan → match results → assemble context → generate sections → synthesize → save report)
  * Full automated research workflow (start session → LangGraph executes → report saved)
  * Session resume (create session, pause, resume from saved state)
  * Result reuse (create research_result items, trigger matching, verify reuse)
  * Context assembly with real collection items (excerpts, research_results, research_queries)
  * Report retrieval and markdown rendering

* Manual test plan:
  * Create collection with 10 items (3 research_results, 5 excerpts, 2 research_queries)
  * Trigger manual research workflow, complete all 6 steps
  * Verify prompt generation at each step contains correct context
  * Verify saved sections appear in database with correct metadata
  * Verify final report renders correctly with citations
  * Verify report appears in collection page report list
  * Pause manual session at step 3, close browser, resume session, verify state restored
  * Create second collection with existing research_result matching sub-question, verify result matching suggests reuse
  * Trigger automated research workflow, monitor progress, verify completion
  * Compare manual vs automated report quality for same collection

## Acceptance Criteria (Checklist)

* [ ] Database migrations create research_sessions, research_sections, research_reports tables with correct schema
* [ ] SQLAlchemy models for ResearchSession, ResearchSection, ResearchReport with relationships defined
* [ ] All 11 API endpoints implemented and return correct response formats
* [ ] "Deep Research" button appears on collection page header when collection has >= 5 items
* [ ] "Deep Research" button does NOT appear when collection has < 5 items
* [ ] Mode selection modal opens with Manual and Automated options
* [ ] Manual research wizard displays 6 steps with correct UI for each
* [ ] Step 1 (Planning) generates and copies planning prompt to clipboard
* [ ] Step 2 (Result Matching) calls match-results endpoint and displays recommendations
* [ ] Step 2 prompts user to approve reuse strategy when matches found
* [ ] Step 3 (Context Assembly) calls context endpoint and displays token count
* [ ] Step 4 (Section Generation) saves section content to database with metadata
* [ ] Step 4 loops through all sub-questions from research plan
* [ ] Step 5 (Synthesis) saves final report to research_reports table
* [ ] Step 6 (Quality Evaluation) is optional and skippable
* [ ] Session state persisted to database after each step completion
* [ ] Session can be resumed from any step by loading state from database
* [ ] Collection detail page displays list of research reports
* [ ] Report list shows session type, creation date, and executive summary preview
* [ ] Clicking report card opens full report view with markdown rendering
* [ ] Citations in report are linked back to source collection items
* [ ] Automated research mode triggers LangGraph workflow execution
* [ ] LangGraph workflow executes all 6 nodes in correct order
* [ ] Node 2 (Query Executor) checks for existing research_result matches with similarity > 0.85
* [ ] Node 2 reuses existing results when quality score meets threshold
* [ ] Node 5 (Quality Evaluator) triggers refinement when quality below threshold
* [ ] Checkpointer persists state to research_sessions.state_data after each node
* [ ] Automated session progress visible on collection page (current phase, sections completed)
* [ ] Automated session completes and saves report to research_reports table
* [ ] Unit tests pass for CRUD operations, result matching, context assembly, API endpoints, LangGraph nodes
* [ ] Integration tests pass for full manual workflow, full automated workflow, session resume
* [ ] Manual test plan completed successfully with sample collection
* [ ] No XSS vulnerabilities in markdown rendering of reports
* [ ] Session access restricted to collection owner (authorization checks)
* [ ] LLM API failures handled gracefully with retry logic (3 attempts)

## Rollout / Migration Plan

* Deploy database migrations in staging environment first, validate schema creation and indexes
* Run integration tests in staging to ensure migrations do not break existing functionality
* Deploy backend API changes to staging, smoke test all endpoints
* Deploy frontend changes to staging, test manual wizard and automated trigger end-to-end
* Conduct UAT with 2-3 internal users using staging environment
* Schedule production deployment during low-traffic window
* Deploy migrations to production database (no downtime expected, additive changes only)
* Deploy backend changes to production
* Deploy frontend changes to production
* Monitor error logs, API response times, and session creation rate for first 24 hours
* If critical issues: rollback frontend/backend (database rollback not needed, additive schema)
* If successful: announce feature to users with documentation link

## Risks and Alternatives

* Risks:
  * LangGraph automation may produce lower-quality reports than manual workflow → Mitigation: Implement quality thresholds and refinement loops, allow users to choose manual mode for critical research
  * Result reuse may introduce stale or incorrect information → Mitigation: Implement freshness checks, similarity thresholds, and user approval in manual mode
  * Token budget estimation may be inaccurate leading to context truncation or bloat → Mitigation: Test empirically with sample collections, add dynamic adjustment logic based on actual usage
  * Manual wizard may be too complex for users unfamiliar with LLM prompting → Mitigation: Provide clear instructions, example prompts, and tooltips at each step
  * Session state JSONB may grow too large causing database performance issues → Mitigation: Implement state compression, archive old sessions, monitor JSONB column sizes
  * LLM API rate limits may block automated research completion → Mitigation: Implement exponential backoff, queue system for concurrent sessions, fallback to manual mode
  * Citation hallucination in LLM-generated sections → Mitigation: Basic validation (check if cited works exist in collection), clear user guidance to review citations

* Alternatives considered:
  * Alternative 1 (Manual-only implementation first): Implement only manual workflow, defer LangGraph automation to Phase 2 → Rejected because user explicitly requested both modes in scope
  * Alternative 2 (CLI scripts instead of web wizard): Use Python CLI scripts with clipboard integration (as in deep-research-strategy.md) → Rejected because user requested web-based UI (Q3)
  * Alternative 3 (Celery for background tasks): Use Celery instead of FastAPI BackgroundTasks for automated research → Considered but deferred; BackgroundTasks sufficient for MVP, can migrate to Celery if needed
  * Alternative 4 (Separate vector index for result matching): Build dedicated vector index for research_result queries → Deferred; use existing embedding infrastructure, optimize if performance issues arise
  * Alternative 5 (Real-time LLM streaming in manual mode): Stream LLM responses directly in wizard UI → Out of scope (user uses external LLM interface per Q10)

## Patterns and Standards Alignment (from documentation/patterns.md)

* Patterns applied:
  * **Three-tier architecture** - Core logic in src/vulcanlab/research, API layer in src/vulcanlab_api/routers/research_sessions.py, UI in vulcanlab_ui/src/components/research
  * **Session management** - Database sessions passed explicitly to CRUD functions (not created inside core logic)
  * **API versioning** - All routes prefixed with /api/v1 in main.py router inclusion
  * **Global exception handling** - API endpoints raise specific exceptions (ValueError, HTTPException), let global handler catch unhandled 500s
  * **Dual configuration system** - Core logic uses vulcanlab.config for LLM settings, API uses vulcanlab_api.config for server settings
  * **React Server Components** - Collection page uses RSC for initial data fetching, wizard uses Client Components ("use client") for interactivity
  * **usePageData hook** - Report list component uses usePageData for session fetching with loading/error states
  * **useCallback for fetch functions** - All fetch functions wrapped in useCallback to avoid infinite rendering loops
  * **FormField wrapper** - Manual wizard uses react-hook-form with FormField for all user input (text areas, dropdowns)
  * **Component composition** - Wizard built from smaller components (StepHeader, PromptDisplay, ResponseInput, SectionPreview)
  * **Shadcn/Radix components** - Modal uses Dialog primitive, wizard uses Stepper/Tabs, buttons use Button primitive
  * **TailwindCSS for styling** - All UI components use utility classes, theme-aware (text-foreground, bg-card)
  * **Database seeding pattern** - If prompt templates needed for research workflow, use YAML config + .txt files in src/vulcanlab/data/seed_data/

* Deviations (if any):
  * **LangGraph dependency** - Adds new external dependency not currently in patterns.md → Justification: Required for automated orchestration, well-maintained library from LangChain ecosystem, aligns with agentic workflow goals
  * **JSONB state storage** - Heavy use of JSONB for state_data, research_plan, metadata → Justification: Enables flexible schema evolution, checkpointer compatibility, avoids complex relational models for ephemeral state
  * **Background task execution** - Uses FastAPI BackgroundTasks (not mentioned in patterns.md) → Justification: Simplest solution for MVP, can migrate to Celery if scaling needed, aligns with "avoid over-engineering" principle

## Implementation Notes (Non-binding)

* Consider using a queue system (Redis + Celery) if multiple automated sessions cause LLM API rate limiting
* Thread ID format (manual_{timestamp}_{random} vs auto_{collection_id}_{timestamp}) enables easy filtering and debugging
* State compression: If state_data JSONB grows large (>100KB), consider compressing with gzip before storage
* Prompt templates: Store reusable prompts in database or seed_data if they need versioning and updates
* Citation link format: Use markdown link syntax [Author Year, pp. X-Y](link://collection-item/{item_id}) and parse in frontend
* Quality scoring weights: Start with citation_density=40%, freshness=20%, completeness=15%, source_diversity=15%, model_quality=10%, tune empirically
* Embedding model: Use existing VulcanLab embedding infrastructure (likely sentence-transformers or OpenAI embeddings)
* Token counting: Use tiktoken library (OpenAI) or equivalent for accurate token estimation before LLM calls
* Session cleanup: Implement scheduled job to delete failed/paused sessions older than 30 days to avoid database bloat
* Report versioning: If users regenerate reports for same session, increment version field rather than overwriting
* Refinement loop limit: Cap Node 6 refinement iterations at 2 to avoid infinite loops if quality never reaches threshold
* Modal vs dedicated page: Start with modal for wizard, consider dedicated /research-session/{id} page if wizard becomes too complex
* Markdown renderer: Use react-markdown with remark-gfm plugin, sanitize with rehype-sanitize to prevent XSS

## Open Questions

* Q1: Should the system automatically trigger citation validation after Step 5 (Synthesis) in manual mode, or only if user clicks "Evaluate Quality"?
* Q2: What is the expected maximum collection size (number of items) for automated research? (affects token budget and performance testing)
* Q3: Should automated research sessions be resumable if they fail mid-execution, or should they restart from beginning?
* Q4: If a user deletes a collection item that was cited in a research report, should the report be marked as "stale" or citation broken?
* Q5: Should the system support exporting research plans (Step 1 output) as standalone JSON files for reuse across collections?
* Q6: What LLM model should be used for automated research nodes? (Use default from vulcanlab.config or allow user selection?)
* Q7: Should ensemble synthesis (combining multiple research_result items) use all matched results or cap at 3 best results to control token usage?
* Q8: Should the "Deep Research" button be hidden if user lacks sufficient LLM API credits/quota?
