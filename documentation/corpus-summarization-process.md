# Corpus Summarization Process

This document describes the multi-step process for summarizing a corpus (a single work/document) within Vulcanlab.

## Overview

The summarization process is divided into two main phases: **Node-Level Summarization** and **Work-Level Synthesis**. Individual sections of a document are first selected and summarized, and then these summaries are compiled into high-level outputs like abstracts, outlines, and key concept lists.

---

## Phase 1: Node-Level Summarization

This phase focuses on identifying and summarizing the most important parts of the document.

### 1. Node Selection
The system selects specific heading-level chunks (H1–H5) for summarization. Selection is based on **salience scores**, which are computed using several criteria:
*   **Location Prior**: Favoring sections earlier in the document.
*   **Heading Depth**: Weighting levels differently (e.g., H1s are often always summarized).
*   **Keyphrase Density**: Presence of important technical terms.
*   **H2 Top-Percent Filtering**: A configurable percentage of the highest-scoring H2 sections are prioritized.

**LLM Used**: No (Algorithmic).

### 2. Evidence Extraction
For each selected node, the system segments the content into individual sentences and maps them to their original line numbers in the sanitized markdown. This "evidence packet" ensures that all subsequent LLM outputs can be anchored back to specific lines in the source text.

**LLM Used**: No (Algorithmic).

### 3. Individual Node Summarization
The LLM generates a structured summary for the node. This summary includes:
*   **Gist**: A 1–2 sentence high-level summary.
*   **Key Points**: Specific findings or arguments with line references.
*   **Definitions**: Technical terms and their definitions with line references.
*   **Key Terms**: A list of important technical terms.

**LLM Used**: Yes.
**Prompt Template**: `summarize_node`

---

## Phase 2: Work-Level Synthesis (Derived Outputs)

Once all selected nodes have been summarized, the system aggregates the results to produce work-level summaries.

### 4. Abstract Synthesis
The system takes the "gists" from all individual node summaries and synthesizes them into a cohesive, high-level abstract for the entire work.

**LLM Used**: Yes.
**Prompt Template**: `synthesize_abstract`

### 5. Hierarchical Outline Construction
A structured, nested outline is built using the heading hierarchy of the summarized nodes, incorporating their gists to provide a comprehensive table of contents with summaries.

**LLM Used**: No (Algorithmic).

### 6. Key Concepts Refinement
The system aggregates all definitions and key terms extracted during the node summarization phase. An LLM is then used to deduplicate, consolidate, and refine these into a clean, structured list of key concepts for the entire document.

**LLM Used**: Yes.
**Prompt Template**: `organize_key_concepts`

### 7. Chapter Summary Extraction
For major sections (typically H1 and H2), the system extracts and groups the gists to provide "chapter-level" summaries, helping users quickly grasp the content of large sections.

**LLM Used**: No (Algorithmic).
