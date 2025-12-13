# PRD: Simple Conversion Pipeline

---
status: draft
owner: TODO
created: 2025-12-12
slug: simple-conversion-pipeline
---

## 1. Summary

The Simple Conversion Pipeline replaces the existing multi-step manual conversion workflow (conversion → sanitization → chunking) with a streamlined automated process. Users select a PDF/EPUB file from the Conversion page and click "Simple Conversion" which routes them to a dedicated workflow page. They provide bibliographic metadata and choose Automatic or Manual mode. The system parses the file, intelligently routes through either full-LLM processing (small documents) or heuristic-assisted LLM (large documents), and produces chunks in the database ready for vectorization. All artifacts (parsed markdown, sanitized markdown, heading modifications) are stored in database tables, eliminating output folder dependency.

## 2. Problem & Context

### Current Pain Points
The existing conversion process requires multiple manual steps across three separate UI pages:
- **Conversion page**: Upload → Convert → Inspect variants → Select → Add to database
- **Sanitization page**: Extract titles → LLM suggest changes → Review → Apply
- **Chunking page**: Extract sanitized titles → LLM vectorization suggestions → Review → Apply heading chunks → Apply content chunks

This multi-step process is time-consuming, requires constant user intervention, and creates numerous intermediate files in the output folder that need manual management.

### Affected Users
- Primary: Internal users processing academic papers, books, and research documents for RAG
- Secondary: Future external users who need fast document ingestion

### Background
The existing pipeline was built incrementally with manual checkpoints for quality control. While this provides transparency, it's inefficient for batch processing and trusted conversion workflows.

## 3. Goals & Non-Goals

### 3.1 Goals
- **G1**: Reduce conversion from 10+ manual steps to 1 automated flow (input file → chunks in DB)
- **G2**: Eliminate output folder dependency - store all artifacts in database
- **G3**: Intelligently route documents based on size (small vs large processing)
- **G4**: Maintain LLM quality for structure cleanup and vectorization decisions
- **G5**: Provide manual LLM execution mode for debugging and cost control
- **G6**: Make token threshold configurable via UI settings
- **G7**: Provide complete frontend workflow for simple conversion

### 3.2 Non-Goals
- Migration of existing conversion data to new schema
- Parallel batch processing of multiple files
- Custom LLM model selection per document
- Real-time progress streaming during conversion
- File upload in Simple Conversion UI (files come from existing Conversion page)

## 4. Users & Use Cases

### 4.1 User Segments
- **Primary**: Internal researchers and data processors ingesting academic content
- **Secondary**: Developers debugging conversion quality and LLM prompts

### 4.2 Key Use Cases / User Stories

**UC1: Quick Automatic Conversion**
- As a user, I want to click "Simple Conversion" from the Conversion page, enter metadata, click "Automatic Conversion", and have chunks created without further intervention.

**UC2: Manual LLM Execution for Large Documents**
- As a developer, I want to choose "Manual" mode, copy the LLM prompt, run it externally, paste the response, and continue the pipeline for cost control or debugging.

**UC3: Configuration Management**
- As a user, I want to configure the small/large token threshold in settings and edit LLM prompt templates like other templates in the system.

## 5. Requirements

### 5.1 Functional Requirements

**FR1: Step 1 - Parsing & Classification**
- FR1.1: Accept PDF or EPUB file path + bibliographic metadata (title, authors, year, work_type)
- FR1.2: Parse PDF using `conv_pdf2md.py` to generate style and hier variants (in-memory)
- FR1.3: Use `style_v_hier.py` to select best markdown version
- FR1.4: Parse EPUB using `conv_epub2md.py` to generate markdown
- FR1.5: Create Work record with provided metadata
- FR1.6: Store chosen markdown in new `ParsedMarkdown` table (work_id, content, file_type, classification)
- FR1.7: Calculate token count as `(word_count * 1.33)`
- FR1.8: Classify as "small" if tokens < threshold, otherwise "large"
- FR1.9: Threshold must be configurable in `vulcanlab.config.json` (default: 15,000 tokens, range: 100 - 200,000)

**FR2: Step 2A - Small Document Processing (Full LLM)**
- FR2.1: Load parsed markdown from `ParsedMarkdown` table
- FR2.2: Load LLM prompt template from `PromptTemplate` table (function_tag: "simple_sanitize_small")
- FR2.3: Use LangChain template format with variable: `{markdown}`
- FR2.4: LLM must adjust document hierarchy (correct heading levels, remove non-title headings)
- FR2.5: LLM must sanitize content (fix conversion artifacts, remove meta info, references, TOC, page numbers)
- FR2.6: LLM must return clean markdown with only RAG-relevant content
- FR2.7: Store sanitized markdown in `SanitizedMarkdown` table (work_id, content, token_count, created_at)
- FR2.8: All headings in sanitized markdown are assumed to be vectorized (no separate vectorization decision)

**FR3: Step 2B - Large Document Processing (Heuristics + LLM)**
- FR3.1: Load parsed markdown from `ParsedMarkdown` table
- FR3.2: Extract titles using logic similar to `extract_titles.py`
- FR3.3: For each title block, extract first 2 and last 2 sentences until next title
- FR3.4: Create condensed document with format: `{line_number}: {heading}\n{first 2 sentences}...\n{last 2 sentences}`
- FR3.5: Load LLM prompt template from `PromptTemplate` table (function_tag: "simple_sanitize_large")
- FR3.6: Use LangChain template format with variable: `{condensed_document}`
- FR3.7: Generate LLM prompt with condensed document to determine:
  - Heading level changes or removal
  - Title cleanup (whitespace, formatting)
  - Vectorization decision (VECTORIZE/SKIP)
- FR3.8: Store LLM response in `HeadingModifications` table with fields:
  - `work_id`, `line_number`, `original_heading`, `modified_heading`, `action` (remove/change/keep), `vectorize_flag`
- FR3.9: Apply modifications to original markdown to create sanitized version
- FR3.10: Store sanitized markdown in `SanitizedMarkdown` table

**FR4: Step 3 - Chunking**
- FR4.1: Load sanitized markdown from `SanitizedMarkdown` table
- FR4.2: Use refactored chunking logic from `chunk_headings.py`
- FR4.3: For Step 2A (small): Vectorize all headings
- FR4.4: For Step 2B (large): Vectorize only headings with `vectorize_flag=true`
- FR4.5: Create heading chunks in `Chunk` table with `vector_status='to_vec'`
- FR4.6: Use refactored logic from `content_chunking.py` to create content chunks
- FR4.7: Create content chunks in `Chunk` table

**FR5: LLM Execution Modes**
- FR5.1: Support "Automatic" mode: API call to LLM, wait for response, apply automatically
- FR5.2: Support "Manual" mode: Generate full prompt, return to UI for copy/paste
- FR5.3: In Manual mode, provide "Run with API" button to execute LLM call directly
- FR5.4: In Manual mode, accept LLM response as pasted input to continue pipeline
- FR5.5: Mode is selected per-execution in UI (no global "Always Automatic" setting)

**FR6: Configuration & Settings**
- FR6.1: Add "Conversion Settings" section in Settings page
- FR6.2: Expose "Small/Large Token Threshold" (default: 15,000, range: 100 - 200,000)
- FR6.3: Store settings in `vulcanlab.config.json`
- FR6.4: Allow editing LLM prompt templates in Settings (like existing template editing)
- FR6.5: Templates: "simple_sanitize_small" and "simple_sanitize_large" stored in `PromptTemplate` table

**FR7: Database Schema**
- FR7.1: Create `ParsedMarkdown` table:
  - `id` (PK), `work_id` (FK), `content` (TEXT), `file_type` (ENUM: pdf/epub), `classification` (ENUM: small/large), `token_count` (INT), `created_at`
- FR7.2: Create `SanitizedMarkdown` table:
  - `id` (PK), `work_id` (FK), `content` (TEXT), `token_count` (INT), `created_at`
- FR7.3: Create `HeadingModifications` table:
  - `id` (PK), `work_id` (FK), `line_number` (INT), `original_heading` (TEXT), `modified_heading` (TEXT), `action` (ENUM: remove/change/keep), `vectorize_flag` (BOOLEAN), `created_at`
- FR7.4: Seed `PromptTemplate` table with two new templates:
  - `simple_sanitize_small` - Full document sanitization template (LangChain format)
  - `simple_sanitize_large` - Condensed document analysis template (LangChain format)

**FR8: API Endpoints**
- FR8.1: `POST /simple-conversion/start` - Parse file, create Work, classify, store parsed markdown
- FR8.2: `GET /simple-conversion/work/{work_id}` - Get work status and metadata
- FR8.3: `POST /simple-conversion/sanitize` - Execute Step 2 (auto-detects small vs large from classification)
  - Request: `{ work_id, mode: "automatic" | "manual" }`
  - Response (auto): `{ sanitized_id, token_count, next_step: "chunk" }`
  - Response (manual): `{ prompt, condensed_document?, next_step: "apply_sanitize" }`
- FR8.4: `POST /simple-conversion/apply-sanitize` - Apply manually executed LLM response
  - Request: `{ work_id, llm_response }`
  - Response: `{ sanitized_id, token_count, next_step: "chunk" }`
- FR8.5: `POST /simple-conversion/chunk` - Execute Step 3 (chunking)
  - Request: `{ work_id }`
  - Response: `{ heading_chunks_count, content_chunks_count, vectorized_count }`
- FR8.6: `GET /simple-conversion/work/{work_id}/parsed` - Get parsed markdown
- FR8.7: `GET /simple-conversion/work/{work_id}/sanitized` - Get sanitized markdown

**FR9: Frontend Workflow**
- FR9.1: **Conversion Page Enhancement**:
  - When user clicks on an input PDF/EPUB file, show two buttons:
    - "Start Conversion" (existing workflow)
    - "Simple Conversion" (new workflow)
  - "Simple Conversion" button navigates to `/simple-conversion/{io_file_id}`

- FR9.2: **New Left Nav Item**:
  - Add "Simple Conversion" to left navigation menu

- FR9.3: **Simple Conversion Page** (`/simple-conversion/{io_file_id}`):
  - Similar layout to Sanitization detail page
  - Does NOT show markdown preview initially (no markdown exists yet)
  - Shows:
    - File information (filename, size, type)
    - Metadata input form:
      - Title field with "Parse from Citation" button (like existing pattern)
      - Authors field (multi-input)
      - Year field
      - Work Type dropdown
    - Two action buttons:
      - "Automatic Conversion" (primary)
      - "Manual Conversion" (secondary)

- FR9.4: **Automatic Mode Flow**:
  - Click "Automatic Conversion"
  - Show loading spinner with status updates:
    - "Parsing document..." → `POST /simple-conversion/start`
    - "Sanitizing content..." → `POST /simple-conversion/sanitize` (mode: automatic)
    - "Creating chunks..." → `POST /simple-conversion/chunk`
  - On completion, show success message with chunk counts
  - Provide link to view chunks or continue to vectorization

- FR9.5: **Manual Mode Flow**:
  - Click "Manual Conversion"
  - Execute parse step → `POST /simple-conversion/start`
  - Execute sanitize in manual mode → `POST /simple-conversion/sanitize` (mode: manual)
  - Show prompt screen with:
    - **Copyable prompt** in code block
    - **Condensed document** (for large docs) in separate section
    - **Two action buttons**:
      - "Run with API" - Execute LLM call directly (same as automatic but user triggered)
      - "Paste Response" - Opens text area to paste external LLM response
  - After paste or API execution:
    - Apply response → `POST /simple-conversion/apply-sanitize`
    - Automatically proceed to chunking → `POST /simple-conversion/chunk`
  - Show completion message

- FR9.6: **Status Tracking**:
  - Display current step: "Parsing", "Sanitizing", "Chunking", "Complete"
  - Show classification badge: "Small Document" or "Large Document"
  - Display token count and threshold comparison
  - Error handling with clear messages and retry options

### 5.2 Non-Functional Requirements

**NFR1: Performance**
- Parsing (Step 1) must complete within 60 seconds for typical PDFs (<500 pages)
- LLM calls (Step 2A/2B) timeout after 5 minutes with clear error messaging
- Frontend should show loading indicators during all async operations

**NFR2: Reliability**
- LLM failures must not corrupt Work record or partial data
- Each step must be idempotent (re-runnable without side effects)
- Store all intermediate artifacts in database for recovery

**NFR3: Storage**
- All intermediate artifacts stored in database (no output folder writes)
- Sanitized markdown compressed if >1MB (application layer, Python gzip)

**NFR4: Security**
- Input file paths must be validated to prevent path traversal
- LLM prompts must not leak sensitive system information

**NFR5: Testing**
- Unit tests must NEVER hit the database - use mocks only
- CLI tools must be functional standalone tools, not just test utilities
- Integration tests may use test database containers

## 6. UX / UI Notes

### Simple Conversion Page Layout

```
┌─────────────────────────────────────────────────────────┐
│ Simple Conversion                                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ File: research_paper.pdf (1.2 MB)                      │
│ Status: [●●●○○] Sanitizing... (Step 2 of 3)           │
│ Classification: Small Document (8,547 / 15,000 tokens) │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Metadata                                            │ │
│ │ ─────────                                           │ │
│ │ Title: [The Impact of AI on Medicine              ]│ │
│ │        [Parse from Citation]                       │ │
│ │                                                     │ │
│ │ Authors: [Dr. Jane Smith                          ]│ │
│ │          [+ Add Author]                            │ │
│ │                                                     │ │
│ │ Year: [2024]                                       │ │
│ │                                                     │ │
│ │ Type: [Article ▼]                                  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Automatic Conversion]  [Manual Conversion]            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Manual Mode Prompt Screen

```
┌─────────────────────────────────────────────────────────┐
│ Manual LLM Execution                                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Classification: Large Document                         │
│ Mode: Manual (Step 2B - Heuristic + LLM)              │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ LLM Prompt (Copy and paste into your LLM)          │ │
│ │ ─────────                                           │ │
│ │ You are an expert document processor...            │ │
│ │                                                     │ │
│ │ {full prompt content}                               │ │
│ │                                                     │ │
│ │ [Copy to Clipboard]                                │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Condensed Document                                  │ │
│ │ ─────────                                           │ │
│ │ 5: ## Introduction                                  │ │
│ │   This paper presents... [preview]                  │ │
│ │ ...                                                 │ │
│ │ [View Full Condensed Document]                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ LLM Response                                        │ │
│ │ ─────────                                           │ │
│ │ [Paste LLM response here...                       ] │ │
│ │ [                                                  ] │ │
│ │ [                                                  ] │ │
│ │                                                     │ │
│ │ [Continue with Pasted Response]                    │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ OR                                                      │
│                                                         │
│ [Run with API]                                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 7. Analytics & Success Metrics

### KPIs
- **Conversion Time**: Median time from file input to chunks in DB (target: <5 min for small docs, <15 min for large docs)
- **Automatic Completion Rate**: % of conversions that complete without manual intervention (target: >95%)
- **LLM Cost Efficiency**: Average tokens used per document (compare Step 2A vs 2B)

### Leading Indicators
- Number of documents processed per day via simple conversion
- Ratio of small vs large document processing
- Manual mode usage frequency (should be low, indicates debugging or cost concerns)

### Tracking Needs
- Log each step completion with timestamps (parse, sanitize, chunk)
- Log LLM token usage per document
- Log manual vs automatic execution mode usage
- Track error rates at each step

## 8. Dependencies & Risks

### Dependencies
- **Existing Libraries**: `conv_pdf2md.py`, `conv_epub2md.py`, `style_v_hier.py`, `chunk_headings.py`, `content_chunking.py`
- **LLM API**: Requires existing "FULL" model configuration
- **Database**: Requires new migrations for `ParsedMarkdown`, `SanitizedMarkdown`, `HeadingModifications` tables
- **Config System**: Requires `vulcanlab.config.json` read/write capability
- **Prompt Templates**: Requires `PromptTemplate` table and seed data
- **LangChain**: Template rendering for prompt variables

### Risks
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM quality degrades for large docs with condensed context | High | Medium | Provide manual editing checkpoint for `HeadingModifications` before applying (future enhancement) |
| Token threshold misconfiguration causes cost spikes | High | Low | Add validation (100 - 200,000 range) and clear documentation |
| Database size grows rapidly with parsed + sanitized markdown | Medium | High | Implement compression for content >1MB, add retention policy |
| Step 2B heuristic extraction fails for complex layouts | Medium | Medium | Log extraction failures, provide fallback to Step 2A |
| Conversion page "Simple Conversion" button confuses users | Low | Medium | Clear labeling and tooltips explaining difference |

## 9. Rollout & Milestones

### Phase 1: Backend Foundation (Week 1)
- Create database migrations for new tables
- Implement `simple_parse.py` with ParsedMarkdown storage
- Seed prompt templates in database
- Update config system for token threshold

### Phase 2: Sanitization Modules (Week 2)
- Implement `simple_sanitize_small.py` with LangChain templates
- Implement `simple_sanitize_large.py` with condensed extraction
- Refactor chunking modules for reusability
- Implement `simple_chunk.py`

### Phase 3: API Layer (Week 3)
- Implement all API endpoints
- Add response models with proper validation
- Implement error handling and status tracking
- Test API workflows (automatic and manual)

### Phase 4: Frontend Integration (Week 4)
- Add "Simple Conversion" button to Conversion page
- Create new left nav item
- Build Simple Conversion page with metadata form
- Implement automatic mode workflow
- Implement manual mode prompt screen
- Add status tracking and error handling

### Phase 5: Testing & Validation (Week 5)
- Unit tests (all mocked, no DB)
- Integration tests with sample documents
- End-to-end UI testing
- Performance benchmarking
- LLM prompt quality validation

## 10. Implementation Notes

### CLI Tools as Standalone Utilities
All CLI tools must be functional standalone utilities, not just test helpers:
- `python -m vulcanlab.simple_conversion.cli_parse` - Parse and classify document
- `python -m vulcanlab.simple_conversion.cli_sanitize` - Sanitize document (auto or manual)
- `python -m vulcanlab.simple_conversion.cli_chunk` - Create chunks from sanitized markdown
- Each CLI should have `--help`, proper argument parsing, and clear output

### Unit Test Requirements
- **NEVER** hit the database in unit tests
- Use mocks for all database operations (SQLAlchemy sessions, queries, commits)
- Test logic, not infrastructure
- Integration tests (separate suite) may use test database containers

### LangChain Template Format
Follow existing pattern for prompt templates:
```python
# Example small document template
template = """You are an expert document processor preparing academic and research documents for a Retrieval-Augmented Generation (RAG) system.

Your task is to process the provided markdown document...

## Document to Process

{markdown}

## Sanitized Output
"""

# Load from DB
template_record = session.query(PromptTemplate).filter_by(function_tag="simple_sanitize_small").first()
prompt = template_record.render(markdown=parsed_markdown)
```

## 11. Open Questions

1. **ParsedMarkdown Retention**: Should we keep parsed markdown indefinitely or delete after successful sanitization to save space?

2. **Partial Failure Recovery**: If Step 3 (chunking) fails, should we allow re-running chunking without re-sanitizing?

3. **Template Versioning**: Should we track which template version was used for each conversion for debugging?

4. **Batch Processing**: Should "Simple Conversion" support selecting multiple files at once (future enhancement)?

5. **Vectorization Trigger**: Should chunks be automatically queued for vectorization after creation, or require separate user action?

6. **Error Notification**: How should users be notified of conversion failures - in-app notification, email, or just error display on page?

7. **Undo/Retry**: Should we provide "Start Over" button to re-run conversion with different mode or settings?
