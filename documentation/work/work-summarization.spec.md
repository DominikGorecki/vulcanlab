# Title: Work Summarization Feature

## Summary

* Add a new "Summarize" feature that generates structured summaries (gist, key points, definitions, key terms, examples) for works in the corpus
* Implement salience-based node selection with configurable thresholds to determine which heading-level chunks receive deep summaries
* Use local NLP extraction (spaCy/regex) to build "evidence packets" before LLM summarization calls
* Store summary data in a `summary_nodes` table with line-number references back to source chunks
* Provide on-demand generation of derived outputs (abstract, outline, key concepts, chapter summaries) from the summary_nodes
* Add new UI pages: Summarize settings tab, Summarize list page (left nav), and per-work summary view with derived output generation

## Problem / Context

* Users have works in the corpus but no way to quickly understand their content without reading them in full
* No automated summarization exists; users must manually review sanitized markdown
* The chunking system already segments works into heading-level (H1-H5) and content-level chunks, but this structure is not leveraged for summarization
* Users need summaries that reference specific line numbers in the source for verification and navigation

## Goals

* Enable users to generate structured summaries for any work in the corpus
* Provide line-anchored summaries that allow users to navigate back to source content
* Support generation of multiple derived outputs (abstract, outline, key concepts, chapter summaries) from base summary data
* Implement cost-efficient LLM usage via evidence packet extraction and salience-based node selection
* Allow configuration of salience thresholds via Settings UI

## Non-goals (Strict)

* Real-time/streaming summarization (summaries are generated as batch operations)
* Automatic summarization on work import (user must explicitly trigger)
* Cross-work summarization or corpus-level summaries
* Editing or manual modification of generated summaries
* Graph-based relationships between summary nodes (no Apache AGE integration)
* Snippet hashing for line anchor re-alignment (deferred to future phase)

## Scope

### In scope

* New `summary_nodes` table with structured summary fields and chunk references
* New `work_summaries` polymorphic table for derived outputs (abstract, outline, key_concepts, chapter_summaries)
* Salience scoring system for node selection with configurable thresholds
* Local NLP evidence packet extraction using spaCy and regex patterns
* LLM integration for summarization with escalation loop for insufficient evidence
* API endpoints for triggering summarization and retrieving results
* UI: Settings tab for salience configuration
* UI: "Summarize" page in left nav showing works with summaries
* UI: Per-work summary view with derived output generation buttons
* UI: "Summarize" button on Corpus work detail page

### Out of scope

* Bulk summarization of multiple works at once
* Scheduled/automatic summarization
* Summary comparison or versioning
* Export of summaries to external formats
* Integration with Research (RAG) sessions
* Snippet hash anchoring for source change detection

## Requirements (Functional)

* R1: System SHALL create summary_nodes for heading-level chunks (H1-H5) based on salience scoring
* R2: Each summary_node SHALL contain: gist, key_points, definitions, key_terms, examples, chunk_id reference, start_line, end_line
* R3: Salience scoring SHALL consider: heading depth, token length, definition density, list density, keyphrase novelty, location priors
* R4: Salience thresholds SHALL be configurable via Settings UI (Summarize tab)
* R5: Evidence packets SHALL be extracted locally using spaCy and regex before LLM calls
* R6: Evidence packets SHALL include: topic sentences, definition-like sentences, enumerations, emphasis cues, keyphrases/entities
* R7: LLM summarization SHALL return structured fields with line anchors for each claim
* R8: Escalation loop SHALL trigger when LLM reports insufficient evidence, pulling additional context
* R9: Derived outputs (abstract, outline, key_concepts, chapter_summaries) SHALL be generated on-demand from summary_nodes
* R10: Derived outputs SHALL be stored in work_summaries table with type discriminator
* R11: Derived outputs SHALL include line references (potentially multiple) back to source
* R12: UI SHALL show "Summarize" button on Corpus work detail page
* R13: UI SHALL show list of works with summaries on dedicated Summarize page
* R14: UI SHALL allow users to generate or view derived outputs for summarized works
* R15: Summarization SHALL be synchronous with progress streaming; async deferred to future phase
* R16: LLM model for summarization SHALL be configurable via Settings (using existing vulcanlab.config pattern)
* R17: Users SHALL be able to re-summarize a work, which deletes existing summary_nodes before regenerating (with confirmation dialog)

## Requirements (Non-functional)

* Performance:
  * Evidence packet extraction SHALL complete within 30 seconds for works under 100K tokens
  * LLM summarization SHALL use batched requests where possible to reduce latency
  * Derived output generation SHALL complete within 60 seconds

* Reliability:
  * Failed summarization SHALL not corrupt existing chunk data
  * Partial summarization progress SHALL be recoverable (node-by-node processing)
  * LLM API failures SHALL be retried with exponential backoff (max 3 retries)

* Security / Privacy:
  * No new authentication requirements (uses existing session)
  * LLM API keys managed via existing vulcanlab_api config

* Observability:
  * Summarization progress SHALL be logged with work_id and node counts
  * LLM token usage SHALL be tracked per summarization operation
  * Errors SHALL be logged with sufficient context for debugging

## Proposed Solution (High-level)

* Architecture follows the three-tier pattern: Core Module (vulcanlab) -> API Layer (vulcanlab_api) -> Frontend (vulcanlab_ui)
* Core module implements: salience scoring, evidence packet extraction (NLP), LLM summarization orchestration, derived output compilation
* New database tables: `summary_nodes` (per-node summaries), `work_summaries` (derived outputs with type column)
* API endpoints expose summarization triggers and data retrieval
* Frontend adds: Settings tab, Summarize list page, per-work summary view

### Data Flow

1. User clicks "Summarize" on Corpus work detail page
2. API triggers core module summarization
3. Core module: loads heading-level chunks -> computes salience scores -> filters by thresholds
4. For each selected node: extract evidence packet -> call LLM -> store summary_node
5. If LLM reports insufficient evidence: escalation loop pulls more context and retries
6. User navigates to Summarize page, selects work, chooses derived output to generate
7. Core module compiles derived output from summary_nodes -> stores in work_summaries
8. UI displays derived output with clickable line references

## Interfaces / APIs / Contracts

* `POST /api/v1/summarize/{work_id}` - Trigger summarization for a work
  * Response: `{ job_id: string, status: "started" | "already_exists" }`

* `GET /api/v1/summarize/{work_id}/status` - Get summarization status
  * Response: `{ status: "pending" | "in_progress" | "completed" | "failed", progress: { total_nodes: int, completed_nodes: int }, error?: string }`

* `GET /api/v1/summarize/{work_id}/nodes` - Get summary nodes for a work
  * Response: `{ nodes: SummaryNode[] }`

* `POST /api/v1/summarize/{work_id}/derive` - Generate a derived output
  * Body: `{ type: "abstract" | "outline" | "key_concepts" | "chapter_summaries" }`
  * Response: `{ summary_id: int, type: string, content: object }`

* `GET /api/v1/summarize/{work_id}/summaries` - Get all derived outputs for a work
  * Response: `{ summaries: WorkSummary[] }`

* `GET /api/v1/summarize/works` - List works with summary data
  * Response: `{ works: { work_id: int, title: string, node_count: int, summaries: string[] }[] }`

* `GET /api/v1/settings/summarize` - Get salience configuration
* `PUT /api/v1/settings/summarize` - Update salience configuration

## Data Model / Storage

### summary_nodes table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| chunk_id | INTEGER | FK chunks(id) ON DELETE CASCADE, NOT NULL | Reference to source heading-level chunk |
| work_id | INTEGER | FK works(id) ON DELETE CASCADE, NOT NULL, INDEX | Denormalized for query efficiency |
| gist | TEXT | NOT NULL | 1-2 sentence summary |
| key_points | JSONB | NOT NULL | Array of { text: string, start_line: int, end_line: int } |
| definitions | JSONB | NOT NULL | Array of { term: string, definition: string, start_line: int, end_line: int } |
| key_terms | JSONB | NOT NULL | Array of { term: string, start_line: int, end_line: int } |
| examples | JSONB | NOT NULL | Array of { text: string, start_line: int, end_line: int } |
| start_line | INTEGER | NOT NULL | Start line in sanitized markdown |
| end_line | INTEGER | NOT NULL | End line in sanitized markdown |
| salience_score | FLOAT | NOT NULL | Computed salience score for this node |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |

### work_summaries table (polymorphic)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| work_id | INTEGER | FK works(id) ON DELETE CASCADE, NOT NULL, INDEX | Reference to work |
| type | VARCHAR(30) | NOT NULL, CHECK (type IN ('abstract', 'outline', 'key_concepts', 'chapter_summaries')) | Summary type discriminator |
| content | JSONB | NOT NULL | Type-specific content structure |
| line_references | JSONB | NOT NULL | Array of { start_line: int, end_line: int } for source attribution |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |
| UNIQUE | | (work_id, type) | One of each type per work |

### Content JSONB structures by type

* **abstract**: `{ text: string }`
* **outline**: `{ sections: [{ heading: string, gist: string, depth: int, start_line: int, end_line: int, children: [...] }] }`
* **key_concepts**: `{ concepts: [{ term: string, definition: string, occurrences: [{ start_line: int, end_line: int }] }] }`
* **chapter_summaries**: `{ chapters: [{ heading: string, summary: string, start_line: int, end_line: int }] }`

### summarize_settings table (or extend existing settings)

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | PRIMARY KEY |
| h1_always_summarize | BOOLEAN | Always deep-summarize H1 nodes (default: true) |
| h2_top_percent | INTEGER | Top N% of H2 nodes by salience (default: 100) |
| h3_salience_threshold | FLOAT | Minimum salience for H3 nodes (default: 0.5) |
| h4_salience_threshold | FLOAT | Minimum salience for H4+ nodes (default: 0.7) |
| definition_density_weight | FLOAT | Weight for definition density in salience (default: 0.3) |
| list_density_weight | FLOAT | Weight for list density (default: 0.2) |
| keyphrase_novelty_weight | FLOAT | Weight for keyphrase novelty (default: 0.2) |
| location_prior_weight | FLOAT | Weight for intro/conclusion boost (default: 0.15) |
| heading_depth_weight | FLOAT | Weight for heading depth (default: 0.15) |

## UX / Workflows

### Workflow 1: Summarize a Work

1. User navigates to Corpus page, clicks on a work to view details
2. User clicks "Summarize" button in the work detail header
3. System shows progress indicator (X of Y nodes processed)
4. On completion, user sees success message with link to Summarize page

### Workflow 2: View and Generate Derived Outputs

1. User clicks "Summarize" in left navigation
2. User sees list of works that have summary_nodes
3. User clicks on a work to view its summary
4. User sees summary_nodes displayed hierarchically (matching heading structure)
5. User clicks "Generate Abstract" / "Generate Outline" / etc. buttons
6. System generates and displays the derived output
7. Line references in output are clickable, navigating to source in Corpus view

### Workflow 3: Configure Salience Thresholds

1. User navigates to Settings page
2. User clicks "Summarize" tab
3. User adjusts salience weights and thresholds via form inputs
4. User clicks "Save"
5. Settings apply to future summarization operations

## Work Breakdown (Ticket Seed)

### Phase 0: Foundations

* T01: Add spaCy dependency to pyproject.toml; verify sentence segmentation works
* T02: Create summarize_settings table and seed default configuration
* T03: Add Settings tab UI scaffold for Summarize configuration

### Phase 1: Data / Migrations

* T04: Create summary_nodes table migration with indexes
* T05: Create work_summaries table migration with type check constraint
* T06: Add SQLAlchemy models: SummaryNode, WorkSummary, SummarizeSettings
* T07: Update init_db.py with new table creation functions

### Phase 2: Core Domain / Modules

* T08: Implement salience scoring module (src/vulcanlab/summarize/salience.py)
  * Heading depth scoring
  * Definition density detection (regex patterns)
  * List density calculation
  * Keyphrase extraction (TF-IDF or YAKE)
  * Location prior (intro/conclusion detection)
  * Composite score calculation with configurable weights

* T09: Implement evidence packet extraction (src/vulcanlab/summarize/evidence.py)
  * Sentence segmentation with line mapping (spaCy)
  * Topic sentence extraction (first sentence per paragraph)
  * Definition-like sentence detection (regex: "X is...", "defined as...", etc.)
  * Enumeration detection (bullets, numbered lists)
  * Emphasis cue detection (regex: "key", "important", "note that", etc.)
  * Keyphrase/entity extraction

* T10: Implement LLM summarization orchestrator (src/vulcanlab/summarize/llm_summarize.py)
  * Prompt template for structured summary extraction
  * Response parsing into SummaryNode fields
  * Insufficient evidence detection from LLM response
  * Escalation loop: pull additional context and retry

* T11: Implement node selection logic (src/vulcanlab/summarize/node_selector.py)
  * Load heading-level chunks for work
  * Compute salience scores
  * Apply threshold filtering based on settings
  * Handle parent-child relationships to avoid content duplication

* T12: Implement summarization orchestrator (src/vulcanlab/summarize/orchestrator.py)
  * Main entry point: summarize_work(work_id, session)
  * Progress tracking and status updates
  * Error handling and partial recovery
  * Transaction management

* T13: Implement derived output compilation (src/vulcanlab/summarize/compile.py)
  * Abstract generation from work-level digest
  * Outline generation from summary_nodes hierarchy
  * Key concepts aggregation and deduplication
  * Chapter summaries from H1/H2 level nodes

### Phase 3: External APIs / Integrations

* T14: Create summarize router (src/vulcanlab_api/routers/summarize.py)
  * POST /api/v1/summarize/{work_id} - trigger summarization
  * GET /api/v1/summarize/{work_id}/status - get status
  * GET /api/v1/summarize/{work_id}/nodes - get summary nodes
  * POST /api/v1/summarize/{work_id}/derive - generate derived output
  * GET /api/v1/summarize/{work_id}/summaries - get derived outputs
  * GET /api/v1/summarize/works - list summarized works

* T15: Add summarize settings endpoints to settings router
  * GET /api/v1/settings/summarize
  * PUT /api/v1/settings/summarize

* T16: Register summarize router in main.py with /api/v1 prefix

### Phase 4: UI / Client

* T17: Add "Summarize" nav item to nav-bar.tsx (with BookOpen icon)

* T18: Create Summarize settings tab (vulcanlab_ui/src/components/settings/summarize-tab.tsx)
  * Form for salience weights and thresholds
  * Save/reset functionality

* T19: Create Summarize list page (vulcanlab_ui/src/app/summarize/page.tsx)
  * Fetch works with summary data
  * Display as table with work title, node count, available summaries
  * Click to navigate to work summary detail

* T20: Create work summary detail page (vulcanlab_ui/src/app/summarize/[id]/page.tsx)
  * Display summary_nodes in hierarchical tree view
  * Show gist, key points, definitions, terms, examples for each node
  * Line references as clickable links to /corpus/[id]?line=X

* T21: Add derived output generation UI (vulcanlab_ui/src/app/summarize/[id]/page.tsx)
  * Buttons: Generate Abstract, Generate Outline, Generate Key Concepts, Generate Chapter Summaries
  * Display generated outputs in collapsible sections
  * Line references clickable

* T22: Add "Summarize" button to Corpus work detail page
  * Button in StickyDetailHeader actions
  * Progress modal during summarization
  * Success/error toast notifications

### Phase 5: Testing + Observability + Hardening

* T23: Unit tests for salience scoring module
* T24: Unit tests for evidence packet extraction (mock spaCy)
* T25: Unit tests for LLM summarization (mock LLM responses)
* T26: Unit tests for derived output compilation
* T27: API integration tests for summarize endpoints
* T28: Add logging for summarization progress and LLM token usage
* T29: Add error handling for LLM API failures with retry logic

### Phase 6: Rollout

* T30: Update documentation with summarization feature guide
* T31: Seed prompt templates for summarization LLM calls
* T32: Manual testing checklist execution
* T33: Version bump and changelog update

## Testing Plan

* Unit tests:
  * Salience scoring: test each factor independently and composite calculation
  * Evidence extraction: test sentence segmentation, definition detection, enumeration detection
  * LLM summarization: test prompt construction, response parsing, escalation trigger
  * Derived compilation: test abstract, outline, key concepts, chapter summaries generation
  * Node selection: test threshold filtering, parent-child deduplication

* Integration tests:
  * API endpoints: test full summarization flow with test database
  * Settings persistence: test save/load of salience configuration

* Manual test plan:
  * [ ] Trigger summarization on a work with mixed heading levels
  * [ ] Verify summary_nodes created with correct line references
  * [ ] Verify salience filtering respects configured thresholds
  * [ ] Generate each derived output type and verify content
  * [ ] Click line references and verify navigation to correct source location
  * [ ] Modify salience settings and verify they apply to new summarization
  * [ ] Test summarization on a work with sparse headings
  * [ ] Test summarization on a large work (>50K tokens)
  * [ ] Test error recovery: stop summarization mid-way, restart
  * [ ] Test escalation loop: work with sections that trigger insufficient evidence

## Acceptance Criteria (Checklist)

* [ ] User can trigger summarization from Corpus work detail page
* [ ] summary_nodes table populated with gist, key_points, definitions, key_terms, examples
* [ ] Each summary field includes start_line and end_line references
* [ ] Salience scoring selects appropriate nodes based on configured thresholds
* [ ] Evidence packets extracted using spaCy and regex before LLM calls
* [ ] Escalation loop triggers when LLM reports insufficient evidence
* [ ] User can view summarized works on dedicated Summarize page
* [ ] User can generate derived outputs (abstract, outline, key_concepts, chapter_summaries) on demand
* [ ] Derived outputs stored in work_summaries table with correct type
* [ ] Line references in UI are clickable and navigate to source
* [ ] Salience thresholds configurable via Settings > Summarize tab
* [ ] All new API endpoints follow /api/v1 prefix convention
* [ ] Unit tests pass for core summarization modules
* [ ] No regressions in existing Corpus or Chunk functionality

## Rollout / Migration Plan

* Migration 029_add_summary_tables.sql creates summary_nodes and work_summaries tables
* Migration is additive only; no changes to existing tables
* Feature is opt-in: users must explicitly click Summarize
* No data backfill required
* Rollback: drop summary_nodes and work_summaries tables (no impact on existing data)

## Risks and Alternatives

* Risks:
  * LLM costs may be significant for large works; mitigated by salience filtering and evidence packets
  * spaCy dependency increases package size; mitigated by using small model (en_core_web_sm)
  * Line number drift if source markdown is edited after summarization; deferred snippet hashing to future phase
  * Escalation loop may cause excessive LLM calls for poorly-structured works; mitigated by max retry limit

* Alternatives considered:
  * **Full-text LLM summarization**: Rejected due to cost and context window limits
  * **Chunk-level summarization only**: Rejected; heading-level provides better structure
  * **Store summaries as markdown files**: Rejected; database provides better querying and referential integrity
  * **Separate tables per derived output type**: Rejected; polymorphic table is more flexible and reduces schema complexity

## Patterns and Standards Alignment (from documentation/patterns.md)

* Patterns applied:
  * **Three-tier architecture**: Core logic in vulcanlab, thin API layer, React frontend
  * **Session management**: Database sessions passed explicitly to functions
  * **API versioning**: All new routes under /api/v1 prefix
  * **Enum capitalization**: Any new enums will use lowercase values to match DB CHECK constraints
  * **UI Page Lifecycle**: usePageData hook with useCallback-wrapped fetch functions
  * **Error handling**: Global exception handlers, specific exceptions raised from core
  * **Database initialization**: New tables added to schema/ modules, migrations in migrations/

* Deviations (if any):
  * None identified; spec follows all patterns.md guidelines

## Implementation Notes (Non-binding)

* spaCy model: Use `en_core_web_sm` for sentence segmentation; larger models not needed for this use case
* LLM prompt: Consider using existing prompt template infrastructure (seed_data/templates/)
* Evidence packet size: Target 10-40 snippets per node to balance cost and quality
* Salience defaults: Start conservative (process more nodes), tune based on user feedback
* UI hierarchy display: Consider react-arborist or similar for tree visualization of summary_nodes
* Line reference links: Format as `/corpus/{work_id}?highlight={start_line}-{end_line}` (may need Corpus page enhancement)

## Open Questions

* None - all questions resolved during spec creation.
