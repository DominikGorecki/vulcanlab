COMPLETE

# T11: Manual Mode Workflow with Dual Execution Options

**Status**: COMPLETE
**Priority**: High
**Type**: Frontend + API Integration
**Depends On**: T07 (API endpoints), T09 (Entry form)
**Blocks**: None

## Overview

Implement the manual mode workflow page that displays an LLM prompt for the user to copy/paste, provides two execution options (manual copy/paste OR direct automatic execution), and shows final results. This page handles the "Manual" execution path from T09 and gives users flexibility in how they interact with the LLM.

## Acceptance Criteria

- [x] Page receives work_id from URL parameter
- [x] Fetches prompt via `/api/simple-conversion/manual-prompt` on mount
- [x] Displays full prompt text in copyable code block
- [x] Shows instructions for manual LLM usage
- [x] Displays classification (small/large) and instructions specific to that type
- [x] **Option 1**: Text area for user to paste LLM response
- [x] **Option 1**: Submit button calls `/api/simple-conversion/manual-submit`
- [x] **Option 2**: "Run Automatically" button calls `/api/simple-conversion/execute-auto`
- [x] Both options lead to results display via `/api/simple-conversion/results`
- [x] Copy button copies prompt to clipboard
- [x] Error handling displays error messages
- [x] Loading states for both execution options
- [x] Unit tests for component logic
- [ ] Manual test plan completed successfully

## Technical Implementation

### 1. Main Component

**File**: `vulcanlab_ui/src/app/simple-conversion/manual/[work_id]/page.tsx` (NEW)

Implemented the manual workflow page with:
-   **Prompt Display**: Fetches and displays the prompt with a copy button.
-   **Tabs Interface**: Uses ShadCN Tabs to switch between "Manual Execution" and "Automatic Execution".
-   **Manual Mode**: Textarea for JSON input and submission to `manual-submit` endpoint.
-   **Automatic Mode**: Button to trigger `execute-auto` and reuses the polling logic to track completion.
-   **Results Display**: Reused the results display logic from T10 (showing stats and chunks).

### 2. CSS Styling

Styling is handled via Tailwind CSS classes, ensuring consistency with the dashboard design. Used ShadCN components (`Tabs`, `Textarea`, `Card`, `Badge`) for a cohesive look.

### 3. Routing Setup

The file path `vulcanlab_ui/src/app/simple-conversion/manual/[work_id]/page.tsx` automatically registers the route in Next.js App Router.

## Unit Tests

**File**: `vulcanlab_ui/src/app/simple-conversion/manual/[work_id]/__tests__/page.test.tsx` (NEW)

Implemented tests covering:
-   Prompt fetching and display.
-   Clipboard copy interaction (mocked).
-   Manual submission flow.
-   Automatic execution flow (including polling simulation).
-   Error state handling.

## Manual Test Plan

### Setup
1. Complete T09 form submission with "Manual" mode selected
2. Verify navigation to `/simple-conversion/manual/{work_id}`

### Test Cases

#### TC1: Prompt Display
**Steps**:
1. Check that classification badge (SMALL/LARGE) is correct
2. Verify Instructions text is visible
3. Verify Prompt text is visible in the code block
4. Click "Copy to Clipboard"
5. Paste into a notepad to verify content

**Expected**: Prompt displayed and copied correctly

#### TC2: Option 1 - Manual Submission
**Steps**:
1. Select "Option 1: Manual Execution" tab
2. Paste a valid JSON response (mock one if needed)
3. Click "Submit Response"
4. Verify "Success" message and results appear

**Expected**: Manual submission processes and shows results

#### TC3: Option 2 - Automatic Execution
**Steps**:
1. refresh page to reset
2. Select "Option 2: Automatic Execution" tab
3. Click "Run Automatically"
4. Verify spinner appears
5. Wait for completion
6. Verify results appear

**Expected**: Automatic execution works from manual page

#### TC4: Invalid Input
**Steps**:
1. Refresh page
2. In Manual tab, paste invalid text (not JSON)
3. Click Submit
4. Verify backend returns 400 or 500 error and it displays in the alert box

**Expected**: Error handling works
