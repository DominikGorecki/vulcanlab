# Ticket: eval-prompt-answer-pair-improvements.T03 - Answer Detail Page with Evaluation Display

## Source

* Spec: documentation/work/eval-prompt-answer-pair-improvements.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create dedicated detail page for answer-pairs showing complete answer data and evaluation metrics
* Display collapsible prompt context for reference
* Provide delete functionality from detail page with navigation back to prompt list
* Enable users to review all answer fields and evaluation details in comprehensive read-only view

## Scope

### In scope

* New page route: `vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/answers/[answerId]/page.tsx`
* Fetch answer detail from `GET /api/v1/eval/answers/{answerId}` endpoint
* Display answer fields: answer_x, answer_y, answer_a, answer_b, is_x_mapped_to_a, created_at
* Display evaluation metrics if evaluated: overall_score, unblinded_score, justification, dimension_scores, created_at
* Collapsible "Prompt Context" card showing parent prompt text
* StickyDetailHeader with back navigation and "Delete Answer" action button
* Delete functionality with confirmation and navigation back to prompt page
* Page follows usePageData lifecycle pattern with loading/error states

### Out of scope

* Evaluation overwrite functionality (T04)
* Editing answer or evaluation data (read-only view)
* PasteResultDialog integration (T04)
* Bulk operations

## Dependencies

* Depends on: T01 (requires GET endpoint), T02 (provides navigation from table)
* Unblocks: T04 (detail page hosts paste/overwrite button)

## Implementation plan

1. Create new file: `vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/answers/[answerId]/page.tsx`

2. Set up page component with route params:
   - Mark as "use client"
   - Use `use(params)` to unwrap Promise<{id, promptId, answerId}>
   - Import required components: StickyDetailHeader, Card, PageLoadingState, PageErrorState, ConfirmDialog
   - Import icons: MessageSquare, Calendar, Trash2, ChevronDown

3. Implement data fetching with usePageData:
   - Create `fetchAnswer` with useCallback wrapping GET `/api/v1/eval/answers/{answerId}`
   - Create `fetchPrompt` with useCallback wrapping GET `/api/v1/eval/prompts/{promptId}` for context
   - Use usePageData for both answer and prompt
   - Handle loading, error states with PageLoadingState, PageErrorState

4. Create "Prompt Context" card (collapsible):
   - Use shadcn/ui Collapsible component
   - Card header with ChevronDown icon, title "Prompt Context"
   - CollapsibleContent shows prompt text in styled container (bg-muted/50, whitespace-pre-wrap)
   - Default to collapsed state

5. Create "Answer Data" card:
   - Card with title "Answer Data"
   - Grid layout showing:
     - "Answer X" section with answer_x text
     - "Answer Y" section with answer_y text
     - "Answer A (Blind)" section with answer_a text
     - "Answer B (Blind)" section with answer_b text
     - Mapping indicator: "X mapped to: {is_x_mapped_to_a ? 'A' : 'B'}"
     - Created timestamp
   - Use scrollable containers with max-height for large text

6. Create "Evaluation Results" card (conditional):
   - Only render if answer.evaluation exists
   - Display overall_score with label
   - Display unblinded_score with explanation: "Unblinded Score (positive = X wins)"
   - Display justification in bordered container if present
   - Display dimension scores in grid or list:
     - Sort by dimension display_order (if available) or name
     - Show dimension_name: score for each
   - Display evaluation created_at timestamp

7. Implement StickyDetailHeader:
   - Title: "Answer Pair Details"
   - Subtitle: Experiment name (fetch from experiment endpoint or pass via query)
   - Back navigation to `/eval/${experimentId}/prompts/${promptId}`
   - Actions: "Delete Answer" button with Trash2 icon, variant="destructive"

8. Implement delete functionality:
   - State for delete confirmation dialog
   - handleDelete calls DELETE `/api/v1/eval/answers/{answerId}`
   - On success, navigate to `/eval/${experimentId}/prompts/${promptId}` using router.push
   - On error, show toast and keep user on page
   - Use ConfirmDialog with variant="destructive"

9. Add TypeScript interfaces:
   - AnswerDetailData matching AnswerDetailResponse from backend
   - EvaluationData for nested evaluation object
   - PromptData for prompt context

### Patterns to apply

* Page Lifecycle Pattern: Use usePageData with useCallback-wrapped fetch functions
* Component Library: StickyDetailHeader, Card, ConfirmDialog, PageLoadingState, PageErrorState
* App Router: Follow Next.js 15 App Router pattern with async params
* Theme Awareness: Use semantic Tailwind classes (text-foreground, bg-card, bg-muted)
* Props-In, Events-Out: Components receive data, communicate via callbacks

### Deviations (if any)

* None

## Unit tests (required)

* Add tests for:
  * `test_page_loads_answer_detail()`: Mock fetch, verify answer data displayed
  * `test_page_shows_evaluation_when_present()`: Mock answer with evaluation, verify evaluation card rendered
  * `test_page_hides_evaluation_when_absent()`: Mock answer without evaluation, verify evaluation card not rendered
  * `test_prompt_context_collapsible()`: Verify prompt context card can expand/collapse
  * `test_mapping_indicator_correct()`: Verify "X mapped to A/B" shows correct value based on is_x_mapped_to_a
  * `test_delete_button_calls_endpoint()`: Mock delete, click button, verify DELETE called
  * `test_delete_success_navigates_back()`: Mock successful delete, verify router.push called
  * `test_unblinded_score_displayed()`: Verify unblinded_score matches expected calculation
  * `test_dimension_scores_sorted()`: Mock evaluation with dimensions, verify display order

* Suggested locations:
  * `vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/answers/[answerId]/__tests__/page.test.tsx`

* Mocking/fakes needed:
  * Mock fetch API for GET answer, GET prompt endpoints
  * Mock DELETE endpoint
  * Mock Next.js router (useRouter, router.push)
  * Mock useToast hook
  * Sample answer data with/without evaluation
  * Sample prompt data

## Acceptance criteria (checklist)

- [ ] Page route exists at `/eval/[id]/prompts/[promptId]/answers/[answerId]/page.tsx`
- [ ] Page fetches and displays answer_x, answer_y, answer_a, answer_b
- [ ] Mapping indicator correctly shows "X mapped to: A" or "X mapped to: B"
- [ ] Created timestamp displayed for answer
- [ ] Collapsible "Prompt Context" card shows parent prompt text
- [ ] Prompt context card defaults to collapsed state
- [ ] Evaluation Results card shown only when answer has evaluation
- [ ] Overall score, unblinded score, and justification displayed when evaluated
- [ ] All dimension scores displayed in sorted order
- [ ] Evaluation created timestamp shown
- [ ] StickyDetailHeader includes "Delete Answer" button
- [ ] Delete button shows confirmation dialog before deletion
- [ ] Successful deletion navigates back to `/eval/[id]/prompts/[promptId]`
- [ ] Back button in header navigates to prompt detail page
- [ ] Loading state shown while fetching data
- [ ] Error state shown if fetch fails with retry option
- [ ] All unit tests pass

## Manual verification

* Steps:
  1. Navigate to `/eval/[id]/prompts/[promptId]` and click "View Details" on an unevaluated answer
  2. Verify detail page loads with answer data (X, Y, A, B)
  3. Verify mapping indicator shows correct A or B assignment
  4. Verify "Prompt Context" card is collapsed by default
  5. Click to expand prompt context, verify prompt text displays
  6. Verify Evaluation Results card is NOT shown (no evaluation)
  7. Navigate back and click "View Details" on an evaluated answer
  8. Verify Evaluation Results card IS shown
  9. Verify overall_score, unblinded_score, justification all display
  10. Verify all dimension scores shown with names and values
  11. Click "Delete Answer" button in header
  12. Verify confirmation dialog appears
  13. Confirm deletion and verify navigation back to prompt page
  14. Verify answer no longer appears in table
  15. Test 404 handling by manually navigating to non-existent answer ID

* Expected results:
  * All answer fields display correctly
  * Mapping indicator matches database is_x_mapped_to_a value
  * Prompt context loads and is collapsible
  * Evaluation section only appears when evaluation exists
  * Unblinded score calculation is correct (check both positive and negative cases)
  * Dimension scores are sorted by display_order
  * Delete functionality works and navigates back
  * Back navigation works correctly
  * 404 error shown for invalid answer IDs
  * No infinite rendering loops (useCallback used correctly)

## Notes

* Requirements covered: R2, R3, R4, R5, R6, R9, R10
* Unblinded score calculation: `overall_score * (1 if is_x_mapped_to_a else -1)`
* Large answer text should use max-height and scrolling to avoid page overflow
* Consider using code block styling for answer text to preserve formatting
* The existing experiment context can be fetched or inferred from URL params for header subtitle
* Delete confirmation text should match AnswersTable: "delete answer and evaluation"
