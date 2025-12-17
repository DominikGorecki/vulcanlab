# Ticket: markdown-import-export.T09 - Navigation and Tab Component

## Source
- Spec: documentation/work/markdown-import-export.spec.md
- Patterns: documentation/patterns.md

## Goal
- Add "MD Import/Export" navigation item to main nav bar
- Create shared tab navigation component for switching between export and import pages
- Ensure navigation item is always visible (not dependent on advanced mode)

## Scope
### In scope
- Update nav-bar.tsx to include new navigation item
- Create shared tab navigation component for /markdown routes
- Add tabs to export and import pages
- Route structure: /markdown/export and /markdown/import
- Icon selection for navigation item

### Out of scope
- Advanced/simple mode filtering for this nav item
- Nested sub-navigation beyond export/import tabs
- Breadcrumb navigation

## Dependencies
- Depends on: T05, T08
- Unblocks: none (completes navigation requirements)

## Implementation plan
1. Update vulcanlab_ui/src/components/nav-bar.tsx:
   - Add new nav item to navItems array:
     - href: "/markdown/export" (default to export page)
     - label: "MD Import/Export"
     - icon: FileImport from lucide-react
     - alwaysVisible: true (always show, not dependent on advancedModeEnabled)
   - Place after "Corpus" and before "Simple Conversion" for logical grouping
2. Create vulcanlab_ui/src/components/markdown/MarkdownTabs.tsx:
   - Shared component for tab navigation between export and import
   - Use Tabs component from shadcn/ui
   - Two tabs: "Export" and "Import"
   - Clicking tab navigates to respective route
   - Active tab determined by current pathname
   - Style consistently with rest of application
3. Update vulcanlab_ui/src/app/markdown/export/page.tsx:
   - Import and render MarkdownTabs component at top of page
4. Update vulcanlab_ui/src/app/markdown/import/page.tsx:
   - Import and render MarkdownTabs component at top of page
5. Create vulcanlab_ui/src/app/markdown/layout.tsx (optional):
   - Shared layout for /markdown routes
   - Include MarkdownTabs in layout so it appears on both pages
   - Reduces duplication
6. Patterns to apply:
   - Next.js App Router: Use app/markdown/ directory structure
   - Component reuse: Shared tabs component
   - Navigation: Use Next.js Link for client-side navigation
   - Styling: TailwindCSS and shadcn/ui patterns
   - Active state: Use usePathname() to determine active tab
- Deviations (if any): none

## Unit tests (required)
- Add tests for:
  - Nav bar includes "MD Import/Export" item
  - Nav item is always visible (not filtered by advanced mode)
  - Nav item links to /markdown/export
  - Nav item has correct icon (FileImport)
  - MarkdownTabs component renders two tabs
  - Export tab links to /markdown/export
  - Import tab links to /markdown/import
  - Active tab determined by current pathname
  - Clicking tab navigates to correct route
- Suggested locations:
  - vulcanlab_ui/src/components/__tests__/nav-bar.test.tsx (extend)
  - vulcanlab_ui/src/components/markdown/__tests__/MarkdownTabs.test.tsx
- Mocking/fakes needed:
  - Mock usePathname from next/navigation
  - Mock useRouter for navigation tests
  - Mock ConversionSettingsContext for nav bar tests

## Acceptance criteria (checklist)
- [ ] "MD Import/Export" navigation item appears in nav bar
- [ ] Nav item always visible (alwaysVisible: true)
- [ ] Nav item uses FileImport icon
- [ ] Clicking nav item navigates to /markdown/export
- [ ] MarkdownTabs component displays on export page
- [ ] MarkdownTabs component displays on import page
- [ ] Export tab active when on /markdown/export
- [ ] Import tab active when on /markdown/import
- [ ] Clicking tabs navigates between pages
- [ ] Tab styling matches application design
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. View application, verify "MD Import/Export" appears in nav bar
  2. Verify nav item visible in both simple and advanced modes
  3. Click nav item, verify navigation to /markdown/export
  4. Verify tabs appear at top of export page
  5. Verify "Export" tab is active
  6. Click "Import" tab
  7. Verify navigation to /markdown/import
  8. Verify "Import" tab is now active
  9. Click "Export" tab, verify return to export page
  10. Use browser back button, verify tabs update correctly
- Expected results:
  - Navigation item always visible and functional
  - Tabs work seamlessly for switching between pages
  - Active tab styling clear and consistent
  - Browser back/forward works correctly with tabs

## Notes
- FileImport icon from lucide-react provides clear visual representation
- Tab component should use shadcn/ui Tabs for consistency
- Consider using layout.tsx to reduce duplication of tabs component
- Active tab styling should match other active states in application (e.g., nav bar active item)
- Tabs should be keyboard accessible (Tab key navigation, Enter to select)
- Consider adding aria-labels for accessibility
- Position in nav bar matters: placing after Corpus makes logical sense as both deal with works
