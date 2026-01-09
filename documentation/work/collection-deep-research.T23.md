# Ticket: collection-deep-research.T23 - Research Report List and Viewing

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Display list of completed research reports on collection detail page
* Implement report viewing UI with markdown rendering and citation links
* Enable navigation from report list to full report view

## Phase

* Frontend

## Scope

### In scope

* ResearchReportList component on collection detail page
* ResearchReportCard component with session metadata and preview
* ResearchReportView component with markdown rendering and citation links
* Integration with API endpoints: GET /api/v1/collections/{collection_id}/research-sessions, GET /api/v1/research-sessions/{session_id}/report
* Markdown rendering with syntax highlighting and citation link handling

### Out of scope

* Manual wizard (covered in T18-T21)
* Automated research trigger (covered in T22)
* PDF export (out of scope per spec)

## Dependencies

* Depends on: T09 (report endpoint), T20 (wizard completion)
* Unblocks: none (final frontend ticket)

## Implementation plan

* Update collection page (vulcanlab_ui/src/app/collection/[id]/page.tsx):
  * Fetch completed sessions:
    * Call GET /api/v1/collections/{collectionId}/research-sessions
    * Filter sessions with status='completed'
  * Render ResearchReportList component below collection items section
* Create ResearchReportList component:
  * Props: {collectionId: number}
  * Fetch completed sessions using usePageData hook
  * Display section header: "Research Reports"
  * If no reports: show EmptyState: "No research reports yet. Start deep research to create one."
  * If reports exist: render ResearchReportCard for each session
  * Sort by created_at DESC (most recent first)
* Create ResearchReportCard component:
  * Props: {session: ResearchSession, onClick: () => void}
  * Card layout (Shadcn Card component):
    * Session type badge: "Manual" or "Automated" (StatusBadge component)
    * Created date (formatted: "Jan 8, 2026")
    * Executive summary preview (first 150 chars + "...")
    * Word count and citation count (from metadata)
    * "View Report" button → onClick
  * Hover effect: border highlight per patterns.md
  * Theme-aware styling
* Create ResearchReportView component:
  * Props: {sessionId: number, onClose: () => void}
  * Fetch report: GET /api/v1/research-sessions/{sessionId}/report
  * Display in modal (Dialog component) or dedicated page
  * Modal layout:
    * Header: "Research Report" with close button
    * Body: scrollable content area with markdown
  * Markdown rendering:
    * Use react-markdown with remark-gfm plugin
    * Syntax highlighting for code blocks (if any) using react-syntax-highlighter
    * Sanitize with rehype-sanitize to prevent XSS
    * Custom link renderer for citations:
      * Parse citation links with format: link://collection-item/{item_id}
      * Render as clickable links that open item detail or show preview
      * Regular links ([text](url)) render as external links
  * Styling:
    * Use prose classes from Tailwind Typography plugin
    * prose-invert for dark mode
    * Max width 800px for readability
  * Footer: "Close" button
* Add citation link handling:
  * Parse markdown links with link:// protocol
  * Extract item_id from link://collection-item/{item_id}
  * On click: fetch collection item preview and show in tooltip or modal
  * Fallback: if item not found, display citation text only
* Patterns to apply:
  * **usePageData hook** - For fetching sessions and report per patterns.md section 4.2
  * **Modal pattern** - Use Dialog primitive for report view per patterns.md section 4.3
  * **Theme awareness** - Use semantic Tailwind classes per patterns.md section 4.2
  * **Component composition** - Build from primitives (Card, Dialog, Badge) per patterns.md section 4.2
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * ResearchReportList fetches completed sessions
  * ResearchReportList renders ResearchReportCard for each session
  * ResearchReportList shows EmptyState when no reports
  * ResearchReportCard displays session type, date, summary preview
  * ResearchReportCard "View Report" button opens ResearchReportView
  * ResearchReportView fetches report by session_id
  * ResearchReportView renders markdown content correctly
  * ResearchReportView sanitizes markdown to prevent XSS
  * ResearchReportView custom link renderer handles citation links (link://)
  * Citation links extract item_id correctly
  * Citation links clickable and show item preview (or fallback)
  * Syntax highlighting works for code blocks (if any)
  * Theme-aware styling (prose-invert for dark mode)
* Suggested locations:
  * tests/unit/components/research/test_ResearchReportList.test.tsx
  * tests/unit/components/research/test_ResearchReportCard.test.tsx
  * tests/unit/components/research/test_ResearchReportView.test.tsx
* Mocking/fakes needed:
  * Mock API calls (GET sessions, GET report)
  * Mock react-markdown rendering
  * Mock collection item preview fetch

## Acceptance criteria (checklist)

* [ ] ResearchReportList displays on collection page (R10)
* [ ] Report cards show session type, date, executive summary preview (R10)
* [ ] Report cards display word count and citation count from metadata
* [ ] Clicking report card opens ResearchReportView (R11)
* [ ] ResearchReportView renders full markdown report (R11)
* [ ] Markdown sanitized to prevent XSS (security requirement)
* [ ] Citation links clickable and navigate to source items (R12, citation links)
* [ ] Syntax highlighting for code blocks (if present)
* [ ] Theme-aware styling (prose classes, dark mode support)
* [ ] EmptyState shown when no reports
* [ ] Unit tests pass for report list and viewing

## Manual verification

* Steps:
  * Complete manual or automated research workflow (from T18-T22)
  * Navigate to collection page
  * Verify "Research Reports" section appears below collection items
  * Verify report card displayed with:
    * Session type badge ("Manual" or "Automated")
    * Created date
    * Executive summary preview (first 150 chars)
    * Word count and citation count
  * Click "View Report" button
  * Verify modal or page opens with full report
  * Verify markdown renders correctly:
    * Headings, lists, bold/italic text
    * Citations as clickable links
  * Click a citation link (e.g., [Author 2020])
  * Verify item preview shown or navigates to item detail
  * Verify syntax highlighting for code blocks (if any in report)
  * Switch to dark mode
  * Verify prose-invert styling applied, readable in dark mode
  * Close report view
  * Create second report
  * Verify both reports displayed, sorted by date DESC
* Expected results:
  * Report list displays all completed reports
  * Report view renders markdown correctly
  * Citation links work
  * Theme-aware styling works

## Notes

* Requirements covered: R10 (display report list on collection page), R11 (view full markdown reports with citations), R12 (source attribution)
* Report cards provide preview to help users identify reports quickly
* Modal vs dedicated page: start with modal (simpler), can upgrade to dedicated page later for better SEO/linking
* Citation link format link://collection-item/{item_id} per spec Implementation Notes
* Sanitization with rehype-sanitize prevents XSS per R6 security requirement
* Prose classes from Tailwind Typography plugin provide beautiful markdown rendering
