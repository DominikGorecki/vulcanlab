# RAG Pipeline: How VulcanLab Finds and Delivers Relevant Information

This document explains how VulcanLab's Retrieval-Augmented Generation (RAG) system finds the most relevant information from your documents and presents it to an AI model for generating accurate, cited responses.

## Overview

The VulcanLab RAG pipeline consists of three main stages:

1. **Retrieval** - Finding the most relevant document chunks
2. **Consolidation** - Organizing and merging related chunks for better context
3. **Augmentation** - Formatting the information and generating the final AI prompt

Each stage can be configured independently through RAG configuration presets, allowing you to optimize for different use cases.

---

## Stage 1: Retrieval

The retrieval stage identifies the most relevant content from your document database. It uses a sophisticated multi-layer approach to ensure both high recall (finding everything relevant) and high precision (ranking the best matches first).

### How It Works

#### Step 1: Broad Search (Casting a Wide Net)

VulcanLab uses two complementary search methods:

**Dense Search (Semantic Similarity)**
- Uses vector embeddings to find semantically similar content
- Powered by `pgvector` in PostgreSQL for fast similarity search
- Excellent at understanding meaning and context, even when exact words differ
- Example: Searching for "memory problems" will find text about "cognitive decline" or "forgetfulness"

**Lexical Search (Keyword Matching)**
- Uses PostgreSQL's full-text search (`websearch_to_tsquery`)
- Critical for finding exact terms, acronyms, and specific phrases
- Supports quoted phrases, Boolean operators (AND, OR), and negation
- Example: Searching for "DSM-5" will find exact matches that vector search might miss

**Optional Sentence Filtering**
- If enabled, filters out chunks with too few sentences during the database query
- Helps focus retrieval on substantive content rather than fragments
- Configured via `min_sentence_filter_enabled` and `min_sentence_count` settings

#### Step 2: Fusion (Combining Results)

Results from both search methods are merged using **Reciprocal Rank Fusion (RRF)**:
- A proven mathematical technique for combining ranked lists
- Gives weight to items that appear highly ranked in multiple searches
- Extremely fast because it only processes rankings, not text content
- Produces a shortlist of top candidates (typically 60-75 chunks)

Formula: `score = 1.0 / (k + rank)` where `k` is typically 50

#### Step 3: Enrichment (Adding Context)

Before reranking, chunks are enriched with additional context using the document hierarchy:

**Parent Traversal Process**
- Checks if a chunk has enough content (word count threshold)
- If not, walks up the `parent_id` chain to find a larger parent chunk
- Merges parent content to provide complete context
- Applies sliding window truncation if content gets too long

**Why This Matters**
- Short fragments gain necessary context (surrounding paragraphs, section headers)
- The reranker and AI model see the full picture, not isolated sentences
- Works entirely from the database—no local files required

**Sliding Window Algorithm**
- Preserves all markdown headings for structure
- Keeps the original chunk content intact
- Adds surrounding context up to a maximum word count
- Finds complete sentence boundaries to avoid cutting mid-sentence

#### Step 4: Reranking (Deep Analysis)

The shortlist is passed to a **Cross-Encoder reranker** model (`BAAI/bge-reranker-large`):
- A specialized AI model that deeply analyzes how well each chunk answers the query
- Much more accurate than initial search, but also slower
- Only runs on the shortlist (not all millions of chunks) for efficiency
- Produces a relevance score for each (query, enriched chunk) pair

**Additional Scoring Adjustments**
- **Entity Boost**: Chunks containing entities from the query get a score boost (default: +0.05 per entity)
- **Intent Bias**: Different question types prefer different content structures
  - Definitions prefer H2/H3 headings with moderate length
  - Mechanisms prefer H3/H4 headings or detailed chunks
  - Comparisons prefer H2/H3 headings with tables or lists
  - Study details prefer longer, detailed content

#### Step 5: Diversity Selection (MMR)

**Maximal Marginal Relevance (MMR)** ensures variety in selected chunks:
- Iteratively selects chunks that are relevant to the query
- While also being diverse compared to already-selected chunks
- Prevents redundant information (e.g., five chunks all saying the same thing)
- Controlled by `mmr_lambda` parameter (default: 0.7 = 70% relevance, 30% diversity)

### Why Two-Stage Retrieval?

You might wonder: why use both RRF fusion and BGE reranking?

This is a standard practice in high-performance RAG systems called **Two-Stage Retrieval**:

1. **Stage 1 (RRF) = Speed + Recall**: Quickly identifies anything that might be relevant from millions of database rows. Fast and cheap.
2. **Stage 2 (BGE) = Accuracy + Precision**: Deeply analyzes only the top candidates. Slow but highly accurate.

This gives you the best of both worlds: database-speed search with AI-quality ranking.

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `dense_limit` | 19 | Maximum results from vector similarity search |
| `lexical_limit` | 5 | Maximum results from keyword search |
| `rrf_k` | 50 | RRF constant controlling rank weighting |
| `top_k_rrf` | 75 | Number of candidates to keep after RRF fusion |
| `top_n_final` | 17 | Final number of chunks after reranking and MMR |
| `entity_boost` | 0.05 | Score boost per query entity found in chunk |
| `mmr_lambda` | 0.7 | Balance between relevance (1.0) and diversity (0.0) |
| `min_word_count` | 150 | Minimum words to trigger parent enrichment |
| `max_word_count` | 1000 | Maximum words for enriched content |
| `min_sentence_filter_enabled` | false | Enable database filtering by sentence count |
| `min_sentence_count` | 5 | Minimum sentences required (if filter enabled) |
| `reranker_batch_size` | 8 | Number of query-chunk pairs processed at once |
| `reranker_max_length` | 512 | Maximum token length for reranker input |

---

## Stage 2: Consolidation

Consolidation transforms the list of retrieved chunks into a cleaner set of context groups by analyzing document structure and relationships.

### Why Consolidation?

Retrieved chunks might be:
- Small fragments from the same section
- Overlapping pieces of a larger passage
- Adjacent paragraphs that should be read together

Consolidation merges these into coherent context blocks while preserving document structure.

### How It Works

#### Phase 1: Coverage-Based Replacement

**Process:**
1. Groups retrieved chunks by their common parent
2. Calculates what percentage of the parent's content is represented by the children
3. If coverage exceeds the threshold (default: 50%), replaces all fragments with the complete parent content

**Example:**
- Parent section P has 2000 characters
- Retrieved chunks: f1 (500 chars), f2 (300 chars), f3 (400 chars)
- Coverage: (500+300+400) / 2000 = 60%
- Result: Replace all three fragments with the complete parent (2000 chars)

**Why This Works:**
- When you've retrieved most of a section anyway, showing the complete section provides better context
- Prevents awkward gaps in the middle of explanations
- Reduces redundancy in the final context

#### Phase 2: Adjacent Merging

**Process:**
1. Merges chunks that are close together in the original document
2. Configurable line gap threshold (default: 7 lines)
3. Can optionally extract content directly from parent chunk to ensure perfect continuity

**Hierarchy Preservation:**
- Every consolidated group retains its heading chain (breadcrumb path)
- Example: "Chapter 3 > Methodology > Data Collection > Sampling"
- Helps the AI understand the structural context of each piece of information

#### Iteration Strategy

The consolidation algorithm:
- Repeats until no more merging is possible
- Works from the deepest hierarchical levels upward
- Stores results in the `clean_retrieval_context` field

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `coverage_threshold` | 0.5 | Minimum parent coverage (50%) to trigger replacement |
| `line_gap` | 7 | Maximum lines between chunks for adjacency merging |
| `min_content_length` | 350 | Minimum character count for consolidated groups |
| `enrich_from_parent` | true | Extract merged content directly from parent chunk |

---

## Stage 3: Augmentation

Augmentation is the final stage where consolidated context is formatted into a complete prompt for the AI model.

### How It Works

#### Step 1: Context Formatting

Each consolidated group is formatted as a distinct, cited block:

```
[S1] Source: Clinical Psychology Textbook > Chapter 5 > Assessment Methods > Standardized Tests
(work_id=42, lines 234-267)

[Content of the consolidated group...]

[S2] Source: DSM-5 Diagnostic Manual > Mood Disorders > Major Depressive Disorder
(work_id=18, lines 89-134)

[Content of the consolidated group...]
```

**Citation System:**
- Each block gets a unique citation tag (`[S1]`, `[S2]`, etc.)
- Source information includes document title and heading breadcrumb
- Line numbers provide traceability back to original documents

#### Step 2: Prompt Engineering

The system builds a complete RAG prompt with:

**Instructions Section:**
- Evidence policy (prioritize provided sources, allow general knowledge if marked)
- Citation rules (mandatory `[S#]` tags for every claim)
- Response formatting guidance

**Context Section:**
- All formatted context blocks with citations
- Metadata about query intent and extracted entities

**Query Section:**
- Original user question
- Intent classification (e.g., DEFINITION, MECHANISM, COMPARISON)
- Entity hints for relevance

**Template System:**
- RAG templates are stored in the database
- Customizable for different use cases
- Falls back to default template if needed

#### Step 3: LLM Execution

The complete augmented prompt is sent to the configured AI provider with:
- System instructions for evidence-based responses
- Formatted context with citations
- User query with metadata
- Rules for citation and knowledge usage

### Intent-Based Guidance

Different question intents receive tailored instructions:

| Intent | AI Guidance | Example |
|--------|------------|---------|
| DEFINITION | Provide clear, concise definitions with examples | "What is cognitive behavioral therapy?" |
| MECHANISM | Explain processes and how things work | "How does SSRIs affect serotonin levels?" |
| COMPARISON | Use tables or structured comparisons | "Compare CBT and DBT approaches" |
| APPLICATION | Focus on practical applications and case studies | "When should you use exposure therapy?" |
| STUDY_DETAIL | Provide comprehensive details about research | "What were the findings of the 2018 Smith study?" |
| CRITIQUE | Analyze strengths, limitations, and critiques | "What are criticisms of the DSM-5?" |

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `top_n_contexts` | 5 | Number of consolidated groups to include in prompt |

---

## Database-Driven Architecture

VulcanLab's RAG pipeline is entirely **database-driven**, meaning all context enrichment and consolidation happens using the chunk hierarchy stored in the database.

### Key Advantages

**No File Dependencies**
- Doesn't require local sanitized markdown files on the server
- All context is retrieved from the `chunks` table via `parent_id` relationships
- More robust and easier to deploy

**Works with All Conversion Types**
- Compatible with "Simple Conversion" (structural chunking without file export)
- Compatible with "Full Conversion" (comprehensive parsing with markdown export)
- No special handling needed for different document types

**Hierarchical Reconstruction**
- Document structure is preserved through parent-child relationships
- Headings and section context are reconstructed from parent chunks
- Breadcrumb trails show the path from root to each chunk

### Data Model

**Chunk Table:**
```
- id (Primary Key)
- parent_id (Foreign Key → chunks.id)
- work_id (Foreign Key → works.id)
- level: 'H1' | 'H2' | 'H3' | 'H4' | 'H5' | 'sentence' | 'chunk'
- content: Full text content
- heading_breadcrumbs: JSON array of heading hierarchy
- embedding: 768-dimensional vector (pgvector)
- start_line, end_line: Position in original document
- sentence_count: Number of sentences (optional)
```

**Query Table:**
```
- id (Primary Key)
- original_query: User's question
- intent: Classified intent type
- entities: Extracted entities (JSON)
- embedding_original: Query vector
- retrieved_context: Full retrieval results (JSON)
- clean_retrieval_context: Consolidated results (JSON)
```

---

## RAG Configuration Presets

VulcanLab supports multiple RAG configuration presets, allowing you to optimize the pipeline for different use cases.

### Configuration Structure

```json
{
  "retrieval": {
    "dense_limit": 19,
    "lexical_limit": 5,
    "rrf_k": 50,
    "top_k_rrf": 75,
    "top_n_final": 17,
    "entity_boost": 0.05,
    "min_word_count": 150,
    "max_word_count": 1000,
    "mmr_lambda": 0.7,
    "min_sentence_filter_enabled": false,
    "min_sentence_count": 5,
    "reranker_batch_size": 8,
    "reranker_max_length": 512
  },
  "consolidation": {
    "coverage_threshold": 0.5,
    "line_gap": 7,
    "min_content_length": 350,
    "enrich_from_parent": true
  },
  "augmentation": {
    "top_n_contexts": 5
  }
}
```

### Using Presets

**Via API:**
```python
# Use default preset
POST /rag/queries/{id}/retrieve

# Use named preset
POST /rag/queries/{id}/retrieve?config_preset=high-precision

# Consolidate with specific preset
POST /rag/queries/{id}/consolidate?config_preset=detailed-context
```

**Managing Presets:**
- `GET /api/rag-config/` - List all presets
- `GET /api/rag-config/default` - Get default preset
- `POST /api/rag-config/` - Create new preset
- `PUT /api/rag-config/{name}` - Update preset
- `DELETE /api/rag-config/{name}` - Delete preset

---

## Practical Examples

### Example 1: Parent Traversal Enrichment

**Scenario:** Small chunk retrieved (50 words)

**Process:**
1. Chunk A (50 words) has parent B (200 words) and grandparent C (400 words)
2. `min_word_count=150` requires more content
3. System walks to Parent B: combined content = 250 words
4. 250 > 150 ✓ - traversal stops
5. **Result:** Context includes full content of Parent B (which contains A)

**Enrichment Metrics Tracked:**
- `enrichment_percentage`: % of chunks that needed enrichment
- `average_traversal_depth`: Average number of parent hops
- `traversal_reached_root_count`: Chunks that reached root without meeting threshold
- `fallback_count`: Chunks that couldn't be enriched

### Example 2: Sliding Window Truncation

**Scenario:** Parent content exceeds maximum word count

**Process:**
1. Grandparent C (1000 words) is reached during traversal
2. `max_word_count=750` limits total content
3. System applies sliding window algorithm:
   - Preserves all markdown headings
   - Keeps the original chunk content
   - Adds surrounding context up to 750 words
   - Finds sentence boundaries to avoid mid-sentence cuts
4. **Result:** Concise 750-word context with structure and relevant history

### Example 3: Coverage-Based Consolidation

**Scenario:** Multiple fragments from same section

**Process:**
1. Parent section P: 2000 characters
2. Retrieved fragments: f1 (500), f2 (300), f3 (400)
3. Coverage calculation: (500+300+400) / 2000 = 0.6 (60%)
4. Threshold check: 60% ≥ 50% ✓
5. **Result:** All three fragments replaced with complete parent (2000 chars)

---

## Performance and Logging

### Logging System

VulcanLab generates detailed logs for each pipeline stage when logging is enabled:

**Retrieval Logs** (`retrieve_query_{id}_{timestamp}.json`):
- Search parameters and settings
- Dense search results with ranks
- Lexical search results with ranks
- RRF fusion scores
- Reranking scores with entity/intent boosts
- MMR diversity selection
- Final selected chunks

**Consolidation Logs** (`consolidate_query_{id}_{timestamp}.json`):
- Initial retrieved chunks
- Coverage calculations
- Parent replacement decisions
- Adjacent merging operations
- Final consolidated groups

**Augmentation Logs** (`augment_query_{id}_{timestamp}.json`):
- Selected context groups
- Formatted citation blocks
- Complete generated prompt
- Template information

### Configuration

Enable logging in `config.yaml`:
```yaml
logging:
  enabled: true
  log_dir: "/path/to/logs"
```

---

## API Workflow

### Full Pipeline (Automatic)

```
POST /rag/auto
{
  "query": "What are the symptoms of major depression?",
  "config_preset": "default"
}
```

This automatically runs all stages and returns the AI response.

### Step-by-Step Pipeline (Manual)

For more control, run each stage independently:

```
1. POST /rag/queries (create query)
2. POST /rag/queries/{id}/embed (vectorize)
3. POST /rag/queries/{id}/retrieve?config_preset=high-recall (retrieve)
4. POST /rag/queries/{id}/consolidate?config_preset=detailed-context (consolidate)
5. GET /rag/queries/{id}/augment/prompt (generate prompt)
6. POST /rag/queries/{id}/augment/run (run LLM)
```

---

## Summary

VulcanLab's RAG pipeline delivers accurate, cited responses through a sophisticated three-stage process:

1. **Retrieval** uses dual search (semantic + keyword), fusion, enrichment, reranking, and diversity selection to find the best chunks
2. **Consolidation** merges related fragments into coherent context blocks while preserving document structure
3. **Augmentation** formats everything into a well-structured prompt with citations and intent-based guidance

The entire system is database-driven, configurable through presets, and designed for both accuracy and performance.
