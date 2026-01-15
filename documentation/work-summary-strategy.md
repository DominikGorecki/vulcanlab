## 1) Local NLP’s job: build “evidence packets” per node (cheap, deterministic, line-addressable)

Instead of “send the whole section” vs “send first/last N sentences,” you locally assemble a **high-information-density packet** for each heading node.

### What to extract locally (practical + robust)

For each section (H1/H2/H3 node), compute and store:

**A) Structure & boundaries**

* `heading_path` (H1 > H2 > H3)
* `line_start`, `line_end`
* token/char counts

**B) Sentence + paragraph segmentation with line mapping**

* Sentence boundaries and *their line ranges*
* Paragraph boundaries and *their line ranges*

(You don’t need fancy models for this; you mainly need *stable segmentation + mapping*.)

**C) High-signal content selectors**
Pick candidates that usually contain “the payload”:

* **Topic sentences**: first sentence of each paragraph (often better than first paragraph only)
* **Definition-like sentences** (regex + heuristics):

  * “X is…”, “X refers to…”, “defined as…”, “we call…”
* **Enumerations**:

  * bullet lists, numbered lists, “(1)…(2)…”
* **Emphasis cues**:

  * “key”, “important”, “in summary”, “note that”, “crucially”
* **Figures/tables callouts** (even if you can’t parse the figure, the surrounding text matters)

**D) Keyphrase / entity hints (optional but very useful)**
Use lightweight extraction to produce:

* keyphrases (YAKE / RAKE / TF-IDF)
* named entities / noun chunks (spaCy)
* “term candidates” (Title Case, bolded terms in markdown, glossary-like patterns)

These aren’t the summary; they’re **handles** for the LLM to stay grounded.

### Output: the Evidence Packet (per node)

Think of it as:

* **Header:** path + line range + short stats
* **Selected snippets:** ~10–40 short snippets max, each with line range
* **Always include all local lists/bullets** (these are often the best ROI)
* **Keyphrase/entity list** + “definitions detected” list

This packet makes your input cost scale with *information density*, not raw length.

---

## 2) Provenance-first: make the LLM produce “claims with anchors,” not just prose

If you want verification by line numbers, make it structural: every meaningful output element carries a line anchor.

### Canonical persisted fields for each node

For each section node, store a structured record like:

* **gist** (1–2 sentences)
* **key_points** (bullets)
* **definitions** (term → definition)
* **key_terms** (list)
* **examples / evidence** (bullets)
* **open_questions / ambiguities**
* **relations** (optional: “connects to X”, “contrasts with Y”)

And critically, for each bullet/definition/example:

* `support`: one or more `{line_start, line_end}` spans
* optionally a **tiny quote fragment** (like 10–20 words) to help re-anchor later if lines shift

This turns your summaries into *auditable objects*.

---

## 3) Adjusting LangGraph: shift to a “Work Digest” as the core artifact

Right now you’re thinking “summarize the work.” Instead, your system should build a **Work Digest** that everything else compiles from.

### New top-level goal

**Produce a Work Digest = (Outline Tree) + (Per-node structured summaries w/ anchors) + (Work-level rollups).**

Once you have that, generating:

* outline,
* abstract,
* executive summary,
* key concepts,
* chapter summaries,
  becomes **cheap compilation** over existing digests, not re-reading the book.

---

## 4) The revised LangGraph flow (high level)

### Stage A — Build/normalize the outline tree (mostly local)

1. Parse markdown headings → tree nodes with line ranges.
2. If headings are weak/missing, do *local* topic segmentation to create pseudo-headings (optional).

Persist: node boundaries, hashes, and a stable node_id.

### Stage B — Evidence packet builder (local)

For each node:

* build evidence packet (selectors above)
* compute salience score (see next section)

### Stage C — Leaf summarization subgraph (LLM, but constrained)

For each node, call the LLM with the evidence packet (not full text by default) and ask for:

* structured fields + line anchors
* “insufficient evidence” flags (so the system can escalate)

### Stage D — Escalation loop (only when needed)

If the LLM says “not enough to summarize X well” (or your validator detects vagueness):

* pull *more* context locally:

  * add the top-K additional sentences around missing concepts
  * or include the “middle paragraphs” with highest keyphrase density
    Then re-run summarization for that node.

This is how you avoid paying full-text by default while still having a path to quality.

### Stage E — Bottom-up reduce

Compose parent summaries from children summaries (not raw text):

* chapter summaries from section digests
* work summary from chapter digests

This is where cost collapses: you’re combining compact objects.

### Stage F — Compilation subgraph (cheap, flexible)

Now generating different outputs is just:

* **Outline:** take the tree + each node’s gist/key points.
* **Key concepts:** aggregate `definitions + key_terms` across nodes, dedupe, cluster, then optionally one LLM pass to clean/organize.
* **Abstract / exec summary:** one LLM pass over *work-level digest*, not the book.

---

## 5) Local salience scoring: how to choose depth without guessing

For huge works, you need a deterministic way to decide “which nodes get deep summaries.”

A simple, effective salience score can blend:

* heading depth (H1/H2 gets a boost)
* token length (very short sections may not need deep work)
* **definition density** (count of detected definitional sentences)
* **list density** (bullets/numbered lines)
* **keyphrase novelty** (new terms not seen earlier)
* location priors (intro/conclusion chapters are usually high leverage)

Then apply budget rules:

* Always deep-summarize all H1 nodes.
* Deep-summarize top N% of H2 nodes by score.
* H3 nodes: only if score high *or* parent marked “core.”

This gives you predictable spend and coverage.

---

## 6) Line numbers: one warning + one fix

### The warning

Line numbers are brittle if markdown changes. If you edit the work, anchors drift.

### The fix (simple and strong)

Store **both**:

* line ranges (for fast navigation *now*)
* a short **anchor snippet hash** (or tiny quote fragment) for re-alignment later

If the file changes, you can re-locate the snippet and update line mappings without re-summarizing everything.

---

## 7) What this gets you (the “generality” you want)

Once every node has:

* gist,
* key points,
* definitions,
* key terms,
* examples,
  all with anchors…

Then:

* **Outline** = headings + per-node gist/key points (no new read).
* **Chapter summaries** = reduce children (no raw text).
* **Key concepts** = merge definitions + key terms + one cleanup pass.
* **Abstract / exec summary** = one pass over work-level reduced digests.
* **Section summaries** are already there.

Most works will require:

* one LLM pass per “selected” node (not every node),
* plus 1–3 compilation calls for the final artifacts.

