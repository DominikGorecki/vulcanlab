# simple_conversion (AI README)

## Purpose
- Streamlined pipeline for converting PDF/EPUB documents to sanitized markdown and chunked content for RAG systems
- Automates the multi-step conversion workflow (parse → sanitize → chunk) with intelligent routing based on document size
- Replaces manual multi-page workflows with a single automated process that stores all artifacts in the database

## Quick start
- **Entry point**: Use via API router (`/api/simple-conversion/*`) or CLI commands (`simple_parse_classify`, `simple_sanitize_small`, `simple_sanitize_large`, `simple_chunk`)
- **Typical flow**: `parse_and_classify()` → `sanitize_small_document()` or `sanitize_large_document()` → `create_heading_chunks_simple()` → `create_content_chunks_simple()`
- **Dependencies**: Requires spaCy model (`python -m spacy download en_core_web_sm`), tiktoken, SQLAlchemy session, database models (Work, ParsedMarkdown, SanitizedMarkdown, Chunk)
- **Testing**: Unit tests in `tests/unit/test_*.py` for each module

## Architecture overview
- **Four-stage pipeline**: Parse/classify → Sanitize (size-dependent) → Create heading chunks → Create content chunks
- **Size-based routing**: Documents classified as SMALL (<threshold) use full LLM processing; LARGE documents use condensed heading analysis
- **Two-step chunking**: First creates heading chunks (H1-H5) as scaffolding with parent hierarchy, then creates content chunks (paragraphs/tables/figures) under headings
- **Database-driven**: All intermediate states stored in database tables (ParsedMarkdown, SanitizedMarkdown, Chunk, HeadingModification) rather than files
- **LLM integration**: Uses LangChain chat models (ModelTier.LIGHT) with configurable templates loaded from database with hardcoded fallbacks
- **Token counting**: Uses tiktoken cl100k_base encoding for accurate token estimation matching OpenAI models

## Entry points and main flows
- **Entry points**:
  - `parse_classify.py::parse_and_classify()` - Parse markdown, count tokens, classify as SMALL/LARGE
  - `sanitize_small.py::sanitize_small_document()` - Full document sanitization for small docs
  - `sanitize_large.py::sanitize_large_document()` - Condensed heading-based sanitization for large docs
  - `chunk_simple.py::create_heading_chunks_simple()` - Create heading chunks (step 1)
  - `chunk_simple.py::create_content_chunks_simple()` - Create content chunks (step 2)

- **Typical flows**:
  - **Automatic pipeline**: Parse → Classify → Sanitize (branch by size) → Create heading chunks → Create content chunks
  - **Small document flow**: Full markdown → LLM sanitization → Heading chunks → Content chunks with paragraph merging
  - **Large document flow**: Extract headings with context → Create condensed markdown → LLM analyzes headings → Apply modifications → Heading chunks → Content chunks

## Key conventions
- **Processing status**: All functions update `Work.processing_status` JSON field with step tracking (`simple_conversion_step`, `simple_conversion_classification`, `token_count`, etc.)
- **SQLAlchemy change detection**: Must reassign dict for JSON columns: `new_status = dict(work.processing_status) if work.processing_status else {}`
- **Chunk hierarchy**: Heading chunks have `parent_id` linking to parent heading; content chunks have `parent_id` linking to their containing heading chunk
- **Vector status**: Heading chunks use `vector_status="no_vec"`; content chunks use `"to_vec"` (paragraphs), `"tbl"` (tables), or `"fig"` (figures)
- **Standalone functions**: Each main function has a `*_standalone()` variant for CLI usage that manages database sessions internally
- **Error handling**: Functions raise `ValueError` for invalid states (work not found, wrong classification, missing dependencies)
- **Logging**: Uses module-level logger (`logging.getLogger(__name__)`) with INFO/DEBUG/WARNING levels

## Dependencies overview
- **Runtime dependencies**: 
  - `spacy` with `en_core_web_sm` model (sentence tokenization for chunking)
  - `tiktoken` (token counting using cl100k_base encoding)
  - `sqlalchemy` (database ORM, Session management)
  - `vulcanlab.data.models` (Work, ParsedMarkdown, SanitizedMarkdown, Chunk, HeadingModification)
  - `vulcanlab.data.database` (get_session)
  - `vulcanlab.ai.llm_factory` (create_langchain_chat)
  - `vulcanlab.ai.config` (ModelTier enum)
  - `vulcanlab.data.template_loader` (load_template)
  - `vulcanlab.config.conversion_config` (get_token_threshold)
- **Dev dependencies and tooling**: Standard Python logging, typing annotations
- **External services**: LLM API (via LangChain) for sanitization, database for persistence

## APIs and contracts
- **Function signatures**: All main functions take `work_id: int` and `session: Session`; standalone variants take only `work_id: int`
- **Return types**: Main functions return model instances (ParsedMarkdown, SanitizedMarkdown, List[Chunk]); standalone variants return tuples or counts
- **Data models**: 
  - `ParsedMarkdown`: Stores raw markdown, token_count, classification (SMALL/LARGE), file_type
  - `SanitizedMarkdown`: Stores cleaned markdown, token_count (auto-compressed if >1MB)
  - `Chunk`: Stores content, heading_breadcrumbs, start_line, end_line, level, parent_id, vector_status
  - `HeadingModification`: Tracks LLM-suggested changes (action: keep/change/remove, vectorize_flag)
- **Configuration**: Token threshold from `get_token_threshold()` determines SMALL vs LARGE classification
- **Templates**: LLM prompts loaded from database templates (`simple_sanitize_small`, `simple_sanitize_large`) with hardcoded fallback functions

## Subfolders
No subfolders present in this directory.

## File tree (depth 3)
```
simple_conversion/
├── __init__.py                    # Module package marker
├── __pycache__/                   # Python bytecode cache
├── chunk_simple.py                # Two-step chunking (heading + content chunks)
├── parse_classify.py              # Token counting and document classification
├── sanitize_large.py              # Large document sanitization (condensed approach)
└── sanitize_small.py              # Small document sanitization (full LLM processing)
```

## LLM handoff
- **When asking an LLM to work in this folder, include**:
  - `chunk_simple.py` - Core chunking logic with two-step architecture
  - `parse_classify.py` - Token counting and classification entry point
  - `sanitize_small.py` - Full document sanitization flow
  - `sanitize_large.py` - Condensed heading-based sanitization flow
  - `vulcanlab/data/models/` - Database model definitions (Work, ParsedMarkdown, SanitizedMarkdown, Chunk)
  - `vulcanlab_api/routers/simple_conversion.py` - API integration example
  - `tests/unit/test_*.py` - Test files showing expected usage patterns
- **Good first questions to ask**:
  - What is the current processing step for work_id X? (check `Work.processing_status['simple_conversion_step']`)
  - Should I use the standalone or session-based function variant?
  - Are heading chunks already created before calling `create_content_chunks_simple()`?
  - What classification (SMALL/LARGE) does this document have?
- **Guardrails**:
  - Always check `Work.processing_status` to determine current step before calling functions
  - Must create heading chunks before content chunks (two-step requirement)
  - Must sanitize before chunking (content chunks read from SanitizedMarkdown)
  - Never skip SQLAlchemy dict reassignment for JSON columns (`new_status = dict(...)`)
  - Respect chunk hierarchy: content chunks must have valid `parent_id` pointing to heading chunk
  - Small chunks (<MIN_CHUNK_WORDS) are merged with adjacent chunks automatically
  - LLM responses must be parsed carefully (JSON for large docs, literal markdown for small docs)

## Gotchas
- **SQLAlchemy JSON columns**: Must reassign entire dict to trigger change detection (`work.processing_status = new_status`), not just modify in place
- **Chunk parent requirement**: Content chunks without a parent heading chunk are skipped (logs warning but continues)
- **spaCy model dependency**: `en_core_web_sm` must be installed separately (`python -m spacy download en_core_web_sm`) or chunking will fail
- **Large document approach**: Large docs use condensed heading analysis, not full content processing - modifications only affect headings, not body text
- **Token counting**: Uses tiktoken cl100k_base which matches OpenAI models but may differ from other tokenizers

