# Changes: Line-Based Sanitization & Literal Markdown Output

## Summary

Updated the simple conversion sanitization process to use line numbers instead of text matching for large documents, and changed small documents to return literal markdown instead of JSON.

## Date
2025-12-14

## Changes Made

### 1. Large Document Sanitization (Line-Based)

**Problem:** The old implementation used text matching to find and modify headings, which failed when there were duplicate headings or when the LLM returned headings with different formatting.

**Solution:** Use line numbers to precisely identify and modify headings.

#### Code Changes:

**`sanitize_large.py`:**
- `create_condensed_markdown()`: Changed output format from enumerated headings to line-numbered format
  - Old: `## Heading 1\n**Level:** 1\n**Text:** Main Heading`
  - New: `LINE 1: # Main Heading`

- `apply_modifications_to_markdown()`: Completely rewritten to use line numbers
  - Old: Matched headings by text using `mod_map = {mod['original']: mod for mod in modifications}`
  - New: Matches headings by line number using `mod_map = {mod['line']: mod for mod in modifications}`
  - Now handles full heading replacement (including # markers)

- `create_heading_modifications_large()`: Updated to read `vectorize` field from JSON
  - Old: Hardcoded `vectorize_flag=False`
  - New: `vectorize_flag = mod.get('vectorize', False)`
  - Now uses line numbers from JSON instead of looking up by text

- `get_hardcoded_template_large()`: Simplified template
  - Removed complex hierarchy rules and verbose instructions
  - Clear JSON format with `line`, `action`, `new`, `vectorize` fields
  - Instructs LLM to return full heading with # markers in `new` field

#### Template Changes:

**Expected LLM Response (Large Documents):**
```json
{
  "modifications": [
    {"line": 5, "action": "remove", "vectorize": false},
    {"line": 12, "action": "change", "new": "## Methods", "vectorize": true},
    {"line": 25, "action": "keep", "vectorize": true}
  ]
}
```

Fields:
- `line`: Line number in original markdown (required)
- `action`: "keep", "change", or "remove" (lowercase, required)
- `new`: Full corrected heading with # markers (required if action="change")
- `vectorize`: Boolean indicating if section should be indexed (required)

### 2. Small Document Sanitization (Literal Markdown)

**Problem:** The JSON format was unnecessary complexity for small documents where the entire content fits in context.

**Solution:** LLM returns literal sanitized markdown instead of JSON.

#### Code Changes:

**`sanitize_small.py`:**
- `parse_llm_response()`: Changed from JSON parser to markdown extractor
  - Old: Extracted `sanitized_markdown` and `modifications` from JSON
  - New: Strips code fences and returns literal markdown

- `sanitize_small_document()`: Removed heading modification tracking
  - No longer creates `HeadingModification` records for small documents
  - Directly uses the returned markdown as sanitized content

- `create_heading_modifications()`: Function removed (no longer needed)

- `get_hardcoded_template_small()`: Simplified template
  - Removed JSON output requirement
  - Instructions to return literal markdown only

#### Template Changes:

**Expected LLM Response (Small Documents):**
```markdown
# Document Title

## Introduction

This is the introduction...

## Methods

Content here...
```

Just the literal sanitized markdown - no JSON, no code fences, no metadata.

### 3. API Router Updates

**`simple_conversion.py`:**
- Updated `submit_manual_result()` to handle new formats for both small and large documents
- Small documents: Parse literal markdown
- Large documents: Parse JSON with line numbers

### 4. Test Updates

**`test_sanitize_large.py`:**
- `test_create_condensed_markdown()`: Updated assertions for new format
- `test_apply_modifications_to_markdown_*()`: All tests updated to use `line` instead of `original`
- `test_sanitize_large_document_success()`: Updated mock LLM response to new JSON format

### 5. Documentation

Created two template documentation files:
- [`documentation/template_simple_sanitize_small.md`](template_simple_sanitize_small.md)
- [`documentation/template_simple_sanitize_large.md`](template_simple_sanitize_large.md)

## Benefits

1. **Reliability**: Line-based matching eliminates ambiguity with duplicate headings
2. **Simplicity**: Literal markdown output for small documents is more natural
3. **Correctness**: LLM returns full headings with # markers, avoiding level confusion
4. **Vectorization**: Large documents now properly track which sections should be indexed
5. **Debugging**: Line numbers make it easy to trace modifications back to source

## Migration Notes

### Database Template Updates

Update templates in the database through the settings page using the documentation files:

1. **simple_sanitize_small**: Use content from `template_simple_sanitize_small.md`
2. **simple_sanitize_large**: Use content from `template_simple_sanitize_large.md`

Remember to escape curly braces in the database:
- Use `{{` and `}}` for literal braces in examples
- Only `{condensed_document}` and `{markdown}` are actual template variables

### Testing

All unit tests pass:
```bash
pytest tests/unit/test_sanitize_large.py -v  # 18/18 passed
```

## Breaking Changes

- Existing manual workflow responses using the old format will fail
- Any saved LLM responses from manual mode cannot be reused
- Heading modification records for small documents are no longer created

## Next Steps

1. Update database templates through settings UI
2. Test manual conversion workflow with a sample document
3. Monitor LLM output quality with new templates
4. Consider adding validation for line numbers in LLM responses
