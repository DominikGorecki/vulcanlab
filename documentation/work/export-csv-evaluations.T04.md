# Ticket: export-csv-evaluations.T04 - UI Layer: "Export CSV" Button Integration

## Source

* Spec: documentation/work/export-csv-evaluations.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add an "Export CSV" button to the experiment detail page.
* Implement the file download trigger and user notifications (toasts).
* Ensure the button is properly placed in the sticky header.

## Scope

### In scope

* Frontend: Update `vulcanlab_ui/src/app/eval/[id]/page.tsx`.
* Component: Adding a new `Button` to the `actions` prop of `StickyDetailHeader`.
* Logic: Implementation of `handleExportCSV` to trigger the browser download.
* UX: Adding a loading state and success/error toast notifications.

### Out of scope

* Backend implementation (handled in T01-T03).

## Dependencies

* Depends on: export-csv-evaluations.T03
* Unblocks: none

## Implementation plan

* Import `Download` (or similar) icon from `lucide-react`.
* Locate the `actions` prop in the `StickyDetailHeader` component within `vulcanlab_ui/src/app/eval/[id]/page.tsx`.
* Add a new `Button` component with the label "Export CSV".
* Place it to the right of the "Add Prompt" (or "Add Answers" if applicable) area, or within the `actions` list next to "Delete".
* Implement a `handleExportCSV` function that:
    * Sets a loading state.
    * Uses `window.location.href` or a dynamic `<a>` tag to trigger the API download.
    * Displays a success toast when triggered.
    * Displays an error toast if the request fails (optional, as browser downloads often handle their own failures).
* Patterns to apply:
    * Frontend Page Lifecycle - Using standard UI patterns for actions.

## Unit tests (required)

* Add tests for:
    * "Export CSV" button renders correctly on the experiment detail page.
    * Clicking the button calls the expected API endpoint URL.
* Suggested locations:
    * `vulcanlab_ui/src/app/eval/[id]/page.test.tsx` (if tests exist).
* Mocking/fakes needed:
    * Mock `useToast` and `fetch` if needed.

## Acceptance criteria (checklist)

* [ ] "Export CSV" button is visible in the `StickyDetailHeader`.
* [ ] Clicking the button initiates the file download.
* [ ] The UI remains responsive during the export trigger.
* [ ] Toast notifications provide feedback to the user.

## Manual verification

* Steps:
    * Open the application in a browser.
    * Navigate to an experiment detail page (`/eval/[id]`).
    * Click the "Export CSV" button.
* Expected results:
    * A CSV file is downloaded.
    * A success toast notification appears.

## Notes

* Requirements covered: Not explicitly enumerated in spec (UI integration).
* Note: The user requested the button to be placed "right of 'Add Answers'". If "Add Answers" is not on this page, place it alongside the existing "Delete" button in the header.

