# Ticket: work-summarization.T10 - Seed Summarization Prompt Templates

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create prompt templates for LLM summarization calls following existing template patterns
* Seed templates into prompt_templates database table via templates.yaml configuration
* Create prompt_meta entries for variable documentation
* Ensure templates are editable via Settings > Templates UI

## Phase

* Core Modules

## Scope

### In scope

* Create template content files in src/vulcanlab/data/seed_data/templates/:
  - summarize_node.txt - Evidence packet to structured summary
  - synthesize_abstract.txt - Gists to abstract
  - organize_key_concepts.txt - Raw concepts to organized list
* Update src/vulcanlab/data/seed_data/templates.yaml with new template metadata
* Create prompt_meta entries in src/vulcanlab/data/seed_data/variables.yaml for variable documentation
* Update FUNCTION_LABELS in templates-tab.tsx to include new templates
* Templates stored in database via existing seeding infrastructure
* Templates editable via existing Settings > Templates UI

### Out of scope

* LLM calling logic (T07 - will read templates from database)
* Derived output compilation logic (T09)
* New UI components (use existing template editor)

## Dependencies

* Depends on: T03 (database must exist for seeding)
* Unblocks: T07, T09 (templates must exist in DB before those are tested end-to-end)

## Implementation plan

1. Create src/vulcanlab/data/seed_data/templates/summarize_node.txt:
   - System context: structured summarization task
   - Input format: heading path, line range, snippets with line numbers, keyphrases
   - Output format: JSON with gist, key_points, definitions, key_terms, examples
   - Each output item must include start_line, end_line from provided snippets
   - Include insufficient_evidence flag and missing_concepts list
   - Emphasize: only use line numbers from provided snippets
   - Variables: {heading_path}, {line_start}, {line_end}, {snippets}, {keyphrases}

2. Create src/vulcanlab/data/seed_data/templates/synthesize_abstract.txt:
   - Input: list of section gists with headings
   - Output: cohesive 2-4 paragraph abstract
   - Maintain academic/technical tone
   - Variables: {work_title}, {gists}

3. Create src/vulcanlab/data/seed_data/templates/organize_key_concepts.txt:
   - Input: raw list of terms and definitions
   - Output: organized, deduplicated list grouped by theme
   - Preserve line references
   - Variables: {concepts}, {work_title}

4. Update src/vulcanlab/data/seed_data/templates.yaml with entries:
   ```yaml
   - function_tag: summarize_node
     version: 1
     title: "Summarization - Node Evidence to Structured Summary"
     template_type: summarize
     is_active: true
     content_file: summarize_node.txt

   - function_tag: synthesize_abstract
     version: 1
     title: "Summarization - Abstract Synthesis"
     template_type: summarize
     is_active: true
     content_file: synthesize_abstract.txt

   - function_tag: organize_key_concepts
     version: 1
     title: "Summarization - Key Concepts Organization"
     template_type: summarize
     is_active: true
     content_file: organize_key_concepts.txt
   ```

5. Update src/vulcanlab/data/seed_data/variables.yaml with prompt_meta entries:
   - summarize_node: heading_path, line_start, line_end, snippets, keyphrases
   - synthesize_abstract: work_title, gists
   - organize_key_concepts: concepts, work_title
   - Include descriptions for each variable

6. Update vulcanlab_ui/src/components/settings/templates-tab.tsx FUNCTION_LABELS:
   ```typescript
   summarize_node: "Summarization - Node Summary",
   synthesize_abstract: "Summarization - Abstract",
   organize_key_concepts: "Summarization - Key Concepts",
   ```

7. Update vulcanlab_ui/src/app/settings/templates/[function_tag]/page.tsx FUNCTION_LABELS similarly

8. Test template loading: `python scripts/test_template_seeding.py`

9. Run seeding to add templates: `python -m vulcanlab.data.init_db -v`

* Patterns to apply:
  * File-based YAML configuration for templates per patterns.md
  * Templates in .txt files, metadata in templates.yaml
  * Variables documented in variables.yaml -> prompt_meta table
  * Idempotent seeding (only inserts new templates)
  * template_type: "summarize" for filtering in UI
* Deviations (if any):
  * None - follows existing template patterns exactly

## Unit tests (required)

* Add tests for:
  * summarize_node.txt template file exists and is non-empty
  * synthesize_abstract.txt template file exists and is non-empty
  * organize_key_concepts.txt template file exists and is non-empty
  * templates.yaml includes all three new entries with template_type: summarize
  * variables.yaml includes prompt_meta entries for all three function_tags
  * Template metadata has required fields (function_tag, version, title, template_type)
  * Template content includes JSON output format instructions (summarize_node)
  * Template content includes line number anchoring instructions (summarize_node)
  * FUNCTION_LABELS updated in both templates-tab.tsx and editor page
* Suggested locations:
  * tests/unit/data/seed_data/test_summarize_templates.py
  * vulcanlab_ui/src/components/settings/__tests__/templates-tab.test.tsx (update)
* Mocking/fakes needed:
  * None - tests read actual template files

## Acceptance criteria (checklist)

* [ ] summarize_node.txt created with structured JSON output format
* [ ] summarize_node.txt requests line anchors for all output items
* [ ] summarize_node.txt includes insufficient_evidence flag
* [ ] synthesize_abstract.txt created for abstract compilation
* [ ] organize_key_concepts.txt created for concept organization
* [ ] templates.yaml updated with all three entries (template_type: summarize)
* [ ] variables.yaml updated with prompt_meta entries for all templates
* [ ] FUNCTION_LABELS updated in templates-tab.tsx
* [ ] FUNCTION_LABELS updated in template editor page
* [ ] Template seeding script passes validation
* [ ] Templates seed successfully to database
* [ ] Templates visible in Settings > Templates UI
* [ ] Templates editable via existing template editor
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Run `python scripts/test_template_seeding.py`
  2. Run `python -m vulcanlab.data.init_db -v`
  3. Query database: `SELECT function_tag, version, template_type FROM prompt_templates WHERE template_type = 'summarize'`
  4. Start UI, navigate to Settings > Templates
  5. Verify three new summarization templates appear
  6. Click Edit on summarize_node template
  7. Verify template content and variables display correctly
  8. Make a small edit, save, verify persisted
* Expected results:
  * Validation passes
  * Three new templates appear in database with template_type='summarize'
  * Templates visible and editable in Settings > Templates UI

## Notes

* Requirements covered: R7 (prompt structure), R8 (insufficient evidence detection)
* Templates are seeded from files but stored in database - all runtime reads from DB
* JSON output format in prompt should be explicit schema, not just "return JSON"
* Line anchoring instruction is critical: "Only reference line numbers that appear in the provided snippets"
* insufficient_evidence should trigger when LLM cannot confidently summarize
* missing_concepts list helps escalation know what additional context to fetch
* Consider including example output in template for better LLM compliance
* template_type: "summarize" allows filtering in UI (existing pattern from "research", "eval")
* FUNCTION_LABELS are cosmetic - provide human-readable names in the UI
