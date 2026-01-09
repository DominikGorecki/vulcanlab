# Ticket: collection-deep-research.T04 - Research Planning Module

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement research planning logic that analyzes collection metadata and items to generate research plans
* Produce structured research plans with sub-questions, token budgets, and synthesis approach
* Provide foundation for both manual wizard (Step 1) and automated LangGraph planning node

## Phase

* Core Modules

## Scope

### In scope

* Module src/vulcanlab/research/research_planner.py
* Function analyze_collection(collection_id, session) - fetches collection and items metadata
* Function generate_research_plan(collection_data, llm_client) - calls LLM to generate plan
* Function validate_research_plan(plan_dict) - validates JSON structure
* Research plan schema definition (TypedDict or dataclass)
* Prompt template for research planning (stored in seed_data per patterns.md)

### Out of scope

* LLM client implementation (use existing VulcanLab LLM infrastructure)
* Manual wizard UI (covered in T20)
* LangGraph node implementation (covered in T16)
* Saving plan to database (handled by CRUD functions in T03)

## Dependencies

* Depends on: T02 (models), T03 (CRUD)
* Unblocks: T16 (ResearchPlannerNode), T20 (Manual wizard Step 1)

## Implementation plan

* Create src/vulcanlab/research/ module directory
* Create research_planner.py
* Define ResearchPlan TypedDict:
  * research_goal: str
  * key_themes: list[str]
  * sub_questions: list[SubQuestion] where SubQuestion has {id, question, rationale, estimated_tokens, relevant_items}
  * synthesis_approach: str
* Implement analyze_collection:
  * Query collection by ID, fetch description, tags, item count by type
  * Query collection_items, get notes, types, IDs
  * For research_result items, fetch preview (first 200 chars)
  * For excerpt items, fetch work metadata (title, authors, year)
  * Return structured dict with collection metadata and item summaries
* Implement generate_research_plan:
  * Accept collection_data dict and LLM client (from vulcanlab.config)
  * Load planning prompt template from seed_data (or inline for now)
  * Format prompt with collection_data (name, description, item counts, item notes)
  * Call LLM with prompt, parse JSON response
  * Validate response structure matches ResearchPlan schema
  * Return ResearchPlan dict
* Implement validate_research_plan:
  * Check required fields present (research_goal, sub_questions)
  * Validate sub_questions is list with at least 1 item
  * Validate each sub_question has id, question, estimated_tokens
  * Raise ValueError if validation fails
* Create prompt template in src/vulcanlab/data/seed_data/templates/research_planning.txt:
  * Include collection overview format
  * Specify JSON output format with ResearchPlan schema
  * Guidance: 3-7 sub-questions, 20K-40K tokens per question
* Patterns to apply:
  * **Core module independence** - No FastAPI imports, session passed explicitly per patterns.md section 2
  * **Database seeding pattern** - Prompt template in seed_data per patterns.md section 2
  * **Configuration** - Use vulcanlab.config.load_config() for LLM settings per patterns.md section 3.3
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * analyze_collection returns correct structure with collection metadata
  * analyze_collection includes item notes and types
  * generate_research_plan calls LLM with correct prompt format
  * generate_research_plan parses valid JSON response correctly
  * generate_research_plan raises error on invalid JSON response
  * validate_research_plan accepts valid plan dict
  * validate_research_plan rejects plan missing required fields
  * validate_research_plan rejects plan with empty sub_questions list
  * validate_research_plan rejects sub_question missing estimated_tokens
* Suggested locations:
  * tests/unit/research/test_research_planner.py
* Mocking/fakes needed:
  * Mock database session and Collection/CollectionItem queries
  * Mock LLM client to return synthetic research plan JSON
  * Mock config.load_config() to return test LLM settings

## Acceptance criteria (checklist)

* [ ] ResearchPlan TypedDict defined with all required fields
* [ ] analyze_collection fetches collection and items metadata correctly
* [ ] generate_research_plan calls LLM with formatted prompt
* [ ] generate_research_plan returns valid ResearchPlan dict
* [ ] validate_research_plan enforces schema requirements
* [ ] Prompt template created in seed_data/templates/ (or inline if seed_data not ready)
* [ ] Module has no FastAPI imports (core module independence)
* [ ] Unit tests pass for all functions with mocked LLM and database

## Manual verification

* Steps:
  * Create test collection with 10 items (mix of excerpts, research_results, queries)
  * Call analyze_collection with collection_id, verify returned dict has correct item counts
  * Mock LLM to return sample research plan JSON
  * Call generate_research_plan, verify it parses JSON correctly
  * Call validate_research_plan with valid plan, verify no errors
  * Call validate_research_plan with invalid plan (missing sub_questions), verify ValueError raised
* Expected results:
  * analyze_collection returns structured collection data
  * generate_research_plan produces valid ResearchPlan
  * validate_research_plan enforces schema correctly

## Notes

* Requirements covered: R5 (Research Planner node logic), R13 (research questions in final report)
* Planning prompt should guide LLM to generate 3-7 sub-questions per spec
* Token budget estimation (20K-40K) per question per spec's "Token Budget Strategy"
* relevant_items field maps sub-questions to collection item IDs for context assembly (T06)
* If seed_data pattern not ready, inline prompt template as module constant for now
