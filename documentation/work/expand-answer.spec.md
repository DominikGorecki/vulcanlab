# Title: Expand Answer Feature

## Summary

- Adds ability to expand any RAG research result into a comprehensive multi-section report
- First LLM call breaks the original answer into 3-7 logical sections with headings, summaries, and generated prompts
- Each section runs through the full RAG pipeline (expansion, retrieval, augmentation) independently
- Sections can be processed automatically or manually with per-section status tracking
- Final output combines all section responses into one unified document
- Expanded answers appear in a dedicated "Expansions" view with links from the source result

## Problem / Context

- Current RAG answers provide a single response that may lack depth on complex topics
- Users have no way to systematically expand an answer into a more comprehensive report
- When a RAG answer covers multiple themes, users must manually create separate queries for each
- No workflow exists to break down an answer, research each part, and recombine into a structured report

## Goals

- Enable one-click expansion of any RAG result into a multi-section deep-dive report
- Leverage existing RAG infrastructure (expansion, retrieval, consolidation, augmentation) for each section
- Provide visibility into expansion progress with per-section status and retry capability
- Support both automatic (LLM-driven) and manual (copy/paste) execution modes
- Store expansion data separately from standard queries to avoid polluting the main query list

## Non-goals (Strict)

- User editing or reordering of AI-generated sections (sections are generated and fixed)
- Specifying target section count (AI determines 3-7 sections based on content)
- Real-time WebSocket/SSE progress updates (polling-based status is sufficient)
- Recursive expansion (expanding an already-expanded answer)
- Exporting expanded reports to external formats (PDF, DOCX)

## Scope

### In scope

- New data models: `AnswerExpansion`, `ExpansionSection`
- LLM prompt template for breaking down answers into sections
- API endpoints for expansion lifecycle (create, get status, run sections, combine)
- Core module logic for section breakdown and section-level RAG orchestration
- UI: "Expand" button on result detail page
- UI: Expansions list view with status indicators
- UI: Expansion detail page showing sections and combined report
- Per-section retry capability for failed sections
- Toggle between automatic and manual execution modes

### Out of scope

- Batch expansion of multiple results
- Scheduling/background job processing (expansions run synchronously or via existing patterns)
- Custom prompt templates per expansion (uses single system template)
- Version history for expansions

## Requirements (Functional)

- R1: User can initiate expansion from the result detail page (`/rag/{query_id}/results/{result_id}`)
- R2: System validates source answer is under 30,000 estimated tokens before breakdown; rejects with error if exceeded
- R3: System breaks the original answer into 3-7 sections via LLM, each with: heading, summary, expansion prompt, and query expansion data
- R4: Each section's expansion prompt goes through the full RAG pipeline (vectorize, retrieve, consolidate, augment)
- R5: User can toggle between automatic mode (system runs all section LLM calls) and manual mode (user copies prompts and pastes responses)
- R6: Automatic mode processes sections with limited parallelism (2 concurrent sections) to balance speed and API rate limits
- R7: System tracks per-section status: `pending`, `expanding`, `ready`, `generating`, `completed`, `failed`
- R8: User can retry any failed section without restarting the entire expansion
- R9: Once all sections complete, system combines section responses into a single unified report
- R10: Combined report includes a link back to the original answer (not the answer text itself)
- R11: Expanded answers are accessible via a dedicated Expansions view, separate from the main Queries list
- R12: Result detail page shows link to its expansion (if one exists)
- R13: Expansion data does not create entries in the standard `queries` table

## Requirements (Non-functional)

- Performance:
  - Source answer validated against 30,000 token limit (using existing token estimation heuristic) before processing
  - Initial breakdown LLM call should complete within 30 seconds
  - Section RAG pipeline should reuse existing retrieval infrastructure without degradation
  - Automatic mode processes 2 sections concurrently to balance speed and API rate limits
  - UI should remain responsive during automatic expansion (no blocking)

- Reliability:
  - Failed sections should not block other sections from completing
  - Expansion state should be persisted so users can resume after page refresh
  - Database transactions should be scoped per-section to avoid large rollbacks

- Security / Privacy:
  - Expansion endpoints follow existing API authentication patterns
  - No new sensitive data exposure beyond what exists in RAG results

- Observability:
  - Log expansion creation, section transitions, and failures
  - Include expansion_id and section_id in log context

## Proposed Solution (High-level)

- New `AnswerExpansion` model links to source `Result`, stores combined report and metadata
- New `ExpansionSection` model stores per-section data: question, prompt, RAG context, response, status
- Breakdown step: LLM parses original answer into structured JSON with sections
- Section processing: Each section creates ephemeral query data (not in `queries` table), runs full RAG pipeline, stores results in `ExpansionSection`
- Combination step: After all sections complete, concatenate responses with headings into `AnswerExpansion.combined_report`
- API endpoints under `/api/v1/expansions/` for CRUD and operations
- UI components: Expand button, Expansions list page, Expansion detail page

## Interfaces / APIs / Contracts

### Endpoints

- `POST /api/v1/expansions/` - Create expansion from result_id, returns expansion_id
- `GET /api/v1/expansions/` - List all expansions with status summary
- `GET /api/v1/expansions/{expansion_id}` - Get expansion detail with sections
- `POST /api/v1/expansions/{expansion_id}/breakdown` - Run initial breakdown LLM call
- `POST /api/v1/expansions/{expansion_id}/sections/{section_id}/expand` - Run RAG pipeline for section
- `POST /api/v1/expansions/{expansion_id}/sections/{section_id}/generate` - Run LLM generation for section
- `POST /api/v1/expansions/{expansion_id}/sections/{section_id}/manual` - Save manual response for section
- `POST /api/v1/expansions/{expansion_id}/combine` - Combine completed sections into final report
- `GET /api/v1/results/{result_id}/expansion` - Get expansion for a result (if exists)

### Request/Response Shapes

```
CreateExpansionRequest:
  result_id: int
  mode: "automatic" | "manual"

CreateExpansionResponse:
  expansion_id: int
  status: "created"

ExpansionDetailResponse:
  id: int
  result_id: int
  query_id: int
  original_answer_url: str  # e.g., "/rag/{query_id}/results/{result_id}"
  source_answer_preview: str (first 500 chars)
  mode: "automatic" | "manual"
  status: "created" | "breakdown_pending" | "breakdown_complete" | "sections_in_progress" | "combining" | "completed" | "failed"
  sections: list[SectionSummary]
  combined_report: str | null
  created_at: datetime
  updated_at: datetime

SectionSummary:
  id: int
  order: int
  heading: str
  summary: str
  status: "pending" | "expanding" | "ready" | "generating" | "completed" | "failed"
  error_message: str | null

SectionDetailResponse:
  id: int
  heading: str
  summary: str
  expansion_prompt: str
  expanded_queries: list[str] | null
  hyde_answer: str | null
  intent: str | null
  entities: list[str] | null
  clean_retrieval_context: list[dict] | null
  augmented_prompt: str | null
  response_text: str | null
  status: str
  error_message: str | null
```

## Data Model / Storage

### New Tables

**answer_expansions**
| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PRIMARY KEY |
| result_id | INTEGER | NOT NULL, FK results(id) ON DELETE CASCADE, UNIQUE |
| query_id | INTEGER | NOT NULL, FK queries(id) ON DELETE CASCADE |
| mode | VARCHAR(20) | NOT NULL, CHECK IN ('automatic', 'manual') |
| status | VARCHAR(30) | NOT NULL, CHECK IN ('created', 'breakdown_pending', 'breakdown_complete', 'sections_in_progress', 'combining', 'completed', 'failed') |
| combined_report | TEXT | NULL |
| metadata | JSONB | NULL |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |

Note: `query_id` stored to enable link back to original answer context (`/rag/{query_id}/results/{result_id}`).

**expansion_sections**
| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PRIMARY KEY |
| expansion_id | INTEGER | NOT NULL, FK answer_expansions(id) ON DELETE CASCADE |
| order | INTEGER | NOT NULL |
| heading | VARCHAR(500) | NOT NULL |
| summary | TEXT | NOT NULL |
| expansion_prompt | TEXT | NOT NULL |
| expanded_queries | JSONB | NULL |
| hyde_answer | TEXT | NULL |
| intent | VARCHAR(200) | NULL |
| entities | JSONB | NULL |
| retrieved_context | JSONB | NULL |
| clean_retrieval_context | JSONB | NULL |
| augmented_prompt | TEXT | NULL |
| response_text | TEXT | NULL |
| status | VARCHAR(20) | NOT NULL, CHECK IN ('pending', 'expanding', 'ready', 'generating', 'completed', 'failed') |
| error_message | TEXT | NULL |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |

### Indexes

- `idx_answer_expansions_result_id` on `answer_expansions(result_id)`
- `idx_answer_expansions_status` on `answer_expansions(status)`
- `idx_expansion_sections_expansion_id` on `expansion_sections(expansion_id)`
- `idx_expansion_sections_status` on `expansion_sections(status)`

### Relationships

- `Result` 1:0..1 `AnswerExpansion` (one result can have at most one expansion)
- `AnswerExpansion` 1:N `ExpansionSection` (one expansion has 3-7 sections)

## UX / Workflows

### Workflow 1: Initiate Expansion

1. User views result detail page at `/rag/{query_id}/results/{result_id}`
2. User clicks "Expand Answer" button
3. Modal appears with mode toggle (Automatic / Manual)
4. User selects mode and confirms
5. System creates expansion record, redirects to expansion detail page

### Workflow 2: Automatic Expansion

1. System runs breakdown LLM call, creates sections
2. Sections processed with limited parallelism (2 concurrent):
   - Run query expansion (MQE, HyDE, intent, entities)
   - Generate embeddings for section query
   - Retrieve relevant chunks
   - Consolidate context
   - Generate augmented prompt
   - Run LLM to generate section response
3. Once all sections complete, combine into final report with link to original answer
4. User sees completed expansion with full report

### Workflow 3: Manual Expansion

1. System runs breakdown LLM call, creates sections
2. For each section, user:
   - Clicks section to view expansion prompt
   - Copies prompt, runs in external LLM
   - Pastes response back into UI
   - System saves response, marks section complete
3. Once all sections have responses, user clicks "Combine"
4. System generates combined report

### Workflow 4: Retry Failed Section

1. User views expansion with one or more failed sections
2. User clicks "Retry" on failed section
3. System re-runs the failed step (expand, generate, or full pipeline)
4. Section status updates accordingly

## Work Breakdown (Ticket Seed)

### Phase 0: Foundations

- T01: Add `AnswerExpansion` and `ExpansionSection` SQLAlchemy models with enums
- T02: Add schema creation in `specialized_tables.py` (idempotent)
- T03: Create prompt template file and YAML entry for `answer_breakdown`
- T04: Add `FUNCTION_LABELS` entry in UI template settings

### Phase 1: Data / Migrations

- T05: Verify schema via `init_db.py`, no data backfill needed (new tables)

### Phase 2: Core Domain / Modules

- T06: Create `src/vulcanlab/expansion/` module with `__init__.py`
- T07: Implement `breakdown_answer(result_id, session, llm_client)` - validates token limit, parses answer into sections
- T08: Implement `expand_section(section_id, session)` - runs full RAG pipeline for one section
- T09: Implement `generate_section(section_id, session, llm_client)` - runs augmentation LLM
- T10: Implement `combine_sections(expansion_id, session)` - merges sections into final report with link to original answer
- T11: Add unit tests for core expansion logic (mocked DB, mocked LLM)

### Phase 3: External APIs / Integrations

- T12: Create `src/vulcanlab_api/routers/expansions.py` with CRUD endpoints
- T13: Add operation endpoints (breakdown, expand, generate, manual, combine)
- T14: Create Pydantic schemas in `src/vulcanlab_api/schemas/expansions.py`
- T15: Register router in `main.py` under `/api/v1/expansions`
- T16: Add `GET /api/v1/results/{result_id}/expansion` helper endpoint

### Phase 4: UI / Client

- T17: Add "Expand Answer" button to result detail page
- T18: Create expansion creation modal with mode toggle
- T19: Create Expansions list page at `/expansions`
- T20: Create Expansion detail page at `/expansions/{id}` with sections list
- T21: Implement section status badges and retry button
- T22: Implement manual mode: prompt display, response textarea, save button
- T23: Add combined report display with markdown rendering
- T24: Add link from result detail page to its expansion (if exists)
- T25: Add Expansions nav item (if desired) or ensure discoverability

### Phase 5: Testing + Observability + Hardening

- T26: Add integration tests for expansion API endpoints
- T27: Add logging with expansion_id/section_id context
- T28: Add error handling for partial failures (section-level isolation)
- T29: Manual test plan execution and bug fixes

### Phase 6: Rollout

- T30: Update `init_db.py` and document schema changes
- T31: Deploy and verify in staging
- T32: Monitor logs for expansion operations post-deploy

## Testing Plan

- Unit tests:
  - `test_breakdown_answer` - verify JSON parsing, section count validation (3-7)
  - `test_breakdown_answer_token_limit` - verify rejection when source exceeds 30,000 tokens
  - `test_expand_section` - verify RAG pipeline steps called correctly (mocked)
  - `test_combine_sections` - verify markdown concatenation with headings and original answer link
  - `test_expansion_status_transitions` - verify valid state machine transitions
  - `test_parallel_section_processing` - verify 2-concurrent limit in automatic mode

- Integration tests:
  - Create expansion from existing result, verify record created
  - Run breakdown endpoint, verify sections created with correct fields
  - Run section expand/generate, verify status updates
  - Run combine, verify combined_report populated
  - Test retry on failed section

- Manual test plan:
  - [ ] Create expansion in automatic mode, verify full pipeline completes
  - [ ] Create expansion in manual mode, paste responses, verify combine works
  - [ ] Trigger failure (e.g., invalid LLM response), verify retry works
  - [ ] Verify expansion appears in Expansions list
  - [ ] Verify link from result detail page to expansion
  - [ ] Verify expansions don't appear in main Queries list

## Acceptance Criteria (Checklist)

- [ ] "Expand Answer" button visible on result detail page
- [ ] Clicking button creates expansion record and redirects to detail page
- [ ] Breakdown LLM call produces 3-7 sections with headings, summaries, prompts
- [ ] Each section can be expanded through full RAG pipeline
- [ ] Automatic mode processes all sections without user intervention
- [ ] Manual mode allows user to paste responses for each section
- [ ] Failed sections can be retried individually
- [ ] Combined report displays all section responses with headings and link to original answer
- [ ] Expansions appear in dedicated Expansions view
- [ ] Result detail page shows link to expansion when one exists
- [ ] No expansion data pollutes the main Queries table

## Rollout / Migration Plan

- No data migration required (new tables only)
- Schema changes applied via `python -m vulcanlab.data.init_db -v`
- Feature can be deployed without affecting existing RAG functionality
- No feature flag required (additive feature)

## Risks and Alternatives

- Risks:
  - LLM may produce inconsistent section counts or malformed JSON - mitigate with robust parsing and validation
  - Full RAG pipeline per section could be slow for 7 sections - mitigated by 2-concurrent parallelism
  - Large combined reports may strain UI rendering - implement pagination or lazy loading if needed
  - API rate limiting with parallel requests - 2-concurrent limit provides buffer; add exponential backoff if needed

- Alternatives considered:
  - Reusing `ResearchSession`/`ResearchSection` models - rejected because those are collection-based and have different semantics
  - Storing sections in JSONB instead of separate table - rejected for queryability and per-section status tracking
  - WebSocket progress updates - deferred to future enhancement, polling sufficient for MVP

## Patterns and Standards Alignment (from documentation/patterns.md)

- Patterns applied:
  - Three-tier architecture: Core module (`vulcanlab.expansion`) -> API layer (`vulcanlab_api.routers.expansions`) -> UI
  - Prompt templates: `answer_breakdown` template stored in database, editable via Settings > Templates
  - Database session passing: All core functions receive `session` as parameter
  - Enum value capitalization: Status enums use lowercase values matching CHECK constraints
  - API versioning: New endpoints under `/api/v1/expansions/`
  - Schema changes via init_db: Idempotent `CREATE TABLE IF NOT EXISTS` in `specialized_tables.py`

- Deviations (if any):
  - None anticipated

## Implementation Notes (Non-binding)

- The breakdown prompt should instruct the LLM to output structured JSON matching the `SectionBreakdown` schema
- Use existing token estimation heuristic (e.g., `estimate_tokens()` from utils) to validate 30,000 token input limit
- Automatic mode uses `asyncio.Semaphore(2)` or similar to limit concurrent section processing
- Section order should be preserved from breakdown through to combined report
- The expansion module can import from `vulcanlab.retrieval` and `vulcanlab.augmentation` for RAG steps
- UI can poll `/api/v1/expansions/{id}` every 2-3 seconds during automatic processing
- Combined report header should include markdown link: `[View Original Answer](/rag/{query_id}/results/{result_id})`

## Open Questions

None - all questions resolved.
