COMPLETE

# T10: Automatic Mode Workflow with Status Tracking

**Status**: COMPLETE
**Priority**: High
**Type**: Frontend + API Integration
**Depends On**: T07 (API endpoints), T09 (Entry form)
**Blocks**: None

## Overview

Implement the automatic mode workflow page that executes the full conversion pipeline automatically, displays real-time status updates via polling, and shows final results with chunk preview. This page handles the "Automatic" execution path from T09.

## Acceptance Criteria

- [x] Page receives work_id from URL parameter
- [x] Auto-executes pipeline on mount via `/api/simple-conversion/execute-auto`
- [x] Polls `/api/simple-conversion/status` every 2 seconds during execution
- [x] Displays current step (converting, parsing, sanitizing, chunking, complete)
- [x] Shows progress indicator for each step
- [x] Displays classification (small/large) when available
- [x] Shows token count and chunk count when available
- [x] On completion, fetches and displays results via `/api/simple-conversion/results`
- [x] Shows chunk preview list (heading + content preview)
- [x] Error handling displays error messages
- [x] "View Full Results" button navigates to results page (if exists) or displays inline
- [x] Unit tests for component logic
- [ ] Manual test plan completed successfully

## Technical Implementation

### 1. Main Component

**File**: `vulcanlab_ui/src/app/simple-conversion/automatic/[work_id]/page.tsx` (NEW)

Implemented the automatic workflow functionality:
-   Uses `fetch` to trigger execution and poll status.
-   Uses Tailwind CSS and ShadCN components for UI.
-   Visualizes progress steps with active/completed states.
-   Displays classification and statistics.
-   Shows final results with a list of chunks inside a ScrollArea.

### 2. CSS Styling

Styling is handled via Tailwind CSS utility classes within the component, maintaining consistency with the application's design system. Custom animations for progress indicators were added using standard Tailwind patterns.

### 3. Routing Setup

The file path `vulcanlab_ui/src/app/simple-conversion/automatic/[work_id]/page.tsx` automatically registers the route in Next.js App Router for `/simple-conversion/automatic/:workId`.

## Unit Tests

**File**: `vulcanlab_ui/src/app/simple-conversion/automatic/[work_id]/__tests__/page.test.tsx` (NEW)

Implemented tests covering:
-   Automatic execution on component mount.
-   Status polling mechanism (using fake timers).
-   Correct rendering of progress steps and metadata.
-   Successful completion and results rendering.
-   Error state handling for both execution failure and pipeline errors.

## Manual Test Plan

### Setup
1. Complete T09 form submission successfully
2. Backend API ready to handle automatic execution
3. Test work prepared with PDF/EPUB

### Test Cases

#### TC1: Automatic Execution Start
**Steps**:
1. Submit form in T09 with "Automatic" mode
2. Verify navigation to `/simple-conversion/automatic/{work_id}`
3. Verify page automatically calls execute-auto endpoint
4. Verify status polling begins

**Expected**: Pipeline executes automatically

#### TC2: Status Updates During Execution
**Steps**:
1. Watch progress steps indicator
2. Verify steps highlight as they complete:
   - Parse & Classify
   - Sanitize
   - Chunk
   - Complete
3. Verify spinner shows during execution
4. Verify current step label updates

**Expected**: Real-time status updates displayed

#### TC3: Classification Display
**Steps**:
1. Wait for parsing step to complete
2. Verify classification (SMALL or LARGE) displays
3. Verify token count displays

**Expected**: Classification information appears dynamically

#### TC4: Completion and Results
**Steps**:
1. Wait for pipeline to reach "Complete" step
2. Verify polling stops
3. Verify "Success" message displays
4. Verify results summary (Title, Author, Stats) appears
5. Verify Chunks list is populated with previews

**Expected**: Full results displayed without refreshing

#### TC5: Error Handling
**Steps**:
1. Trigger a backend error (e.g. stop server or force fail)
2. Verify error alert displays with message
3. Verify "Return to Start" button works

**Expected**: Graceful error handling
