-- Migration 016: Create tables for simple conversion pipeline
-- Description: Creates parsed_markdown, sanitized_markdown, and heading_modifications tables
--              Adds simple_conversion flag to io_files table
--              Seeds two new prompt templates for simple conversion

BEGIN;

-- Create ENUMs
DO $$ BEGIN
    CREATE TYPE file_type AS ENUM ('pdf', 'epub');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE document_classification AS ENUM ('small', 'large');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE modification_action AS ENUM ('remove', 'change', 'keep');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create parsed_markdown table
CREATE TABLE IF NOT EXISTS parsed_markdown (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    content BYTEA NOT NULL,  -- Stores compressed markdown
    file_type file_type NOT NULL,
    classification document_classification NOT NULL,
    token_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_parsed_markdown_work_id ON parsed_markdown(work_id);

-- Create sanitized_markdown table
CREATE TABLE IF NOT EXISTS sanitized_markdown (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    content BYTEA NOT NULL,  -- Stores compressed markdown
    token_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_sanitized_markdown_work_id ON sanitized_markdown(work_id);

-- Create heading_modifications table
CREATE TABLE IF NOT EXISTS heading_modifications (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    original_heading TEXT NOT NULL,
    modified_heading TEXT,
    action modification_action NOT NULL,
    vectorize_flag BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_heading_modifications_work_id ON heading_modifications(work_id);
CREATE INDEX IF NOT EXISTS ix_heading_modifications_work_line ON heading_modifications(work_id, line_number);

-- Add simple_conversion flag to io_files
ALTER TABLE io_files ADD COLUMN IF NOT EXISTS simple_conversion BOOLEAN DEFAULT FALSE;

-- Seed simple conversion prompt templates
-- Note: Only insert if they don't already exist

INSERT INTO prompt_templates (function_tag, version, title, template_content, is_active, created_at, updated_at)
SELECT
    'simple_sanitize_small',
    1,
    'Simple Conversion - Small Document Sanitization',
    'You are an expert document sanitizer preparing academic and research Markdown for a Retrieval-Augmented Generation (RAG) system.

Transform the input Markdown into clean, retrieval-ready Markdown whose heading hierarchy is semantically correct. Your highest priority is fixing heading levels and removing false headings.

Output ONLY the sanitized Markdown. No explanations. No code fences. No extra text.

---

# 0) Success Criteria

You must satisfy all of the following:

* Exactly one H1 for the document title, and only one.
* No skipped heading levels anywhere. Never jump from ## to #### without ### in between.
* Sibling consistency. Headings that are conceptually siblings must share the same heading level.
* No orphans. A subsection must not appear without an appropriate parent heading above it.
* False headings must not remain headings. Anything that is not a real title must not start with Markdown heading markers.

---

# 1) Identify and Classify Every Heading Line

For every line that begins with one or more # characters, classify it as either REAL HEADING or NOT A HEADING.

## 1A) NOT A HEADING Patterns

A line is NOT A HEADING if it is any of the following:

* Page numbers, running headers, running footers, repeated chapter headers, repeated book or article title lines
* Table of Contents, Contents, Outline, List of Figures, List of Tables, Index
* References, Bibliography, Works Cited, Footnotes, Endnotes
* Acknowledgments, Dedication, About the Author, Copyright, Permissions, ISBN
* Download or source notes, URLs, repository notes, scan metadata, conversion tool stamps
* Navigation entries such as Title ..... 23 or any dot leader ToC lines
* OCR or conversion noise masquerading as headings, such as random caps, broken glyphs, single symbols, character soup

### What to do when a line is NOT A HEADING

* If it is non-topical noise, delete it.
* If it is topical content that was mistakenly marked as a heading, remove only the leading # markers and keep the text as a normal paragraph line.

## 1B) REAL HEADING Definition

A line is a REAL HEADING only if it genuinely introduces a section of substantive content that follows.

---

# 2) Build the Correct Heading Hierarchy

Infer structure from:

* Numbering patterns like 1, 1.1, 1.1.1, Chapter 3, Part II, Appendix A
* Standard academic structure like Introduction, Methods, Results, Discussion, Conclusion
* Context: the content that follows and how it relates to surrounding headings
* Repetition: repeated headers and footers are not structure

## 2A) Choose the single H1 Title

* If a clear global title exists, make it the only # heading.
* If multiple candidates exist, choose the most global and demote the others to H2 or lower, or convert them to plain text if they are not true section titles.
* If no clear title exists, promote the highest-level meaningful heading to H1. Do not invent titles.

## 2B) Map Levels by Semantics

Use this default mapping unless the document clearly implies something else:

* Parts, Chapters, Major Sections, Appendices: H2 under the H1
* Sections within a chapter: H3
* Subsections: H4
* Deeper levels continue as needed, without skipping levels

## 2C) Enforce Numbering Consistency

If headings use numbering, enforce the implied nesting:

* 2 and 3 are siblings at the same level
* 2.1 is exactly one level deeper than 2
* 2.1.3 is exactly one level deeper than 2.1
  Do not renumber. Do not invent missing numbers.

## 2D) No-Level-Skip Repair

When adjusting headings:

* If a heading is too deep relative to its nearest valid parent, raise it.
* If a heading is too shallow relative to its siblings and children, lower it.
* Ensure parent and child differ by exactly one heading level.

## 2E) Orphan Handling

If a heading looks like a subsection but no appropriate parent exists above it:

* Prefer promoting it to the nearest valid level so it is not orphaned.
* Do not reorder large blocks of content unless it is necessary to fix an obvious conversion artifact like a dumped table of contents.

---

# 3) Content Sanitization

Hierarchy comes first. After hierarchy is correct, sanitize content.

## 3A) Remove Entire Non-Topical Sections

Delete these sections completely, including their content, unless they contain substantive definitions central to the document topic:

* Table of Contents and similar lists
* References and bibliography sections
* Index
* Acknowledgments and author bio material
* Copyright and legal boilerplate and publisher metadata

## 3B) Remove Unrecoverable Garbage

Delete content that is clearly corrupted and unrecoverable:

* Character soup
* Garbled OCR fragments with no reconstructable meaning
* Repeated headers, footers, isolated page numbers

## 3C) Repair Recoverable Conversion Artifacts

Fix using context:

* Replace broken glyphs or replacement characters with the intended text where obvious
* Merge words split by line breaks or hyphenation where clearly the same word
* Normalize excessive whitespace and line breaks
* Preserve meaningful tables and figure or table captions when they add retrieval value

## 3D) Preserve Topical Substance

Keep all substantive content related to the main topic:

* Definitions, explanations, arguments, examples, key claims
* Captions that explain figures or tables
  Inline citations are fine. Remove only standalone reference-list formatting.

---

# 4) Output Rules

* Output ONLY the sanitized Markdown.
* Do not add explanations or metadata.
* Do not wrap the output in code fences.
* Preserve valid Markdown for headings, lists, emphasis, blockquotes, and paragraphs.

---

## Document to Process

{markdown}

---

## Sanitized Output',
    TRUE,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM prompt_templates WHERE function_tag = 'simple_sanitize_small'
);

INSERT INTO prompt_templates (function_tag, version, title, template_content, is_active, created_at, updated_at)
SELECT
    'simple_sanitize_large',
    1,
    'Simple Conversion - Large Document Analysis',
    'You are an expert document structure analyst preparing heading-level corrections for a Retrieval-Augmented Generation (RAG) system.

You will receive a CONDENSED representation of a large document. Each entry contains a line number, a Markdown heading, and a small amount of surrounding context. Your job is to decide what to do with each heading and whether the associated section should be indexed.

Output ONLY the required structured list. Do not add any explanations, commentary, or code fences.

---

# Primary Objective

Produce heading decisions that yield a clean, semantically correct hierarchy suitable for chunking and retrieval.

You must ensure:

* Exactly one top-level document title exists in the final structure, and it should be H1 if present.
* No skipped levels in the final hierarchy. Children must be exactly one level deeper than their parent.
* Sibling consistency. Headings at the same conceptual level use the same H level.
* No orphans. A subsection must not exist without an appropriate parent above it.
* False headings are removed.

You must not reorder headings. Only decide KEEP, CHANGE, or REMOVE for each heading.

---

# How to Decide Heading Actions

## 1) Determine whether the line is a real heading

A heading is NOT real if it is any of the following:

* Page numbers or navigation markers like Page 3, p. 12, 12, 12 of 300
* Running headers or footers, repeated book or article title lines, repeated chapter titles
* Table of Contents, Contents, Outline, List of Figures, List of Tables, Index
* References, Bibliography, Works Cited, Footnotes, Endnotes
* Acknowledgments, Dedication, About the Author
* Copyright, Permissions, ISBN, publisher boilerplate
* Download metadata, scan metadata, URLs, repository notes, conversion tool stamps
* Dot leader ToC lines like Title ..... 23
* OCR noise or character soup

If it is not a real heading:

* ACTION must be REMOVE
* VECTORIZE must be SKIP
* MODIFIED must be blank

## 2) If the heading is real, decide KEEP vs CHANGE

Use CHANGE if any of the following are true:

* The heading level is wrong for the implied hierarchy
* The heading is a sibling but uses a different level than its siblings
* The heading creates a level skip relative to its parent or children
* The heading text needs cleanup, such as:

  * Extra whitespace
  * Weird or broken characters or replacement glyphs
  * Obvious OCR artifacts
  * Redundant prefixes like repeated running header text
  * Truncated titles that can be safely completed from context

Use KEEP only if both the level and the text are already correct.

When ACTION is CHANGE, MODIFIED must include the corrected Markdown heading line, including the correct number of # markers and cleaned text.

---

# Hierarchy Rules for Level Changes

Infer structure using:

* Numbering patterns like 1, 1.1, 1.1.1, Chapter 3, Part II, Appendix A
* Standard academic organization like Introduction, Methods, Results, Discussion, Conclusion
* Context snippets that show whether this is a major section, a subsection, or a subsubsection

Apply these constraints:

* No skipped levels.
* Parent and child differ by exactly one heading level.
* Siblings share the same heading level.
* If a heading looks like a subsection but no parent exists above it, promote it to the nearest valid level to avoid orphans.
* Preserve existing numbering if present. Do not renumber and do not invent missing numbers.

Title rule:

* If a clear global title exists, it should be the only H1.
* If multiple apparent titles exist, keep only the most global as H1 and demote others to appropriate levels or treat them as non-headings if they are boilerplate.

---

# Vectorize Decision Rules

VECTORIZE should reflect whether the section content is worth indexing for RAG.

Choose VECTORIZE for:

* Core topical content: definitions, explanations, arguments, examples, methods, results, discussion, conclusions, substantive appendices
* Substantive figure or table captions and analyses
* Glossary-like sections only if they contain real definitions useful for retrieval

Choose SKIP for:

* Table of contents and navigation material
* References and bibliography lists
* Index
* Acknowledgments, dedications, author bio
* Copyright and publisher boilerplate
* Download metadata, scan metadata, URLs
* Purely administrative or non-topical material

If ACTION is REMOVE, VECTORIZE must be SKIP.

---

# Output Format (strict)

For each heading entry, output exactly:

LINE: {line_number}
ACTION: {KEEP|CHANGE|REMOVE}
MODIFIED: {new heading if ACTION=CHANGE, otherwise blank}
VECTORIZE: {VECTORIZE|SKIP}
---------------------------

Do not change field names. Do not add extra fields. Do not include any additional separators.

---

## Condensed Document

{condensed_document}

---

## Your Modifications',
    TRUE,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM prompt_templates WHERE function_tag = 'simple_sanitize_large'
);

COMMIT;
