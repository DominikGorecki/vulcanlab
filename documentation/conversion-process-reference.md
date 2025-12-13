# Conversion Process Reference

Quick reference for the three-step conversion pipeline: PDF/EPUB → Markdown → Sanitized → Chunks

---

## STEP 1: CONVERSION (PDF/EPUB → Markdown)

### UI
- **Component:** `vulcanlab_ui/src/app/conv/page.tsx`
- Shows Input Files (left) and Pending Completion (right)
- User selects file → converts → inspects variants → selects best → adds to database

### API Endpoints
- `POST /conv/convert-file` - Main conversion trigger
- `GET /conv/inspection/{io_file_id}` - Check conversion variants
- `POST /conv/generate-toc-titles/{io_file_id}` - Extract PDF bookmarks
- `POST /conv/select-file/{io_file_id}` - Choose style vs hier version
- `POST /conv/add-to-database/{io_file_id}` - Create Work record

### Core Modules
- **`conv_pdf2md.py`** - Docling-based PDF→MD (creates `.style.md` + `.hier.md`)
- **`conv_epub2md.py`** - EPUB→MD converter
- **`style_v_hier.py`** - Scores & recommends best version
- **`pdf_bookmarks2toc.py`** - Extracts PDF bookmarks to `.toc_titles.md`
- **`new_work.py`** - Creates Work database entry

### Database
- **IOFile** - Tracks input/output files during conversion
- **Work** - Created with: `title`, `authors`, `year`, `markdown_path`
  - `files` JSON: stores all pipeline files with paths/hashes
  - `toc`: table of contents array

### Output Files
- `{name}.md` - Selected main markdown
- `{name}.style.md`, `{name}.hier.md` - Conversion variants
- `{name}.toc_titles.md` - PDF bookmarks

---

## STEP 2: SANITIZATION (Structure Cleanup)

### UI
- **Component:** `vulcanlab_ui/src/app/sanitization/page.tsx`
- Table of works showing: "No markdown", "Needs work", "Sanitized"
- Detail page: `/sanitization/{work_id}` - Extract → Suggest → Apply workflow

### API Endpoints
- `POST /sanitization/work/{work_id}/extract-titles` - Extract all headings
- `POST /sanitization/work/{work_id}/suggest-title-changes` - LLM suggests hierarchy fixes
- `POST /sanitization/work/{work_id}/apply-title-changes` - Apply changes → sanitized.md
- `GET/PUT /sanitization/work/{work_id}/title-changes/content` - Edit suggestions manually

### Core Modules
- **`extract_titles.py`** - Extracts headings to `.titles.md` (format: `line_num: heading`)
- **`suggest_heading_changes.py`** - LLM analyzes structure, suggests improvements → `.title_changes.md`
- **`apply_title_changes.py`** - Applies modifications → `.sanitized.md`
- **`title_changes_interactive.py`** - Table editor for manual edits

### Database
- **Work.files** updated with:
  - `titles` - Extracted headings file
  - `title_changes` - LLM suggestions
  - `sanitized` - Final cleaned markdown

### Output Files
- `{name}.titles.md` - Line-numbered headings
- `{name}.title_changes.md` - Suggested modifications
- `{name}.sanitized.md` - Final sanitized version

---

## STEP 3: CHUNKING (Semantic Division)

### UI
- **Component:** `vulcanlab_ui/src/app/chunk/page.tsx`
- Table of works with sanitized files showing chunk status
- Detail page: `/chunk/{work_id}` - Extract titles → Vectorization suggestions → Apply chunks

### API Endpoints
- `POST /chunk/work/{work_id}/extract-sanitized-titles` - Extract from sanitized.md
- `POST /chunk/work/{work_id}/vec-suggestions/run` - LLM suggests VECTORIZE/SKIP
- `POST /chunk/work/{work_id}/vec-suggestions/manual-all-vectorize` - Mark all VECTORIZE
- `POST /chunk/work/{work_id}/apply-heading-chunks` - Create heading Chunks in DB
- `POST /chunk/work/{work_id}/apply-content-chunks` - Create content Chunks in DB

### Core Modules
- **`suggested_chunks.py`** - LLM generates vectorization decisions → `.vec_sugg.md`
- **`chunk_headings.py`** - Creates Chunk records for headings marked VECTORIZE
- **`content_chunking.py`** - Creates sentence/paragraph Chunks
- **`vec_suggestions_interactive.py`** - Table editor for vectorization decisions

### Database
- **Work.files** updated with:
  - `sanitized_titles` - Headings from sanitized
  - `vec_suggestions` - VECTORIZE/SKIP decisions
- **Work.processing_status** tracks:
  - `heading_chunks`: "completed"|"pending"|"failed"
  - `content_chunks`: "completed"|"pending"|"failed"
- **Chunk** records created:
  - Fields: `work_id`, `parent_id`, `level` (H1-H5, sentence, chunk)
  - `content`, `heading_breadcrumbs`, `start_line`, `end_line`
  - `embedding` (768-dim, initially NULL)
  - `vector_status`: "to_vec" | "vec" | "no_vec" | "vec_err"

### Output Files
- `{name}.sanitized_titles.md` - Extracted headings
- `{name}.vec_sugg.md` - VECTORIZE/SKIP per heading
- Database: Hierarchical Chunk tree ready for vectorization

---

## Complete Data Flow

```
PDF/EPUB Input
    ↓
CONVERSION: Docling → .style.md + .hier.md → Select best → Work.files['original_markdown']
    ↓
SANITIZATION: Extract titles → LLM suggests fixes → Apply → .sanitized.md
    ↓
CHUNKING: Extract sanitized titles → LLM suggests VECTORIZE/SKIP → Create Chunk records
    ↓
Chunks ready for vectorization (vector_status='to_vec')
```

## Key Router Files
- **Conversion:** `src/vulcanlab_api/routers/conversion.py` (1,375 lines)
- **Sanitization:** `src/vulcanlab_api/routers/sanitization.py` (1,161 lines)
- **Chunking:** `src/vulcanlab_api/routers/chunking.py` (902 lines)
