# Title: Eval Prompt Answer-Pair Improvements

## Summary

- Modify the `/eval/[id]/prompts/[id]` page to properly delete answer-pairs (not just evaluations) when the delete action is triggered
- Add a new answer-pair detail page at `/eval/[id]/prompts/[promptId]/answers/[answerId]` to view full answer data and evaluation metrics
- Enable overwriting existing evaluations via paste-result functionality with confirmation dialog
- Add "View Details" action button to the answer-pair table for navigation to detail page
- Display comprehensive evaluation summary including all dimensions, metadata, and unblinded scores on the detail page

## Problem / Context

Currently, the `/eval/[id]/prompts/[id]` page has two critical UX issues:
1. When users delete an answer-pair from the table, it only removes the evaluation record but leaves the answer-pair in the database. This is confusing because the answer-pair remains in the list without its evaluation, creating orphaned records.
2. Users cannot view the detailed contents of an answer-pair (answer_x, answer_y, answer_a, answer_b, blind mapping) or see comprehensive evaluation metrics beyond basic status. This makes it difficult to review what was actually submitted and evaluated.
3. Once an evaluation is pasted, users cannot correct mistakes or update evaluations without first deleting and re-pasting.

These issues affect researchers and evaluators using the experiment system to conduct blind A/B evaluations. The lack of visibility into answer contents and evaluation details reduces trust and makes debugging difficult. The inability to update evaluations creates friction in the evaluation workflow.

## Goals

- Enable proper deletion of answer-pairs from the prompt detail page (cascade delete evaluations)
- Provide comprehensive read-only detail view for answer-pairs showing all fields and evaluation data
- Allow overwriting existing evaluations with user confirmation
- Maintain existing blind evaluation integrity (don't expose mapping during active evaluation workflows)
- Follow VulcanLab UI patterns (App Router, DataTable, StickyDetailHeader, etc.)

## Non-goals (Strict)

- Editing answer content (answer_x, answer_y) after creation
- Editing evaluation scores inline on the detail page
- Bulk operations on answer-pairs (bulk delete, bulk re-evaluate)
- Adding new answer-pairs from the answer detail page
- Un-blinding answers before evaluation is complete (this is handled by existing data model)
- Migration of existing data (current schema already supports all required fields)

## Scope

### In scope

- Backend: Add DELETE endpoint for answer-pairs at `/api/v1/eval/answers/{answer_id}`
- Backend: Add GET endpoint for answer detail at `/api/v1/eval/answers/{answer_id}`
- Backend: Modify paste-result logic to support overwrite mode for existing evaluations
- Frontend: Update delete action in AnswersTable to call answer DELETE endpoint instead of evaluation DELETE
- Frontend: Add "View Details" button to AnswersTable actions column
- Frontend: Create new page at `/eval/[id]/prompts/[promptId]/answers/[answerId]` for answer detail view
- Frontend: Add collapsible "Prompt Context" card on detail page showing parent prompt text
- Frontend: Add "Delete Answer" action button to detail page header
- Frontend: Modify PasteResultDialog to support overwrite mode with confirmation
- Frontend: Display comprehensive evaluation summary with dimensions, scores, and metadata
- Unit tests for new backend functions (delete_answer_pair, get_answer_detail)

### Out of scope

- Integration tests (not requested)
- Modifying experiment statistics or aggregate views
- Adding edit capabilities to answer or evaluation data
- Changing the blind randomization logic (is_x_mapped_to_a remains immutable)
- Auto-evaluation workflow changes

## Requirements (Functional)

- R1: DELETE action on answer-pair in AnswersTable must delete the entire answer record (cascade deletes evaluation if exists)
- R2: Answer detail page must display answer_x, answer_y, is_x_mapped_to_a, answer_a, answer_b, and created_at
- R3: If answer has evaluation, detail page must show overall_score, justification, all dimension_scores, created_at, and unblinded_score
- R4: "View Details" button must navigate to `/eval/[id]/prompts/[promptId]/answers/[answerId]`
- R5: Answer detail page must include collapsible "Prompt Context" card displaying the parent prompt text
- R6: Answer detail page header must include "Delete Answer" action button with confirmation dialog
- R7: PasteResultDialog must detect if evaluation already exists and show confirmation before overwriting
- R8: Overwriting evaluation must replace all fields (overall_score, justification, dimension_scores)
- R9: Answer detail page must be read-only (no inline editing)
- R10: Navigation from answer detail page must return to prompt detail page at `/eval/[id]/prompts/[promptId]`

## Requirements (Non-functional)

- Performance:
  - Answer detail page load time under 500ms for typical answer sizes
  - DELETE operation completes within 200ms
  - No N+1 queries when loading answer with evaluation and dimensions

- Reliability:
  - CASCADE delete ensures no orphaned evaluation records
  - Transaction rollback if answer deletion fails
  - Proper 404 handling for non-existent answer IDs

- Security / Privacy:
  - No authorization changes required (same experiment-level access)
  - Maintain existing CORS and API key policies
  - No sensitive data exposure beyond existing endpoints

- Observability:
  - Log answer deletions with answer_id and prompt_id
  - Log evaluation overwrites with evaluation_id
  - Return descriptive error messages for validation failures

## Proposed Solution (High-level)

- Backend (Core Module):
  - Add `delete_answer_pair(session, answer_id)` function in `src/vulcanlab/eval/answers.py`
  - Function queries answer, verifies existence, deletes record (CASCADE handles evaluation)
  - Reuse existing `get_answer_by_id()` for detail retrieval
  - Modify `submit_evaluation()` to support upsert mode (update if evaluation exists)

- Backend (API Layer):
  - Add `DELETE /api/v1/eval/answers/{answer_id}` endpoint in `src/vulcanlab_api/routers/eval.py`
  - Add `GET /api/v1/eval/answers/{answer_id}` endpoint returning AnswerResponse with optional evaluation
  - Modify `POST /api/v1/eval/answers/{answer_id}/evaluations` to accept optional `overwrite` query param

- Frontend:
  - Update AnswersTable delete handler to call answer DELETE endpoint (not evaluation DELETE)
  - Add "View Details" button to AnswersTable actions column with Eye icon
  - Create `/eval/[id]/prompts/[promptId]/answers/[answerId]/page.tsx` with:
    - StickyDetailHeader with back navigation
    - Card showing answer data (X, Y, A, B, mapping indicator)
    - Card showing evaluation metrics if evaluated (scores, dimensions, metadata)
    - "Paste/Overwrite Result" button that opens PasteResultDialog
  - Enhance PasteResultDialog to check for existing evaluation and show confirmation if overwriting

## Interfaces / APIs / Contracts

### New Backend Endpoints

**DELETE /api/v1/eval/answers/{answer_id}**
- Returns: 204 No Content on success
- Errors: 404 if answer not found, 500 on database error

**GET /api/v1/eval/answers/{answer_id}**
- Returns: AnswerDetailResponse (extends AnswerResponse with optional evaluation)
- Errors: 404 if answer not found

**AnswerDetailResponse Schema** (new):
```typescript
{
  id: number
  prompt_id: number
  answer_x: string
  answer_y: string
  is_x_mapped_to_a: boolean
  answer_a: string
  answer_b: string
  created_at: datetime
  updated_at: datetime
  evaluation?: {
    id: number
    overall_score: number
    unblinded_score: number  // computed: overall_score * (1 if is_x_mapped_to_a else -1)
    justification: string | null
    dimension_results: Array<{dimension_name: string, score: number}>
    created_at: datetime
  }
}
```

### Modified Endpoints

**POST /api/v1/eval/answers/{answer_id}/evaluations?overwrite=true**
- Query param `overwrite` (optional, default: false)
- If overwrite=true and evaluation exists, UPDATE instead of INSERT
- Returns: EvaluationResponse

## Data Model / Storage

No schema changes required. Existing tables support all functionality:

- `experiment_answers` table has all required fields (answer_x, answer_y, is_x_mapped_to_a)
- `experiment_evaluations` table has CASCADE DELETE on answer_id foreign key
- `experiment_dimension_results` table has CASCADE DELETE on evaluation_id foreign key

Deletion cascade chain: Answer -> Evaluation -> DimensionResults

## UX / Workflows

### Workflow 1: Delete Answer-Pair
1. User navigates to `/eval/[id]/prompts/[promptId]`
2. User clicks trash icon in answer-pair row
3. ConfirmDialog appears: "Delete answer-pair? This will permanently delete the answer and any associated evaluation."
4. User confirms
5. Frontend calls DELETE `/api/v1/eval/answers/{answer_id}`
6. Table refreshes, answer-pair is removed

### Workflow 2: View Answer-Pair Details
1. User navigates to `/eval/[id]/prompts/[promptId]`
2. User clicks "View Details" button in answer-pair row
3. Browser navigates to `/eval/[id]/prompts/[promptId]/answers/[answerId]`
4. Page displays:
   - Header with back button to prompt detail and "Delete Answer" action
   - Collapsible "Prompt Context" card showing parent prompt text
   - "Answer Data" card showing X, Y, A, B, mapping indicator
   - "Evaluation Results" card (if evaluated) showing scores, dimensions, metadata
   - "Paste/Overwrite Result" button

### Workflow 3: Overwrite Existing Evaluation
1. User on answer detail page with existing evaluation
2. User clicks "Paste/Overwrite Result" button
3. PasteResultDialog opens, detects existing evaluation
4. Dialog shows: "This answer already has an evaluation. Overwrite?"
5. User confirms, pastes new evaluation JSON
6. Frontend calls POST with `overwrite=true` query param
7. Evaluation updates, page refreshes with new data

## Testing Plan

### Unit tests

- `test_delete_answer_pair()`: Verify answer deletion cascades to evaluation and dimensions
- `test_delete_answer_pair_not_found()`: Verify 404 error for non-existent answer
- `test_get_answer_detail_with_evaluation()`: Verify full answer detail retrieval with evaluation joined
- `test_get_answer_detail_without_evaluation()`: Verify answer detail retrieval when not evaluated
- `test_submit_evaluation_overwrite()`: Verify overwrite mode updates existing evaluation
- `test_submit_evaluation_overwrite_forbidden()`: Verify overwrite=false rejects duplicate evaluation

### Integration tests

- Not applicable (unit tests sufficient per patterns.md)

### Manual test plan

- Create experiment with prompt and 3 answer-pairs (1 evaluated, 2 not evaluated)
- Delete unevaluated answer-pair from table, verify it disappears from table
- Delete evaluated answer-pair from table, verify both answer and evaluation are removed from database
- Click "View Details" on remaining answer-pair, verify navigation to detail page
- Verify detail page header shows "Delete Answer" button and back navigation
- Verify "Prompt Context" card is collapsible and shows parent prompt text
- Verify detail page shows correct answer_x, answer_y, answer_a, answer_b
- Verify mapping indicator correctly shows is_x_mapped_to_a status
- Click "Paste Result" on unevaluated answer, paste evaluation, verify success
- Click "Paste/Overwrite Result" on evaluated answer, verify confirmation dialog appears
- Confirm overwrite, paste new evaluation, verify evaluation updates with new scores
- Verify evaluation metadata shows created_at and unblinded_score correctly
- Click "Delete Answer" button on detail page, confirm deletion, verify navigation back to prompt page
- Navigate back to prompt detail page, verify answer-pair still exists with updated evaluation status
- Test 404 handling by manually navigating to non-existent answer ID

## Acceptance Criteria (Checklist)

- [ ] DELETE `/api/v1/eval/answers/{answer_id}` endpoint implemented and cascade deletes evaluation
- [ ] GET `/api/v1/eval/answers/{answer_id}` endpoint returns answer with optional evaluation data
- [ ] `delete_answer_pair()` function added to `src/vulcanlab/eval/answers.py`
- [ ] AnswersTable delete action calls answer DELETE endpoint (not evaluation DELETE)
- [ ] "View Details" button added to AnswersTable actions column
- [ ] Answer detail page created at `/eval/[id]/prompts/[promptId]/answers/[answerId]/page.tsx`
- [ ] Detail page includes collapsible "Prompt Context" card showing parent prompt text
- [ ] Detail page header includes "Delete Answer" action button with confirmation dialog
- [ ] Detail page displays all answer fields (X, Y, A, B, mapping, timestamps)
- [ ] Detail page displays evaluation metrics when answer is evaluated (scores, dimensions, metadata, unblinded score)
- [ ] PasteResultDialog supports overwrite mode with confirmation
- [ ] Overwrite confirmation dialog warns user before replacing existing evaluation
- [ ] Unit tests pass for delete_answer_pair, get_answer_detail, and evaluation overwrite
- [ ] Manual testing confirms all workflows function correctly
- [ ] No orphaned evaluation records remain after answer deletion
- [ ] Navigation between pages works correctly (back to prompt detail)
- [ ] Delete from detail page navigates back to prompt detail page after success

## Rollout / Migration Plan

Not applicable. No database migrations required. Changes are additive (new endpoints) or behavioral (delete target change).

## Risks and Alternatives

### Risks

- Risk: Users accidentally delete answer-pairs thinking they're only deleting evaluation
  - Mitigation: Clear confirmation dialog text specifying "delete answer and evaluation"

- Risk: Evaluation overwrite could cause data loss if user pastes wrong content
  - Mitigation: Confirmation dialog warns before overwrite; consider audit log in future

- Risk: Exposing unblinded score (X vs Y winner) on detail page might bias future evaluations
  - Mitigation: Detail page is post-evaluation review tool; blind evaluation already complete

### Alternatives considered

- Alternative 1: Keep current delete behavior (evaluation only) and add separate "Delete Answer" action
  - Rejected: Adds UI complexity; users expect delete to remove the answer-pair

- Alternative 2: Use modal/dialog for answer detail instead of separate page
  - Rejected: Detail page has significant content (answer text can be large); dedicated page provides better UX

- Alternative 3: Allow inline editing of evaluations on detail page
  - Rejected: Violates evaluation integrity; prefer explicit paste/overwrite workflow

## Patterns and Standards Alignment (from documentation/patterns.md)

### Patterns applied

- **Three-tier Architecture**: Core logic in `src/vulcanlab/eval/answers.py`, API in `src/vulcanlab_api/routers/eval.py`, UI in `vulcanlab_ui/src/app/eval`
- **Session Management**: Database sessions passed explicitly to `delete_answer_pair()` and `get_answer_by_id()`
- **API Versioning**: New endpoints use `/api/v1` prefix
- **Error Handling**: Raise specific exceptions (ValueError for not found), let global handler catch 500 errors
- **App Router**: New page follows Next.js App Router pattern in `vulcanlab_ui/src/app/eval/[id]/prompts/[promptId]/answers/[answerId]/page.tsx`
- **Component Library**: Use StickyDetailHeader, Card, DataTable, ConfirmDialog from shared components
- **Page Lifecycle Pattern**: Use `usePageData` hook with `useCallback`-wrapped fetch functions to avoid infinite loops
- **Props-In, Events-Out**: Components receive data via props, communicate via callbacks
- **Theme Awareness**: All UI components use Tailwind semantic classes (text-foreground, bg-card)

### Deviations (if any)

- None. Spec follows all established patterns.

## Implementation Notes (Non-binding)

- Reuse existing `get_answer_by_id()` for detail retrieval; add LEFT JOIN to load evaluation if exists
- Consider adding `unblinded_score` as computed property on evaluation response (overall_score * mapping direction)
- The "View Details" button can use Eye icon from lucide-react
- Answer detail page can show blind mapping as: "X mapped to: {is_x_mapped_to_a ? 'A' : 'B'}"
- For large answer text, consider using scrollable containers with max-height
- "Prompt Context" card should use Collapsible component from shadcn/ui with ChevronDown icon
- Prompt text in context card should be read-only and styled consistently with other prompt displays
- Evaluation dimension results should be displayed in order by dimension display_order
- PasteResultDialog already exists; modify to check for existing evaluation on mount
- Delete confirmation should use existing ConfirmDialog component with variant="destructive"
- Delete button on detail page header should use Trash2 icon and variant="destructive"
- After delete from detail page, navigate using `router.push()` to parent prompt page

## Open Questions

None. All design decisions have been confirmed:
- Audit log for evaluation overwrites: Not required
- Prompt context on detail page: Yes, include collapsible "Prompt Context" card
- Delete button on detail page: Yes, add to header actions for consistency
