# Ticket: collection-deep-research.T06 - Context Assembly Module

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement context assembly logic to fetch and consolidate collection items for sub-question research
* Apply token limits (20K-40K), deduplicate overlapping content, maintain source attribution
* Support both new generation (fetch excerpts) and reuse (fetch existing results) workflows

## Phase

* Core Modules

## Scope

### In scope

* Module src/vulcanlab/research/context_assembler.py
* Function assemble_context_for_question(question_id, relevant_item_ids, reuse_info, session) - main assembly
* Function fetch_collection_items(item_ids, session) - retrieves excerpts, results, queries
* Function deduplicate_content(items) - removes overlapping content
* Function apply_token_limit(content, max_tokens) - truncates to token budget
* Function build_source_attribution(items) - creates source metadata list
* Token counting using tiktoken library

### Out of scope

* Result matching logic (covered in T05)
* Prompt generation for LLM (covered in T04, T07)
* API endpoint (covered in T14)
* Manual wizard UI (covered in T21)

## Dependencies

* Depends on: T02 (models), T03 (CRUD), T05 (result matching)
* Unblocks: T14 (context endpoint), T17 (QueryExecutorNode), T21 (Manual wizard Step 3)

## Implementation plan

* Create src/vulcanlab/research/context_assembler.py
* Install tiktoken if not already in dependencies (for token counting)
* Implement fetch_collection_items:
  * Query CollectionItem by IDs
  * For each item, fetch based on type:
    * research_result: get result content from database
    * excerpt: get enriched_content or chunk content, include work metadata (title, authors, year), heading_breadcrumbs
    * research_query: get query text
  * Return list of dicts: [{item_id, type, content, work_metadata, preview}]
* Implement deduplicate_content:
  * Accept list of items with content
  * Use simple deduplication: if two items have > 80% overlapping text (by character comparison), keep only one
  * For excerpts from same work with overlapping chunks, merge and keep heading_breadcrumbs
  * Return deduplicated list
* Implement apply_token_limit:
  * Accept content string and max_tokens (default 35000)
  * Use tiktoken to count tokens: enc = tiktoken.encoding_for_model("gpt-4"); tokens = enc.encode(content)
  * If token count > max_tokens, truncate content and append "...[truncated]"
  * Return truncated content and final token count
* Implement build_source_attribution:
  * Accept items list
  * For each item, create source entry: {item_id, type, work_id (if excerpt), work_title, preview (first 100 chars)}
  * Return list of source dicts
* Implement assemble_context_for_question:
  * If reuse_info provided (reuse strategy from T05):
    * Fetch reused research_result items by IDs in reuse_info['source_result_ids']
    * Concatenate result contents
  * Else (new generation):
    * Call fetch_collection_items with relevant_item_ids
    * Prioritize by type: research_result > excerpt > research_query per spec
    * Call deduplicate_content
  * Call apply_token_limit with 35K max_tokens
  * Call build_source_attribution
  * Return dict: {context: str, token_count: int, sources: list}
* Patterns to apply:
  * **Core module independence** - No FastAPI imports per patterns.md section 2
  * **Session management** - Pass session explicitly per patterns.md section 2
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * fetch_collection_items retrieves items by IDs correctly
  * fetch_collection_items handles research_result, excerpt, research_query types
  * deduplicate_content removes duplicate items (> 80% overlap)
  * deduplicate_content merges overlapping excerpts from same work
  * apply_token_limit truncates content when token count exceeds max
  * apply_token_limit returns correct token count
  * build_source_attribution creates source list with correct fields
  * assemble_context_for_question assembles context for new generation workflow
  * assemble_context_for_question assembles context for reuse workflow (fetches existing results)
  * assemble_context_for_question applies token limit correctly
* Suggested locations:
  * tests/unit/research/test_context_assembler.py
* Mocking/fakes needed:
  * Mock database session and CollectionItem queries
  * Mock tiktoken encoding for predictable token counts

## Acceptance criteria (checklist)

* [ ] fetch_collection_items retrieves all three item types (research_result, excerpt, research_query)
* [ ] deduplicate_content removes overlapping content
* [ ] apply_token_limit enforces 35K token budget (configurable)
* [ ] build_source_attribution includes item_id, type, work metadata, preview
* [ ] assemble_context_for_question handles both reuse and new generation workflows
* [ ] Token counting uses tiktoken library
* [ ] All functions accept session parameter explicitly
* [ ] Unit tests pass for all context assembly logic

## Manual verification

* Steps:
  * Create collection with 10 excerpts from same work (overlapping chunks)
  * Create relevant_item_ids list with all 10 excerpt IDs
  * Call assemble_context_for_question with relevant_item_ids
  * Verify deduplicate_content reduces overlapping excerpts
  * Verify token_count is within 35K limit
  * Verify sources list includes work metadata for excerpts
  * Create reuse_info with source_result_ids
  * Call assemble_context_for_question with reuse_info
  * Verify context contains result content, not excerpt content
* Expected results:
  * Context assembled correctly for new generation
  * Context assembled correctly for reuse workflow
  * Token limit enforced
  * Source attribution complete

## Notes

* Requirements covered: R12 (source attribution), context assembly for sub-questions
* Token limit 35K chosen as upper bound of 20K-40K optimal range per spec "Token Budget Strategy"
* Deduplication simple for MVP - can be enhanced with semantic similarity later
* Prioritization (research_result > excerpt > research_query) per spec "Collection Item Utilization" section
* tiktoken library standard for OpenAI token counting, works well for other models too
