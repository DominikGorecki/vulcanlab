# Ticket: work-summarization.T15 - Work Summary Detail Page

## Source

* Spec: documentation/work/work-summarization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create work summary detail page showing summary_nodes hierarchically
* Display gist, key points, definitions, terms, examples for each node
* Provide derived output generation buttons and display
* Make line references clickable for source navigation

## Phase

* Frontend

## Scope

### In scope

* Create vulcanlab_ui/src/app/summarize/[id]/page.tsx
* Hierarchical tree view of summary_nodes
* Expandable sections for each node showing all summary fields
* Clickable line references linking to /corpus/[id]?highlight=start-end
* Buttons: Generate Abstract, Generate Outline, Generate Key Concepts, Generate Chapter Summaries
* Display generated derived outputs in collapsible sections
* Loading states for generation operations
* Re-summarize button with confirmation dialog

### Out of scope

* Summarize list page (T14)
* Corpus page Summarize button (T16)
* Settings tab (T13)

## Dependencies

* Depends on: T11 (nodes and derive endpoints), T14 (navigation)
* Unblocks: T16

## Implementation plan

1. Create vulcanlab_ui/src/app/summarize/[id]/page.tsx
2. Define TypeScript interfaces:
   - SummaryNode, KeyPoint, Definition, KeyTerm, Example
   - WorkSummary, DerivedOutput types
3. Implement data fetching:
   - Fetch summary nodes: GET /api/v1/summarize/{work_id}/nodes
   - Fetch derived outputs: GET /api/v1/summarize/{work_id}/summaries
   - Use usePageData with Promise.all for parallel fetch
4. Build hierarchical structure from flat nodes list:
   - Use heading_breadcrumbs or chunk parent_id to build tree
   - Helper function: buildNodeTree(nodes) -> tree structure
5. Create SummaryNodeCard component:
   - Heading with level indicator and breadcrumb path
   - Gist displayed prominently
   - Collapsible sections for: Key Points, Definitions, Key Terms, Examples
   - Each item shows line reference as clickable link
6. Create NodeTree component:
   - Recursive rendering of node tree
   - Indentation based on depth
   - Expand/collapse all functionality
7. Create DerivedOutputSection component:
   - Button to generate (if not exists) or regenerate
   - Display content when available
   - Abstract: formatted text
   - Outline: nested list
   - Key Concepts: term/definition list
   - Chapter Summaries: section list
8. Implement line reference links:
   - Format: /corpus/{work_id}?highlight={start_line}-{end_line}
   - Open in new tab or same window (user preference)
9. Implement derive button handlers:
   - POST /api/v1/summarize/{work_id}/derive with type
   - Show loading spinner during generation
   - Update UI with result
10. Add re-summarize button:
    - ConfirmDialog: "This will delete existing summaries. Continue?"
    - DELETE then POST to regenerate
11. Page layout:
    - StickyDetailHeader with work title, back to /summarize
    - Two-column layout: nodes tree (left), derived outputs (right)
    - Or tabs: Nodes | Abstract | Outline | Key Concepts | Chapters
* Patterns to apply:
  * StickyDetailHeader for navigation
  * usePageData for data fetching
  * ConfirmDialog for destructive actions
  * Collapsible sections for detail content
  * Theme-aware styling
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Page loads summary nodes for work
  * Nodes displayed in hierarchical structure
  * Node card shows gist prominently
  * Collapsible sections expand/collapse
  * Line references render as clickable links
  * Line reference links have correct URL format
  * Generate button triggers derive API call
  * Loading state shown during generation
  * Generated output displays correctly
  * Re-summarize shows confirmation dialog
  * Confirmation triggers delete and regenerate
  * Error state on API failure
* Suggested locations:
  * vulcanlab_ui/src/app/summarize/[id]/__tests__/page.test.tsx
* Mocking/fakes needed:
  * Mock fetch for API calls
  * Mock useParams for work_id
  * Mock useRouter for navigation

## Acceptance criteria (checklist)

* [ ] Page loads at /summarize/[id]
* [ ] Summary nodes displayed hierarchically
* [ ] Each node shows gist, key points, definitions, terms, examples
* [ ] Line references are clickable links to Corpus
* [ ] Derived output generation buttons functional
* [ ] Generated outputs display in appropriate format
* [ ] Loading states during generation
* [ ] Re-summarize with confirmation works
* [ ] Back navigation to /summarize list
* [ ] All unit tests pass

## Manual verification

* Steps:
  1. Navigate to /summarize/[id] for a summarized work
  2. Verify nodes display in tree structure
  3. Expand a node and verify all fields shown
  4. Click a line reference link
  5. Verify navigation to Corpus with correct line highlighted
  6. Click "Generate Outline" button
  7. Verify outline appears after loading
  8. Click "Re-summarize" and confirm
  9. Verify regeneration starts
* Expected results:
  * All summary data displayed correctly
  * Line references navigate to source
  * Derived outputs generate and display

## Notes

* Requirements covered: R13, R14
* Tree view library suggestion: react-arborist or custom recursive component
* Line reference URL format may need Corpus page enhancement for ?highlight param
* Consider lazy loading derived outputs (fetch on tab switch)
* Derived output display formats should match spec JSONB structures
* Re-summarize is R17 - ensure confirmation is clear about data loss
