# RAG Pipeline: Retrieval, Consolidation, and Augmentation

This document provides a detailed overview of the core RAG (Retrieval-Augmented Generation) pipeline in VulcanLab, covering the stages from initial search to final prompt generation.

## 1. Retrieval
The retrieval stage is responsible for identifying the most relevant candidates from the database for a given query. It uses a multi-layered pipeline to ensure high recall and precision.

### Process Flow:

#### Step 1: Broad Search (The Net)
*   **Dense Search**: Performs a vector similarity search using `pgvector` in the PostgreSQL database. It compares the query's embedding against the `embedding` column in the `chunks` table. This catches "semantic" relevance.
*   **Lexical Search**: Performs a full-text search using PostgreSQL's `tsvector` and `websearch_to_tsquery`. This is critical for catching exact keyword matches that vector search might miss.
*   **Sentence-Based Filtering**: During the database search, an optional filter can be applied to exclude very short chunks. If `min_sentence_filter_enabled` is active, the SQL query includes a `WHERE` clause requiring `sentence_count >= min_sentence_count`. This ensures that retrieval focuses on substantive content blocks rather than fragments or headers.

#### Step 2: Shortlisting (RRF Fusion)
*   Results from both searches are combined using **Reciprocal Rank Fusion (RRF)**.
*   **Purpose**: RRF is a mathematical fusion that merges the "Semantic" and "Keyword" lists into a single shortlist of top candidates (typically 60-75). It is extremely fast because it only processes ranks, not text.

#### Step 3: Preparation & Enrichment (Parent Traversal)
Between the initial search and the final reranking, the system performs critical data preparation:
*   **Quality Filtering**: Chunks that are too short (based on `min_word_count`) or appear to be boilerplate are identified for enrichment or exclusion.
*   **Parent Enrichment**: If a retrieved chunk is short, the system "walks up" the document hierarchy using the `parent_id` chain in the database. 
    *   **Context Merging**: It fetches parent chunks and prepends them until the total word count reaches `min_word_count`.
    *   **Sliding Window**: If the combined content exceeds `max_word_count`, a sliding window is applied to keep the most relevant context while preserving the parent's heading.
    *   **Benefit**: This ensures the Reranker and LLM have structural context (headings, preceding paragraphs) without requiring local markdown files.

#### Step 4: Deep Reranking (The Judge)
*   **BGE Reranking**: The shortlist is passed to a local **Cross-Encoder** model (`bge-reranker-large`). 
*   **Logic**: The Reranker looks at the `(Query + Enriched Chunk)` pair. It determines if the enriched text actually answers the user's specific question.
*   **Biasing**: Final scores are adjusted based on `Entity Boost` and `Intent Bias` (favoring specific heading levels).

#### Step 5: Diversity Selection (MMR)
*   To avoid repetitive information, **Maximal Marginal Relevance (MMR)** is applied. It iteratively selects chunks that are both relevant to the query and diverse compared to those already selected.

---

### FAQ: Why use both RRF and BGE Reranking?
It may seem redundant to rank twice, but it is a standard practice for high-performance RAG called "Two-Stage Retrieval":
1.  **RRF is for Recall**: It quickly finds anything that *might* be relevant from millions of rows. It is cheap and fast.
2.  **BGE is for Precision**: It is computationally expensive (slow) but highly accurate. We only run it on the "Shortlist" created by RRF to get the best of both worlds: the speed of a database search and the intelligence of a deep learning model.

---

## 2. Retrieval Settings Reference
The retrieval behavior can be fine-tuned via the following parameters in the RAG configuration.

### Search and Fusion
*   **`dense_limit`**: Maximum number of results to fetch from the vector similarity search (default: 19).
*   **`lexical_limit`**: Maximum number of results to fetch from the full-text keyword search (default: 5).
*   **`rrf_k`**: The constant used in the Reciprocal Rank Fusion formula (default: 50). It controls how much weight is given to lower-ranked items.
*   **`top_k_rrf`**: The number of top candidates to keep after merging dense and lexical results via RRF (default: 75).

### Filtering and Quality
*   **`min_sentence_filter_enabled`**: Boolean flag to enable/disable database-level filtering based on sentence count.
*   **`min_sentence_count`**: The minimum number of sentences a chunk must have to be included in the database search results.
*   **`min_word_count`**: Chunks with fewer than this many words trigger the enrichment process (default: 150).
*   **`max_word_count`**: The maximum allowed word count for an enriched chunk (default: 750). *Prevents context bloat*.
*   **`min_char_count`**: (**Deprecated**) Use `min_word_count`.

### Enrichment (Database-Driven)
*   **`min_content_length`**: (**Deprecated**) Use `min_word_count`.
*   **`enrich_lines_above`**: (**Deprecated**) Replaced by parent traversal.
*   **`enrich_lines_below`**: (**Deprecated**) Replaced by parent traversal.

### Reranking and Scoring
*   **`entity_boost`**: The score boost applied to a chunk for every query entity found in its content (default: 0.05).
*   **`reranker_batch_size`**: The number of query-chunk pairs processed by the BGE reranker at once (default: 8).
*   **`reranker_max_length`**: The maximum token length allowed for the reranker's input (default: 512).

### Final Selection
*   **`top_n_final`**: The final number of chunks to send to the consolidation and augmentation stages (default: 17).
*   **`mmr_lambda`**: The diversity vs. relevance balance for MMR selection (default: 0.7). A higher value (closer to 1.0) prioritizes relevance; a lower value prioritizes diversity.

---

## 3. Consolidation
Consolidation is a structural optimization step. It transforms the list of retrieved chunks into a cleaner set of "Context Groups" by analyzing the document hierarchy.

### Process Flow:
1.  **Hierarchical Grouping**:
    *   The system groups retrieved chunks by their parent document (`work_id`) and their highest common ancestor chunk (`parent_id`).
2.  **Merging & Enrichment Logic**:
    *   **Parent Chunk Extraction**: For each group, the system fetches the full content of the parent chunk(s) from the database.
    *   **Coverage Calculation**: It calculates how much of the parent's content is represented by the retrieved fragments: `(Sum of Fragment Chars) / (Total Parent Chars)`.
    *   **Parent-Level Replacement**: If coverage exceeds the `coverage_threshold` (default: 0.5), the fragments are replaced by the **entire parent content**.
    *   **Range Reconstruction**: If replacement is not triggered, fragments are merged based on their relative positions in the parent text.
3.  **Hierarchy Preservation**:
    *   Every group retains its "Heading Chain" (breadcrumb path). This ensures the LLM knows the chapter and sub-section context for every piece of information.

---

## 4. Consolidation Settings Reference
The consolidation engine uses the following parameters to decide how to group and merge chunks.

### Structural Bridging
*   **`coverage_threshold`**: The percentage of a parent section's characters that must be present in fragments to trigger a "Parent Replacement" (default: 0.5 or 50%).
*   **`line_gap`**: (**Legacy**) Previously used for adjacency merging. Parent-based consolidation is now the preferred method.
*   **`enrich_from_md`**: (**Deprecated**) The system now always uses parent chunks from the database.

### Final Output Quality
*   **`min_group_word_count`**: The minimum word count for a consolidated group to be included in the final context (default: 100).
*   **`min_content_length`**: (**Deprecated**) Use word-count filters.

---

## 5. Simple Conversion Support
The parent-chunk-enrichment system enables full RAG functionality for documents processed via "Simple Conversion":
*   **No File Dependency**: Retrieval enrichment and consolidation no longer require local sanitized markdown files.
*   **Database-Only**: All necessary context is retrieved directly from the `chunks` table using the `parent_id` hierarchy.
*   **Reconstruction**: Structural context (headings and larger sections) is reconstructed using parent chunks stored during the initial ingestion.

## 6. Examples

### Example: Parent Traversal
A small retrieved chunk $A$ (50 words) has a parent $B$ (200 words) and grandparent $C$ (400 words).
*   With `min_word_count=150`:
    *   System walks to Parent $B$ (250 words total).
    *   $250 > 150$, so traversal stops.
    *   **Result**: Context = Content of $B$ (which includes $A$).

### Example: Sliding Window Truncation
If Parent $C$ (1000 words) is added and `max_word_count=750`:
*   The system takes the immediate parent's heading.
*   It then takes the trailing sentences of $C$ and $B$ that fit within 750 words.
*   **Result**: A concise context block that preserves the most recent history and the current heading.

### Example: Coverage Calculation
Parent section $P$ has 2000 characters. Three fragments $\{f1, f2, f3\}$ are retrieved with lengths 500, 300, and 400.
*   **Coverage**: $(500+300+400) / 2000 = 0.6$ (60%).
*   If `coverage_threshold = 0.5`: The system replaces all three fragments with the full 2000-character content of $P$.

---

## 7. Augmentation
Augmentation is the final stage where information is synthesized into a master prompt for the LLM.

### Process Flow:
1.  **Context Formatting**:
    *   The consolidated groups are formatted into distinct, cited blocks (e.g., `[S1]`, `[S2]`). 
    *   Each block includes a header showing the source title and the heading breadcrumb path.
2.  **Prompt Engineering**:
    *   The system loads a **RAG Template** with strict rules:
        *   **Hybrid Evidence Policy**: Prioritize provided sources, allow academic knowledge if marked.
        *   **Citation Rules**: Mandatory use of `[S#]` tags for every claim.
        *   **Intent-Based Guidance**: Tailor answer style (e.g., tables for comparisons).
3.  **Final Synthesis**:
    *   The user question, formatted context, and metadata are injected into the template and sent to the AI provider.

---

## Technical Note: Database-Only Enrichment
VulcanLab has transitioned to a **database-only enrichment model**. The system uses the `parent_id` hierarchy to "read" expanded text and structural gaps without requiring local markdown files on the server. This makes the pipeline more robust, easier to deploy, and fully compatible with all document conversion types.
