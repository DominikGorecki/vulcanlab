# Ticket: rag-query-manual-result-model-tracking.T03 - Frontend Copy/Paste Button Behavior & Model Selection

## Source

* Spec: documentation/work/rag-query-manual-result-model-tracking.spec.md
* Patterns: documentation/patterns.md

## Goal

* Remove automatic modal opening after copying prompt
* Add explicit "Paste Response" button next to "Copy Prompt"
* Add model selection dropdown to paste modal with "Add New..." option
* Implement inline model name input for adding new models
* Complete first vertical slice: user can copy prompt, manually paste response with model selection

## Scope

### In scope

* Modify `vulcanlab_ui/src/app/rag/[id]/page.tsx`:
  * Remove `setCopyDialogOpen(true)` from `handleCopyPrompt` function
  * Add "Paste Response" button to action bar (bottom right, next to "Copy Prompt")
  * Add model selection dropdown to paste modal (Dialog component)
  * Add "Add New..." option in dropdown
  * Show inline text input when "Add New..." selected
  * Fetch models from `GET /api/v1/rag/result-models` API
  * Call `POST /api/v1/rag/result-models` when creating new model
  * Submit model_id or new_model_name with manual result POST
* Unit tests for component behavior (optional - focus on manual verification)

### Out of scope

* Results list and detail page changes (covered in T04, T05)
* Automatic result generation model capture (backend covered in T02, no frontend changes needed)
* Model editing or deletion
* Model validation beyond empty check

## Dependencies

* Depends on: T02 (API endpoints must exist)
* Unblocks: T04, T05

## Implementation plan

1. Modify `handleCopyPrompt` function in `vulcanlab_ui/src/app/rag/[id]/page.tsx`:
   * Remove line `setCopyDialogOpen(true)` (around line 201)
   * Keep clipboard copy and success feedback

2. Add "Paste Response" button to bottom action bar:
   * Locate the action bar div (around line 467-506)
   * Add new button next to "Copy Prompt" button:
     ```tsx
     <Button
       onClick={() => setCopyDialogOpen(true)}
       variant="outline"
       disabled={running}
       className="gap-2"
     >
       <ClipboardPaste className="h-4 w-4" />
       Paste Response
     </Button>
     ```
   * Import `ClipboardPaste` icon from lucide-react

3. Add state for model selection:
   * Add state: `const [models, setModels] = useState<Array<{id: number, name: string}>>([])`
   * Add state: `const [selectedModelId, setSelectedModelId] = useState<number | null>(null)`
   * Add state: `const [showNewModelInput, setShowNewModelInput] = useState(false)`
   * Add state: `const [newModelName, setNewModelName] = useState("")`

4. Fetch models when paste dialog opens:
   * Create `fetchModels` function:
     ```tsx
     const fetchModels = useCallback(async () => {
       try {
         const response = await fetch(`${API_BASE_URL}/api/v1/rag/result-models`);
         if (!response.ok) throw new Error("Failed to load models");
         const data = await response.json();
         setModels(data.models || []);
       } catch (err) {
         console.error("Failed to fetch models:", err);
         setOperationError("Failed to load models");
       }
     }, []);
     ```
   * Call `fetchModels()` when `copyDialogOpen` becomes true (use useEffect)

5. Add model selection dropdown to paste dialog (around line 527-568):
   * After DialogDescription, add:
     ```tsx
     <div className="py-3">
       <Label htmlFor="model-select" className="text-sm font-medium mb-2">
         Model (optional)
       </Label>
       <Select
         value={showNewModelInput ? "new" : (selectedModelId?.toString() || "")}
         onValueChange={(value) => {
           if (value === "new") {
             setShowNewModelInput(true);
             setSelectedModelId(null);
           } else {
             setShowNewModelInput(false);
             setSelectedModelId(value ? parseInt(value, 10) : null);
           }
         }}
       >
         <SelectTrigger id="model-select" className="w-full">
           <SelectValue placeholder="Select a model (optional)" />
         </SelectTrigger>
         <SelectContent>
           <SelectItem value="">Unspecified</SelectItem>
           {models.map(model => (
             <SelectItem key={model.id} value={model.id.toString()}>
               {model.name}
             </SelectItem>
           ))}
           <SelectItem value="new">Add New...</SelectItem>
         </SelectContent>
       </Select>
       {showNewModelInput && (
         <Input
           value={newModelName}
           onChange={(e) => setNewModelName(e.target.value)}
           placeholder="Enter model name (e.g., gpt-4-turbo)"
           className="mt-2"
         />
       )}
     </div>
     ```
   * Import `Input` from "@/components/ui/input" if not already

6. Modify `handleSaveManualResponse` function:
   * Before saving, check if `showNewModelInput` is true:
     - If true and `newModelName` is not empty:
       * Call `POST /api/v1/rag/result-models` with `{name: newModelName}`
       * On success, get new model id from response
       * Use that model_id in the manual result POST
     - Else if `selectedModelId` is not null:
       * Use selectedModelId in the manual result POST
     - Else:
       * Send neither model_id nor new_model_name (NULL)
   * Update API call body to include `model_id` or `new_model_name`
   * Handle model creation errors (409 Conflict if duplicate)

7. Reset model state when dialog closes:
   * In dialog `onOpenChange` handler, reset: `setSelectedModelId(null)`, `setShowNewModelInput(false)`, `setNewModelName("")`

8. Add loading state for model fetching:
   * Add state: `const [modelsLoading, setModelsLoading] = useState(false)`
   * Show loading indicator in dropdown if `modelsLoading` is true

* Patterns to apply:
  * **Frontend Component Patterns**: Use existing Shadcn/Radix components (Dialog, Select, Button, Input)
  * **State Management**: Client component with useState for form state
  * **Critical Rule - Avoid Infinite Loops**: Wrap `fetchModels` in `useCallback` to prevent infinite re-renders
  * **Props-In, Events-Out**: Components communicate via callbacks
  * **Theme Awareness**: Use Tailwind semantic classes for dark/light mode support

* Deviations (if any):
  * None - follows established frontend patterns

## Unit tests (required)

* Add tests for:
  * "Copy Prompt" button copies to clipboard without opening modal
  * "Paste Response" button opens paste modal
  * Model dropdown fetches and displays models when dialog opens
  * Selecting "Add New..." shows inline input field
  * Typing in inline input updates newModelName state
  * Selecting existing model from dropdown sets selectedModelId
  * Save with new model name calls POST /result-models then POST /manual
  * Save with existing model id calls POST /manual with model_id
  * Save with no model selection calls POST /manual without model_id or new_model_name
  * Model creation error (409) displays error message
  * Dialog close resets model selection state

* Suggested locations:
  * `vulcanlab_ui/src/app/rag/[id]/__tests__/page.test.tsx` (if following testing conventions)
  * Or rely on manual verification (unit tests for React components are optional per patterns.md)

* Mocking/fakes needed:
  * Mock fetch API for GET /result-models
  * Mock fetch API for POST /result-models
  * Mock fetch API for POST /augment/manual
  * Mock clipboard API (navigator.clipboard.writeText)

## Acceptance criteria (checklist)

* [ ] "Copy Prompt" button copies prompt to clipboard
* [ ] "Copy Prompt" button does NOT open paste modal
* [ ] "Paste Response" button is visible next to "Copy Prompt"
* [ ] "Paste Response" button opens paste modal with model dropdown
* [ ] Model dropdown fetches models from API when dialog opens
* [ ] Model dropdown displays all models plus "Unspecified" and "Add New..." options
* [ ] Selecting "Add New..." shows inline text input
* [ ] Typing in inline input updates state
* [ ] Selecting existing model from dropdown sets selectedModelId
* [ ] Saving with new model name creates model via API
* [ ] Saving with existing model sends model_id to manual result endpoint
* [ ] Saving with no model selection sends neither parameter (NULL model_id)
* [ ] Model creation error (duplicate name) displays error message
* [ ] Dialog close resets all model selection state
* [ ] All buttons and inputs are theme-aware (work in dark/light mode)
* [ ] No infinite rendering loops (fetchModels is memoized)

## Manual verification

* Steps:
  1. Navigate to `/rag/{id}` page for an existing query
  2. Click "Copy Prompt" button
  3. Verify prompt is copied to clipboard (paste in external editor)
  4. Verify paste modal does NOT open automatically
  5. Click "Paste Response" button
  6. Verify paste modal opens with textarea and model dropdown
  7. Verify model dropdown shows "Unspecified", existing models, and "Add New..."
  8. Select "Add New...", verify inline input appears
  9. Type "test-model-name" in input
  10. Paste response text in textarea, click "Save"
  11. Verify new model is created (check network tab for POST /result-models)
  12. Verify result is saved with new model (check POST /manual payload)
  13. Open paste modal again, select existing model "test-model-name"
  14. Paste response, save, verify result is saved with correct model_id
  15. Open paste modal again, leave model as "Unspecified"
  16. Paste response, save, verify result is saved with NULL model_id
  17. Close modal, verify model selection state is reset
  18. Test in both light and dark mode

* Expected results:
  * Copy Prompt works without opening modal
  * Paste Response button opens modal
  * Model dropdown fetches and displays models
  * "Add New..." shows inline input
  * New model creation works and result is saved
  * Existing model selection works and result is saved
  * Unspecified (NULL) model works
  * Dialog state resets on close
  * UI works in both themes

## Notes

* Requirements covered: R1, R2, R3, R4, R5, R6, R8 (partial - frontend only)
* This is the first vertical slice: enables end-to-end manual result submission with model tracking
* Inline input for new model name should be debounced if needed (not critical for MVP)
* Consider trimming whitespace from newModelName before creating model
* Error handling: Show user-friendly message if model creation fails (duplicate name, network error)
* Model dropdown should load quickly (<200ms per spec non-functional requirements)
* Use existing error state (`operationError`) to display model-related errors
* Reset states when dialog closes to prevent stale data on next open
* ClipboardPaste icon from lucide-react for "Paste Response" button
* Optional improvement: Auto-select most recently used model in dropdown (out of scope for this ticket)
