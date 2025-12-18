# Ticket: rag-parent-chunk-enrichment.T06 - UI Component for Coverage Threshold

## Source
- Spec: documentation/work/rag-parent-chunk-enrichment.spec.md
- Patterns: documentation/patterns.md

## Goal
- Add `coverage_threshold` control to RAG Settings UI
- Enable users to configure parent-level replacement threshold from the interface
- Provide clear UI feedback and validation for threshold values

## Scope
### In scope
- Add coverage_threshold slider/input to consolidation settings section in UI
- Implement value range validation (0.0 to 1.0, step 0.05)
- Connect UI control to backend API for saving/loading
- Add helpful tooltip/description
- Use existing Shadcn/Radix UI components

### Out of scope
- Backend API changes (assume endpoint exists or create minimal required changes)
- Changes to RAG config schema (handled in T04, T05)
- Other UI components or settings
- Integration tests

## Dependencies
- Depends on: T04 (Migration Script), T05 (Update init_db.py)
- Unblocks: T07 (End-to-end Integration)

## Implementation plan
1. Locate RAG Settings UI component in `vulcanlab_ui/src/components/settings/` or `vulcanlab_ui/src/app/`
2. Identify consolidation settings section (likely in a component like `ConsolidationSettings.tsx` or `RagSettings.tsx`)
3. Add new UI control for coverage_threshold:
   - Use Shadcn Slider component (if available) or HTML range input with Tailwind styling
   - Set min=0.0, max=1.0, step=0.05, default=0.5
   - Add label: "Parent Coverage Threshold"
   - Add description/tooltip: "Percentage of parent section required before replacing fragments (0.0-1.0). Higher values require more content overlap before consolidating to parent."
4. Add state management:
   - Use React useState or form state to track slider value
   - Connect to API endpoint for saving changes
   - Load initial value from API on component mount
5. Add visual feedback:
   - Display current value (e.g., "0.50" or "50%")
   - Optional: Color-code slider (green for recommended range, yellow for extremes)
6. Implement save/cancel behavior:
   - Follow existing pattern in RAG settings UI
   - Show success/error toast on save
7. Add client-side validation:
   - Ensure value stays within 0.0-1.0 range
   - Prevent invalid inputs

Patterns to apply:
- Frontend Standards - Use Next.js App Router, TypeScript, TailwindCSS
- Component Library - Use existing Shadcn/Radix components from `vulcanlab_ui/src/components/ui/`
- State Management - Use Client Component with "use client" directive
- API Integration - Use fetch or typed client for backend calls
- Naming Conventions - camelCase for variables, PascalCase for components

Deviations (if any):
- None

## Unit tests (required)
- Add tests for:
  - Component renders with default value (0.5)
  - Component loads initial value from API
  - Slider updates state when dragged
  - Value stays within valid range (0.0-1.0)
  - Step size is 0.05
  - Save button triggers API call with correct value
  - Success toast shown on successful save
  - Error toast shown on failed save
  - Tooltip displays helpful description

- Suggested locations:
  - `vulcanlab_ui/tests/components/settings/ConsolidationSettings.test.tsx`
  - Or `vulcanlab_ui/tests/components/CoverageThresholdControl.test.tsx`

- Mocking/fakes needed:
  - Mock fetch/API client for save/load operations
  - Mock toast notifications
  - Use React Testing Library for component tests

## Acceptance criteria (checklist)
- [ ] Coverage threshold control visible in RAG Settings UI consolidation section
- [ ] Slider/input accepts values from 0.0 to 1.0 with step 0.05
- [ ] Default value is 0.5 (50%)
- [ ] Label "Parent Coverage Threshold" displayed
- [ ] Helpful description/tooltip displayed
- [ ] Current value displayed numerically or as percentage
- [ ] Control loads initial value from API on mount
- [ ] Changes saved to backend on save action
- [ ] Success feedback shown on successful save
- [ ] Error feedback shown on failed save
- [ ] All unit tests pass
- [ ] Component follows TailwindCSS styling patterns

## Manual verification
- Steps:
  1. Start frontend dev server: `cd vulcanlab_ui && npm run dev`
  2. Navigate to RAG Settings page
  3. Locate consolidation settings section
  4. Verify coverage threshold control is visible
  5. Drag slider and verify value updates
  6. Change value and save
  7. Verify API call is made (check network tab)
  8. Reload page and verify value persists
  9. Test edge cases (0.0, 1.0, invalid inputs)

- Expected results:
  - Control renders correctly with proper styling
  - Value updates smoothly as slider moves
  - Save action persists value to database
  - Reloading page shows saved value
  - Tooltip provides helpful guidance

## Notes
- Look for existing slider implementations in `vulcanlab_ui/src/components/ui/slider.tsx`
- Consolidation settings likely in `vulcanlab_ui/src/components/settings/` directory
- Check existing RAG settings components for API integration patterns
- API endpoint might be something like `PUT /api/v1/rag-config/{preset_id}`
- Payload structure: `{ "consolidation": { "coverage_threshold": 0.5 } }`
- If API endpoint doesn't exist, may need minimal backend changes:
  - Add or update endpoint in `src/vulcanlab_api/routers/` to accept coverage_threshold
  - Follow patterns.md routing standards (prefix with `/api/v1`)
- Consider adding visual indicator of what threshold means:
  - 0.0 = "Always merge fragments"
  - 0.5 = "Balanced (recommended)"
  - 1.0 = "Only merge when complete parent retrieved"
- Use existing UI patterns for consistency (button styles, toast messages, form layout)
- Follow TypeScript strict mode (no `any` types)
