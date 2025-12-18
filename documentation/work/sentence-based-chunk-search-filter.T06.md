# Ticket: sentence-based-chunk-search-filter.T06 - Add Sentence Filter Controls to RAG Settings UI

## Source
- Spec: documentation/work/sentence-based-chunk-search-filter.spec.md
- Patterns: documentation/patterns.md

## Goal
- Add UI controls for min_sentence_filter_enabled and min_sentence_count in RAG Settings page
- Display controls in retrieval section
- Validate input and save to RAG config via API

## Scope
### In scope
- Update vulcanlab_ui/src/components/settings/rag-config-tab.tsx (or equivalent RAG settings component)
- Add checkbox for "Enable minimum sentence filter" (min_sentence_filter_enabled)
- Add number input for "Minimum sentences" (min_sentence_count)
- Disable number input when checkbox is unchecked
- Validate min_sentence_count >= 1 on client side
- Update TypeScript types in vulcanlab_ui/src/types/rag-config.ts

### Out of scope
- Backend API changes (already handled in T03)
- Real-time preview of filter impact
- Migration UI

## Dependencies
- Depends on: T03 (API supports new fields)
- Unblocks: End-to-end user testing

## Implementation plan
- Locate RAG settings component in vulcanlab_ui/src/components/settings/rag-config-tab.tsx
- Review existing UI structure for retrieval section
- Add TypeScript interface updates in vulcanlab_ui/src/types/rag-config.ts:
  ```typescript
  retrieval: {
    min_sentence_filter_enabled: boolean;
    min_sentence_count: number;
    // ... existing fields
  }
  ```
- In the retrieval section of the form, add:
  - Checkbox component for min_sentence_filter_enabled
    - Label: "Enable minimum sentence filter"
    - Description: "Only search chunks with at least N sentences"
  - Number input component for min_sentence_count
    - Label: "Minimum sentences"
    - Min value: 1
    - Default: 5
    - Disabled when checkbox unchecked
- Add client-side validation: min_sentence_count must be >= 1
- Hook up to existing form state management (likely React Hook Form or similar)
- Test form submission updates RAG config via API
- Patterns to apply:
  - Frontend: Next.js App Router, React/TypeScript
  - Components: Use Shadcn/Radix UI components (checkbox, input from ui folder)
  - State management: Follow existing patterns in RAG settings page
- Deviations (if any):
  - None

## Unit tests (required)
- Add tests for:
  - Checkbox toggles min_sentence_filter_enabled value
  - Number input disabled when checkbox unchecked
  - Number input enabled when checkbox checked
  - Number input rejects values < 1
  - Form submission includes new fields in payload
  - Default values loaded correctly from API (false, 5)
  - Updated values saved successfully via API
- Suggested locations:
  - vulcanlab_ui/src/components/settings/__tests__/rag-config-tab.test.tsx (create if doesn't exist)
- Mocking/fakes needed:
  - Mock API fetch/update calls
  - Mock form context if using React Hook Form

## Acceptance criteria (checklist)
- [ ] TypeScript types updated to include new fields
- [ ] Checkbox for "Enable minimum sentence filter" rendered in UI
- [ ] Number input for "Minimum sentences" rendered in UI
- [ ] Number input disabled when checkbox unchecked
- [ ] Client-side validation enforces min_sentence_count >= 1
- [ ] Form loads default values from API (false, 5)
- [ ] Form saves updated values via API PUT request
- [ ] UI tests pass for new components
- [ ] UI follows existing Shadcn/Radix patterns

## Manual verification
- Steps:
  1. Start dev server: npm run dev in vulcanlab_ui
  2. Navigate to Settings > RAG Settings
  3. Locate retrieval section
  4. Verify checkbox "Enable minimum sentence filter" is present and unchecked
  5. Verify number input "Minimum sentences" is present, disabled, shows value 5
  6. Check the checkbox
  7. Verify number input becomes enabled
  8. Change number input to 10
  9. Save the form
  10. Verify API PUT request sent with correct payload (check network tab)
  11. Refresh page
  12. Verify values persist (checkbox checked, value 10)
  13. Try setting value to 0
  14. Verify validation error displayed
- Expected results:
  - Checkbox and number input render correctly
  - Number input enabled/disabled based on checkbox state
  - Values save and persist correctly
  - Validation prevents invalid values
  - UI matches existing design patterns

## Notes
- Follow existing RAG settings UI patterns for consistency
- Use existing Shadcn/Radix components from vulcanlab_ui/src/components/ui/
- The API endpoint is likely /api/v1/rag-config or similar (check existing implementation)
- Consider adding a tooltip or help text explaining what the filter does
