# Ticket: work-summarization.T08 - Summarization Orchestrator

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement the main orchestrator that coordinates the full summarization workflow for a work
* Manage progress tracking, error handling, and partial recovery
* Handle re-summarization with existing data cleanup

## Phase

* Core Modules

## Scope

### In scope

* src/vulcanlab/summarize/orchestrator.py module
* Main entry point: summarize_work(work_id, session)
* Progress tracking (total nodes, completed nodes, current status)
* Node-by-node processing with database commits
* Escalation loop coordination when LLM reports insufficient evidence
* Error handling with partial recovery (resume from last successful node)
* Re-summarization support: delete existing summary_nodes before regenerating
* Transaction management per node (not full work)
* Status persistence for progress queries

### Out of scope

* Derived output compilation (T09)
* API endpoints (T11)
* UI progress display (T14, T16)

## Dependencies

* Depends on: T03 (models), T05 (evidence), T06 (node selector), T07 (LLM summarize)
* Unblocks: T09, T11

## Implementation plan

1. Create src/vulcanlab/summarize/orchestrator.py
2. Define status dataclasses:
   - `SummarizationProgress(work_id: int, status: str, total_nodes: int, completed_nodes: int, current_node: str | None, error: str | None)`
   - Status enum: 'pending', 'in_progress', 'completed', 'failed'
3. Implement `get_summarization_status(work_id: int, session: Session) -> SummarizationProgress | None`:
   - Check if summary_nodes exist for work
   - Return progress info or None if never started
4. Implement `delete_existing_summaries(work_id: int, session: Session)`:
   - Delete all summary_nodes for work
   - Delete all work_summaries for work
   - Used for re-summarization
5. Implement `load_full_content(work_id: int, session: Session) -> str`:
   - Load sanitized markdown content for the work
   - Used for escalation context extraction
6. Implement `create_summary_node(selected_node: SelectedNode, summary_response: SummaryResponse, session: Session) -> SummaryNode`:
   - Map SummaryResponse fields to SummaryNode model
   - Convert dataclasses to JSON for JSONB columns
   - Insert and return
7. Implement `process_single_node(node: SelectedNode, full_content: str, session: Session) -> SummaryNode`:
   - Build evidence packet from node content
   - Call LLM summarization
   - If insufficient evidence, run escalation and retry once
   - Create and return SummaryNode
8. Implement `summarize_work(work_id: int, session: Session, force_regenerate: bool = False) -> SummarizationProgress`:
   - If force_regenerate, delete existing summaries
   - If summaries exist and not force_regenerate, return existing status
   - Select nodes for summarization
   - Load full content for escalation
   - Process each node with individual commits
   - Update progress after each node
   - Handle errors: log, mark failed, allow resume
   - Return final progress
9. Implement `resume_summarization(work_id: int, session: Session) -> SummarizationProgress`:
   - Find last completed node
   - Continue from next node
* Patterns to apply:
  * Session passed explicitly
  * Core Module independence
  * Per-node transactions for recovery
  * Logging with work_id context
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * `get_summarization_status` returns None for work with no summaries
  * `get_summarization_status` returns correct progress for partial completion
  * `delete_existing_summaries` removes all summary_nodes and work_summaries
  * `create_summary_node` correctly maps all fields
  * `create_summary_node` converts dataclasses to JSON
  * `process_single_node` calls evidence extraction and LLM
  * `process_single_node` triggers escalation on insufficient evidence
  * `summarize_work` processes all selected nodes
  * `summarize_work` handles force_regenerate flag
  * `summarize_work` returns early if summaries exist and not forcing
  * Error handling: node failure doesn't stop entire process
  * `resume_summarization` continues from correct point
* Suggested locations:
  * tests/unit/summarize/test_orchestrator.py
* Mocking/fakes needed:
  * Mock node selector
  * Mock evidence extractor
  * Mock LLM summarizer
  * Mock session with fake DB operations

## Acceptance criteria (checklist)

* [ ] summarize_work processes all selected nodes
* [ ] Progress tracked accurately (total, completed, status)
* [ ] Per-node commits enable partial recovery
* [ ] Escalation triggered when LLM reports insufficient evidence
* [ ] Re-summarization deletes existing data first
* [ ] Existing summaries detected (no duplicate work)
* [ ] Errors logged with sufficient context
* [ ] Failed status set on unrecoverable error
* [ ] Resume continues from last successful node
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Run summarize_work on a test work
  2. Interrupt mid-way (kill process)
  3. Check database: partial summary_nodes should exist
  4. Run resume_summarization
  5. Verify completion
* Expected results:
  * Partial progress preserved
  * Resume completes remaining nodes
  * Final status is 'completed'

## Notes

* Requirements covered: R1, R2, R8, R15, R17
* Per-node commits are critical for recovery - don't batch all in one transaction
* Progress can be stored in-memory for now; consider adding progress table for persistence across restarts
* Escalation is limited to one retry per node to avoid runaway costs
* force_regenerate=True maps to R17 (re-summarize with confirmation)
* Logging should include work_id, node count, and timing for observability
