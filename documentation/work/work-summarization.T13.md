# Ticket: work-summarization.T13 - UI: Summarization Workflow Page

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create workflow page for manual LLM summarization process
* Display prompts for copying, accept pasted responses
* Show progress through multi-prompt workflow
* Handle regeneration option for existing summaries

## Phase

* Frontend

## Scope

### In scope

* New page `vulcanlab_ui/src/app/summaries/workflow/[work_id]/page.tsx`
* Call prepare endpoint and display heading preview
* Generate prompts and display them one at a time
* Text area for pasting LLM responses
* Submit response and show results
* Progress indicator (Prompt 1 of N)
* Regenerate checkbox when summaries exist

### Out of scope

* Summaries list page (T14)
* Summary viewer page (T15)
* Settings tab (T16)
* Automatic LLM integration (future)

## Dependencies

* Depends on: T10, T11 (API endpoints)
* Unblocks: T14, T15

## Implementation plan

1. Create directory `vulcanlab_ui/src/app/summaries/workflow/[work_id]/`
2. Create `page.tsx` with workflow state machine:
   - States: LOADING, PREPARE, GENERATING, PROMPT_DISPLAY, SUBMITTING, COMPLETE, ERROR
3. Implement preparation phase:
   - Call `POST /api/v1/summarize/works/{work_id}/prepare`
   - Display: work title, heading count, estimated prompts, estimated tokens
   - If `has_existing_summaries`, show checkbox: "Regenerate all summaries"
   - Button: "Generate Prompts"
4. Implement prompt generation:
   - Call `POST /api/v1/summarize/works/{work_id}/generate-prompts`
   - Store prompts array in state
   - Set currentPromptIndex = 0
5. Implement prompt display phase:
   - Show progress: "Prompt {n} of {total}"
   - Display prompt content in copyable text area (read-only)
   - "Copy to Clipboard" button
   - Large text area for pasting LLM response
   - "Submit Response" button
6. Implement response submission:
   - Call `POST /api/v1/summarize/works/{work_id}/submit-response`
   - Show result: "Saved N summaries" or errors
   - If more prompts, advance to next
   - If last prompt, show completion state
7. Implement completion phase:
   - "Summarization Complete" message
   - Show total summaries saved
   - Link to view summary: `/summaries/{work_id}`
   - Link back to corpus
8. Add error handling:
   - Display API errors clearly
   - Allow retry on transient failures
   - Show JSON parsing errors from submit response
9. Use existing UI patterns:
   - `StickyDetailHeader` for navigation
   - `Card` components for sections
   - `Button` with loading states
   - `useToast` for success/error notifications

* Patterns to apply:
  * **Page Lifecycle Pattern** - usePageData for prepare call
  * **useCallback** - Wrap handlers to avoid re-renders
  * **Component Composition** - Use Card, Button, Input from ui/
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Page renders loading state initially
  * Prepare phase displays heading count and token estimate
  * Regenerate checkbox appears when summaries exist
  * Generate button calls correct API endpoint
  * Prompt display shows current prompt content
  * Copy button copies to clipboard
  * Submit button sends response to API
  * Success message shows summaries saved count
  * Error messages display correctly
  * Completion state shows link to view summary
  * Progress indicator updates correctly
* Suggested locations:
  * `vulcanlab_ui/src/app/summaries/workflow/[work_id]/__tests__/page.test.tsx`
* Mocking/fakes needed:
  * Mock fetch for API calls
  * Mock clipboard API
  * Mock useRouter for navigation
  * Mock useToast

## Acceptance criteria (checklist)

* [ ] Page loads and calls prepare endpoint
* [ ] Heading count and estimates displayed
* [ ] Regenerate checkbox shown when applicable
* [ ] Generate Prompts button works
* [ ] Prompts displayed one at a time
* [ ] Copy to clipboard works
* [ ] Response text area accepts input
* [ ] Submit response calls API and shows results
* [ ] Progress indicator accurate
* [ ] Completion links to summary viewer
* [ ] Error states handled gracefully

## Manual verification

* Steps:
  * Navigate to `/summaries/workflow/{work_id}` for a valid work
  * View preparation info (heading count, tokens)
  * Click Generate Prompts
  * Copy first prompt to external LLM
  * Paste response into text area
  * Click Submit Response
  * Repeat for all prompts
  * Verify completion message and link
* Expected results:
  * Smooth workflow progression
  * Prompts are well-formatted and copyable
  * Responses save correctly
  * Clear feedback at each step

## Notes

* Requirements covered: R11 (manual flow UI), R10 (regenerate option)
* This is the core user-facing workflow for summarization
* State management can use useState or a reducer pattern
* Consider persisting workflow state to localStorage for resume capability (Open Question Q1)
* Text areas should be sized for large content (prompts can be 10K+ chars)
