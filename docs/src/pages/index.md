# VulcanLab UI Pages Documentation

This section provides comprehensive documentation for each page and subpage in the VulcanLab UI application. Each page documentation includes:

- **API Calls**: All HTTP endpoints called by the page
- **Backend Processing**: What happens inside each API endpoint
- **Modules Used**: Python modules and functions called by the APIs
- **Database Tables**: Tables accessed and their schema details

## Page Overview

The VulcanLab UI is organized into twelve main functional areas:

### [Research (RAG)](./RAG.md)
Retrieval-Augmented Generation pipeline. Create queries, expand them, retrieve relevant chunks, consolidate context, and generate responses.

**Main Pages:**
- `/rag` - List all queries and manage RAG pipeline
- `/rag/new` - Create a new query with expansion
- `/rag/[id]` - Generate response for a query
- `/rag/[id]/inspect` - Inspect query details and pipeline status
- `/rag/[id]/results` - List all results for a query
- `/rag/[id]/results/[resultId]` - View a specific result

### [Corpus](./Corpus.md)
Works that have completed chunking and are ready for vectorization and RAG operations. Provides read-only access to sanitized content.

**Main Pages:**
- `/corpus` - List all corpus works with statistics
- `/corpus/[id]` - View sanitized markdown content for a specific work

### [Simple Conversion](./SimpleConversion.md)
Streamlined single-page document conversion workflow that automates PDF/EPUB conversion through the entire pipeline (conversion → sanitization → chunking). Supports automatic (LLM-powered) and manual execution modes.

**Main Pages:**
- `/simple-conversion` - File selection, metadata entry, and conversion history
- `/simple-conversion/automatic/[work_id]` - Automated pipeline execution with status tracking
- `/simple-conversion/manual/[work_id]` - Manual LLM prompt/response workflow
- `/simple-conversion/history/[work_id]` - View full conversion results

### [Conversion](./Conversion.md)
Convert PDF and EPUB files to markdown format. Review and inspect conversion artifacts before adding to the database.

**Main Pages:**
- `/conv` - List input files and converted files pending review
- `/conv/[id]` - Review conversion inspection options
- `/conv/[id]/add` - Add converted file to database with bibliographic metadata
- `/conv/[id]/inspect_original_md` - View and edit original markdown
- `/conv/[id]/inspect_style_hier` - Compare style.md vs hier.md versions
- `/conv/[id]/inspect_toc_titles` - View and edit table of contents titles

### [Sanitization](./Sanitization.md)
Clean and structure markdown content by extracting titles, suggesting heading improvements, and applying changes.

**Main Pages:**
- `/sanitization` - List all works with sanitization status
- `/sanitization/add` - Add pre-sanitized markdown directly
- `/sanitization/[id]` - Sanitization workflow for a specific work
- `/sanitization/[id]/titles` - View and edit extracted titles
- `/sanitization/[id]/title-changes` - View and edit title change suggestions
- `/sanitization/[id]/gen-title-changes` - Generate title changes using LLM

### [Chunking](./Chunking.md)
Split sanitized documents into semantic chunks for vectorization. Manage heading-based and content-based chunking.

**Main Pages:**
- `/chunk` - List works ready for chunking
- `/chunk/[id]` - Chunking workflow for a specific work
- `/chunk/[id]/sanitized` - View and edit sanitized file
- `/chunk/[id]/san-titles` - View and edit sanitized titles
- `/chunk/[id]/vec-suggestions` - View and edit vectorization suggestions
- `/chunk/[id]/gen-vec-sugg` - Generate vectorization suggestions using LLM

### [Vectorization](./Vectorization.md)
Generate embeddings for document chunks using embedding models. Process chunks in batches.

**Main Pages:**
- `/vec` - Vectorize eligible chunks (all works or specific work)

### [Search](./Search.md)
Comprehensive search interface for exploring the document corpus. Supports lexical (keyword-based), dense (semantic/embedding-based), and hybrid search modes using Reciprocal Rank Fusion (RRF).

**Main Pages:**
- `/search` - Search interface with configuration options
- `/search/result/[work_id]/[start_line]/[end_line]` - View full document with highlighted result

### [Cleanup](./Cleanup.md)
Data management tool for searching and deleting unwanted chunks from the database. Supports descendant deletion and headings-only filtering.

**Main Pages:**
- `/cleanup` - Search and delete chunks

### [Eval](./Eval.md)
Blind evaluation system for comparing LLM responses. Create experiments, add test prompts, submit answer pairs, and evaluate using blind randomization with comprehensive statistical analysis.

**Main Pages:**
- `/eval` - List all evaluation experiments
- `/eval/new` - Create a new experiment
- `/eval/[id]` - View and manage experiment
- `/eval/[id]/prompts/[promptId]` - Manage answer pairs and evaluations

### [Markdown Import/Export](./MarkdownImportExport.md)
Bidirectional workflow for managing markdown content. Export corpus works as markdown files with metadata, or import markdown files with metadata collection and duplicate detection.

**Main Pages:**
- `/markdown/export` - Export corpus works as markdown files
- `/markdown/import` - Import markdown files into the system

### [Settings](./Settings.md)
Manage system configuration including database settings, LLM models, file paths, templates, and RAG configuration presets.

**Main Pages:**
- `/settings` - Configuration management with multiple tabs
- `/settings/templates/[function_tag]` - Edit specific template

## Documentation Structure

Each page documentation follows this structure:

1. **Page Overview** - Purpose, navigation, and user workflow
2. **API Calls** - Complete list of endpoints with request/response details
3. **API Implementation** - Backend processing for each endpoint
4. **Modules Used** - Python modules and their functions
5. **Database Tables** - Schema and usage details

## Quick Navigation

- [Research (RAG) Documentation](./RAG.md)
- [Corpus Documentation](./Corpus.md)
- [Simple Conversion Documentation](./SimpleConversion.md)
- [Conversion Documentation](./Conversion.md)
- [Sanitization Documentation](./Sanitization.md)
- [Chunking Documentation](./Chunking.md)
- [Vectorization Documentation](./Vectorization.md)
- [Search Documentation](./Search.md)
- [Cleanup Documentation](./Cleanup.md)
- [Eval Documentation](./Eval.md)
- [Markdown Import/Export Documentation](./MarkdownImportExport.md)
- [Settings Documentation](./Settings.md)

