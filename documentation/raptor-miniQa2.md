**Group retrieved chunks → summarize per group wrt query → score → keep top summaries → answer over those.**

Think “mini RAPTOR / mini PaperQA2 RCS” rather than a huge offline pre-processing pipeline.

I’ll break it down into what you’d have to build.

---

## 1. Where this sits in your pipeline

You already have:

1. **Query → retrieval** (BM25 + dense + RRF)
2. **Top-k chunks → LLM answer**

You want:

1. Query → **retrieval** → ~50–100 chunks
2. Chunks → **grouping + summarization + scoring (RAPTOR/PaperQA2-style pass)**
3. Top 5–10 **summaries** (with citations/links to underlying chunks) → LLM answer

So you’re only replacing the “stuff 20 raw chunks into the prompt” step with “stuff 8–12 *summaries* into the prompt”.

---

## 2. Minimal new data model

You need slightly richer metadata on your retrieved chunks and a new “group” abstraction.

**Chunk model** (you probably already have 80% of this):

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    section_id: Optional[str]  # heading / page / section anchor
    text: str
    rank: int                   # overall rank after RRF
    score: float                # RRF score or fused score
    source: str                 # e.g. "bm25", "dense", "hybrid"
    metadata: dict              # year, journal, etc.
```

**Grouped evidence node** (this is your “mini RAPTOR node”):

```python
@dataclass
class EvidenceGroup:
    group_id: str
    doc_id: str
    section_id: Optional[str]
    chunk_ids: List[str]
    combined_text: str          # concatenated chunks
    retrieval_score: float      # e.g. max or sum of chunk scores
    summary: Optional[str] = None
    relevance_score: Optional[float] = None  # 0–1 from LLM
```

You don’t need an offline tree; you just build these groups per query.

---

## 3. The lightweight algorithm (step-by-step)

### Step 1 — Retrieve a *wide* candidate set

* Use your existing hybrid retrieval:

  * e.g. BM25 k=40, dense k=40, fuse to ~60–80 unique chunks.
* These are your raw `Chunk` objects.

### Step 2 — Group chunks (RAPTOR-ish but cheap)

Heuristic grouping that’s “good enough”:

* Primary key: `(doc_id, section_id)` → so chunks from the same section/page end up together.
* Maintain order by `rank`.
* Cap group size (e.g. 3–8 chunks per group) to control token cost.

Pseudo:

```python
def group_chunks(chunks: List[Chunk],
                 max_chunks_per_group: int = 6) -> List[EvidenceGroup]:
    # sort by doc, section, then rank
    chunks = sorted(chunks, key=lambda c: (c.doc_id, c.section_id or "", c.rank))

    groups = []
    current: List[Chunk] = []
    current_doc = None
    current_section = None

    def flush_group():
        if not current:
            return
        combined_text = "\n\n".join(c.text for c in current)
        retrieval_score = max(c.score for c in current)
        groups.append(EvidenceGroup(
            group_id=f"{current[0].doc_id}:{current[0].section_id or 'root'}:{len(groups)}",
            doc_id=current[0].doc_id,
            section_id=current[0].section_id,
            chunk_ids=[c.chunk_id for c in current],
            combined_text=combined_text,
            retrieval_score=retrieval_score
        ))

    for c in chunks:
        key = (c.doc_id, c.section_id)
        if (c.doc_id != current_doc or c.section_id != current_section 
            or len(current) >= max_chunks_per_group):
            flush_group()
            current = []
            current_doc, current_section = key
        current.append(c)
    flush_group()
    return groups
```

This gives you, say, 10–20 `EvidenceGroup`s instead of 60 raw chunks.

### Step 3 — Summarize + score each group (PaperQA2-ish)

For each group, you call the LLM with a **targeted prompt**:

* Input: user query + combined_text (group).
* Output:

  * A short summary of the evidence in that group **relevant to the query**.
  * A numerical relevance score (0–1 or 0–100).
  * Optional: a few key claims with pseudo-citations (chunk indices).

Example prompt (keep it strict so you can parse):

```text
You are helping with scientific question answering using retrieval-augmented generation.

USER QUESTION:
{query}

EVIDENCE GROUP (from one document section):
{combined_text}

TASK:
1. Briefly summarize ONLY the information in this evidence group that is relevant to answering the user question.
2. Rate how relevant this group is on a scale from 0.0 (not helpful) to 1.0 (directly answers the question).
3. List any key claims as bullet points.

Return JSON ONLY in this exact format:

{
  "summary": "<2-4 sentence summary focusing only on content relevant to the question>",
  "relevance": <float between 0.0 and 1.0>,
  "claims": [
    "<short claim 1>",
    "<short claim 2>"
  ]
}
```

Then in code:

```python
import json

def summarize_group(llm, query: str, group: EvidenceGroup) -> EvidenceGroup:
    prompt = build_prompt(query=query, combined_text=group.combined_text)
    raw = llm(prompt)  # whatever client you use
    data = json.loads(raw)
    group.summary = data["summary"]
    group.relevance_score = float(data["relevance"])
    return group
```

This is your **RCS-lite** (Retrieval-Contextual Summarizer) pass.

### Step 4 — Rerank and select top evidence summaries

Now combine retrieval_score (RRF etc.) and relevance_score from the summarizer.

For instance:

```python
def rerank_groups(groups: List[EvidenceGroup],
                  alpha: float = 0.5) -> List[EvidenceGroup]:
    # alpha balances lexical/dense retrieval vs LLM relevance judgment
    for g in groups:
        base = g.retrieval_score
        rel = g.relevance_score if g.relevance_score is not None else 0.0
        g.combined_score = alpha * base + (1 - alpha) * rel
    return sorted(groups, key=lambda g: g.combined_score, reverse=True)
```

Then pick the top N:

* **N ~ 5–10** groups (depending on context window and group summary length).

### Step 5 — Answer using summaries (not raw chunks)

Final answer prompt roughly becomes:

```text
You are answering a scientific question using summarized evidence from papers and textbooks.

USER QUESTION:
{query}

You are given {N} evidence summaries. Each summary may represent multiple chunks from a document section.

EVIDENCE SUMMARIES:
1. [Doc {doc_id}, Section {section_id}]
   {summary_1}

2. [Doc {doc_id}, Section {section_id}]
   {summary_2}

...

INSTRUCTIONS:
- Use ONLY the information from these summaries plus general domain knowledge.
- Explicitly mention when something is uncertain or not directly supported by the evidence.
- Where appropriate, refer to the evidence by number (e.g., "Evidence 3 suggests that...").

Now provide a clear, structured answer to the USER QUESTION.
```

If you want citation-style behavior, you can propagate `chunk_ids` into the summaries and map them back to full bib entries.

---

## 4. Complexity & cost (what you actually pay)

Roughly, per query:

* Retrieval: unchanged (BM25 + dense + RRF).
* **Grouping:** cheap (in-memory Python).
* **Summarization calls:** one LLM call per `EvidenceGroup`.

  * If 60 chunks → 10–15 groups → 10–15 summarization calls.
* **Final answer call:** 1 LLM call.

So compared to your current pipeline:

* **+10–15 short LLM calls**
* But **− tons of raw text in the final prompt**, because you’re sending 5–10 short summaries instead of 20+ long chunks.

If you use the *same* model for summarization and answering, latency goes up but complexity stays simple. If you use a smaller model for summarization, you can keep latency and cost reasonable.

---

## 5. MVP vs “heavier” versions

**MVP (what I just described):**

* No offline clustering.
* No global tree.
* No citation graph crawling.
* Just per-query grouping → summarization → reranking.

You can build this in a day or two on top of your existing RAG.

**Heavier/next steps (if this works):**

* Persist group summaries as a second index (true RAPTOR: tree of summaries).
* Add **multi-level retrieval**: query summaries first, then drill into raw chunks.
* Add **citation traversal** (PaperQA2-style): use citations in top docs to pull in extra candidate documents and run the same grouping/summarization there.
* Train a small **learned relevance model** on your `relevance_score` labels instead of relying purely on the LLM each time.

---

## 6. Sanity reality check

What this pass *gives* you:

* Less “lost in the middle”.
* More compositional answers when evidence is spread across sections.
* A clean hook for:

  * future evaluation (relevance scores),
  * logging (what evidence actually mattered),
  * and agentic behaviors (e.g., “if no group has relevance > 0.5, ask follow-up or expand search”).

What it does *not* magically solve:

* Bad retrieval (garbage in → polished garbage out).
* Deep methodological evaluation of papers (you still need separate logic to reason about study quality, confounds, etc.).

If you want, next step I can help you turn this into a small **LangGraph / Pydantic-AI graph**: nodes for `retrieve → group → summarize → rerank → answer`, with clear state objects for chunks and evidence groups.
