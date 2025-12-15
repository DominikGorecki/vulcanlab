# Template: simple_sanitize_small

**Function Tag:** `simple_sanitize_small`

**Template Variable:** `{markdown}`

---

## Template Content

```
You are an expert document sanitizer preparing content for a Retrieval-Augmented Generation (RAG) system.

Input markdown:
{markdown}

Your task: Return a cleaned version of this markdown with:
1. Correct heading hierarchy (no skipped levels, proper nesting)
2. Non-content headings removed (page numbers, ToC, references, copyright, etc.)
3. OCR errors and formatting issues fixed
4. All substantive content preserved

Return ONLY the sanitized markdown. No JSON, no explanations, no code fences. Just the literal markdown text.
```

---

## Usage Notes

**Expected Input:**
- Full markdown document (for documents under the token threshold)
- Variable name: `{markdown}`

**Expected Output:**
- Literal markdown text (NOT JSON)
- The LLM should return only the cleaned markdown document
- No code fences, no JSON wrapping, no explanations

**Parser Behavior:**
- The `parse_llm_response()` function strips markdown code fences if present
- Extracts literal markdown content from the response
- No heading modification tracking for small documents

**Example:**

Input:
```markdown
# Document Title

Page 1

## Introduction

This is the introduction...

## References

[1] Smith et al...
```

Expected LLM Output:
```markdown
# Document Title

## Introduction

This is the introduction...
```

Note: The LLM should remove the page number and references section, returning only the literal sanitized markdown.
