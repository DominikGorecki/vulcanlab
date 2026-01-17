# Ticket: work-summarization.T16 - UI: Summarize Settings Tab

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add "Summarize" tab to Settings page for configuring summarization parameters
* Allow editing of all summarization settings (thresholds, RRF/MMR params, token budgets)
* Save settings via API

## Phase

* Frontend

## Scope

### In scope

* New tab component `vulcanlab_ui/src/components/settings/summarize-tab.tsx`
* Register tab in Settings page
* Form for all summarization settings
* Save functionality via PUT endpoint

### Out of scope

* Prompt template editing (existing Templates tab handles this)
* Per-work settings overrides (use global settings only)

## Dependencies

* Depends on: T11 (settings API endpoints)
* Unblocks: None (final UI ticket)

## Implementation plan

1. Create `vulcanlab_ui/src/components/settings/summarize-tab.tsx`
2. Define settings form fields grouped by category:
   - **Heading Selection**:
     - min_heading_word_count (input, number)
     - max_total_heading_words (input, number)
   - **Search & Ranking**:
     - dense_top_k (input, number)
     - lexical_top_k (input, number)
     - rrf_k (input, number)
     - rrf_top_k (input, number)
     - mmr_lambda (input, number, step=0.1)
     - mmr_top_n (input, number)
   - **Token Budget**:
     - max_llm_calls (input, number)
     - max_tokens_per_call (input, number)
     - tokens_per_word (input, number, step=0.05)
   - **Pruning Minimums**:
     - h1_h2_min_chunks (input, number)
     - h3_min_chunks (input, number)
3. Implement data fetching:
   - Use `useCallback` with fetch from `GET /api/v1/summarize/settings`
   - Populate form with current values
4. Use react-hook-form for form state:
   - Register all fields
   - Add validation (positive integers, lambda 0-1, etc.)
5. Implement save handler:
   - Collect form values
   - PUT to `/api/v1/summarize/settings`
   - Show success/error toast
6. Add field labels and descriptions:
   - Each field should have clear label
   - Consider helper text explaining what each setting does
7. Update `vulcanlab_ui/src/app/settings/page.tsx`:
   - Import SummarizeTab component
   - Add "Summarize" to TabsList
   - Add TabsContent for summarize
   - Update defaultTab check to include "summarize"
8. Style consistently with other settings tabs:
   - Use Card component
   - Use FormField wrapper
   - Use consistent button styling

* Patterns to apply:
  * **Forms** - react-hook-form with FormField wrapper
  * **useCallback** - Wrap fetch functions
  * **Settings in database** - Load/save via API
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Tab renders with all form fields
  * Form populates with fetched settings
  * Form validation prevents invalid values
  * Save button calls PUT endpoint with form data
  * Success toast shown on save
  * Error handling for API failures
  * Lambda validation (must be 0-1)
  * Integer validation for count fields
* Suggested locations:
  * `vulcanlab_ui/src/components/settings/__tests__/summarize-tab.test.tsx`
* Mocking/fakes needed:
  * Mock fetch for get/put settings
  * Mock useToast
  * Mock react-hook-form if needed

## Acceptance criteria (checklist)

* [ ] "Summarize" tab appears in Settings page
* [ ] All settings fields displayed with current values
* [ ] Fields have appropriate labels and grouping
* [ ] Form validation works (positive numbers, lambda range)
* [ ] Save button persists changes via API
* [ ] Success feedback shown after save
* [ ] Error feedback shown on failure
* [ ] Unit tests pass

## Manual verification

* Steps:
  * Navigate to Settings page
  * Click on "Summarize" tab
  * Verify all settings are displayed with current values
  * Modify a setting (e.g., change mmr_lambda to 0.8)
  * Click Save
  * Refresh page
  * Verify setting persisted
  * Try invalid value (e.g., negative number)
  * Verify validation prevents save
* Expected results:
  * Settings load correctly
  * Changes save and persist
  * Validation prevents invalid input

## Notes

* Requirements covered: Settings UI configuration
* Field groupings make the many settings more manageable
* Consider adding "Reset to Defaults" button (optional)
* mmr_lambda is the only float that needs decimal input; others are integers
* Help text examples:
  - min_heading_word_count: "Minimum words in heading content to include in summarization"
  - mmr_lambda: "Balance between relevance (1.0) and diversity (0.0)"
