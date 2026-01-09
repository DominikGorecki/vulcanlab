# Ticket: collection-deep-research.T13 - LangGraph Context Assembly and Synthesis Nodes

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement LangGraph workflow nodes for Context Assembler and Synthesizer
* Provide automated context assembly with token limits and section content generation
* Integrate with T06 (context assembly module) and T07 (synthesizer module)

## Phase

* LangGraph Automation

## Scope

### In scope

* Node implementations in src/vulcanlab/research/nodes/:
  * context_assembler_node.py - ContextAssemblerNode
  * synthesizer_node.py - SynthesizerNode
* ContextAssemblerNode: consolidates context for each sub-question, applies token limits, deduplicates
* SynthesizerNode: generates section content via LLM, saves to research_sections, extracts metadata
* Integration with T06 assemble_context_for_question
* Integration with T07 generate_section and extract_metadata

### Out of scope

* Planning and execution nodes (covered in T12)
* Quality evaluation and refinement nodes (covered in T14)
* Workflow graph definition (covered in T15)

## Dependencies

* Depends on: T06 (context assembler), T07 (synthesizer), T11 (state schema), T12 (planning/execution nodes)
* Unblocks: T15 (workflow graph)

## Implementation plan

* Create context_assembler_node.py
* Implement ContextAssemblerNode(state: ResearchState, session) -> ResearchState:
  * Get sub_questions from state['research_plan']['sub_questions']
  * For each sub_question:
    * Get question_id, relevant_item_ids from sub_question
    * Get reuse_info from state['reused_sections'][question_id] (if exists)
    * Call assemble_context_for_question from T06 with question_id, relevant_item_ids, reuse_info, session
    * Store result in state['context_per_question'][question_id]:
      * {context: str, token_count: int, sources: list}
  * Update state['current_phase'] = 'synthesis'
  * Return updated state
* Create synthesizer_node.py
* Implement SynthesizerNode(state: ResearchState, session) -> ResearchState:
  * Get sub_questions from state['research_plan']['sub_questions']
  * Get LLM client from vulcanlab.config
  * For each sub_question:
    * Get question_id, question_text
    * Get context from state['context_per_question'][question_id]
    * Call generate_section from T07 with question_text, context['context'], context['sources'], LLM client
    * Get section_content (markdown)
    * Call extract_metadata from T07 with section_content and sources
    * Save section to database using create_research_section from T03:
      * session_id from state
      * question_id, question_text, section_content
      * context_data = context
      * metadata = extracted metadata
      * reuse_info from state['reused_sections'][question_id] if exists
    * Store section in state['sections'][question_id]:
      * {content: section_content, sources: context['sources'], quality: metadata}
  * Update state['current_phase'] = 'evaluation'
  * Return updated state
* Both nodes should handle errors gracefully (LLM failures, context assembly failures)
* Patterns to apply:
  * **Core module independence** - No FastAPI imports per patterns.md section 2
  * **Session management** - Accept session parameter explicitly per patterns.md section 2
  * **Configuration** - Use vulcanlab.config for LLM settings per patterns.md section 3.3
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * ContextAssemblerNode calls assemble_context_for_question for each sub-question
  * ContextAssemblerNode stores context in state['context_per_question']
  * ContextAssemblerNode handles reuse workflow (passes reuse_info to assembler)
  * ContextAssemblerNode updates current_phase to 'synthesis'
  * SynthesizerNode calls generate_section for each sub-question
  * SynthesizerNode calls extract_metadata for each generated section
  * SynthesizerNode saves sections to database via create_research_section
  * SynthesizerNode stores section content in state['sections']
  * SynthesizerNode includes reuse_info when section used reuse strategy
  * SynthesizerNode updates current_phase to 'evaluation'
* Suggested locations:
  * tests/unit/research/nodes/test_context_assembler_node.py
  * tests/unit/research/nodes/test_synthesizer_node.py
* Mocking/fakes needed:
  * Mock assemble_context_for_question from T06
  * Mock generate_section and extract_metadata from T07
  * Mock create_research_section from T03
  * Mock database session
  * Mock LLM client

## Acceptance criteria (checklist)

* [ ] ContextAssemblerNode implemented in context_assembler_node.py
* [ ] SynthesizerNode implemented in synthesizer_node.py
* [ ] ContextAssemblerNode assembles context for all sub-questions
* [ ] ContextAssemblerNode applies token limits via T06 (20K-40K range)
* [ ] SynthesizerNode generates section content for all sub-questions
* [ ] SynthesizerNode saves sections to research_sections table (R6)
* [ ] SynthesizerNode extracts metadata (word_count, citation_count, source_diversity)
* [ ] Both nodes update current_phase correctly
* [ ] Unit tests pass for both nodes

## Manual verification

* Steps:
  * Create test ResearchState with research_plan containing 2 sub-questions
  * Set state['reused_sections']['Q1'] with reuse_info (exact_reuse strategy)
  * Call ContextAssemblerNode(state, session)
  * Verify state['context_per_question']['Q1'] contains context from reused result
  * Verify state['context_per_question']['Q2'] contains context from new generation
  * Verify token_count for each context within 35K limit
  * Mock LLM to return sample section markdown with citations
  * Call SynthesizerNode(state, session)
  * Verify state['sections']['Q1'] contains section content
  * Verify metadata extracted (word_count > 0, citation_count > 0)
  * Verify sections saved to database
* Expected results:
  * Context assembled for all questions with correct workflow (reuse vs new)
  * Sections generated and saved correctly
  * Metadata extracted correctly

## Notes

* Requirements covered: R5 (Context Assembler and Synthesizer nodes), R12 (source attribution), R13 (findings per sub-question)
* ContextAssemblerNode applies token limits per spec "Token Budget Strategy" (20K-40K optimal)
* SynthesizerNode saves sections to database for persistence and manual review
* Both nodes stateless (state in, state out) per LangGraph pattern
* Error handling critical: LLM failures should not crash entire workflow, log and continue or mark for refinement
