# Ticket: chunked-manual-sanitization.T04 - Settings UI for Batch Configuration

## Source

* Spec: documentation/work/chunked-manual-sanitization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add UI controls to Settings → Conversion tab for configuring batch size and context headings.
* Allow users to view and update `batch_size_headings` and `batch_context_headings` configuration.
* Save changes to `vulcanlab.config.json` via API.

## Scope

### In scope

* Two new form fields in `vulcanlab_ui/src/components/settings/conversion-tab.tsx`:
  * Input field for `batch_size_headings` (number input, default 5000).
  * Input field for `batch_context_headings` (number input, default 25).
* API integration to load and save batch configuration settings.
* Form validation (positive integers, batch_context_headings optional validation).
* Unit tests for conversion tab component with new fields.

### Out of scope

* Manual workflow page UI changes (T05, T06).
* API endpoint changes (handled in existing settings endpoints).
* Database changes (T01 already complete).

## Dependencies

* Depends on: T01 (config schema must exist)
* Unblocks: T05 (settings must be configurable before UI uses them)

## Implementation plan

* Open `vulcanlab_ui/src/components/settings/conversion-tab.tsx`.
* Add two new `FormField` components after existing `token_threshold` field:
  * Field for `batch_size_headings`:
    * Label: "Batch Size (Headings)".
    * Description: "Number of headings per batch for large file sanitization. Files exceeding this count will use batched workflow."
    * Input type: number, min: 1000, step: 1000.
    * Default value: 5000.
  * Field for `batch_context_headings`:
    * Label: "Batch Context (Headings)".
    * Description: "Maximum hierarchical context headings from previous batches to include in each prompt."
    * Input type: number, min: 1, max: 100, step: 5.
    * Default value: 25.
* Update `ConversionSettingsData` interface to include:
  * `batch_size_headings: number`.
  * `batch_context_headings: number`.
* Update form registration to include new fields via react-hook-form `register`.
* Update save handler to include new fields in PUT request to `/api/conversion/settings`.
* Add client-side validation:
  * `batch_size_headings` must be >= 1000.
  * `batch_context_headings` must be >= 1 and <= 100.
* Patterns to apply:
  * **Frontend Page Lifecycle** - Use `usePageData` to fetch settings (already used in conversion-tab).
  * **Forms** - Use `react-hook-form` with `FormField` wrapper.
  * **Component Composition** - FormField for consistent input styling.
* Deviations (if any):
  * None; follows established patterns.

## Unit tests (required)

* Add tests for:
  * Conversion tab renders with new fields:
    * Test `batch_size_headings` input field is present.
    * Test `batch_context_headings` input field is present.
    * Test default values are 5000 and 25 respectively.
  * Form validation:
    * Test `batch_size_headings` < 1000 shows validation error.
    * Test `batch_context_headings` > 100 shows validation error.
    * Test valid values pass validation.
  * Save functionality:
    * Test clicking Save with updated values calls API with correct payload.
    * Test successful save shows success message.
  * Load functionality:
    * Test initial load populates fields with values from API response.
* Suggested locations:
  * `vulcanlab_ui/src/components/settings/__tests__/conversion-tab.test.tsx`
* Mocking/fakes needed:
  * Mock fetch calls to `/api/conversion/settings` (GET and PUT).
  * Mock `useConversionSettings` context hook.

## Acceptance criteria (checklist)

* [ ] Input field for `batch_size_headings` added to conversion tab.
* [ ] Input field for `batch_context_headings` added to conversion tab.
* [ ] Fields display default values (5000 and 25) on initial load.
* [ ] Fields populate with existing config values from API on load.
* [ ] Client-side validation prevents invalid values (batch_size < 1000, context > 100).
* [ ] Save button sends updated values to `/api/conversion/settings`.
* [ ] Success message displays after successful save.
* [ ] All unit tests pass.

## Manual verification

* Steps:
  * Navigate to `/settings` page in UI.
  * Click on "Conversion" tab.
  * Verify "Batch Size (Headings)" input field is present with value 5000.
  * Verify "Batch Context (Headings)" input field is present with value 25.
  * Change batch_size_headings to 10000.
  * Change batch_context_headings to 50.
  * Click "Save Changes".
  * Verify success message appears.
  * Refresh page.
  * Verify fields still show 10000 and 50.
  * Check `vulcanlab.config.json` file directly:
    * `"batch_size_headings": 10000`.
    * `"batch_context_headings": 50`.
  * Try setting batch_size_headings to 500 (< 1000).
  * Verify validation error appears.
  * Try setting batch_context_headings to 200 (> 100).
  * Verify validation error appears.
* Expected results:
  * Fields render correctly with default and loaded values.
  * Save updates config file.
  * Validation prevents invalid values.
  * Success/error messages display appropriately.

## Notes

* Requirements covered: R10 (settings page exposes batch configuration).
* Existing API endpoint `/api/conversion/settings` (GET and PUT) should already handle arbitrary config keys under `conversion` section, so no backend changes needed.
* If API endpoint does not handle new keys, may need to update backend schema in `src/vulcanlab_api/routers/conversion.py` to include `batch_size_headings` and `batch_context_headings` in Pydantic model.
* Validation constraints: batch_size_headings should be at least 1000 to avoid creating too many tiny batches; batch_context_headings capped at 100 to avoid prompt bloat.
