# Search Page Documentation

## Overview

The Search page provides a comprehensive search interface for exploring the document corpus with support for lexical (keyword-based), dense (semantic/embedding-based), and hybrid search modes. The hybrid mode uses Reciprocal Rank Fusion (RRF) to combine results from both lexical and dense searches.

### Pages

- **Main Page**: `/search` - Search interface with configuration options
- **Document Viewer**: `/search/result/[work_id]/[start_line]/[end_line]` - View full document with highlighted search result

### User Workflow

1. Enter search query in the search box
2. Select search mode (Lexical, Dense, or both for Hybrid)
3. Optional: Toggle "Headings Only" to search only H1-H5 headings
4. Optional: Adjust max preview words (50-500, default 100)
5. Optional: Configure RRF parameters for hybrid search (in advanced settings)
6. Click "Search" to execute query
7. Review paginated results with relevance scores
8. Click any result to view full document with highlighted context

## API Calls

### GET `/api/v1/search/lexical`

**Called By**: Search page when executing lexical search

**Request Parameters**:
- `q` (string, required): Search query
- `page` (integer, default: 1): Current page number
- `page_size` (integer, default: 20): Results per page
- `headings_only` (boolean, default: false): Search only in H1-H5 headings

**Response**:
```json
{
  "results": [
    {
      "chunk_id": 123,
      "work_id": 45,
      "work_title": "Introduction to Psychology",
      "work_author": "John Doe",
      "work_year": 2024,
      "level": "h2",
      "heading_breadcrumb": "Chapter 1 > Memory Systems",
      "content_preview": "Working memory is a cognitive system...",
      "start_line": 100,
      "end_line": 125,
      "bm25_score": 8.45
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

**Purpose**: Execute keyword-based search using BM25 ranking algorithm.

### GET `/api/v1/search/dense`

**Called By**: Search page when executing dense search

**Request Parameters**:
- `q` (string, required): Search query
- `page` (integer, default: 1): Current page number
- `page_size` (integer, default: 20): Results per page
- `headings_only` (boolean, default: false): Search only in H1-H5 headings

**Response**:
```json
{
  "results": [
    {
      "chunk_id": 89,
      "work_id": 45,
      "work_title": "Introduction to Psychology",
      "work_author": "John Doe",
      "work_year": 2024,
      "level": "sentence",
      "heading_breadcrumb": "Chapter 1 > Memory Systems > Working Memory",
      "content_preview": "The phonological loop and visuospatial...",
      "start_line": 110,
      "end_line": 112,
      "similarity_score": 0.87
    }
  ],
  "total": 203,
  "page": 1,
  "page_size": 20,
  "total_pages": 11
}
```

**Purpose**: Execute semantic search using vector embeddings and cosine similarity.

### GET `/api/v1/search/hybrid`

**Called By**: Search page when both Lexical and Dense modes are selected

**Request Parameters**:
- `q` (string, required): Search query
- `page` (integer, default: 1): Current page number
- `page_size` (integer, default: 20): Results per page
- `headings_only` (boolean, default: false): Search only in H1-H5 headings
- `rrf_k` (integer, default: 60): RRF smoothing constant (controls rank weight decay)
- `dense_top_k` (integer, default: 20): Number of candidates from dense search
- `lexical_top_k` (integer, default: 20): Number of candidates from lexical search
- `dense_weight` (float, default: 0.5): Weight for dense results (0.0-1.0)
- `lexical_weight` (float, default: 0.5): Weight for lexical results (0.0-1.0)

**Response**:
```json
{
  "results": [
    {
      "chunk_id": 123,
      "work_id": 45,
      "work_title": "Introduction to Psychology",
      "work_author": "John Doe",
      "work_year": 2024,
      "level": "h2",
      "heading_breadcrumb": "Chapter 1 > Memory Systems",
      "content_preview": "Working memory is a cognitive system...",
      "start_line": 100,
      "end_line": 125,
      "rrf_score": 0.0324,
      "dense_rank": 3,
      "lexical_rank": 1
    }
  ],
  "total": 189,
  "page": 1,
  "page_size": 20,
  "total_pages": 10,
  "fusion_stats": {
    "dense_candidates": 20,
    "lexical_candidates": 20,
    "total_unique": 28,
    "rrf_k": 60
  }
}
```

**Purpose**: Execute hybrid search combining lexical and dense results using Reciprocal Rank Fusion algorithm.

**RRF Formula**: `RRF_score = Σ (weight / (k + rank))` for each ranking method

### GET `/corpus/work/{work_id}/content`

**Called By**: Document viewer page on component mount

**Request**: Path parameter `work_id` (integer)

**Response**:
```json
{
  "work_id": 45,
  "title": "Introduction to Psychology",
  "author": "John Doe",
  "year": 2024,
  "content": "# Introduction to Psychology\n\n## Chapter 1\n\n..."
}
```

**Purpose**: Fetch full sanitized markdown content for document viewing.

## API Implementation

### Backend Modules Used

**Search Endpoints**: `src/vulcanlab/api/search.py`
- `search_lexical()` - BM25 keyword search
- `search_dense()` - Vector similarity search
- `search_hybrid()` - RRF fusion search

**Search Services**: `src/vulcanlab/services/search_service.py`
- `lexical_search()` - PostgreSQL full-text search with ts_rank_cd
- `dense_search()` - pgvector cosine similarity search
- `hybrid_rrf_search()` - Reciprocal Rank Fusion algorithm
- `apply_headings_filter()` - Filter to H1-H5 chunks only

**Embedding Service**: `src/vulcanlab/services/embedding_service.py`
- `embed_query()` - Generate query embedding for dense search

### Lexical Search Implementation

**Algorithm**: BM25 (Best Matching 25) via PostgreSQL `ts_rank_cd`

**Steps**:
1. Convert query to tsquery with proper operators
2. Filter chunks by `to_tsvector(content) @@ to_tsquery(query)`
3. Optional: Filter to chunks where `level IN ('h1', 'h2', 'h3', 'h4', 'h5')`
4. Rank results using `ts_rank_cd(to_tsvector(content), to_tsquery(query))`
5. Paginate and return results

**SQL Example**:
```sql
SELECT
  c.id, c.work_id, c.level, c.heading_breadcrumb,
  c.content, c.start_line, c.end_line,
  ts_rank_cd(to_tsvector('english', c.content), query) AS bm25_score
FROM chunks c
WHERE to_tsvector('english', c.content) @@ query
ORDER BY bm25_score DESC
LIMIT 20 OFFSET 0;
```

### Dense Search Implementation

**Algorithm**: Cosine similarity via pgvector extension

**Steps**:
1. Generate embedding vector for query using embedding model
2. Query chunks with pgvector cosine similarity operator `<=>`
3. Optional: Filter to heading chunks only
4. Sort by similarity score (1 - cosine_distance)
5. Paginate and return results

**SQL Example**:
```sql
SELECT
  c.id, c.work_id, c.level, c.heading_breadcrumb,
  c.content, c.start_line, c.end_line,
  1 - (c.vector <=> $1::vector) AS similarity_score
FROM chunks c
WHERE c.vector IS NOT NULL
ORDER BY c.vector <=> $1::vector
LIMIT 20 OFFSET 0;
```

### Hybrid RRF Search Implementation

**Algorithm**: Reciprocal Rank Fusion (RRF)

**Steps**:
1. Execute lexical search with `top_k` limit
2. Execute dense search with `top_k` limit
3. Merge results and calculate RRF scores:
   - For each chunk, sum weighted reciprocal ranks: `(weight / (k + rank))`
   - Lexical weight applied to lexical rank
   - Dense weight applied to dense rank
4. Sort by combined RRF score
5. Paginate and return results

**RRF Calculation**:
```python
rrf_score = (lexical_weight / (k + lexical_rank)) + (dense_weight / (k + dense_rank))
```

**Parameters**:
- `k`: Smoothing constant (typical value: 60) - prevents high ranks from dominating
- `dense_weight` / `lexical_weight`: Balance between semantic and keyword matching
- `dense_top_k` / `lexical_top_k`: Number of candidates from each method

### Content Preview Generation

**Module**: `src/vulcanlab/services/search_service.py::generate_preview()`

**Logic**:
1. Truncate content to `max_words` words
2. Append "..." if truncated
3. Handle edge cases (empty content, single word, etc.)

## Database Tables

### chunks

**Description**: Stores semantic chunks with full-text search and vector embeddings

**Key Fields for Search**:
- `id` (INTEGER PRIMARY KEY): Chunk identifier
- `work_id` (INTEGER FOREIGN KEY): References works.id
- `level` (TEXT): Chunk type (h1-h5, sentence)
- `heading_breadcrumb` (TEXT): Full heading path
- `content` (TEXT): Chunk text content (indexed for full-text search)
- `start_line` (INTEGER): Line number in source
- `end_line` (INTEGER): End line number
- `vector` (VECTOR(1536)): Embedding vector for dense search

**Indexes**:
- `idx_chunks_content_tsvector`: GIN index on `to_tsvector('english', content)` for fast lexical search
- `idx_chunks_vector`: HNSW index on `vector` for fast vector similarity search
- `idx_chunks_level`: B-tree index on `level` for headings-only filter

### works

**Description**: Stores work metadata for result display

**Key Fields**:
- `id` (INTEGER PRIMARY KEY): Work identifier
- `title` (TEXT): Work title
- `authors` (TEXT): Author name(s)
- `year` (INTEGER): Publication year
- `sanitized_md` (TEXT): Full document content

**Usage**: JOIN with chunks to include bibliographic information in search results.

## UI Components

### SearchResultCard

**Location**: `/src/app/search/SearchResultCard.tsx`

**Purpose**: Render individual search results with metadata and scores

**Features**:
- Displays bibliographic info (title, author, year)
- Shows heading breadcrumb for context
- Content preview with configurable length
- Level badge (H1-H5 or Sentence)
- Displays appropriate scores based on search mode:
  - Lexical: BM25 rank score
  - Dense: Similarity score (0-1)
  - Hybrid: RRF score + individual dense/lexical ranks
- Click to view full document

### Document Viewer Page

**Location**: `/src/app/search/result/[work_id]/[start_line]/[end_line]/page.tsx`

**Purpose**: Display full document with search result highlighted

**Features**:
- Sticky header with back navigation and "New Search" button
- Markdown rendering using ReactMarkdown
- Floating "Back to Highlight" button for quick navigation
- Highlights the specific chunk that matched the search
- Shows full document context

## Key Features

### Search Modes

1. **Lexical Search** (Keyword-based)
   - Fast, precise matching
   - Best for known terms, names, specific phrases
   - Uses PostgreSQL full-text search with BM25 ranking

2. **Dense Search** (Semantic)
   - Conceptual matching beyond keywords
   - Best for questions, concepts, paraphrased queries
   - Uses vector embeddings and cosine similarity

3. **Hybrid Search** (RRF Fusion)
   - Combines strengths of both approaches
   - Configurable weights and parameters
   - Best overall recall and precision

### Advanced RRF Configuration

**RRF k Constant** (1-200, default: 60)
- Controls how quickly rank importance decays
- Lower k: Top-ranked results weighted more heavily
- Higher k: More uniform weighting across ranks

**Top-K Values** (1-100, default: 20)
- Number of candidates from each search method
- Higher values: Better recall, more fusion candidates
- Lower values: Faster, more focused results

**Weights** (0.0-1.0, default: 0.5 each)
- Balance between lexical and dense contributions
- Higher dense weight: Favor semantic similarity
- Higher lexical weight: Favor keyword matching

### Search Filters

**Headings Only**: Restrict search to H1-H5 heading chunks
- Useful for finding section headers
- Faster search with smaller result set
- Better for navigational queries

**Max Preview Words**: Control result preview length (50-500)
- Shorter: Quick scanning of many results
- Longer: More context per result

### Pagination

- Fixed page size: 20 results per page
- Previous/Next navigation
- Shows current page / total pages
- Maintains all search parameters across pages

## Error Handling

**Validation Errors (422)**:
- Empty query string
- Both weights set to zero in hybrid mode
- Invalid parameter ranges

**Client-Side Validation**:
- Requires at least one search mode selected
- Requires non-empty query
- Validates weight sum > 0 for hybrid mode

**Error Messages**:
```json
{
  "error": "Invalid search parameters",
  "detail": "At least one weight must be greater than zero"
}
```

## Technical Implementation

**Framework**: Next.js 13+ App Router

**State Management**: React hooks (useState, useEffect)

**Form Handling**: Controlled components with validation

**UI Library**: shadcn/ui (Card, Button, Input, Checkbox, Slider, Accordion, Badge)

**Icons**: Lucide React (Search, ChevronLeft, ChevronRight)

**Styling**: Tailwind CSS with responsive design

**Markdown Rendering**: ReactMarkdown with remark-gfm for GitHub-flavored markdown

**Navigation**: Next.js Link and useRouter for client-side navigation

## Performance Considerations

**Database Indexes**:
- GIN index on content tsvector for fast lexical search
- HNSW index on vector for fast similarity search
- Covering indexes for common JOIN patterns

**Query Optimization**:
- Paginated results (20 per page) to limit data transfer
- Content preview truncation to reduce payload size
- Headings-only filter reduces search space

**Caching**:
- Query embeddings could be cached for repeated searches
- Full document content cached on first load

## Use Cases

**Lexical Search Best For**:
- Known terminology or jargon
- Author names, specific concepts
- Exact phrase matching
- Technical terms with precise definitions

**Dense Search Best For**:
- Questions ("What causes memory loss?")
- Conceptual queries ("theories of attention")
- Paraphrased content
- Cross-lingual semantic matching

**Hybrid Search Best For**:
- General-purpose search
- Maximum recall and precision
- When query intent is unclear
- Combining exact matches with related concepts
