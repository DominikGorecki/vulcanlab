# Ticket: manual-summarization-flow.T06 - Manual Derived Output Generation

## Source

* Spec: documentation/work/manual-summarization-flow.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add API endpoints for manual derived output generation (prompt retrieval and response submission)
* Update summary detail page to support manual mode for derived output generation
* Enable copy/paste workflow for abstract, outline, key_concepts, and chapter_summaries

## Scope

### In scope

* API: GET /{work_id}/derive/{type}/prompt - returns formatted prompt
* API: POST /{work_id}/derive/{type}/manual - parses response and stores derived output
* Update summary detail page with manual/automatic toggle for generation
* Modal UI for manual derived output: prompt display, copy button, response textarea
* Response parsing for each derived output type

### Out of scope

* Node summarization (T01-T05)
* Logging/observability (T07)

## Dependencies

* Depends on: T02 (prompt formatter), T03 (response parser patterns)
* Unblocks: T07

## Implementation plan

1. Add derived output prompt endpoint to `src/vulcanlab_api/routers/summarize.py`:
   ```python
   @router.get("/{work_id}/derive/{output_type}/prompt")
   async def get_derive_prompt(
       work_id: int,
       output_type: str,  # abstract, outline, key_concepts, chapter_summaries
       db: Session = Depends(get_db_session)
   ):
       # Validate output_type
       # Load summary_nodes for work
       # Call format_derived_output_prompt(output_type, nodes, db)
       return {"type": output_type, "prompt": prompt}
   ```

2. Add manual derived output submission endpoint:
   ```python
   @router.post("/{work_id}/derive/{output_type}/manual")
   async def submit_manual_derive(
       work_id: int,
       output_type: str,
       request: ManualDeriveRequest,  # { response: string }
       db: Session = Depends(get_db_session)
   ):
       # Parse response based on output_type
       # Store in work_summaries table
       # Return { success: bool, summary_id: int, error?: string }
   ```

3. Add response parsing for derived outputs to `response_parser.py`:
   ```python
   def parse_derived_response(output_type: str, response_text: str) -> dict:
       """Parse manual response for derived output.

       Returns content dict matching WorkSummary.content structure:
       - abstract: { "abstract": string }
       - outline: { "outline": [...] }
       - key_concepts: { "key_concepts": [...] }
       - chapter_summaries: { "chapters": [...] }
       """
   ```

4. Add Pydantic schemas:
   - DerivePromptResponse: type, prompt
   - ManualDeriveRequest: response
   - ManualDeriveResponse: success, summary_id, error

5. Create `vulcanlab_ui/src/components/summarize/manual-derive-dialog.tsx`:
   ```tsx
   interface ManualDeriveDialogProps {
     open: boolean;
     onOpenChange: (open: boolean) => void;
     workId: string;
     outputType: string;  // abstract, outline, key_concepts, chapter_summaries
     onSuccess: () => void;  // Refetch summaries
   }
   ```
   - Fetch prompt on open
   - Display prompt with copy button
   - Response textarea
   - Submit button with loading state
   - Error display for invalid responses

6. Update `vulcanlab_ui/src/app/summarize/[id]/page.tsx`:
   - Add manual/automatic toggle to DerivedOutputSection
   - If manual selected, open ManualDeriveDialog instead of calling automatic endpoint
   - Persist user's mode preference in localStorage

* Patterns to apply:
  * **Three-tier architecture**: Core parsing in response_parser, thin API layer
  * **Prompt Templates**: Load from database via format_derived_output_prompt
  * **UI Component Composition**: ManualDeriveDialog as reusable component

* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * GET /derive/{type}/prompt returns valid prompt for each output type
  * GET /derive/{type}/prompt returns 400 for invalid output type
  * POST /derive/{type}/manual parses valid response and creates WorkSummary
  * POST /derive/{type}/manual returns 400 with clear error for invalid JSON
  * parse_derived_response handles all four output types
  * parse_derived_response validates required fields per type
  * ManualDeriveDialog fetches prompt on open
  * ManualDeriveDialog copies prompt to clipboard
  * ManualDeriveDialog submits response and calls onSuccess

* Suggested locations:
  * `tests/unit/summarize/test_response_parser.py` (extend for derived)
  * `tests/unit/api/test_summarize_router.py` (add derive endpoint tests)
  * `vulcanlab_ui/src/components/summarize/__tests__/manual-derive-dialog.test.tsx`

* Mocking/fakes needed:
  * Mock database session
  * Mock summary_nodes data
  * Mock prompt_formatter.format_derived_output_prompt
  * Mock fetch API for frontend tests
  * Sample valid/invalid JSON for each output type

## Acceptance criteria (checklist)

* [ ] GET /derive/{type}/prompt works for all four types
* [ ] POST /derive/{type}/manual creates WorkSummary for valid responses
* [ ] Invalid responses return 400 with helpful error messages
* [ ] Summary detail page has manual/automatic toggle for generation
* [ ] Manual mode opens dialog with prompt and response textarea
* [ ] Copy prompt button works with success feedback
* [ ] Submit creates derived output and refreshes display
* [ ] User mode preference persists across sessions
* [ ] Unit tests pass

## Manual verification

* Steps:
  * Complete node summarization for a work (manual or automatic)
  * Navigate to /summarize/{work_id}
  * Click "Generate Abstract"
  * Toggle to "Manual" mode
  * Verify dialog shows prompt with copy button
  * Copy prompt, use external LLM to generate abstract
  * Paste response, click Submit
  * Verify abstract appears in UI
  * Repeat for outline, key_concepts, chapter_summaries

* Expected results:
  * All four derived output types work in manual mode
  * Prompts are identical to automated flow
  * Parsed content matches expected structure
  * Invalid JSON shows clear error without corrupting data

## Notes

* Requirements covered: R13, R14
* Content structure for each type is defined in work-summarization.spec.md Data Model section
* The outline type has nested structure (children array) - parser must handle recursively
* Consider adding "View Prompt" option even for automatic mode (transparency)
* localStorage key suggestion: `vulcanlab_derive_mode_preference`
