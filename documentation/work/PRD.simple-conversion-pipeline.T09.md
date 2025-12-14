COMPLETE

# T09: Simple Conversion Page with Metadata Form

**Status**: COMPLETE
**Priority**: High
**Type**: Vertical Slice (Frontend + API Integration)
**Depends On**: T07 (API endpoints), T08 (Navigation button)
**Blocks**: T10, T11 (Workflow pages depend on this foundation)

## Overview

Implement the main Simple Conversion page with a form to collect file path and metadata (title, author, year), mode selection (Automatic/Manual), and submission to initiate the conversion pipeline. This page is the entry point to the simple conversion workflow.

## Acceptance Criteria

- [x] Page fetches input files from `/conv/io-folder-data` endpoint
- [x] Page displays form with file selector dropdown (from input folder)
- [x] Form includes title, author, year (optional) metadata fields
- [x] Radio buttons for mode selection (Automatic/Manual)
- [x] Submit button calls `/api/simple-conversion/start` endpoint
- [x] Form validation (file selected, required fields, valid year)
- [x] Success: navigate to appropriate workflow page (T10 for auto, T11 for manual)
- [x] Error handling displays error messages
- [x] Loading state during submission and file fetch
- [x] Responsive design for mobile and desktop
- [x] Unit tests for component logic
- [ ] Manual test plan completed successfully

## Technical Implementation

### 1. Main Component

**File**: `vulcanlab_ui/src/app/simple-conversion/page.tsx` (MODIFIED)

Replaced placeholder with full implementation using React hooks, ShadCN components, and Tailwind CSS.
Fetching files from API, validating form input, and submitting to backend.

### 2. Styling

Used Tailwind CSS classes for consistent styling. Matches ShadCN/UI design system. Mode selection implemented with styled radio inputs (custom implementation to avoid extra dependencies).

### 3. Unit Tests

**File**: `vulcanlab_ui/src/app/simple-conversion/__tests__/page.test.tsx` (NEW)

Implemented Jest/React Testing Library tests for:
- Initial file loading
- Error states
- Validation
- Submission logic

## Manual Test Plan

### Setup
1. Ensure input files exist in the configured input folder
2. Start backend API server (FastAPI)
3. Start frontend dev server (Next.js)
4. Navigate to `/simple-conversion` page

### Test Cases

#### TC1: File List Loading
**Steps**:
1. Navigate to `/simple-conversion`
2. Verify loading spinner displays initially
3. Wait for files to load
4. Verify file dropdown populates with files from input folder

**Expected**: Files load from `/conv/io-folder-data` endpoint

#### TC2: Empty Input Folder
**Steps**:
1. Clear all files from input folder
2. Navigate to `/simple-conversion`
3. Verify dropdown shows "No files in input folder" message
4. Verify dropdown is disabled
5. Verify submit button is disabled

**Expected**: Empty state handled gracefully

#### TC3: File Fetch Error
**Steps**:
1. Stop backend API server
2. Navigate to `/simple-conversion`
3. Verify error alert displays
4. Verify "Retry" button appears
5. Restart API server and click "Retry"
6. Verify files load successfully

**Expected**: Fetch error handled with retry option

#### TC4: File Selection from Dropdown
**Steps**:
1. Open file dropdown
2. Verify all input folder files are listed
3. Select a file (e.g., "sample.pdf")
4. Verify dropdown displays selected filename
5. Verify no validation error appears

**Expected**: File selection works correctly

#### TC5: Required Field Validation
**Steps**:
1. Leave file dropdown unselected
2. Leave Title and Author empty
3. Click "Start Conversion"
4. Verify error messages appear:
   - "Please select a file" under dropdown
   - "Title is required"
   - "Author is required"
5. Verify form does not submit

**Expected**: Validation prevents submission for all required fields

#### TC6: Year Field Validation
**Steps**:
1. Fill required fields correctly (select file, enter title/author)
2. Enter invalid year "999" in Year field
3. Submit form
4. Verify error message "Please enter a valid year"
5. Change year to "3000" (future year beyond current + 1)
6. Submit form
7. Verify same error message

**Expected**: Year validation enforces range [1000, current year + 1]

#### TC7: Mode Selection - Automatic
**Steps**:
1. Verify "Automatic" mode is selected by default
2. Verify automatic mode card has green border highlight
3. Select file from dropdown: "test-book.pdf"
4. Fill Title: "Test Book"
5. Fill Author: "Test Author"
6. Fill Year: "2023" (optional)
7. Click "Start Conversion"
8. Verify button shows "Starting Conversion..." with loading spinner
9. Wait for API response
10. Verify navigates to `/simple-conversion/automatic/{work_id}`

**Expected**: Automatic mode submission navigates to automatic workflow

#### TC8: Mode Selection - Manual
**Steps**:
1. Click "Manual" mode radio button
2. Verify manual mode card highlights
3. Verify automatic mode card unhighlights
4. Select file from dropdown
5. Fill all required fields
6. Submit
7. Verify navigates to `/simple-conversion/manual/{work_id}`

