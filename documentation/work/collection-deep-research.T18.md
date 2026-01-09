# Ticket: collection-deep-research.T18 - Manual Research Wizard (Steps 1-2: Planning and Result Matching)

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement first two steps of manual research wizard UI
* Enable user to generate research plan (Step 1) and check for matching results (Step 2)
* Provide clipboard integration for copying prompts and pasting LLM responses

## Phase

* Frontend

## Scope

### In scope

* ManualResearchWizard component with stepper UI (6 steps total, this ticket covers Steps 1-2)
* Step 1 (Planning): collection overview display, copy prompt button, paste response area, save plan action
* Step 2 (Result Matching): sub-question display, check matches button, match results display, strategy selection, confirm action
* Clipboard utility functions (copy to clipboard, show toast notification)
* Integration with API endpoints: PUT /api/v1/research-sessions/{session_id} (save plan), POST /api/v1/research-sessions/{session_id}/match-results

### Out of scope

* Steps 3-6 of wizard (covered in T19-T20)
* Automated research (covered in T22)
* Report viewing (covered in T23)

## Dependencies

* Depends on: T09 (API endpoints), T10 (match-results endpoint), T17 (modal)
* Unblocks: T19 (wizard Steps 3-4)

## Implementation plan

* Create vulcanlab_ui/src/components/research/ManualResearchWizard.tsx:
  * Props: {collectionId: number, sessionId: number, onComplete: () => void}
  * State: const [currentStep, setCurrentStep] = useState(1)
  * State: const [researchPlan, setResearchPlan] = useState<ResearchPlan | null>(null)
  * State: const [matchingResults, setMatchingResults] = useState<Record<string, any>>({})
  * Render stepper UI (6 steps: Planning, Result Matching, Context Assembly, Section Generation, Synthesis, Quality Evaluation)
  * Use Shadcn Stepper or Tabs component for step navigation
* Create Step1Planning component:
  * Fetch collection data to display overview (name, description, item counts by type)
  * Display collection overview in card
  * "Generate Research Plan" button:
    * onClick: copy planning prompt to clipboard (use copyToClipboard utility)
    * Prompt format from T08 research_planning.txt template
    * Show toast: "Planning prompt copied to clipboard"
  * Text area for user to paste LLM response (JSON)
  * "Save Plan" button:
    * onClick: validate JSON (parse and check ResearchPlan schema)
    * If valid: call PUT /api/v1/research-sessions/{sessionId} with {research_plan: parsedJSON}
    * Update researchPlan state
    * Advance to Step 2: setCurrentStep(2)
    * If invalid: show error toast
* Create Step2ResultMatching component:
  * Get sub_questions from researchPlan
  * State: const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  * Display current sub-question (question text, rationale)
  * "Check for Matching Results" button:
    * onClick: call POST /api/v1/research-sessions/{sessionId}/match-results with {question_id, question_text}
    * Store response in matchingResults[question_id]
    * Display matched results list (if any) with similarity scores, quality assessments, recommended strategy
  * If matches found:
    * Radio group for strategy selection: "Exact Reuse", "Partial Reuse", "Ensemble", "Generate New"
    * Preview panel showing result content if reuse selected
  * "Confirm Selection" button:
    * onClick: save matching info to session via PUT /api/v1/research-sessions/{sessionId}
    * If more questions: setCurrentQuestionIndex(index + 1)
    * If all questions done: advance to Step 3
* Create clipboard utility in vulcanlab_ui/src/lib/clipboard.ts:
  * export async function copyToClipboard(text: string): Promise<void>
  * Use navigator.clipboard.writeText(text)
  * Return promise
* Use react-hook-form for text areas and form validation
* Patterns to apply:
  * **useCallback for fetch functions** - Wrap API calls in useCallback per patterns.md section 4.1
  * **FormField wrapper** - Use react-hook-form with FormField per patterns.md section 4.1
  * **Component composition** - Build wizard from smaller components per patterns.md section 4.2
  * **Theme awareness** - Use semantic Tailwind classes per patterns.md section 4.2
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Step1Planning renders collection overview correctly
  * Step1Planning "Generate Research Plan" button copies prompt to clipboard
  * Step1Planning validates JSON on "Save Plan" click
  * Step1Planning advances to Step 2 after valid plan saved
  * Step2ResultMatching displays current sub-question
  * Step2ResultMatching calls match-results API on "Check" button click
  * Step2ResultMatching displays matched results when available
  * Step2ResultMatching allows strategy selection when matches found
  * Step2ResultMatching loops through all sub-questions
  * Step2ResultMatching advances to Step 3 after all questions processed
  * copyToClipboard utility works correctly
* Suggested locations:
  * tests/unit/components/research/test_ManualResearchWizard.test.tsx
  * tests/unit/lib/test_clipboard.test.ts
* Mocking/fakes needed:
  * Mock API fetch calls (PUT /api/v1/research-sessions, POST match-results)
  * Mock navigator.clipboard.writeText
  * Mock collection data

## Acceptance criteria (checklist)

* [ ] ManualResearchWizard component renders with 6-step stepper UI
* [ ] Step 1 displays collection overview (name, description, item counts) (R3)
* [ ] Step 1 "Generate Research Plan" button copies prompt to clipboard (R4)
* [ ] Step 1 text area accepts LLM response paste (R4)
* [ ] Step 1 validates JSON and saves plan to database (R4)
* [ ] Step 2 displays sub-question with text and rationale (R3)
* [ ] Step 2 "Check for Matching Results" calls match-results endpoint (R7, R8)
* [ ] Step 2 displays matched results with similarity and quality (R8)
* [ ] Step 2 allows user to select reuse strategy (R8)
* [ ] Step 2 loops through all sub-questions
* [ ] Clipboard utility shows toast notification after copy
* [ ] Unit tests pass for Steps 1-2

## Manual verification

* Steps:
  * Open collection page with 5+ items
  * Click "Deep Research" button, select "Manual Research"
  * Verify wizard opens with Step 1 (Planning)
  * Verify collection overview displayed (name, item counts)
  * Click "Generate Research Plan" button
  * Verify toast: "Planning prompt copied to clipboard"
  * Paste sample research plan JSON into text area
  * Click "Save Plan"
  * Verify advances to Step 2 (Result Matching)
  * Verify first sub-question displayed (Q1)
  * Click "Check for Matching Results"
  * Verify API called, matched results displayed (if any)
  * Select strategy "Exact Reuse"
  * Click "Confirm Selection"
  * Verify advances to Q2
  * Complete all questions
  * Verify advances to Step 3 (to be built in T19)
* Expected results:
  * Steps 1-2 work correctly
  * Clipboard integration works
  * API calls successful
  * State persisted

## Notes

* Requirements covered: R3 (manual wizard Steps 1-2), R4 (copy prompts, paste responses, save to database), R7-R8 (match results, user approval)
* Stepper UI provides visual progress through 6 steps
* Clipboard integration key UX feature for manual workflow
* Result matching enables reuse per spec "Result Reuse Strategy"
* FormField wrapper ensures consistent form styling per patterns.md
