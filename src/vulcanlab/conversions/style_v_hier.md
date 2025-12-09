### `style_v_hier.py` & `style_v_hier__cli.py` — Best Markdown Hierarchy Selector

This module + CLI compares two markdown conversions of the same source:

* `<file>.style.md` – style-driven conversion
* `<file>.hier.md`  – hierarchy-driven conversion

and then:

* Chooses the **better structured** markdown file based on the heuristic below
* Copies the **winner** to: `<file>.md`
* Leaves both `.style.md` and `.hier.md` files untouched for reference

---

## Goal

Pick the candidate that:

1. Preserves a **clean, logical heading hierarchy** (H1–H4+)
2. Distributes major sections (H1/H2) **evenly across the document**
3. Produces **chunk-friendly sections** (not absurdly huge or tiny)
4. Avoids obvious structural pathologies (heading level jumps, repeated junk headings, etc.)

---

## Heuristic Overview

For each candidate markdown file:

1. **Extract headings & structure**
2. **Compute structural metrics**
3. **Compute chunkability metrics**
4. **Apply penalties**
5. **Compute a final score and pick the higher one**

   * If scores are effectively tied, use deterministic tie-breakers.

---

## 1. Extract headings & structure

For each file:

* Walk the document and collect **all headings**:

  * Heading level: H1–H6
  * Heading text (normalized, trimmed)
  * Starting **line number** of the heading
* For each heading, determine:

  * The line range from this heading down to:

    * The next heading at the same or higher level, or
    * End of file

This lets you compute:

* Section boundaries
* Section sizes (lines / estimated words)
* Nesting structure (H1 → H2 → H3, etc.)

---

## 2. Structural metrics

### 2.1 Heading coverage & evenness (major sections)

* Look at **H1 and H2 headings**:

  * Count how many there are.
  * Compute the **distance in lines** between consecutive H1/H2.
  * Compute a dispersion measure (e.g., variance / standard deviation) of these distances.
* Intuition:

  * A document where top-level sections are **clustered at the start** and then nothing but raw text is bad.
  * A doc where H1/H2 are **reasonably spread across the full length** is better.

**Score idea** (conceptually):

* More H1/H2 = better, up to a reasonable limit.
* More even spacing (lower variance of distances) = better.

### 2.2 Hierarchical depth & correctness

Evaluate:

* **Max depth** of headings (e.g., presence of H3/H4).
* **Average depth** actually used (not just H1 everywhere).
* **Level transitions** between consecutive headings:

  * Penalize big jumps, e.g., H1 → H4, H2 → H5.
  * Prefer smooth transitions, e.g., H1 → H2 → H3 or H2 → H2 → H3.

Intuition:

* A good document uses:

  * H1 for the whole work or major parts (chapters),
  * H2/H3 for sections / subsections,
  * H4+ sparingly.
* A bad document:

  * Uses only H1 everywhere, or
  * Randomly jumps levels (H1 then H4 then H2…).

---

## 3. Chunkability metrics

We care that sections are **good candidates for RAG chunks** (or at least chunk boundaries).

For each section (the text under a heading until the next “sibling or ancestor” heading):

* Estimate its size (e.g., lines or approximate words).
* Count how many sections fall into:

  * **Target range**: “reasonable” chunk size (e.g., ~150–400 words).
  * **Too small**: trivial sections (e.g., < 30–50 words).
  * **Too large**: huge unbroken sections (e.g., > 800–1000 words).

Heuristic:

* Reward documents where:

  * A large share of sections are within a **chunk-friendly range**.
  * There are **fewer very large** monolithic sections.
* Slightly penalize documents with:

  * Many tiny, contentless sections (heading followed by 1–2 lines and another heading).

This pushes you toward a structure that’s easy to slice into RAG chunks while preserving semantics.

---

## 4. Structural cleanliness penalties

Apply penalties for obvious “bad smells”:

* **Repeated junk headings**

  * e.g., same heading text repeated many times in a row (“Contents”, “Figure”, “Table”, etc.) with almost no content.
* **Heading-only runs**

  * Long stretches of headings with almost no body text between them.
* **Missing top-level structure**

  * Entire document basically at one level (all H3, or all H1, no nesting).
* **Extreme section length imbalance**

  * One or two sections contain the majority of the text, rest are tiny.

You don’t need perfect detection—just enough to down-rank obviously broken structure.

---

## 5. Scoring & tie-breaking

For each candidate:

1. Combine:

   * **Heading coverage/evenness score**
   * **Hierarchy depth/correctness score**
   * **Chunkability score**
   * Minus **penalties**
2. Produce a **final score**.

General weighting guideline:

* Structural hierarchy & correctness: **high weight**
* Chunkability: **high weight**
* Coverage/evenness: **medium weight**
* Cleanliness penalties: used to break ties / punish obviously bad layouts.

### Tie-breaking rules

If final scores are within a small epsilon:

1. Prefer the candidate with:

   * Better **chunkability** (more sections in target size band).
2. If still tied, prefer the one with:

   * Cleaner **hierarchical transitions** (fewer big level jumps).
3. If still tied, prefer:

   * A consistent H1/H2 structure (stronger top-level scaffolding).
4. If still tied, fall back to a deterministic rule:

   * e.g., prefer `<file>.hier.md` over `<file>.style.md` (or vice versa, but be consistent).

---

## 6. File copying behavior

Once the "better" candidate is chosen:

* **Winner**

  * Copied to: `<file>.md`
* **Original files**

  * Both `<file>.style.md` and `<file>.hier.md` remain untouched
  * Can be manually deleted later if desired

**Important**: If `<file>.md` already exists, the tool will raise an error and refuse to overwrite it. The user must manually remove the existing file first.

---

This heuristic gives you:

* A **structure-aware** choice (not just “more headings wins”).
* A strong bias toward **good sectioning and chunk sizes**, which is what you actually care about for RAG and later processing.
