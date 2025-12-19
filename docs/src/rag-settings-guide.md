# RAG Settings Guide

This guide provides detailed explanations of all RAG (Retrieval-Augmented Generation) configuration settings in VulcanLab. Understanding these settings will help you optimize the RAG pipeline for your specific use case.

## Overview

RAG settings control the three-stage pipeline that finds and delivers relevant information:

1. **Retrieval** - Finding relevant chunks (17 parameters)
2. **Consolidation** - Merging and organizing chunks (4 parameters)
3. **Augmentation** - Formatting context for the LLM (1 parameter)

Settings are organized into **presets** - named configurations that can be saved, modified, and switched between easily.

---

## RAG Presets

### What Are Presets?

Presets are named collections of RAG parameters. Instead of adjusting 22+ individual settings every time, you can:
- Save configurations as presets
- Switch between presets for different use cases
- Set a default preset for standard operations
- Create specialized presets for specific document types or query patterns

### Managing Presets

**Create a Preset:**
1. Configure all desired parameters
2. Enter a preset name (e.g., "High Precision" or "Fast Retrieval")
3. Optionally add a description
4. Click "Create Preset"

**Switch Presets:**
1. Select a preset from the dropdown
2. Parameters automatically update to match the preset
3. Changes take effect immediately for new queries

**Update a Preset:**
1. Load the preset you want to modify
2. Adjust parameters as needed
3. Click "Update Preset"

**Delete a Preset:**
1. Select the preset
2. Click "Delete Preset"
3. Confirm deletion

**Set Default:**
1. Select the preset you want as default
2. Click "Set as Default"
3. This preset will be used when no specific preset is requested

---

## Retrieval Parameters

Retrieval parameters control how VulcanLab searches for and selects relevant chunks from your document database.

### Search Parameters

#### `dense_limit`
**Default:** 19
**Range:** 0-100
**What It Does:** Maximum number of chunks to retrieve per dense vector search.

**How It Works:**
- Dense search uses vector embeddings to find semantically similar content
- Higher limit = more candidates from vector similarity
- Each expanded query (MQE) or HyDE variant runs a separate dense search

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Low (5-10) | Faster, more focused retrieval | Documents are highly structured, queries are specific |
| Medium (15-25) | Balanced recall and precision | General-purpose usage, default recommendation |
| High (30-50+) | Maximum recall, slower | Complex queries, need to cast wide net |
| Zero (0) | Disables dense search entirely | Relying only on keyword matching |

**Example:**
- `dense_limit=19`: Each of 3 expanded queries returns up to 19 chunks = max 57 dense candidates
- `dense_limit=10`: Each of 3 expanded queries returns up to 10 chunks = max 30 dense candidates

---

#### `lexical_limit`
**Default:** 5
**Range:** 0-50
**What It Does:** Maximum number of chunks to retrieve per lexical (keyword) search.

**How It Works:**
- Lexical search uses PostgreSQL full-text search for exact keyword matches
- Critical for finding specific terms, acronyms, proper nouns
- Uses BM25-style ranking (considers term frequency and document length)

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Low (2-5) | Primarily semantic search | General queries, well-embedded concepts |
| Medium (5-15) | Balanced keyword + semantic | Technical documents with specific terminology |
| High (20-50) | Strong keyword focus | Searching for rare terms, acronyms, codes |
| Zero (0) | Disables lexical search | Pure semantic search only |

**Example:**
- Query: "DSM-5 diagnostic criteria for ADHD"
- Lexical search excels at finding exact matches for "DSM-5" and "ADHD"
- Dense search finds semantically related content about attention disorders

---

### Fusion Parameters

#### `rrf_k`
**Default:** 50
**Range:** 1-100
**What It Does:** The constant used in Reciprocal Rank Fusion (RRF) formula.

**How It Works:**
- RRF combines multiple ranked lists (dense results + lexical results) into one
- Formula: `score = 1 / (k + rank)`
- Lower k = more weight to top-ranked items
- Higher k = more balanced weighting across ranks

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Low (10-30) | Heavily favors top results | Trust that best results rank highly |
| Medium (40-60) | Balanced fusion, default | General-purpose usage |
| High (70-100) | More democratic weighting | Want to include lower-ranked items |

**Example:**
```
k=50:
  Rank 1: score = 1/(50+1) = 0.0196
  Rank 10: score = 1/(50+10) = 0.0167
  Rank 50: score = 1/(50+50) = 0.0100

k=20:
  Rank 1: score = 1/(20+1) = 0.0476 (higher!)
  Rank 10: score = 1/(20+10) = 0.0333
  Rank 50: score = 1/(20+50) = 0.0143
```

Lower k creates bigger score differences between ranks.

---

#### `top_k_rrf`
**Default:** 75
**Range:** 1-200
**What It Does:** Number of top candidates to keep after RRF fusion.

**How It Works:**
- After merging dense and lexical results via RRF, this limits the candidate pool
- These candidates proceed to the expensive reranking stage
- Acts as a "shortlist" before deep analysis

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Low (20-40) | Faster reranking, less context | Speed is priority, simple queries |
| Medium (60-100) | Balanced performance | General-purpose usage |
| High (100-200) | Maximum context, slower | Complex queries, maximum recall needed |

**Constraint:** Must be ≥ `top_n_final`

**Performance Note:** Reranking is the slowest stage. Higher `top_k_rrf` = longer processing time.

---

### Enrichment Parameters

#### `min_word_count`
**Default:** 150
**Range:** 0-1000
**What It Does:** Minimum word count threshold that triggers parent enrichment.

**How It Works:**
- After retrieval, chunks below this word count are enriched
- System walks up the parent_id chain to find larger context
- Stops when combined content reaches this threshold

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Low (50-100) | Less enrichment, faster | Chunks are already well-sized |
| Medium (150-250) | Balanced context | Default recommendation |
| High (300-500) | More enrichment, larger context | Need substantial context per chunk |
| Zero (0) | No enrichment | Use original chunk sizes only |

**Example:**
```
Chunk A: 50 words
Parent B: 200 words
Grandparent C: 400 words

min_word_count=150:
  - A (50 words) < 150 → walk to B
  - A+B content (200 words) ≥ 150 → stop
  - Result: 200-word context

min_word_count=300:
  - A (50 words) < 300 → walk to B
  - A+B (200 words) < 300 → walk to C
  - A+B+C (400 words) ≥ 300 → stop
  - Result: 400-word context
```

---

#### `max_word_count`
**Default:** 1000
**Range:** Not explicitly limited, but typically 500-2000
**What It Does:** Maximum word count for enriched chunk content.

**How It Works:**
- If parent enrichment produces content exceeding this limit, a sliding window truncates it
- Preserves original chunk content and all headings
- Finds sentence boundaries to avoid cutting mid-sentence

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Low (500-750) | Compact context, faster reranking | Want concise chunks |
| Medium (1000-1500) | Balanced detail | Default recommendation |
| High (2000-3000) | Maximum context | Need full sections |

**Note:** Very high values may exceed reranker token limits.

---

#### `min_char_count`
**Default:** 250
**Range:** 0-5000
**What It Does:** Minimum character count for chunk inclusion (legacy parameter).

**Status:** Deprecated in favor of `min_word_count`. Use `min_word_count` instead.

---

#### `min_content_length`
**Default:** 750
**Range:** 0-5000
**What It Does:** Minimum content length before enrichment (legacy parameter).

**Status:** Deprecated in favor of `min_word_count`. Use `min_word_count` instead.

---

#### `enrich_lines_above`
**Default:** 0
**Range:** 0-50
**What It Does:** Lines to add above chunk when enriching (legacy parameter).

**Status:** Deprecated. Parent traversal is now the primary enrichment method.

---

#### `enrich_lines_below`
**Default:** 13
**Range:** 0-50
**What It Does:** Lines to add below chunk when enriching (legacy parameter).

**Status:** Deprecated. Parent traversal is now the primary enrichment method.

---

### Reranking Parameters

#### `reranker_batch_size`
**Default:** 8
**Range:** 1-32
**What It Does:** Number of query-chunk pairs to process simultaneously during reranking.

**How It Works:**
- BGE reranker processes pairs in batches for efficiency
- Larger batches = better GPU utilization but more memory
- Smaller batches = less memory but more API calls

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Small (1-4) | Lower memory usage | Limited GPU memory, CPU inference |
| Medium (8-16) | Balanced performance | Default for most GPUs |
| Large (16-32) | Faster with good GPU | Powerful GPU with ample memory |

**Note:** Requires reranker model loaded in memory. Not relevant if using API-based reranking.

---

#### `reranker_max_length`
**Default:** 512
**Range:** 128-1024
**What It Does:** Maximum token length for reranker input (query + chunk).

**How It Works:**
- Reranker models have maximum context windows
- Content exceeding this length is truncated
- Affects how much text the reranker can analyze

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Low (128-256) | Faster, sees less context | Short chunks, performance critical |
| Medium (512) | Balanced, default | General-purpose usage |
| High (768-1024) | Slower, sees more context | Long chunks, need full analysis |

**Trade-off:** Higher values provide more context to reranker but slower inference.

---

### Scoring Parameters

#### `entity_boost`
**Default:** 0.05
**Range:** 0.0-0.5
**What It Does:** Score boost applied for each query entity found in chunk content.

**How It Works:**
- VulcanLab extracts entities from the query (names, places, concepts, etc.)
- For each entity found in a chunk, add this score boost
- Helps prioritize chunks that mention query-specific entities

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| None (0.0) | No entity bias | Entity matching not important |
| Low (0.01-0.03) | Subtle entity preference | Slight preference for entity matches |
| Medium (0.05-0.1) | Moderate entity boost | Default, balanced approach |
| High (0.15-0.5) | Strong entity focus | Entity matching very important |

**Example:**
```
Query: "How does Freud's theory explain dreams?"
Entities: ["Freud", "theory", "dreams"]

Chunk 1: Mentions "Freud" and "dreams" → +0.10 boost (2 entities × 0.05)
Chunk 2: Mentions "dreams" only → +0.05 boost (1 entity × 0.05)
Chunk 3: Mentions none → +0.00 boost
```

---

### Diversity Parameters

#### `mmr_lambda`
**Default:** 0.7
**Range:** 0.0-1.0
**What It Does:** Balance between relevance and diversity in final selection (Maximal Marginal Relevance).

**How It Works:**
- MMR iteratively selects chunks that are both relevant and diverse
- Lambda controls the balance:
  - 1.0 = Pure relevance (ignore diversity)
  - 0.0 = Pure diversity (ignore relevance)
  - 0.7 = 70% relevance, 30% diversity

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| High (0.9-1.0) | Maximize relevance, allow redundancy | Want best matches even if similar |
| Medium (0.6-0.8) | Balanced approach | Default, general-purpose |
| Low (0.3-0.5) | Maximize diversity | Want varied perspectives |
| Very Low (0.0-0.2) | Maximum diversity, less relevance | Exploratory queries |

**Example:**
```
lambda=0.9 (high relevance focus):
  - May select multiple chunks from same section
  - All chunks highly relevant to query
  - Some information redundancy

lambda=0.5 (balanced):
  - Selects chunks from different sections
  - Balance of relevance and variety
  - Less redundancy

lambda=0.2 (high diversity focus):
  - Selects chunks from diverse sources
  - Maximum variety in perspectives
  - Some less relevant chunks included
```

---

### Final Selection Parameters

#### `top_n_final`
**Default:** 17
**Range:** 1-50
**What It Does:** Final number of chunks selected after reranking and MMR.

**How It Works:**
- After reranking scores all candidates, MMR selects this many chunks
- These chunks proceed to consolidation stage
- More chunks = more context but also more noise and processing

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Low (5-10) | Focused, concise context | Simple queries, clear answers |
| Medium (15-20) | Balanced coverage | Default, general-purpose |
| High (25-40) | Comprehensive coverage | Complex queries, need thorough answer |
| Very High (40+) | Maximum information | Exploratory research queries |

**Constraint:** Must be ≤ `top_k_rrf`

**Cost Note:** More chunks = more tokens sent to LLM = higher API costs.

---

### Sentence Filtering Parameters

#### `min_sentence_filter_enabled`
**Default:** false
**What It Does:** Enable/disable filtering chunks by minimum sentence count during database search.

**How It Works:**
- When enabled, database query includes `WHERE sentence_count >= min_sentence_count`
- Filters out very short chunks (fragments, isolated headings) at query time
- Reduces retrieval of low-quality, fragmentary content

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Disabled | Retrieve all chunks | Chunks already well-sized, or need all content |
| Enabled | Filter short chunks | Want only substantive content blocks |

**Use Cases:**
- Enable when document processing created many small fragments
- Disable when short chunks might contain important information (definitions, glossaries)

---

#### `min_sentence_count`
**Default:** 5
**Range:** 1+
**What It Does:** Minimum number of sentences required in a chunk (when filter is enabled).

**How It Works:**
- Only applies when `min_sentence_filter_enabled=true`
- Chunks with fewer sentences are excluded from search results
- Helps focus on substantive content

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Low (1-3) | Minimal filtering | Include shorter content blocks |
| Medium (5-7) | Balanced filtering | Default, filter fragments |
| High (10+) | Strict filtering | Want only long paragraphs/sections |

**Note:** This filter happens at database query time, before enrichment. Very efficient but strict.

---

## Consolidation Parameters

Consolidation parameters control how retrieved chunks are merged and organized into coherent context groups.

### Coverage Parameters

#### `coverage_threshold`
**Default:** 0.5 (50%)
**Range:** 0.0-1.0
**What It Does:** Percentage of parent content that must be present in child chunks to trigger parent replacement.

**How It Works:**
- Groups retrieved chunks by their common parent
- Calculates: `coverage = (total child characters) / (parent characters)`
- If coverage ≥ threshold, replaces all children with complete parent content

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Low (0.3-0.4) | More aggressive merging | Want complete sections when possible |
| Medium (0.5-0.6) | Balanced consolidation | Default recommendation |
| High (0.7-0.9) | Conservative merging | Prefer granular chunks |
| 1.0 | Only merge if 100% of parent retrieved | Rare, very conservative |

**Example:**
```
Parent section: 2000 characters
Retrieved chunks:
  - Chunk A: 500 chars
  - Chunk B: 300 chars
  - Chunk C: 400 chars
Total: 1200 chars

Coverage: 1200 / 2000 = 0.6 (60%)

threshold=0.5: 60% ≥ 50% → Replace with full parent (2000 chars)
threshold=0.7: 60% < 70% → Keep individual chunks
```

**When to Adjust:**
- **Lower (0.3-0.4):** You have many small fragments that should be unified
- **Higher (0.7-0.9):** You want to preserve granular chunk boundaries

---

### Merging Parameters

#### `line_gap`
**Default:** 7
**Range:** 0-50
**What It Does:** Maximum number of lines between chunks to consider them adjacent for merging.

**How It Works:**
- Chunks within this line gap are candidates for merging
- Helps combine closely-related content that wasn't grouped by parent
- Works on line numbers in the original document

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Small (0-3) | Only merge very adjacent chunks | Strict boundaries important |
| Medium (5-10) | Moderate merging | Default, bridges small gaps |
| Large (15-30) | Aggressive merging | Want larger consolidated blocks |
| Zero (0) | No adjacency merging | Disable this consolidation method |

**Example:**
```
Chunk A: lines 100-110
Chunk B: lines 115-125
Gap: 115 - 110 = 5 lines

line_gap=7: 5 ≤ 7 → Merge chunks A and B
line_gap=3: 5 > 3 → Keep chunks separate
```

---

### Quality Parameters

#### `min_content_length`
**Default:** 350
**Range:** 0-5000
**What It Does:** Minimum character count for a consolidated group to be included in final context.

**How It Works:**
- After consolidation, groups below this length are filtered out
- Prevents very short fragments from cluttering the final context
- Applied after merging operations

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Low (100-250) | Include shorter groups | All content valuable |
| Medium (300-500) | Filter small fragments | Default, balanced |
| High (600-1000) | Only substantial groups | Want only major sections |
| Zero (0) | No filtering | Include everything |

**Note:** This is separate from retrieval's `min_word_count`. This filters *consolidated* groups, not individual chunks.

---

#### `enrich_from_md`
**Default:** true
**What It Does:** Whether to read content from markdown files during consolidation (legacy parameter).

**Status:** Deprecated. VulcanLab now uses database-only consolidation via parent chunks.

**Current Behavior:** Always uses parent chunks from database regardless of this setting.

---

## Augmentation Parameters

Augmentation parameters control the final prompt generation stage.

### Context Selection

#### `top_n_contexts`
**Default:** 5
**Range:** 1-20
**What It Does:** Number of consolidated groups to include in the final augmented prompt.

**How It Works:**
- After consolidation, selects the top N groups by score
- Each group becomes a citation block (`[S1]`, `[S2]`, etc.) in the prompt
- More groups = more comprehensive context but longer prompts

**Impact of Changes:**

| Setting | Effect | Use When |
|---------|--------|----------|
| Low (1-3) | Concise, focused prompts | Simple queries, clear answers |
| Medium (4-7) | Balanced context | Default, general-purpose |
| High (8-15) | Comprehensive prompts | Complex queries needing multiple sources |
| Very High (15-20) | Maximum context | Research queries, need thorough coverage |

**Trade-offs:**
- **More contexts** = Better coverage, higher LLM costs, potentially more noise
- **Fewer contexts** = Faster, cheaper, but might miss important information

**Example:**
```
top_n_contexts=3:
  [S1] First consolidated group (highest score)
  [S2] Second consolidated group
  [S3] Third consolidated group

top_n_contexts=7:
  [S1] through [S7] → More comprehensive but longer prompt
```

---

## Preset Recommendations

Here are recommended preset configurations for different use cases:

### 1. Fast Retrieval (Speed Optimized)

**Use Case:** Quick lookups, simple queries, speed is priority

```json
{
  "retrieval": {
    "dense_limit": 10,
    "lexical_limit": 3,
    "rrf_k": 50,
    "top_k_rrf": 40,
    "top_n_final": 10,
    "entity_boost": 0.05,
    "min_word_count": 100,
    "max_word_count": 750,
    "mmr_lambda": 0.8,
    "reranker_batch_size": 16,
    "reranker_max_length": 256,
    "min_sentence_filter_enabled": true,
    "min_sentence_count": 5
  },
  "consolidation": {
    "coverage_threshold": 0.6,
    "line_gap": 5,
    "min_content_length": 250
  },
  "augmentation": {
    "top_n_contexts": 3
  }
}
```

**Key Adjustments:**
- Fewer candidates at each stage
- Smaller context windows
- Higher lambda (favor relevance over diversity)
- Fewer final contexts

---

### 2. High Precision (Quality Optimized)

**Use Case:** Academic research, detailed analysis, quality over speed

```json
{
  "retrieval": {
    "dense_limit": 25,
    "lexical_limit": 10,
    "rrf_k": 50,
    "top_k_rrf": 100,
    "top_n_final": 25,
    "entity_boost": 0.08,
    "min_word_count": 200,
    "max_word_count": 1500,
    "mmr_lambda": 0.6,
    "reranker_batch_size": 8,
    "reranker_max_length": 768,
    "min_sentence_filter_enabled": false,
    "min_sentence_count": 5
  },
  "consolidation": {
    "coverage_threshold": 0.4,
    "line_gap": 10,
    "min_content_length": 400
  },
  "augmentation": {
    "top_n_contexts": 8
  }
}
```

**Key Adjustments:**
- More candidates at each stage
- Larger context windows
- Lower lambda (more diversity)
- More final contexts
- Higher entity boost

---

### 3. Balanced Default

**Use Case:** General-purpose queries, balanced performance

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
    "reranker_batch_size": 8,
    "reranker_max_length": 512,
    "min_sentence_filter_enabled": false,
    "min_sentence_count": 5
  },
  "consolidation": {
    "coverage_threshold": 0.5,
    "line_gap": 7,
    "min_content_length": 350
  },
  "augmentation": {
    "top_n_contexts": 5
  }
}
```

This is the default configuration.

---

### 4. Keyword-Focused

**Use Case:** Technical documents, searching for specific terms/codes

```json
{
  "retrieval": {
    "dense_limit": 10,
    "lexical_limit": 20,
    "rrf_k": 40,
    "top_k_rrf": 75,
    "top_n_final": 15,
    "entity_boost": 0.10,
    "min_word_count": 150,
    "max_word_count": 1000,
    "mmr_lambda": 0.7,
    "reranker_batch_size": 8,
    "reranker_max_length": 512,
    "min_sentence_filter_enabled": false,
    "min_sentence_count": 5
  },
  "consolidation": {
    "coverage_threshold": 0.5,
    "line_gap": 7,
    "min_content_length": 350
  },
  "augmentation": {
    "top_n_contexts": 5
  }
}
```

**Key Adjustments:**
- Higher lexical limit (more keyword results)
- Lower dense limit (less semantic search)
- Higher entity boost (reward entity matches)
- Lower RRF k (favor top keyword matches)

---

## Tuning Guidelines

### Starting Point

1. **Begin with Default preset** - Test performance on representative queries
2. **Identify bottlenecks** - Is it speed, quality, or cost?
3. **Adjust incrementally** - Change one parameter at a time
4. **Test thoroughly** - Run same queries before/after changes
5. **Document results** - Keep notes on what works

### Common Issues and Solutions

#### "Retrieval is too slow"

**Solutions:**
1. Lower `dense_limit` and `lexical_limit` (fewer candidates)
2. Lower `top_k_rrf` (smaller shortlist)
3. Lower `top_n_final` (fewer reranking operations)
4. Increase `reranker_batch_size` (if using GPU)
5. Lower `reranker_max_length` (faster reranking)

#### "Results are not diverse enough"

**Solutions:**
1. Lower `mmr_lambda` (increase diversity weight)
2. Increase `top_n_final` (more candidates for MMR to choose from)
3. Lower `coverage_threshold` (merge less aggressively)

#### "Missing relevant results"

**Solutions:**
1. Increase `dense_limit` and `lexical_limit` (cast wider net)
2. Increase `top_k_rrf` (keep more candidates)
3. Disable `min_sentence_filter_enabled` (don't filter short chunks)
4. Increase `entity_boost` (reward entity matches more)

#### "Too much redundant information"

**Solutions:**
1. Increase `mmr_lambda` (still favors relevance but MMR will filter)
2. Increase `coverage_threshold` (merge fragments more aggressively)
3. Lower `top_n_contexts` (fewer final blocks)
4. Increase `min_content_length` (filter smaller groups)

#### "Context chunks are too short"

**Solutions:**
1. Increase `min_word_count` (trigger more enrichment)
2. Increase `max_word_count` (allow larger enriched chunks)
3. Lower `coverage_threshold` (merge more into parents)
4. Increase `line_gap` (merge adjacent chunks)

#### "Context chunks are too long"

**Solutions:**
1. Decrease `min_word_count` (less enrichment)
2. Decrease `max_word_count` (truncate sooner)
3. Increase `coverage_threshold` (keep fragments separate)
4. Decrease `line_gap` (merge less)

---

## API Usage

### Specifying Presets via API

**Retrieve with preset:**
```bash
POST /rag/queries/123/retrieve?config_preset=high-precision
```

**Consolidate with preset:**
```bash
POST /rag/queries/123/consolidate?config_preset=balanced
```

**Full pipeline with preset:**
```bash
POST /rag/auto
{
  "query": "What is cognitive behavioral therapy?",
  "config_preset": "fast-retrieval"
}
```

### Creating Presets Programmatically

```bash
POST /api/rag-config/
{
  "preset_name": "Custom Preset",
  "description": "Optimized for medical queries",
  "is_default": false,
  "config": {
    "retrieval": { ... },
    "consolidation": { ... },
    "augmentation": { ... }
  }
}
```

---

## Summary

RAG settings provide fine-grained control over VulcanLab's retrieval pipeline. The 22 parameters are organized into three stages:

**Retrieval (17 parameters):**
- Search limits control how many candidates are found
- Fusion parameters merge search results
- Enrichment parameters add context to chunks
- Reranking parameters optimize accuracy
- Scoring parameters adjust relevance calculations
- Diversity parameters prevent redundancy
- Final selection determines how many chunks proceed

**Consolidation (4 parameters):**
- Coverage threshold controls parent replacement
- Line gap controls adjacency merging
- Quality filters ensure substantive content

**Augmentation (1 parameter):**
- Context count controls final prompt size

Use presets to save configurations and switch between optimized settings for different use cases. Start with defaults and adjust incrementally based on your specific needs.

For general VulcanLab settings, see the [Settings Guide](settings-guide.md).
