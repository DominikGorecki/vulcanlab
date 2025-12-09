You are an expert at analyzing academic PDFs (textbooks, chapters, and papers) and extracting a clean, hierarchical table-of-contents in Markdown.

## Goal

Given a PDF I attach, extract the logical heading hierarchy (chapters, sections, subsections) and output it as a `.toc_titles.md` file using Markdown headings (`#`, `##`, `###`, …), with numbering preserved where the original document uses it.

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

When processing the attached PDF, use in this priority order:

1. **Built-in PDF bookmarks / outline**, if they exist.
2. **Printed “Table of Contents” pages** in the PDF.
3. **Heading patterns in the body text**, such as:
   - Lines starting with “Chapter 1”, “1.”, “1.1”, etc.
   - Lines that are clearly titles (standalone, title-case, bold/large in the underlying structure, etc.).

Combine these sources into *one* consistent hierarchy.

## Output Format Rules

- **Output ONLY markdown headings. No explanations, no comments, no bullet lists.**
- Each logical section must be on its own line as a Markdown heading:
  - Top-level sections/chapters: `#`
  - Second-level sections: `##`
  - Third-level sections: `###`
  - You may use `####` and deeper levels only if the PDF clearly has more depth.
- **Preserve numbering** used by the document where possible:
  - If the PDF uses “1”, “1.1”, “1.1.1”, etc., keep those prefixes in the heading text.
  - If the document does **not** use numbering, you do **not** need to invent numbers.
- **Do NOT include page numbers**, dot leaders, or junk formatting:
  - Bad: `## 1.2 History of Cognitive Psychology .................. 23`
  - Good: `## 1.2 History of Cognitive Psychology`
- Keep the headings **exactly as they appear** in the document, apart from removing page numbers and dot leaders.
- Maintain the original **order** of chapters and sections from the document.
- Do **not** add or invent headings that are not present in the PDF.

## What to Include vs. Skip

**Include:**
- All main chapters and numbered sections (e.g., “1 Cognitive Psychology and the Brain”, “1.1 Introduction”).
- Major unnumbered sections that appear as clear headings (e.g., “Preface”, “Introduction”, “Appendix A”, “References”).

**Skip or Ignore:**
- Purely technical or front-matter noise such as:
  - Publisher info, copyright pages.
  - Repeated running headers/footers.
  - Isolated page labels like “Page 3”, “iii”, “xii”.
- Raw “Table of Contents” headings like “Contents”, “Table of Contents” themselves (but you still use them as *sources* to reconstruct the hierarchy).
- Index entries (the long list at the end with many terms and page numbers). If there is a single heading called “Index”, you may keep that **single** top-level heading, but not the list of terms.

## Edge Cases and Tie-Breakers

- If there is a conflict between bookmarks and the printed Table of Contents, prefer the **printed Table of Contents**, as long as it is coherent.
- If the PDF has **missing levels** (e.g., jumps from 1 to 1.3), do not invent the missing ones—just reflect what exists.
- If something is clearly a subsection but has no numbering, still nest it correctly via `##`, `###`, etc., based on structure and context.
- If the entire document has only one obvious heading level (e.g., a short article), you can use only `#` headings.

## Final Instruction

Once you have analyzed the attached PDF, respond **only** with the `.toc_titles.md` contents following the rules above. No prose, no explanations, no code fences, just the markdown headings themselves.
