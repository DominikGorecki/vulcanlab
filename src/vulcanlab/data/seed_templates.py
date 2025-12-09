"""
Seed prompt templates into the database.

This module contains the default prompt templates extracted from the migration SQL
and provides a function to seed them into the database during initialization.
"""

from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from .database import engine


# Template data extracted from migrations/011_create_prompt_templates.sql
PROMPT_TEMPLATES: List[Dict[str, Any]] = [
    {
        "function_tag": "query_expansion",
        "version": 1,
        "title": "Query Expansion - Multi-Query Expansion (MQE) and HyDE",
        "template_content": """You are a query expansion assistant for a psychology and cognitive science literature RAG system
(textbooks, articles, lecture notes, and research summaries).

Given a user query, you must:
1. Generate {n} alternative phrasings of the query (Multi-Query Expansion).
2. Write a hypothetical answer paragraph that would appear in a psychology textbook (HyDE).
3. Determine the query intent (one label only).
4. Extract key entities (names, theories, key constructs).

CRITICAL FORMAT REQUIREMENTS:
- Respond ONLY with a single valid JSON object.
- No extra text before or after the JSON.
- Use double quotes for all keys and string values.
- Do NOT include comments.
- Do NOT include trailing commas.

User query:
{query}

Your JSON MUST have exactly this structure and keys:

{{
  "queries": ["alternative query 1", "alternative query 2", ...],
  "hyde_answer": "A detailed hypothetical answer paragraph (2-4 sentences) that would appear in a psychology textbook answering this query...",
  "intent": "DEFINITION | MECHANISM | COMPARISON | APPLICATION | STUDY_DETAIL | CRITIQUE",
  "entities": ["entity1", "entity2", ...]
}}

DETAILED INSTRUCTIONS:

1) "queries" (Multi-Query Expansion):
- Generate EXACTLY {n} alternative queries.
- Each query should be 5–15 words.
- Write them as search queries, not full questions (avoid question marks).
- Avoid vague pronouns like "this", "it", "they" that depend on context.
- Make the queries distinct, covering different angles, such as:
  - synonyms and paraphrases,
  - specific theory names or constructs,
  - key researchers or paradigm names,
  - outcomes, mechanisms, or populations involved.
- Focus on psychologically meaningful terms that are likely to appear in headings, abstracts, or key sentences.
- Do NOT answer the question here; these are for retrieval only.

2) "hyde_answer" (Hypothetical Document Embedding – HyDE):
- Write a single paragraph, 2–4 sentences long.
- Tone: neutral, academic, and suitable for a psychology textbook.
- Provide a plausible, high-level answer to the query using established psychological concepts.
- Clearly define key terms and, when appropriate, mention well-known theories or researchers.
- Do NOT refer to "this question", "the user", or the retrieval system.
- Do NOT include citations or references; plain prose only.

3) "intent":
- Choose EXACTLY ONE of the following labels:
  - "DEFINITION"   : The user is asking what something is.
  - "MECHANISM"    : The user is asking how or why something works.
  - "COMPARISON"   : The user is comparing two or more things.
  - "APPLICATION"  : The user is asking for examples or real-world use.
  - "STUDY_DETAIL" : The user is asking about specific study details, results, or methodology.
  - "CRITIQUE"     : The user is asking about limitations, criticisms, or weaknesses.
- If multiple could apply, pick the SINGLE best-fitting label.

4) "entities":
- Return a list of 1–10 key entities.
- Entities can include:
  - researcher names (e.g., "Baumeister", "Spearman"),
  - theory/model names (e.g., "Process Overlap Theory", "CHC model"),
  - core constructs (e.g., "negativity bias", "working memory capacity"),
  - named tasks/paradigms (e.g., "Stroop task", "marshmallow test").
- Avoid generic words like "people", "study", "research" unless they are part of a standard term.
- Prefer concise noun phrases or proper names.
- Do not duplicate entities in the list.

Remember:
- Output MUST be valid JSON matching the schema above.
- Do not include any explanation or commentary outside the JSON.""",
        "is_active": True,
    },
    {
        "function_tag": "rag_augmentation",
        "version": 1,
        "title": "RAG Augmented Prompt - Context Integration",
        "template_content": """You are an academic assistant that answers questions using a set of retrieved source passages
plus your own general knowledge when appropriate.

Your job is to:
1. Read and understand the source passages in the CONTEXT section below.
2. Answer the user's question as accurately and clearly as possible.
3. Clearly distinguish between:
   - Information that is directly supported by the provided sources.
   - Information that comes from your broader academic knowledge but is NOT explicitly in the sources.
4. Explicitly reference which source passages you are using, with the keys [S1], [S2], etc.

HYBRID EVIDENCE POLICY (VERY IMPORTANT)
- PRIMARY: Treat the provided sources as the main evidence base.
- SECONDARY: You MAY use general academic knowledge, but:
  - Only if it is standard and non-controversial in the relevant field.
  - You MUST clearly separate it from what is supported by the sources.
- If the sources do not contain enough information to fully answer the question:
  - Say what can be concluded from the sources.
  - Then optionally add a clearly marked section with general knowledge and search.

CITATION RULES
- Each context block below is tagged with a label like [S1], [S2], etc.
- Each block may also include metadata such as work_id, start_line and end_line in parentheses.
  Example header:
    [S1] Source: Some Book Title -- section title | (work_id=123, start_line=23, end_line=32)
- When you make a claim that is supported by one or more sources:
  - Add the relevant source labels at the end of the sentence or paragraph, e.g. [S1], [S1][S3].
  - Do NOT invent new source labels beyond those given.
  - Do NOT cite work_id or start_line or end_line directly in the prose; just use [S#].
- Our system will later map [S#] back to work_id, start_line, and end_line for linking to the original content.

STRUCTURE YOUR ANSWER AS FOLLOWS
1. **Answer**
   - Provide a direct, well-organized answer to the question.
   - Use citations [S#] whenever you rely on information from the sources.
   - If multiple sources contribute to a point, cite each of them.
2. **Explanation and Details**
   - Expand on key concepts, mechanisms, comparisons, or study details.
   - Group related ideas logically (e.g., definitions, mechanisms, evidence, limitations).
   - Continue to use [S#] citations where appropriate.
3. **From General Knowledge or Search (Outside Provided Sources)** (optional)
   - Only include this section if you add material that is NOT clearly supported by the sources.
   - Clearly mark that this section is based on your broader academic knowledge or search.
   - Do NOT attach [S#] citations to statements in this section.
4. **Sources Used**
   - List the source labels you actually relied on in your answer, e.g.:
     - Sources used: [S1], [S3], [S5]

INTENT AND ENTITIES (GUIDANCE ONLY)
- The question intent type is: {intent}
  Possible values include: DEFINITION, MECHANISM, COMPARISON, APPLICATION, STUDY_DETAIL, CRITIQUE.
- Key entities and concepts for this question are:
  {entities_str}

Use this information to shape your answer style:
- DEFINITION: Start with a clear definition, then elaborate.
- MECHANISM: Focus on explaining processes, causes, and "how/why".
- COMPARISON: Explicitly compare similarities and differences between entities.
- APPLICATION: Emphasize examples and real-world implications.
- STUDY_DETAIL: Highlight study design, samples, methods, and key findings.
- CRITIQUE: Emphasize limitations, criticisms, and alternative interpretations.

TONE AND STYLE
- Write in a clear, academic style suitable for an advanced student or researcher.
- Define technical terms when they first appear, if the context does not already define them.
- Do not simply repeat large chunks of the sources; synthesize and explain them.
- If the sources disagree or present multiple perspectives, acknowledge this explicitly.

============================================================
CONTEXT (RETRIEVED SOURCE PASSAGES)
Each block is labeled [S#] and may include work_id and parent_id metadata
that our system uses to link back to the original document.

{context_blocks}
============================================================

USER QUESTION
{user_question}
""",
        "is_active": True,
    },
    {
        "function_tag": "vectorization_suggestions",
        "version": 1,
        "title": "Vectorization Suggestions - Heading Analysis",
        "template_content": """You are analyzing a document's heading structure to determine which sections contain valuable content worth vectorizing for a RAG (Retrieval Augmented Generation) system. Your goal is to include headings whose underlying sections contain explanatory, conceptual, or narrative content, and to exclude purely structural, navigational, or index-like sections.
```

{bib_section}
## Document Headings

{titles_content}

## Task

For each heading line number, determine whether it should be:

* **VECTORIZE**: The section under this heading likely contains meaningful prose or explanatory content that would help answer questions about the document's subject matter.
* **SKIP**: The section is primarily structural, navigational, index-like, or otherwise not useful as semantic knowledge for RAG.

## Decision Strategy

First, classify each heading based on its title. Then, enforce hierarchy rules so that parent headings are consistent with their children.

### A. Hierarchy rules

* Infer heading levels from markdown markers ("#", "##", "###", etc.) and/or numbering (e.g., "1.", "1.1.", "2.3.4").
* If any sub-heading is **VECTORIZE**, all of its ancestor headings (its parent, the parent's parent, etc.) MUST also be **VECTORIZE**.
* If a high-level heading looks structural (e.g., "Appendices", "Back Matter") but has child headings that clearly describe substantive content (e.g., "Appendix A: Experimental Stimuli"), treat those child headings and their ancestors as **VECTORIZE**.
* Do NOT force children to SKIP just because a parent is SKIP; children can still be **VECTORIZE** if they look like substantive content sections.

### B. Content to SKIP (structural / non-semantic)

Mark a heading as **SKIP** when it clearly indicates one of the following:

* Table of contents and navigation:

  * "Contents", "Table of Contents", "Detailed Contents", "List of Chapters"
  * "List of Figures", "List of Tables", "List of Boxes", "List of Abbreviations", "List of Acronyms"
* Indexes:

  * "Index", "Subject Index", "Author Index", "Name Index"
* References and bibliographic material:

  * "References", "Reference List", "Bibliography", "Works Cited", "Notes" / "Endnotes" sections that are primarily citation notes
* Pure front matter:

  * "Title Page", "Copyright", "Imprint", "Publication Data", "Dedication"
  * "Acknowledgments" / "Acknowledgements", "About the Author", "Foreword" (unless clearly domain-explanatory)
* Pure back matter or raw reference material:

  * Headings that obviously denote only raw data, item lists, or mechanical material such as:

    * "Data Tables", "Codebook", "Questionnaire Items", "Survey Items", "Answer Key"
    * "Appendix: Tables", "Appendix: Data", "Appendix: Raw Scores"
* Any heading that is clearly just a navigation/structure label with no real prose under it (e.g., "Part I", "Section I" by itself), **unless** its children are VECTORIZE (in which case the parent must also be VECTORIZE).

Only mark a heading as **SKIP** if it is very likely to be structurally / mechanically focused rather than explanatory content.

### C. Content to VECTORIZE (semantic / explanatory)

Mark a heading as **VECTORIZE** when the section under it is likely to contain any of the following:

* Core chapters and numbered sections that present the main subject matter.

  * e.g., "Chapter 1: Introduction to Cognitive Psychology", "2.3 Working Memory Capacity"
* Sections that define, explain, or discuss concepts, theories, models, mechanisms, or arguments.

  * e.g., "Theories of Intelligence", "Reinforcement Learning", "Social Identity Theory"
* Sections that describe methods, procedures, or empirical findings in a way that could answer user questions.

  * e.g., "Method", "Participants", "Procedure", "Results", "Discussion", "Implications", "Limitations"
* Sections that summarize, synthesize, or generalize information.

  * e.g., "Summary", "Conclusion", "General Discussion", "Practical Applications", "Future Directions"
* Worked examples, case studies, and explanatory exercises that teach or illustrate concepts.

  * e.g., "Case Study: Phineas Gage", "Example Problems", "Worked Example"
* Appendices that look conceptual or explanatory rather than purely tabular / raw data.

  * e.g., "Appendix A: Mathematical Derivation", "Appendix B: Scale Construction and Interpretation"

When in doubt, if a heading sounds like it could contain substantive explanatory text that would help answer questions about the topic, prefer **VECTORIZE** over **SKIP**.

## Output Format

Return ONLY a list in this exact format, one line per heading, preserving the original order of headings:

```
[line_number]: [SKIP|VECTORIZE]
```

Example:

```
10: SKIP
13: SKIP
18: VECTORIZE
19: VECTORIZE
20: VECTORIZE
```

Do NOT include any other commentary, explanations, or text. Analyze the headings and provide only your final SKIP/VECTORIZE labels:""",
        "is_active": True,
    },
    {
        "function_tag": "toc_extraction",
        "version": 1,
        "title": "Manual ToC Extraction - Manual Prompt for LLM",
        "template_content": """You are an expert at analyzing academic Markdown documents (textbooks, chapters, and papers) and extracting a clean, hierarchical table-of-contents in Markdown.

## Goal

Given a Markdown document I provide, extract the logical heading hierarchy (chapters, sections, subsections) and output it as a `.toc_titles.md` file using Markdown headings (`#`, `##`, `###`, …), with numbering preserved where the original document uses it.

Your output must look like this style (this is just an example, NOT the document you are processing):

# 1 Cognitive Psychology and the Brain

## 1.1 Introduction

## 1.2 History of Cognitive Psychology

## 1.3 What is Cognitive Psychology?

## 1.4 Relations to Neuroscience

## 1.5 Conclusion

# 2 Problem Solving from an Evolutionary Perspective

## 2.1 Introduction

## 2.2 Restructuring - The Gestalt Approach

## What You Should Use

When processing the provided Markdown document, use in this priority order:

1. **Any explicit "Table of Contents" section**, if it exists.
2. **Existing Markdown heading hierarchy**, using `#`, `##`, `###`, and deeper levels.
3. **Heading patterns in the body text**, such as:

   * Lines starting with "Chapter 1", "1.", "1.1", etc.
   * Lines that are clearly titles (standalone, title-case, visually separated in the original source, etc.).

Combine these sources into *one* consistent hierarchy.

## Output Format Rules

* **Output ONLY markdown headings. No explanations, no comments, no bullet lists.**
* Each logical section must be on its own line as a Markdown heading:

  * Top-level sections/chapters: `#`
  * Second-level sections: `##`
  * Third-level sections: `###`
  * You may use `####` and deeper levels only if the document clearly has more depth.
* **Preserve numbering** used by the document where possible:

  * If the document uses "1", "1.1", "1.1.1", etc., keep those prefixes in the heading text.
  * If the document does **not** use numbering, you do **not** need to invent numbers.
* **Do NOT include page numbers**, dot leaders, or junk formatting:

  * Bad: `## 1.2 History of Cognitive Psychology .................. 23`
  * Good: `## 1.2 History of Cognitive Psychology`
* Keep the headings **exactly as they appear** in the document, apart from removing page numbers and dot leaders.
* Maintain the original **order** of chapters and sections from the document.
* Do **not** add or invent headings that are not present in the document.

## What to Include vs. Skip

**Include:**

* All main chapters and numbered sections (e.g., "1 Cognitive Psychology and the Brain", "1.1 Introduction").
* Major unnumbered sections that appear as clear headings (e.g., "Preface", "Introduction", "Appendix A", "References").

**Skip or Ignore:**

* Purely technical or front-matter noise such as:

  * Publisher info, copyright pages.
  * Repeated running headers/footers.
  * Isolated page labels like "Page 3", "iii", "xii".
* Raw "Table of Contents" headings like "Contents", "Table of Contents" themselves (but you still use them as *sources* to reconstruct the hierarchy).
* Index entries (the long list at the end with many terms and page numbers). If there is a single heading called "Index", you may keep that **single** top-level heading, but not the list of terms.

## Edge Cases and Tie-Breakers

* If there is a conflict between any existing outline metadata and a written Table of Contents section, prefer the written Table of Contents, as long as it is coherent.
* If the document has **missing levels** (e.g., jumps from 1 to 1.3), do not invent the missing ones, just reflect what exists.
* If something is clearly a subsection but has no numbering, still nest it correctly via `##`, `###`, etc., based on structure and context.
* If the entire document has only one obvious heading level (e.g., a short article), you can use only `#` headings.

## Final Instruction

Once you have analyzed the provided Markdown document, respond **only** with the `.toc_titles.md` contents following the rules above. No prose, no explanations, no code fences, just the markdown headings themselves.""",
        "is_active": True,
    },

    {
        "function_tag": "heading_hierarchy",
        "version": 1,
        "title": "Heading Hierarchy Corrections - ToC Alignment",
        "template_content": """You are an expert at analyzing document structure and markdown formatting.

## Task
Analyze the headings from a markdown document and assign the correct heading levels so that:
- The overall structure is consistent with the document's table of contents (ToC)
- The hierarchy is as informative as possible for chunking and context
- No meaningful heading information from the current document is lost

## Document Information
- **Title:** {title}
- **Author(s):** {authors}

## Table of Contents from Database (authoritative high-level structure)
Use this ToC as the primary guide for:
- Overall ordering of sections
- Canonical wording of titles when possible
- The *relative* depth of major parts/chapters/sections

{toc_text}

## Current Headings in Document
Each line shows: [line_number]: [current_heading]
```

{titles_codeblock}

```

## Heading Hierarchy Rules
Treat markdown heading levels as a strict outline hierarchy:

- **H1 (#)**: Main parts, chapters, or major top-level sections
  - Usually mapped from top-level ToC entries
- **H2 (##)**: Sections within a part/chapter
- **H3 (###)**: Subsections
- **H4 (####)**: Sub-subsections (use for additional nesting; do not go deeper than H4)
- **REMOVE**: Only for non-semantic items that clearly are *not* headings
  (e.g., page numbers, running headers/footers, repeated book title on every page, copyright notices)
- **NO_CHANGE**: Heading level is already correct, but you may still normalize the title text

The hierarchy must be *nested and consistent*:
- Do not jump levels in a way that breaks outline logic (avoid H1 → H4 with no H2/H3 in between unless structure clearly demands it)
- Preserve the reading order of the original headings; do not reorder anything

## ToC vs Current Headings (VERY IMPORTANT)
The ToC from the database may be *shallower* (fewer levels) than the actual document headings. Handle this as follows:

1. **ToC as anchor, headings add detail**
   - Use the ToC to determine:
     - Which headings are major (H1) vs subordinate (H2–H4)
     - The canonical wording of titles where there is a clear match
   - Use the current headings to *refine and deepen* the structure under those ToC entries.

2. **Do NOT discard real structure just because ToC is shallow**
   - If the ToC only has chapter-level entries but the document headings clearly contain sections/subsections:
     - Map the chapter to **H1**
     - Map its internal headings to **H2/H3/H4** while preserving their relative nesting.
   - Do **not** REMOVE a heading solely because it is missing in the ToC.

3. **Relative hierarchy preservation**
   - When aligning to the ToC, preserve the *relative* nesting of headings:
     - Example rule: if for a group of headings the original levels are (H2, H3, H4) and you determine that the first one should actually be H1 (because it matches a top-level ToC entry), then the group should become (H1, H2, H3).
   - More generally:
     - If you "promote" or "demote" one heading to align with the ToC, apply the same offset to its direct descendants so that the internal structure under it stays the same.

4. **Matching titles**
   - If a heading clearly corresponds to a ToC entry:
     - Use the ToC title text as the authoritative `title_text` (fixing capitalization, punctuation, numbering if needed).
   - If there is no clear ToC match:
     - Keep the best, cleaned-up version of the current heading text as `title_text`, and assign a level (H1–H4) based on context.

5. **Special sections**
   - Common structural sections like "Foreword", "Preface", "Introduction", "Conclusion", "Appendix", "References", "Bibliography", "Glossary", "Index" should usually be kept as headings (often H1 or H2) unless they are clearly decorative repetitions.

## Instructions
1. Use your knowledge of this work (if you recognize it) to understand its typical structure.
2. If helpful, search the web for information about this specific work's structure (e.g., canonical chapter layout).
3. Compare the ToC from the database with the current headings:
   - Use text similarity, numbering patterns (e.g., "1.", "1.1"), and ordering to align them.
4. For **each line number** in the headings list:
   - Decide whether to assign H1, H2, H3, H4, NO_CHANGE, or REMOVE.
   - When in doubt between flattening or preserving additional structure, prefer preserving a *richer* and *consistent* hierarchy (i.e., more granularity, not less).
5. Do **not** suggest removing lower-level headings that are missing from the ToC. Instead:
   - Keep them, assign the best-fitting level (H2–H4), and maintain their relative position and nesting under the closest higher-level ToC-aligned parent.

## Output Format
Return **only** the mapping in the following format, one line **per heading line**:

[line_number] : [ACTION] : [title_text]

Where:
- `ACTION` is one of: `NO_CHANGE`, `REMOVE`, `H1`, `H2`, `H3`, `H4`
- `title_text` is:
  - The canonical title from the ToC, when there is a clear match, or
  - A cleaned-up version of the current heading text, when there is no ToC match
  - Empty only for `REMOVE`

Notes:
- Even for `NO_CHANGE`, still provide the authoritative `title_text` (which may normalize spacing/capitalization/numbering).
- Do **not** output anything other than these lines.

### Example
10 : NO_CHANGE : Introduction
13 : H1 : Chapter 1: Getting Started
18 : H1 : Methods
19 : H2 : Data Collection
20 : H3 : Survey Design
25 : REMOVE :

Provide the complete list of mappings for **all** headings shown above.""",
        "is_active": True,
    },
]


def seed_prompt_templates(verbose: bool = False) -> None:
    """
    Seed the database with default prompt templates.

    This function is idempotent - it will only insert templates that don't
    already exist (based on function_tag and version).

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Seeding prompt templates...")

    with engine.connect() as conn:
        for template_data in PROMPT_TEMPLATES:
            # Check if template already exists
            result = conn.execute(
                text("""
                    SELECT COUNT(*) FROM prompt_templates
                    WHERE function_tag = :function_tag AND version = :version
                """),
                {
                    "function_tag": template_data["function_tag"],
                    "version": template_data["version"]
                }
            )
            count = result.scalar()

            if count > 0:
                if verbose:
                    print(
                        f"  Template '{template_data['function_tag']}' v{template_data['version']} "
                        f"already exists, skipping"
                    )
                continue

            # Insert the template
            try:
                conn.execute(
                    text("""
                        INSERT INTO prompt_templates
                        (function_tag, version, title, template_content, is_active, created_at, updated_at)
                        VALUES (:function_tag, :version, :title, :template_content, :is_active, NOW(), NOW())
                    """),
                    {
                        "function_tag": template_data["function_tag"],
                        "version": template_data["version"],
                        "title": template_data["title"],
                        "template_content": template_data["template_content"],
                        "is_active": template_data["is_active"]
                    }
                )
                conn.commit()

                if verbose:
                    print(
                        f"  ✓ Inserted template '{template_data['function_tag']}' "
                        f"v{template_data['version']}: {template_data['title']}"
                    )

            except IntegrityError as e:
                # Handle race conditions or constraint violations
                if verbose:
                    print(
                        f"  Warning: Could not insert '{template_data['function_tag']}' "
                        f"v{template_data['version']}: {e}"
                    )
                conn.rollback()
        
        # Backfill any NULL timestamps (fixes issue where tables created via metadata 
        # lack server-side defaults but raw inserts didn't provide values)
        try:
            result = conn.execute(
                text("""
                    UPDATE prompt_templates 
                    SET created_at = NOW(), updated_at = NOW() 
                    WHERE created_at IS NULL OR updated_at IS NULL
                """)
            )
            conn.commit()
            if result.rowcount > 0 and verbose:
                print(f"  ✓ Fixed {result.rowcount} templates with missing timestamps")
        except Exception as e:
            if verbose:
                print(f"  Warning: Could not fix missing timestamps: {e}")

    if verbose:
        print("Prompt template seeding complete")
