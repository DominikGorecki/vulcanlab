# Ticket: work-summarization.T13 - Summarize Settings UI Tab

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create Settings tab for configuring summarization salience weights and thresholds
* Provide form inputs for all configurable parameters
* Support save and reset functionality

## Phase

* Frontend

## Scope

### In scope

* vulcanlab_ui/src/components/settings/summarize-tab.tsx component
* Form inputs for all salience weights and thresholds
* Input validation (ranges, numeric types)
* Save button to persist settings
* Reset to defaults functionality
* Loading and error states
* Integration with Settings page tab structure

### Out of scope

* Summarize list page (T14)
* Work summary detail page (T15)
* Corpus page integration (T16)

## Dependencies

* Depends on: T12 (settings API endpoints)
* Unblocks: none (parallel with T14-T16)

## Implementation plan

1. Create vulcanlab_ui/src/components/settings/summarize-tab.tsx
2. Define TypeScript interfaces:
   - `SummarizeSettings` matching API response
3. Implement data fetching:
   - Use usePageData hook with useCallback-wrapped fetch
   - GET /api/v1/settings/summarize
4. Create form using react-hook-form:
   - h1_always_summarize: checkbox
   - h2_top_percent: number input (0-100)
   - h3_salience_threshold: number input (0.0-1.0, step 0.1)
   - h4_salience_threshold: number input (0.0-1.0, step 0.1)
   - definition_density_weight: number input (0.0-1.0, step 0.05)
   - list_density_weight: number input (0.0-1.0, step 0.05)
   - keyphrase_novelty_weight: number input (0.0-1.0, step 0.05)
   - location_prior_weight: number input (0.0-1.0, step 0.05)
   - heading_depth_weight: number input (0.0-1.0, step 0.05)
5. Add form sections:
   - "Node Selection Thresholds" section for H1-H4 settings
   - "Salience Weights" section for weight inputs
   - Include helper text explaining each setting
6. Implement save handler:
   - PUT /api/v1/settings/summarize
   - Show success toast on save
   - Show error toast on failure
7. Implement reset handler:
   - Confirm dialog before reset
   - PUT with default values
8. Add loading state using PageLoadingState
9. Add error state using PageErrorState
10. Export and add tab to Settings page tabs array
* Patterns to apply:
  * usePageData hook with useCallback-wrapped fetch
  * react-hook-form for form handling
  * FormField wrapper for inputs
  * Theme-aware styling with Tailwind semantic classes
  * Toast notifications for save/error feedback
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Component renders with loading state initially
  * Component displays form after data loads
  * Form inputs have correct initial values from API
  * h2_top_percent validates range 0-100
  * Threshold inputs validate range 0.0-1.0
  * Weight inputs validate range 0.0-1.0
  * Save button calls PUT endpoint with form values
  * Success toast shown on successful save
  * Error toast shown on failed save
  * Reset button shows confirmation dialog
  * Reset restores default values
* Suggested locations:
  * vulcanlab_ui/src/components/settings/__tests__/summarize-tab.test.tsx
* Mocking/fakes needed:
  * Mock fetch for API calls
  * Mock toast notifications

## Acceptance criteria (checklist)

* [ ] Tab renders in Settings page
* [ ] All settings fields displayed with current values
* [ ] Form validation prevents invalid values
* [ ] Save persists settings to API
* [ ] Success/error feedback shown via toast
* [ ] Reset to defaults with confirmation
* [ ] Loading and error states handled
* [ ] Theme-aware styling (dark/light mode)
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Navigate to Settings page
  2. Click "Summarize" tab
  3. Modify h3_salience_threshold value
  4. Click Save
  5. Refresh page and verify value persisted
  6. Click Reset to Defaults
  7. Confirm and verify values reset
* Expected results:
  * Settings load and display correctly
  * Changes persist across page refresh
  * Reset restores default values

## Notes

* Requirements covered: R4
* Helper text should explain what each setting does (e.g., "Higher values mean fewer H3 sections are summarized")
* Consider grouping weights with visual indicator that they should sum to 1.0 (or note that they are relative weights)
* The tab should match styling of existing settings tabs (conversion-tab.tsx as reference)
