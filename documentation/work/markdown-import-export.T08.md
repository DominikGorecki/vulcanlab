# Ticket: markdown-import-export.T08 - Import Frontend Page (Vertical Slice)

## Source
- Spec: documentation/work/markdown-import-export.spec.md
- Patterns: documentation/patterns.md

## Goal
- Create import page UI that lists available markdown files
- Implement metadata entry modal with form validation
- Implement sanitization decision modal
- Implement duplicate warning modal
- Second end-to-end vertical slice for import feature

## Scope
### In scope
- Page component: vulcanlab_ui/src/app/markdown/import/page.tsx
- Metadata entry modal component
- Sanitization decision modal component
- Duplicate warning modal component
- File listing with import button
- Form validation and error handling

### Out of scope
- Status page (covered in T10)
- Tab navigation (covered in T09)
- Batch import operations
- File preview functionality

## Dependencies
- Depends on: T07
- Unblocks: T09, T10

## Implementation plan
1. Create vulcanlab_ui/src/app/markdown/import/page.tsx:
   - "use client" directive
   - State management:
     - files: MarkdownFile[]
     - loading: boolean
     - selectedFile: MarkdownFile | null
     - showMetadataModal: boolean
     - showSanitizationModal: boolean
     - showDuplicateModal: boolean
     - duplicateInfo: {workId: number, workTitle: string} | null
     - metadata: {title: string, author: string, year: number}
   - useEffect to fetch files from GET /api/v1/markdown/files
   - handleImportClick(file: MarkdownFile):
     - Set selectedFile
     - If file has metadata, pre-populate form
     - Show metadata modal
   - handleMetadataSubmit(metadata):
     - Check for duplicate via GET /api/v1/markdown/check-duplicate
     - If duplicate: show duplicate modal
     - Else: show sanitization modal
   - handleDuplicateDecision(proceed: boolean):
     - If cancel: close modal, return to file list
     - If proceed: show sanitization modal
   - handleSanitizationDecision(isSanitized: boolean):
     - Call POST /api/v1/markdown/import with metadata and is_sanitized
     - On success: redirect to status page with work_id
     - On error: show error modal
   - Render:
     - Page header: "Import Markdown"
     - Table listing files (Filename, Has Metadata, Actions)
     - Import button for each file
2. Create MetadataEntryModal component:
   - Form with fields: title, author, year (all required)
   - Pre-populate from file metadata if available
   - Validation: non-empty strings, valid year integer
   - Submit and Cancel buttons
3. Create SanitizationDecisionModal component:
   - Question: "Is this markdown already sanitized?"
   - Two buttons: "Yes, it's sanitized" and "No, needs sanitization"
   - Explanation text about what sanitization does
4. Create DuplicateWarningModal component:
   - Warning message: "A work with this title and author already exists"
   - Display existing work title and ID
   - Two buttons: "Import Anyway" and "Cancel"
5. Patterns to apply:
   - Next.js App Router: app/markdown/import/page.tsx
   - Client component: Use "use client"
   - Shadcn/Radix UI: Use Dialog for modals, Form for inputs
   - Form validation: Client-side validation before API call
   - Error handling: Display user-friendly messages
- Deviations (if any): none

## Unit tests (required)
- Add tests for:
  - Page fetches files on mount
  - Files displayed in table correctly
  - Import button opens metadata modal
  - Metadata form pre-populates if file has metadata
  - Metadata form validates required fields
  - Duplicate check runs after metadata submit
  - Duplicate modal shown if duplicate exists
  - User can proceed or cancel from duplicate modal
  - Sanitization modal shown after metadata/duplicate flow
  - Import API called with correct parameters
  - Redirect to status page on successful import
  - Error modal shown on import failure
- Suggested locations:
  - vulcanlab_ui/src/app/markdown/import/__tests__/page.test.tsx
  - vulcanlab_ui/src/components/markdown/__tests__/MetadataEntryModal.test.tsx
- Mocking/fakes needed:
  - Mock fetch for all API endpoints
  - Mock useRouter for redirect
  - Mock form submission events

## Acceptance criteria (checklist)
- [ ] Import page lists all markdown files from API
- [ ] Import button opens metadata entry modal
- [ ] Metadata modal pre-populates if file has frontmatter
- [ ] Metadata form validates all fields
- [ ] Duplicate check runs after metadata submission
- [ ] Duplicate warning modal appears if duplicate detected
- [ ] User can proceed or cancel from duplicate modal
- [ ] Sanitization decision modal appears after metadata flow
- [ ] Import API called with correct is_sanitized value
- [ ] Success redirects to status page with work_id
- [ ] Error modal displays error message
- [ ] All unit tests pass

## Manual verification
- Steps:
  1. Navigate to /markdown/import
  2. Verify file list displays
  3. Click import for file with metadata, verify form pre-populated
  4. Submit metadata, verify duplicate check runs
  5. If no duplicate, verify sanitization modal appears
  6. Select "Yes, it's sanitized"
  7. Verify redirect to status page
  8. Import file without metadata, fill form manually
  9. Submit with duplicate title/author
  10. Verify duplicate warning modal appears
  11. Click "Import Anyway"
  12. Verify sanitization modal appears
  13. Select "No, needs sanitization"
  14. Verify redirect to status page
- Expected results:
  - All modals appear in correct sequence
  - Form validation works correctly
  - Duplicate detection functions properly
  - Import completes and redirects appropriately

## Notes
- Modal sequence: Metadata → Duplicate (if exists) → Sanitization → Import
- Year validation should accept integers in reasonable range (1000-2100)
- Consider adding file preview in modal (show first few lines of markdown)
- Error messages should be specific and actionable
- Loading states on buttons during API calls
- This is the second vertical slice: user can import files end-to-end
- Metadata modal should support keyboard navigation (Enter to submit, Esc to cancel)
