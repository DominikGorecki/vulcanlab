# Ticket: collection-deep-research.T17 - Collection Page Deep Research Button and Modal

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Add "Deep Research" button to collection detail page header (conditional on item count >= 5)
* Implement modal component for mode selection (Manual vs Automated)
* Provide UI entry point for both manual and automated research workflows

## Phase

* Frontend

## Scope

### In scope

* "Deep Research" button in collection page header (vulcanlab_ui/src/app/collection/[id]/page.tsx)
* Conditional rendering: button only appears when collection has >= 5 items
* DeepResearchModal component (vulcanlab_ui/src/components/research/DeepResearchModal.tsx)
* Mode selection UI with two cards: Manual Research, Automated Research
* Modal state management (open/close)

### Out of scope

* Manual wizard implementation (covered in T18-T21)
* Automated research progress tracking (covered in T22)
* Report list display (covered in T23)

## Dependencies

* Depends on: none (UI can be built in parallel with API)
* Unblocks: T18 (manual wizard), T22 (automated research trigger)

## Implementation plan

* Update vulcanlab_ui/src/app/collection/[id]/page.tsx:
  * Add state: const [isDeepResearchModalOpen, setIsDeepResearchModalOpen] = useState(false)
  * Fetch collection data (already done for collection page)
  * Count collection items: const itemCount = collection.items?.length || 0
  * Add "Deep Research" button to page header (next to collection title):
    * Conditional render: {itemCount >= 5 && <Button onClick={() => setIsDeepResearchModalOpen(true)}>Deep Research</Button>}
    * Button should use primary variant from Shadcn Button primitive
  * Add DeepResearchModal component:
    * <DeepResearchModal isOpen={isDeepResearchModalOpen} onClose={() => setIsDeepResearchModalOpen(false)} collectionId={collection.id} />
* Create vulcanlab_ui/src/components/research/DeepResearchModal.tsx:
  * Import Dialog from @radix-ui/react-dialog (or Shadcn Dialog wrapper)
  * Props: {isOpen: boolean, onClose: () => void, collectionId: number}
  * State: const [selectedMode, setSelectedMode] = useState<'manual' | 'automated' | null>(null)
  * Render Dialog with isOpen prop
  * Dialog content:
    * Title: "Start Deep Research"
    * Description: "Choose how you want to conduct research on this collection"
    * Two card options (use Shadcn Card component):
      * Manual Research card:
        * Title: "Manual Research"
        * Description: "Step-by-step guided workflow. You control LLM interactions and paste responses."
        * Button: "Start Manual" → onClick: setSelectedMode('manual')
      * Automated Research card:
        * Title: "Automated Research"
        * Description: "Fully automated using LangGraph. System handles all LLM calls."
        * Button: "Start Automated" → onClick: setSelectedMode('automated')
  * When selectedMode changes:
    * If 'manual': transition to ManualResearchWizard component (to be built in T18)
    * If 'automated': call API to start automated research (to be built in T22)
* Style using TailwindCSS:
  * Modal: centered, max-width 600px, theme-aware (bg-card, text-foreground)
  * Cards: grid layout (2 columns on desktop, 1 column on mobile), hover effect (border-primary on hover)
  * Buttons: primary variant for "Start" buttons
* Patterns to apply:
  * **Modal/Dialog pattern** - Use Shadcn Dialog primitive per patterns.md section 4.3
  * **Theme awareness** - Use semantic Tailwind classes (bg-card, text-foreground) per patterns.md section 4.2
  * **Component composition** - Modal built from smaller primitives (Dialog, Card, Button) per patterns.md section 4.2
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Collection page renders "Deep Research" button when itemCount >= 5
  * Collection page does NOT render button when itemCount < 5
  * Clicking "Deep Research" button opens DeepResearchModal
  * DeepResearchModal renders with two mode cards (Manual, Automated)
  * Clicking "Start Manual" sets selectedMode to 'manual'
  * Clicking "Start Automated" sets selectedMode to 'automated'
  * DeepResearchModal closes when onClose called
* Suggested locations:
  * tests/unit/components/research/test_DeepResearchModal.test.tsx
  * tests/unit/app/collection/test_collection_page.test.tsx
* Mocking/fakes needed:
  * Mock collection data with varying item counts
  * Mock Dialog component behavior

## Acceptance criteria (checklist)

* [ ] "Deep Research" button appears in collection page header when itemCount >= 5 (R1)
* [ ] "Deep Research" button does NOT appear when itemCount < 5 (R1)
* [ ] Clicking button opens DeepResearchModal
* [ ] DeepResearchModal displays two mode cards (Manual, Automated) (R2)
* [ ] Manual card has correct description and "Start Manual" button
* [ ] Automated card has correct description and "Start Automated" button
* [ ] Modal styled with TailwindCSS, theme-aware
* [ ] Modal uses Shadcn Dialog primitive
* [ ] Unit tests pass for button rendering and modal behavior

## Manual verification

* Steps:
  * Navigate to collection page with 3 items
  * Verify "Deep Research" button does NOT appear
  * Add 2 more items to collection (total 5)
  * Refresh page, verify button appears in header
  * Click "Deep Research" button
  * Verify modal opens with title "Start Deep Research"
  * Verify two cards displayed: "Manual Research" and "Automated Research"
  * Verify descriptions match spec
  * Hover over cards, verify hover effect (border highlight)
  * Click "Start Manual", verify selectedMode state updates
  * Close modal, verify it closes correctly
* Expected results:
  * Button conditional rendering works correctly
  * Modal opens and displays mode selection
  * Cards interactive and styled correctly

## Notes

* Requirements covered: R1 (button appears when 5+ items), R2 (mode selection modal)
* Button placement "next to collection title" per spec UX section
* Modal uses Radix Dialog primitive per patterns.md component library
* Theme-aware styling ensures dark mode compatibility
* selectedMode state will trigger wizard (T18) or API call (T22) in next tickets
