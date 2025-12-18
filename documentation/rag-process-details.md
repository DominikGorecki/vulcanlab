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

#### Step 3: The Bridge (Preparation & Enrichment)
Between the initial search and the final reranking, the system performs critical data preparation:
*   **Quality Filtering**: Chunks that are too short (based on word or character count) or appear to be boilerplate (e.g., page headers or single-word lines) are dropped to save computation time in later stages. This is a secondary filter to the database-level sentence filter.
*   **Content Enrichment**: If a retrieved chunk is short, the system reads the **local sanitized markdown file** to grab extra lines above and below the chunk. This is vital because the Reranker and the LLM need surrounding context to understand the chunk's true meaning.

#### Step 4: Deep Reranking (The Judge)
*   **BGE Reranking**: The shortlist is passed to a local **Cross-Encoder** model (`bge-reranker-large`). 
*   **Logic**: Unlike the initial searches which look at vectors or keywords in isolation, the Reranker looks at the `(Query + Enriched Chunk)` pair as a whole. It "reads" the text to determine if it actually answers the user's specific question.
*   **Biasing**: Final scores are adjusted based on `Entity Boost` (matches for key names/theories) and `Intent Bias` (favoring specific heading levels based on query type).

#### Step 5: Diversity Selection (MMR)
*   To avoid providing the LLM with repetitive information, **Maximal Marginal Relevance (MMR)** is applied. This iteratively selects chunks that are both relevant to the query and diverse compared to chunks already selected for the final set.

---

### FAQ: Why use both RRF and BGE Reranking?
It may seem redundant to rank twice, but it is a standard practice for high-performance RAG called "Two-Stage Retrieval":
1.  **RRF is for Recall**: It quickly finds anything that *might* be relevant from millions of rows. It is cheap and fast.
2.  **BGE is for Precision**: It is computationally expensive (slow) but highly accurate. We only run it on the "Shortlist" created by RRF to get the best of both worlds: the speed of a database search and the intelligence of a deep learning model.

---

## 2. Consolidation
Consolidation is a structural optimization step. It transforms the list of individual retrieved chunks into a cleaner, more readable set of "Context Groups" by analyzing the document hierarchy.

### Process Flow:
1.  **Hierarchical Analysis**:
    *   The system groups retrieved chunks by their parent document (`work_id`) and their parent heading (`parent_id`).
2.  **Merging Logic**:
    *   **Adjacency Merging**: If two retrieved chunks are very close in the original document (separated by only a few lines), the system reads the **local markdown file** to bridge the gap and merges them into a single block.
    *   **Parent-Level Replacement**: If a significant percentage of a section's content (the "Coverage Threshold") has been retrieved as separate pieces, the system replaces all those fragments with the **entire section** read directly from the local file.
3.  **Hierarchy Preservation**:
    *   Every consolidated group retains its "Heading Chain" (breadcrumbs). This ensures that even if a paragraph is retrieved from the middle of a book, the LLM knows exactly which chapter and sub-section it belongs to.

---

## 3. Augmentation
Augmentation is the final stage where the retrieved and consolidated information is synthesized into a master prompt for the LLM.

### Process Flow:
1.  **Context Formatting**:
    *   The consolidated groups are formatted into distinct, cited blocks (e.g., `[S1]`, `[S2]`). 
    *   Each block includes a header showing the source title and the heading breadcrumb path.
2.  **Prompt Engineering**:
    *   The system loads a **RAG Template** that defines strict rules for the LLM. These include:
        *   **Hybrid Evidence Policy**: Instructions to prioritize the provided sources but allow general academic knowledge if clearly marked.
        *   **Citation Rules**: Requirement to use `[S#]` tags for every claim supported by the text.
        *   **Intent-Based Guidance**: Directions to tailor the answer style based on the query's intent (e.g., "COMPARISON" prompts the LLM to use tables or bulleted differences).
3.  **Final Synthesis**:
    *   The original user question, the formatted context blocks, and the metadata (entities/intent) are injected into the template. This final string is what is sent to the AI provider (OpenAI or Gemini).

---

## Technical Note: Local File Dependency
A critical characteristic of the current VulcanLab architecture is its dependency on **local sanitized markdown files** during the Retrieval (Enrichment) and Consolidation stages. 

*   The system uses the database to **find** where information is (line numbers).
*   It uses local files to **read** the expanded text and structural gaps.
*   **Limitation**: For "Simple Conversion" documents where sanitized content exists only in the database, these specific structural optimizations are currently bypassed.
