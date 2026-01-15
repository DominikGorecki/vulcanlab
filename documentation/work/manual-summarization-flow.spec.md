# Title: Manual Summarization Flow

## Summary

* Add a manual execution mode for work summarization where users copy prompts and paste LLM responses step-by-step
* Present a choice dialog (manual vs automatic) when user clicks "Summarize" on the Corpus work detail page
* Implement a wizard UI that guides users through each summary node one at a time with copy/paste workflow
* Track manual summarization sessions in the database for resumability
* Extend manual mode support to derived output generation (abstract, outline, key_concepts, chapter_summaries)
* Expose the exact same prompts used by the automated flow for transparency

## Problem / Context

* The current summarization feature only supports automated LLM execution
* Users may want to use their own LLM interface (Claude web, ChatGPT, etc.) for cost control or preference reasons
* Other features in VulcanLab (simple conversion, deep research) already support manual copy/paste workflows
* Users cannot currently pause and resume summarization if using external LLMs
* No visibility into the actual prompts being sent to LLMs during automated summarization

## Goals

* Allow users to choose between manual and automatic summarization modes
* Provide a step-by-step wizard for manual summarization with one node at a time
* Enable session persistence so users can pause and resume manual summarization
* Maintain prompt transparency by exposing the exact prompts used in automated mode
* Support manual mode for both initial node summarization and derived output generation

## Non-goals (Strict)

* Batch/parallel manual prompt handling (all nodes at once) - explicitly out of scope per requirements
* Creating simplified or alternative prompts for manual mode - must use identical prompts as automated
* Hybrid mode where some nodes are manual and others automatic within the same session
* Manual mode for the salience scoring or evidence extraction phases (these remain automatic)
* Real-time validation of pasted LLM responses before submission

## Scope

### In scope

* New `summarization_sessions` table to track manual/automated session state
* Mode selection dialog when clicking "Summarize" on Corpus detail page
* Manual summarization wizard page with single-node-at-a-time workflow
* API endpoints to get formatted prompts for each node and derived output type
* API endpoints to submit manual LLM responses and advance session state
* Session resumption from last completed node
* Manual mode for derived output generation (abstract, outline, key_concepts, chapter_summaries)

### Out of scope

* Modifying existing automated summarization logic (it remains unchanged)
* Bulk prompt export/import functionality
* Response validation or format checking beyond basic JSON parsing
* Integration with external LLM APIs for manual mode (purely copy/paste)

## Requirements (Functional)

* R1: When user clicks "Summarize" on Corpus detail page, system SHALL display a modal with manual/automatic mode selection
* R2: Selecting "Automatic" SHALL trigger existing automated summarization flow unchanged
* R3: Selecting "Manual" SHALL create a new summarization_session with type='manual' and redirect to wizard page
* R4: Manual wizard SHALL display one node at a time in sequential order (by salience score descending)
* R5: For each node, wizard SHALL show: heading path, evidence packet preview, copy-to-clipboard prompt button
* R6: The prompt exposed for manual mode SHALL be identical to prompts used in automated `llm_summarize.py`
* R7: User SHALL paste LLM response in a textarea and submit to advance to next node
* R8: System SHALL parse submitted response and create summary_node record identical to automated flow
* R9: Session progress SHALL be persisted to database after each node completion
* R10: User SHALL be able to navigate away and resume session from last completed node
* R11: Resuming a session SHALL skip already-completed nodes and continue from next pending node
* R12: After all nodes complete, user SHALL be redirected to the work summary detail page
* R13: Derived output generation (abstract, outline, key_concepts, chapter_summaries) SHALL support manual mode
* R14: Manual derived output flow SHALL show prompt, accept pasted response, and store result
* R15: Re-summarization with manual mode SHALL delete existing session and nodes before starting fresh
* R16: Session status (pending, in_progress, completed, failed) SHALL be queryable via API

## Requirements (Non-functional)

* Performance:
  * Prompt generation for manual mode SHALL complete within 5 seconds per node
  * Session state queries SHALL complete within 500ms

* Reliability:
  * Session state SHALL survive server restarts (database-backed)
  * Partial session completion SHALL be recoverable at any point
  * Invalid JSON responses SHALL display clear error messages without corrupting session state

* Security / Privacy:
  * No additional authentication required (uses existing session)
  * Prompts may contain work content; same security model as automated flow

* Observability:
  * Manual session creation and completion SHALL be logged
  * Failed response parsing attempts SHALL be logged with context

## Proposed Solution (High-level)

* Architecture follows existing three-tier pattern: Core Module -> API Layer -> Frontend
* New `summarization_sessions` table tracks session type, status, and progress
* Core module adds prompt formatting functions that expose internal prompt construction
* API layer adds endpoints for session management and prompt/response handling
* Frontend adds mode selection dialog and multi-step wizard component

### Data Flow (Manual Mode)

1. User clicks "Summarize" on Corpus detail page -> mode selection dialog appears
2. User selects "Manual" -> API creates session, selects nodes, returns session_id
3. Frontend redirects to `/summarize/manual/[work_id]` wizard page
4. Wizard fetches current node prompt from API -> displays with copy button
5. User copies prompt, uses external LLM, pastes response -> submits
6. API parses response, creates summary_node, advances session -> returns next node
7. Repeat steps 4-6 until all nodes complete
8. Wizard redirects to `/summarize/[work_id]` detail page
9. For derived outputs, similar copy/paste flow on detail page with manual mode toggle

## Interfaces / APIs / Contracts

* `POST /api/v1/summarize/{work_id}/session` - Create new summarization session
  * Body: `{ mode: "manual" | "automatic" }`
  * Response: `{ session_id: int, mode: string, status: string, total_nodes: int }`

* `GET /api/v1/summarize/{work_id}/session` - Get current session state
  * Response: `{ session_id: int, mode: string, status: string, current_node_index: int, total_nodes: int, completed_nodes: int }`

* `GET /api/v1/summarize/{work_id}/session/current-prompt` - Get prompt for current node
  * Response: `{ node_index: int, heading_path: string, evidence_preview: string, prompt: string, chunk_id: int }`

* `POST /api/v1/summarize/{work_id}/session/submit` - Submit manual response for current node
  * Body: `{ response: string }`
  * Response: `{ success: bool, next_node_index: int | null, completed: bool, error?: string }`

* `DELETE /api/v1/summarize/{work_id}/session` - Cancel/delete current session
  * Response: `{ success: bool }`

* `GET /api/v1/summarize/{work_id}/derive/{type}/prompt` - Get prompt for derived output (manual mode)
  * Response: `{ type: string, prompt: string }`

* `POST /api/v1/summarize/{work_id}/derive/{type}/manual` - Submit manual derived output response
  * Body: `{ response: string }`
  * Response: `{ success: bool, summary_id: int, error?: string }`

## Data Model / Storage

### summarization_sessions table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| work_id | INTEGER | FK works(id) ON DELETE CASCADE, NOT NULL, UNIQUE | One active session per work |
| mode | VARCHAR(20) | NOT NULL, CHECK (mode IN ('manual', 'automatic')) | Session execution mode |
| status | VARCHAR(20) | NOT NULL, CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')) | Current session status |
| current_node_index | INTEGER | NOT NULL, DEFAULT 0 | Index of current node being processed |
| total_nodes | INTEGER | NOT NULL | Total nodes selected for summarization |
| selected_node_ids | JSONB | NOT NULL | Ordered array of chunk_ids to process |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Session creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update time |

### Enum additions (enums.py)

```python
class SummarizationMode(str, enum.Enum):
    """
    IMPORTANT: Values MUST match database CHECK constraint exactly (lowercase):
    CHECK (mode IN ('manual', 'automatic'))
    """
    MANUAL = 'manual'
    AUTOMATIC = 'automatic'
```

## UX / Workflows

### Workflow 1: Start Manual Summarization

1. User navigates to Corpus page, clicks on a work to view details
2. User clicks "Summarize" button in the work detail header
3. Modal appears with two options: "Manual" and "Automatic"
4. User selects "Manual" and clicks "Start"
5. System creates session, selects nodes based on salience, redirects to wizard

### Workflow 2: Complete Manual Summarization Wizard

1. User sees wizard page showing: progress indicator, heading path, evidence preview
2. User clicks "Copy Prompt" to copy formatted prompt to clipboard
3. User pastes prompt into external LLM (Claude, ChatGPT, etc.)
4. User copies LLM response and pastes into response textarea
5. User clicks "Submit & Continue"
6. System validates JSON, creates summary_node, advances to next node
7. Repeat until all nodes complete
8. System shows success message and redirects to summary detail page

### Workflow 3: Resume Manual Summarization

1. User navigates to Summarize list page or Corpus detail page
2. System detects existing in_progress manual session
3. User clicks "Resume" button
4. Wizard loads at last incomplete node
5. User continues from step 2 of Workflow 2

### Workflow 4: Manual Derived Output Generation

1. User on summary detail page clicks "Generate Abstract" (or other derived type)
2. Modal appears with manual/automatic toggle (defaults to user's preference)
3. If manual: modal shows prompt with copy button and response textarea
4. User copies prompt, gets LLM response, pastes and submits
5. System parses response and stores derived output

## Work Breakdown (Ticket Seed)

### Phase 0: Foundations

* T01: Add `SummarizationMode` enum to enums.py following existing patterns

### Phase 1: Data / Migrations

* T02: Create migration for `summarization_sessions` table with indexes and constraints
* T03: Add SQLAlchemy model `SummarizationSession` in models/
* T04: Update init_db.py with new table creation and enum

### Phase 2: Core Domain / Modules

* T05: Implement prompt formatter module (src/vulcanlab/summarize/prompt_formatter.py)
  * Extract prompt construction logic from llm_summarize.py into reusable functions
  * `format_node_summarization_prompt(evidence, chunk_id, session)` -> string
  * `format_derived_output_prompt(type, summary_nodes, session)` -> string
  * Ensure identical prompts to automated flow

* T06: Implement session manager module (src/vulcanlab/summarize/session_manager.py)
  * `create_session(work_id, mode, session)` -> SummarizationSession
  * `get_session(work_id, session)` -> SummarizationSession | None
  * `get_current_node(session_obj, db_session)` -> SelectedNode | None
  * `advance_session(session_obj, db_session)` -> next_index | None
  * `complete_session(session_obj, db_session)`
  * `delete_session(work_id, db_session)`

* T07: Implement manual response parser (src/vulcanlab/summarize/response_parser.py)
  * `parse_node_response(response_text)` -> SummaryResponse
  * `parse_derived_response(type, response_text)` -> dict
  * Reuse existing parsing logic from llm_summarize.py
  * Clear error messages for malformed responses

* T08: Update orchestrator to use sessions for both modes
  * Modify `summarize_work()` to create automatic session and track progress
  * Add `summarize_node_manual(work_id, response_text, session)` for manual submissions

### Phase 3: External APIs / Integrations

* T09: Create summarize session endpoints (extend src/vulcanlab_api/routers/summarize.py)
  * POST /{work_id}/session - create session
  * GET /{work_id}/session - get session state
  * GET /{work_id}/session/current-prompt - get current node prompt
  * POST /{work_id}/session/submit - submit manual response
  * DELETE /{work_id}/session - delete session

* T10: Add manual derived output endpoints
  * GET /{work_id}/derive/{type}/prompt - get derived output prompt
  * POST /{work_id}/derive/{type}/manual - submit manual derived response

* T11: Add Pydantic schemas for new endpoints (schemas/summarize.py)

### Phase 4: UI / Client

* T12: Create SummarizeModeDialog component (components/summarize/summarize-mode-dialog.tsx)
  * Modal with Manual/Automatic selection
  * Brief description of each mode
  * Start button that triggers appropriate flow

* T13: Update Corpus detail page to use mode dialog
  * Replace direct summarization trigger with dialog open
  * Handle both mode selections appropriately

* T14: Create ManualSummarizationWizard page (app/summarize/manual/[work_id]/page.tsx)
  * Progress indicator (node X of Y)
  * Current node info display (heading path, evidence preview)
  * Copy prompt button with success feedback
  * Response textarea with submit button
  * Navigation: back to corpus, cancel session

* T15: Add session resume detection to Corpus detail page and Summarize list page
  * Check for existing in_progress session on load
  * Show "Resume Manual Summarization" button if session exists

* T16: Add manual mode toggle to derived output generation on summary detail page
  * Toggle switch in generation modal
  * Show prompt/response UI when manual mode selected

### Phase 5: Testing + Observability + Hardening

* T17: Unit tests for prompt_formatter module
* T18: Unit tests for session_manager module
* T19: Unit tests for response_parser module
* T20: API integration tests for session endpoints
* T21: Add logging for session lifecycle events

### Phase 6: Rollout

* T22: Update documentation with manual summarization workflow guide
* T23: Manual testing checklist execution

## Testing Plan

* Unit tests:
  * prompt_formatter: verify prompts match automated flow exactly
  * session_manager: test create, advance, complete, delete operations
  * response_parser: test valid JSON parsing, error handling for malformed responses
  * Test session state persistence and recovery

* Integration tests:
  * Full manual flow: create session -> get prompts -> submit responses -> complete
  * Session resume: partial completion -> resume -> complete
  * Derived output manual flow

* Manual test plan:
  * [ ] Click Summarize, select Manual, verify wizard loads with first node
  * [ ] Copy prompt, use external LLM, paste response, verify node created
  * [ ] Navigate away mid-session, return, verify resume works
  * [ ] Complete all nodes, verify redirect to summary detail page
  * [ ] Verify prompts are identical between manual display and automated logs
  * [ ] Test manual derived output generation for each type
  * [ ] Test re-summarization in manual mode (delete existing, start fresh)
  * [ ] Test error handling for invalid JSON responses
  * [ ] Test canceling a manual session

## Acceptance Criteria (Checklist)

* [ ] Clicking "Summarize" on Corpus detail page shows mode selection dialog
* [ ] Selecting "Automatic" triggers existing automated flow unchanged
* [ ] Selecting "Manual" creates session and redirects to wizard page
* [ ] Wizard displays one node at a time with heading path and evidence preview
* [ ] Copy prompt button copies exact prompt used by automated flow
* [ ] Submitting valid response creates summary_node and advances to next node
* [ ] Session progress persists to database and survives page refresh
* [ ] In-progress sessions can be resumed from Corpus or Summarize pages
* [ ] All nodes completing redirects to summary detail page
* [ ] Derived outputs support manual mode with copy/paste workflow
* [ ] Invalid JSON responses show clear error without corrupting session
* [ ] Re-summarization in manual mode properly clears existing data

## Rollout / Migration Plan

* Migration adds `summarization_sessions` table (additive only)
* No changes to existing `summary_nodes` or `work_summaries` tables
* Feature is opt-in: users choose mode when starting summarization
* Existing automated flow remains default and unchanged
* Rollback: drop `summarization_sessions` table (no impact on existing summaries)

## Risks and Alternatives

* Risks:
  * Users may paste incorrectly formatted responses; mitigated by clear error messages and JSON validation
  * Long works with many nodes may lead to tedious manual workflow; mitigated by showing progress and allowing pause/resume
  * Prompts exposed in manual mode reveal internal implementation; accepted as this is the explicit goal (transparency)
  * Session table adds minor complexity; mitigated by simple schema and clear lifecycle

* Alternatives considered:
  * **Batch prompt mode**: Rejected per requirements; one-at-a-time wizard preferred
  * **Simplified prompts for manual mode**: Rejected; transparency requires identical prompts
  * **In-memory session tracking**: Rejected; database persistence required for resume functionality
  * **Hybrid manual/automatic within session**: Rejected as explicit non-goal to keep UX simple

## Patterns and Standards Alignment (from documentation/patterns.md)

* Patterns applied:
  * **Three-tier architecture**: Core logic in vulcanlab/summarize, thin API layer, React frontend
  * **Session management**: Database sessions passed explicitly to functions
  * **API versioning**: All new routes under /api/v1/summarize prefix
  * **Enum capitalization**: New SummarizationMode enum uses lowercase values matching DB CHECK
  * **UI Page Lifecycle**: Wizard page uses usePageData hook with useCallback-wrapped fetch
  * **Prompt Templates**: Manual prompts loaded from database via existing template system
  * **Database initialization**: New table in schema/specialized_tables.py, migration in migrations/

* Deviations (if any):
  * None identified; spec follows all patterns.md guidelines

## Implementation Notes (Non-binding)

* Prompt extraction from llm_summarize.py should be a refactor, not duplication
* Consider adding a "Copy All Prompts" future enhancement (out of scope now)
* The wizard UI can reuse patterns from ManualResearchWizard and simple-conversion manual page
* Session cleanup: consider adding a background job to delete stale sessions (>7 days old, still pending)
* The evidence preview in wizard should be truncated for readability (first 500 chars)

## Open Questions

* None - all questions resolved during spec creation.
