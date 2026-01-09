# Ticket: collection-deep-research.T19 - Manual Research Wizard (Steps 3-4: Context Assembly and Section Generation)

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement Steps 3-4 of manual research wizard UI
* Enable user to fetch context (Step 3) and paste/save section content (Step 4)
* Support looping through all sub-questions for section generation

## Phase

* Frontend

## Scope

### In scope

* Step 3 (Context Assembly): fetch context button, context preview, copy prompt button, token count display
* Step 4 (Section Generation): paste section area, markdown preview, save section action, loop to next question
* Integration with API endpoints: POST /api/v1/research-sessions/{session_id}/context, POST /api/v1/research-sessions/{session_id}/sections
* Markdown preview component using react-markdown

### Out of scope

* Steps 1-2 of wizard (covered in T18)
* Steps 5-6 of wizard (covered in T20)
* Automated research (covered in T22)

## Dependencies

* Depends on: T10 (context endpoint), T18 (wizard Steps 1-2)
* Unblocks: T20 (wizard Steps 5-6)

## Implementation plan

* Update ManualResearchWizard component (from T18):
  * Add state for context: const [contextData, setContextData] = useState<Record<string, any>>({})
  * Add state for sections: const [sections, setSections] = useState<Record<string, string>>({})
  * Add state for current section question: const [currentSectionIndex, setCurrentSectionIndex] = useState(0)
* Create Step3ContextAssembly component:
  * Get current sub-question from researchPlan
  * Display sub-question text
  * If matchingResults[question_id] has reuse strategy 'exact_reuse' or 'ensemble':
    * Display: "Using existing result(s)" with preview of result content
    * Skip "Fetch Context" button (context already in reuse results)
  * Else (new generation):
    * "Fetch Context" button:
      * onClick: call POST /api/v1/research-sessions/{sessionId}/context with {question_id, relevant_item_ids}
      * Store response in contextData[question_id]: {context, token_count, sources}
      * Display context preview (first 500 chars) with "...[truncated]" if longer
      * Display token count: "Token count: {token_count}"
  * "Copy Context Prompt" button:
    * onClick: copy section generation prompt to clipboard
    * Prompt includes: question, context (full or reused result), sources
    * Format from T08 section_generation.txt template
    * Show toast: "Section generation prompt copied to clipboard"
  * "Next" button → advance to Step 4
* Create Step4SectionGeneration component:
  * Get current sub-question
  * Display question text
  * Text area for user to paste LLM-generated section content (markdown)
  * Markdown preview pane:
    * Use react-markdown with remark-gfm plugin
    * Render pasted content in real-time
    * Sanitize with rehype-sanitize to prevent XSS
  * "Save Section" button:
    * onClick: extract metadata (word count, citation count using regex)
    * Call POST /api/v1/research-sessions/{sessionId}/sections with:
      * {question_id, question_text, section_content, context_data: contextData[question_id], metadata: {word_count, citation_count}}
    * Store section in sections[question_id]
    * If more sub-questions remain:
      * Increment currentSectionIndex
      * Loop back to Step 3 for next question
    * Else (all sections complete):
      * Advance to Step 5 (synthesis)
  * Progress indicator: "Section {currentSectionIndex + 1} of {total_questions}"
* Add markdown preview styling:
  * Use prose class from Tailwind Typography plugin (if available)
  * Theme-aware styling (prose-invert for dark mode)
* Patterns to apply:
  * **useCallback for API calls** - Wrap fetch calls in useCallback per patterns.md section 4.1
  * **Theme awareness** - Use semantic Tailwind classes per patterns.md section 4.2
  * **Component composition** - Build from smaller components per patterns.md section 4.2
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Step3ContextAssembly displays sub-question correctly
  * Step3ContextAssembly "Fetch Context" calls context API endpoint
  * Step3ContextAssembly displays context preview and token count
  * Step3ContextAssembly "Copy Context Prompt" copies prompt to clipboard
  * Step3ContextAssembly skips fetch button when reuse strategy selected
  * Step4SectionGeneration text area accepts markdown input
  * Step4SectionGeneration markdown preview renders correctly
  * Step4SectionGeneration extracts metadata (word count, citation count)
  * Step4SectionGeneration calls sections API endpoint on save
  * Step4SectionGeneration loops back to Step 3 for next question
  * Step4SectionGeneration advances to Step 5 when all sections complete
  * Markdown sanitization prevents XSS
* Suggested locations:
  * tests/unit/components/research/test_ManualResearchWizard_Steps34.test.tsx
* Mocking/fakes needed:
  * Mock API calls (POST context, POST sections)
  * Mock react-markdown rendering
  * Mock clipboard utility

## Acceptance criteria (checklist)

* [ ] Step 3 "Fetch Context" button calls context endpoint (R4)
* [ ] Step 3 displays context preview and token count
* [ ] Step 3 "Copy Context Prompt" copies to clipboard (R4)
* [ ] Step 3 handles reuse workflow (displays reused result instead of fetching)
* [ ] Step 4 text area accepts markdown section content (R4)
* [ ] Step 4 markdown preview renders pasted content in real-time
* [ ] Step 4 "Save Section" calls sections endpoint with metadata (R4)
* [ ] Step 4 loops through all sub-questions (R3)
* [ ] Step 4 advances to Step 5 after all sections saved (R3)
* [ ] Progress indicator shows current section number
* [ ] Markdown preview sanitized to prevent XSS (security requirement)
* [ ] Unit tests pass for Steps 3-4

## Manual verification

* Steps:
  * Complete Steps 1-2 from T18 (save research plan with 3 sub-questions)
  * Advance to Step 3 (Context Assembly)
  * Verify Q1 displayed
  * Click "Fetch Context" (assuming new generation workflow)
  * Verify API called, context preview displayed
  * Verify token count displayed (e.g., "Token count: 12,543")
  * Click "Copy Context Prompt"
  * Verify toast notification
  * Paste sample section markdown into Step 4 text area
  * Verify markdown preview renders correctly (headings, lists, citations)
  * Click "Save Section"
  * Verify API called, section saved
  * Verify loop back to Step 3 for Q2
  * Complete Q2 and Q3
  * Verify advances to Step 5 after all sections saved
* Expected results:
  * Context fetched and displayed correctly
  * Section generation works with markdown preview
  * Looping through questions works
  * All sections saved to database

## Notes

* Requirements covered: R3 (manual wizard Steps 3-4), R4 (copy prompts, paste responses, save sections), looping through sub-questions per spec
* Token count display helps user verify context within 20K-40K optimal range
* Markdown preview critical UX feature - user sees rendered output before saving
* Sanitization with rehype-sanitize prevents XSS per R6 security requirement
* Metadata extraction (word count, citation count) per T07 logic, done client-side with simple regex
