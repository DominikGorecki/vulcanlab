# Title: Work Summarization Feature

## Summary

- Enables intelligent summarization of large documents using existing chunk embeddings and hybrid search
- Selects the most relevant content-chunks per heading using dense + lexical search with RRF and MMR
- Generates LLM prompts for manual copy/paste workflow (automatic mode deferred)
- Stores per-heading summaries in a new `summary_results` table for display and reuse
- Adds "Summarize" action to corpus page and a new "Summaries" section in left nav

## Problem / Context

- Users have ingested and vectorized large documents but lack a way to generate structured summaries
- Manual summarization is time-consuming and inconsistent across documents
- Existing chunk infrastructure (embeddings, lexical vectors, hierarchy) is underutilized for summarization
- No mechanism exists to leverage the document's heading structure for section-by-section summaries

## Goals

- Provide a systematic approach to summarize large documents section-by-section
- Use existing embeddings and lexical vectors to select the most relevant content per heading
- Generate LLM prompts that fit within token budgets (max 5 calls, 15K input tokens each)
- Store summaries linked to heading-chunks for display and future retrieval
- Create a manual workflow UI for copying prompts and pasting LLM responses

## Non-goals (Strict)

- Automatic LLM API integration (future enhancement)
- Real-time streaming of LLM responses
- Multi-document cross-summarization
- Summary editing or versioning beyond regeneration
- Export to external formats (PDF, DOCX)
- Integration with external summarization services

## Scope

### In scope

- New `summary_chunks` table to store heading-to-content-chunk relevance scores
- New `summary_results` table to store LLM-generated summaries per heading
- New `summarize_settings` configuration (DB-stored, UI-editable)
- Core module: heading selection, content-chunk ranking (RRF + MMR), prompt generation
- API endpoints for summarization workflow
- UI: "Summarize" button on corpus page, manual LLM workflow, Summaries list page, summary viewer
- New prompt template `summarize_sections` for LLM calls

### Out of scope

- Automatic LLM execution
- Summary quality scoring or evaluation
- Comparison of multiple summary versions
- Batch summarization of multiple works

## Requirements (Functional)

- R1: System shall identify heading-chunks (level without "-chunk") ordered by `start_line`
- R2: System shall filter heading-chunks where `chunks.content` word count is below configurable threshold (default: 500 words)
- R3: System shall enforce a configurable maximum total word count for all heading titles (default: 2,500 words), removing lowest-level shortest headings first
- R4: For each remaining heading-chunk, system shall retrieve child content-chunks and rank them using:
  - Dense search using `heading_breadcrumbs` + first line of heading content as query (top 7)
  - Lexical search using same query (top 7)
  - RRF fusion with configurable K (default: 60), returning top 7
  - MMR re-ranking with configurable lambda (default: 0.7), returning top N (default: 5)
- R5: System shall store ranking results in `summary_chunks` table with scores
- R6: System shall generate LLM prompts fitting within budget (max 5 calls, 15K input tokens each, using 0.75 tokens/word approximation)
- R7: System shall prune content-chunks per heading to fit budget, prioritizing higher-level headings (H1/H2 keep min 2, H3 keeps min 1)
- R8: System shall use prompt template from database (`summarize_sections` function_tag)
- R9: System shall parse JSON LLM responses and store one row per heading-chunk in `summary_results`
- R10: When re-summarizing, system shall offer user choice: regenerate all or skip existing
- R11: UI shall display generated prompts for manual copy and provide input fields for pasting responses
- R12: UI shall display combined summary output ordered by heading `start_line`

## Requirements (Non-functional)

- Performance:
  - Heading selection and chunk ranking shall complete within 10 seconds for documents with up to 500 heading-chunks
  - Prompt generation shall complete within 5 seconds
- Reliability:
  - Partial failures (e.g., invalid JSON response) shall not corrupt existing summaries
  - Transaction rollback on database errors during summary storage
- Security / Privacy:
  - No sensitive data transmitted to external services (manual LLM flow)
  - Standard session-based authentication for API endpoints
- Observability:
  - Log summarization workflow steps with work_id, heading count, chunk counts
  - Store timestamps for summary creation/updates

## Proposed Solution (High-level)

- **Data Layer**: Two new tables (`summary_chunks`, `summary_results`) plus settings in `rag_config` or new `summarize_settings`
- **Core Module**: New `src/vulcanlab/summarization/` package with:
  - `heading_selector.py`: Filter and order heading-chunks
  - `chunk_ranker.py`: RRF + MMR ranking (independent implementation)
  - `prompt_generator.py`: Budget-aware prompt assembly
  - `summary_storage.py`: Parse and store results
- **API Layer**: New router `src/vulcanlab_api/routers/summarize.py` with endpoints for workflow steps
- **UI Layer**:
  - Add "Summarize" action to corpus work row/detail
  - New `/summaries` page listing summarized works
  - New `/summaries/[work_id]` page for workflow and viewing

## Interfaces / APIs / Contracts

- `POST /api/v1/summarize/works/{work_id}/prepare` - Analyze work, return heading list and chunk rankings
  - Response: `{ headings: [...], total_prompts: number, estimated_tokens: number }`
- `POST /api/v1/summarize/works/{work_id}/generate-prompts` - Generate LLM prompts
  - Request: `{ regenerate_all: boolean }`
  - Response: `{ prompts: [{ prompt_index: number, content: string, heading_ids: number[] }] }`
- `POST /api/v1/summarize/works/{work_id}/submit-response` - Submit LLM response for a prompt
  - Request: `{ prompt_index: number, response_json: string }`
  - Response: `{ success: boolean, summaries_saved: number, errors: string[] }`
- `GET /api/v1/summarize/works/{work_id}/summary` - Get combined summary for a work
  - Response: `{ work_id, work_title, sections: [{ heading, summary_content, start_line }] }`
- `GET /api/v1/summarize/works` - List all works with summaries
  - Response: `{ works: [{ work_id, title, summary_count, last_updated }] }`
- `GET /api/v1/summarize/settings` - Get summarization settings
- `PUT /api/v1/summarize/settings` - Update summarization settings

## Data Model / Storage

### New Table: `summary_chunks`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| work_id | INTEGER | FK works.id, NOT NULL | Parent work |
| heading_chunk_id | INTEGER | FK chunks.id, NOT NULL | The heading-chunk being summarized |
| content_chunk_id | INTEGER | FK chunks.id, NOT NULL | Ranked content-chunk |
| word_count | INTEGER | NOT NULL | Word count of content-chunk |
| dense_score | FLOAT | | Dense search score |
| lexical_score | FLOAT | | Lexical search score |
| rrf_score | FLOAT | | RRF fusion score |
| mmr_score | FLOAT | | Final MMR-adjusted score |
| rank_position | INTEGER | NOT NULL | Final rank (1 = best) |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

Indexes: `(work_id)`, `(heading_chunk_id)`, `(heading_chunk_id, rank_position)`

### New Table: `summary_results`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| work_id | INTEGER | FK works.id, NOT NULL | Parent work |
| chunk_id | INTEGER | FK chunks.id, NOT NULL, UNIQUE | Heading-chunk this summary belongs to |
| summary_content | TEXT | NOT NULL | LLM-generated markdown summary |
| prompt_index | INTEGER | | Which prompt batch generated this |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

Indexes: `(work_id)`, `(chunk_id)` UNIQUE

### Settings (in new summarize_settings table or rag_config extension)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| min_heading_word_count | INTEGER | 500 | Min words in heading content to include |
| max_total_heading_words | INTEGER | 2500 | Max combined words for all heading titles |
| dense_top_k | INTEGER | 7 | Dense search candidates per heading |
| lexical_top_k | INTEGER | 7 | Lexical search candidates per heading |
| rrf_k | INTEGER | 60 | RRF smoothing constant |
| rrf_top_k | INTEGER | 7 | Results after RRF fusion |
| mmr_lambda | FLOAT | 0.7 | MMR diversity parameter (0=diverse, 1=relevant) |
| mmr_top_n | INTEGER | 5 | Final chunks per heading after MMR |
| max_llm_calls | INTEGER | 5 | Maximum LLM prompt batches |
| max_tokens_per_call | INTEGER | 15000 | Max input tokens per LLM call |
| tokens_per_word | FLOAT | 0.75 | Token estimation ratio |
| h1_h2_min_chunks | INTEGER | 2 | Minimum chunks for H1/H2 headings |
| h3_min_chunks | INTEGER | 1 | Minimum chunks for H3+ headings |

## UX / Workflows

### Workflow 1: Initiate Summarization
1. User navigates to Corpus page
2. User clicks "Summarize" action on a work row (or from work detail page)
3. System navigates to `/summaries/workflow/[work_id]`
4. System calls prepare endpoint, displays heading count and estimated prompts
5. If work has existing summaries, show checkbox: "Regenerate all summaries" (default: unchecked)

### Workflow 2: Manual LLM Flow
1. User clicks "Generate Prompts" button
2. System displays first prompt in a copyable text area
3. User copies prompt, pastes into external LLM, copies response
4. User pastes JSON response into input field, clicks "Submit"
5. System validates JSON, stores summaries, shows success/error count
6. System advances to next prompt (or shows completion if done)
7. Progress indicator shows "Prompt 2 of 5" etc.

### Workflow 3: View Summary
1. User navigates to Summaries page (left nav)
2. User sees table of works with summaries (title, section count, last updated)
3. User clicks a work row
4. System displays combined summary: heading + summary content, ordered by start_line

## Work Breakdown (Ticket Seed)

### Phase 0: Foundations

- T01: Create migration for `summary_chunks` and `summary_results` tables
- T02: Add SQLAlchemy models for new tables in `src/vulcanlab/data/models/`
- T03: Add summarize settings to database (new table or extend existing config)
- T04: Create prompt template `summarize_sections.txt` and add to `templates.yaml`

### Phase 1: Core Domain / Modules

- T05: Implement `heading_selector.py` - filter and order heading-chunks by criteria
- T06: Implement `chunk_ranker.py` - dense search, lexical search, RRF fusion (independent impl)
- T07: Implement `chunk_ranker.py` - MMR re-ranking step
- T08: Implement `prompt_generator.py` - budget calculation and content pruning
- T09: Implement `prompt_generator.py` - prompt assembly with template
- T10: Implement `summary_storage.py` - JSON parsing and per-heading storage

### Phase 2: External APIs

- T11: Create `src/vulcanlab_api/routers/summarize.py` with prepare endpoint
- T12: Add generate-prompts endpoint
- T13: Add submit-response endpoint
- T14: Add summary retrieval endpoints (single work, list)
- T15: Add settings endpoints (get/put)

### Phase 3: UI / Client

- T16: Add "Summarize" action button to corpus page work rows
- T17: Create summarization workflow page `/summaries/workflow/[work_id]`
- T18: Implement prompt display and response input components
- T19: Create Summaries list page `/summaries`
- T20: Create summary viewer page `/summaries/[work_id]`
- T21: Add "Summaries" link to left navigation
- T22: Add "Summarize" settings tab to Settings page

### Phase 4: Testing + Observability

- T23: Unit tests for heading_selector
- T24: Unit tests for chunk_ranker (RRF, MMR)
- T25: Unit tests for prompt_generator (budget logic)
- T26: Unit tests for summary_storage (JSON parsing)
- T27: API integration tests for summarize endpoints
- T28: Add logging throughout summarization workflow

## Testing Plan

- Unit tests:
  - `test_heading_selector.py`: Filter by word count, ordering, max heading words pruning
  - `test_chunk_ranker.py`: RRF score calculation, MMR diversity, edge cases (no chunks, single chunk)
  - `test_prompt_generator.py`: Token estimation, budget enforcement, pruning priority
  - `test_summary_storage.py`: JSON parsing, error handling, partial saves
- Integration tests:
  - End-to-end workflow with test fixtures
  - Settings persistence and retrieval
- Manual test plan:
  - Verify heading selection matches expected for sample documents
  - Confirm prompt fits within LLM context window
  - Test JSON response parsing with malformed input
  - Verify summary display ordering matches document structure

## Acceptance Criteria (Checklist)

- [ ] Heading-chunks are correctly filtered by word count threshold
- [ ] Content-chunks are ranked using RRF fusion of dense + lexical search
- [ ] MMR re-ranking produces diverse chunk selection
- [ ] Generated prompts fit within configured token budget
- [ ] LLM JSON responses are correctly parsed and stored per heading
- [ ] Regenerate option works (deletes existing before regenerating)
- [ ] Skip-existing option works (incremental summarization)
- [ ] Combined summary displays sections in document order
- [ ] Settings are editable via UI and persist correctly
- [ ] "Summarize" button appears on corpus page
- [ ] "Summaries" link appears in left navigation
- [ ] Workflow UI allows copy/paste of prompts and responses

## Rollout / Migration Plan

- Migration creates tables with IF NOT EXISTS for idempotency
- No data migration required (new feature)
- Settings seeded with defaults on first access
- Prompt template seeded via standard init_db flow
- Feature available immediately after deployment

## Risks and Alternatives

- Risks:
  - Token estimation (0.75 tokens/word) may be inaccurate for technical content with many symbols
  - MMR implementation complexity may introduce bugs; mitigate with thorough unit tests
  - Manual copy/paste workflow may frustrate users; mitigate by prioritizing automatic mode in future
  - Large documents may exceed 5-call budget even after pruning; mitigate with clear error messaging
- Alternatives considered:
  - Use existing RRF from search_hybrid.py: Rejected to keep summarization logic isolated and configurable
  - Store raw LLM responses instead of parsed: Rejected because per-heading storage enables partial updates
  - Automatic LLM calls from start: Rejected to reduce scope and avoid API key management complexity

## Patterns and Standards Alignment (from documentation/patterns.md)

- Patterns applied:
  - **Three-tier architecture**: Core module (summarization/), API layer (routers/summarize.py), UI (Next.js pages)
  - **Session passed explicitly**: All core functions receive `session: Session` parameter
  - **Prompt templates in database**: New template seeded via templates.yaml, loaded via `get_active_template()`
  - **Migration + init_db sync**: SQL migration created alongside schema module updates
  - **Settings in database**: Summarization settings stored in DB, editable via Settings UI tab
  - **usePageData + useCallback**: UI pages follow standard data fetching pattern
- Deviations (if any):
  - None anticipated

## Implementation Notes (Non-binding)

- RRF implementation should be similar to `search_hybrid.py` but independent for configurability
- MMR requires computing pairwise similarity between selected chunks; consider caching embeddings
- Token estimation: `word_count * 0.75` is a rough heuristic; may need adjustment based on testing
- Prompt template should instruct LLM to return JSON array with `id` and `summary` fields
- Consider adding a "preview" mode that shows prompt without saving to summary_chunks

## Open Questions

- Q1: Should the summarization workflow support resuming after browser close (persist prompt state)?
- Q2: Should we display estimated LLM cost alongside token counts (requires model pricing data)?
- Q3: Should MMR use the same embedding model as dense search, or a dedicated model?
