# Ticket: collection-deep-research.T08 - Prompt Template Configuration

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create prompt templates for all research workflow steps using YAML + .txt file pattern
* Store templates in seed_data for version control and easy modification
* Enable loading of templates for planning, result matching, context assembly, section generation, synthesis, quality evaluation

## Phase

* Contracts

## Scope

### In scope

* Prompt templates in src/vulcanlab/data/seed_data/templates/:
  * research_planning.txt - Step 1 planning prompt
  * result_matching.txt - Step 2 result matching prompt
  * context_assembly_new.txt - Step 3 context assembly for new generation
  * context_assembly_ensemble.txt - Step 3 context assembly for ensemble reuse
  * section_generation.txt - Step 4 section generation prompt
  * synthesis.txt - Step 5 final report synthesis prompt
  * quality_evaluation.txt - Step 6 quality evaluation prompt (optional)
* Update templates.yaml with metadata for all research templates
* Loading utility: load_research_template(template_name) in research module

### Out of scope

* Actual seeding to database (prompt templates used directly from files, not stored in prompt_templates table)
* LLM integration (covered in T04-T07)
* Manual wizard UI (covered in T20-T23)

## Dependencies

* Depends on: none (can be done in parallel with T04-T07)
* Unblocks: T04 (planning), T05 (result matching), T06 (context assembly), T07 (synthesis), T16-T18 (LangGraph nodes)

## Implementation plan

* Create src/vulcanlab/data/seed_data/templates/research_planning.txt:
  * Prompt structure: collection overview (name, description, item counts, item notes)
  * Output format: JSON with ResearchPlan schema (research_goal, key_themes, sub_questions, synthesis_approach)
  * Guidance: generate 3-7 sub-questions, estimate 20K-40K tokens per question
* Create result_matching.txt:
  * Prompt structure: sub-question + available research results with previews
  * Output format: JSON with matching recommendations (similarity, quality, strategy)
* Create context_assembly_new.txt:
  * Prompt structure: sub-question + relevant excerpts + work metadata
  * Output format: assembled context with source attribution
* Create context_assembly_ensemble.txt:
  * Prompt structure: sub-question + multiple existing results to synthesize
  * Output format: synthesized context preserving consensus and unique insights
* Create section_generation.txt:
  * Prompt structure: sub-question + context + sources
  * Output requirements: synthesize insights, maintain citations [Author Year, pp. X-Y], identify consensus vs divergent views
  * Output format: markdown with inline citations
* Create synthesis.txt:
  * Prompt structure: all section contents + original research goal
  * Output requirements: executive summary, introduction, integrate sections, cross-cutting insights, limitations, conclusions, references
  * Output format: full markdown report
* Create quality_evaluation.txt:
  * Prompt structure: final report content
  * Evaluation criteria: citation accuracy, source diversity, coherence, completeness, depth
  * Output format: JSON with quality metrics
* Update templates.yaml (or create research_templates.yaml):
  * Add entries for each template with function_tag (e.g., "research_planning"), version, title, description
* Create src/vulcanlab/research/template_loader.py:
  * Implement load_research_template(template_name):
    * Read template file from seed_data/templates/{template_name}.txt
    * Return template string
  * Implement format_template(template, **kwargs):
    * Use string.Template or f-string formatting to substitute variables
    * Return formatted prompt
* Patterns to apply:
  * **Database seeding pattern** - YAML + .txt files per patterns.md section 2
  * **Version control friendly** - Text files easy to diff and modify
* Deviations (if any):
  * Templates not seeded to database (used directly from files for flexibility)

## Unit tests (required)

* Add tests for:
  * All 7 template files exist in seed_data/templates/
  * load_research_template loads each template successfully
  * format_template substitutes variables correctly
  * Templates contain required placeholders (e.g., {collection_name}, {sub_question})
  * Templates specify correct output formats (JSON or markdown)
* Suggested locations:
  * tests/unit/research/test_template_loader.py
* Mocking/fakes needed:
  * None (tests read actual template files)

## Acceptance criteria (checklist)

* [ ] research_planning.txt template created with ResearchPlan JSON schema
* [ ] result_matching.txt template created with matching output format
* [ ] context_assembly_new.txt template created for new generation workflow
* [ ] context_assembly_ensemble.txt template created for ensemble workflow
* [ ] section_generation.txt template created with citation requirements
* [ ] synthesis.txt template created with full report structure
* [ ] quality_evaluation.txt template created with evaluation criteria
* [ ] templates.yaml or research_templates.yaml updated with metadata
* [ ] load_research_template utility implemented
* [ ] format_template utility implemented
* [ ] Unit tests pass for template loading and formatting

## Manual verification

* Steps:
  * Read each template file manually, verify structure and placeholders
  * Call load_research_template("research_planning"), verify returns template string
  * Call format_template with test variables (collection_name="Test"), verify substitution works
  * Verify all templates specify output format (JSON or markdown)
  * Verify planning template specifies 3-7 sub-questions guidance
  * Verify section_generation template specifies citation format [Author Year, pp. X-Y]
* Expected results:
  * All templates readable and well-structured
  * Template loader works correctly
  * Format utility substitutes variables correctly

## Notes

* Requirements covered: R3 (manual wizard steps), R5 (automated workflow nodes), prompt templates for all steps
* Templates follow spec's manual workflow steps (Step 1-6) and automated node requirements
* Using text files directly (not database seeding) for easier iteration during development
* If templates need database storage later, can add seeding step similar to prompt_templates pattern
* Templates encode spec's requirements: token budgets, output formats, citation style, synthesis structure
