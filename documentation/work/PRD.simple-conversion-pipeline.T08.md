# T08: Conversion Page "Simple Conversion" Button

**Status**: PENDING
**Priority**: Medium
**Type**: Frontend-Only
**Depends On**: None (independent UI change)
**Blocks**: T09 (needs navigation to Simple Conversion page)

## Overview

Add a "Simple Conversion" button to the existing Conversion page next to the "Start Conversion" button. This button allows users to access the streamlined simple conversion workflow as an alternative to the traditional multi-step process.

## Acceptance Criteria

- [ ] Button appears on Conversion page next to existing "Start Conversion" button
- [ ] Button labeled "Simple Conversion"
- [ ] Button navigates to `/simple-conversion` route when clicked
- [ ] Button styled consistently with existing UI
- [ ] Button includes hover state
- [ ] Button works on all screen sizes (responsive)
- [ ] No unit test required (simple UI addition)
- [ ] Manual test plan completed successfully

## Technical Implementation

### 1. Update Conversion Page Component

**File**: `vulcanlab_ui/src/components/conversion/ConversionPage.tsx` (MODIFIED)

Locate the existing "Start Conversion" button and add the new button next to it:

```typescript
/**
 * Conversion Page Component
 *
 * Main page for document conversion workflows. Provides access to both
 * the traditional multi-step conversion and the new simple conversion pipeline.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import './ConversionPage.css';

export const ConversionPage: React.FC = () => {
  const navigate = useNavigate();

  const handleStartConversion = () => {
    // Existing conversion workflow
    navigate('/conversion/start');
  };

  const handleSimpleConversion = () => {
    // New simple conversion workflow
    navigate('/simple-conversion');
  };

  return (
    <div className="conversion-page">
      <h1>Document Conversion</h1>

      <p className="page-description">
        Convert your PDF or EPUB documents into structured, searchable chunks.
      </p>

      <div className="conversion-options">
        {/* Existing conversion button */}
        <div className="conversion-option">
          <h2>Standard Conversion</h2>
          <p>
            Multi-step conversion process with full control over each stage:
            conversion, sanitization, and chunking.
          </p>
          <button
            className="btn-primary"
            onClick={handleStartConversion}
          >
            Start Conversion
          </button>
        </div>

        {/* NEW: Simple conversion button */}
        <div className="conversion-option">
          <h2>Simple Conversion</h2>
          <p>
            Streamlined single-page workflow that automatically handles
            conversion, sanitization, and chunking.
          </p>
          <button
            className="btn-primary btn-simple-conversion"
            onClick={handleSimpleConversion}
          >
            Simple Conversion
          </button>
        </div>
      </div>

      {/* Existing content below */}
    </div>
  );
};
```

### 2. Update CSS Styling

**File**: `vulcanlab_ui/src/components/conversion/ConversionPage.css` (MODIFIED)

Add or update styles to support the two-column conversion options layout:

```css
.conversion-page {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.conversion-page h1 {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.page-description {
  color: #666;
  font-size: 1.1rem;
  margin-bottom: 2rem;
}

.conversion-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.conversion-option {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1.5rem;
  background-color: #f9f9f9;
  transition: box-shadow 0.2s ease;
}

.conversion-option:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.conversion-option h2 {
  font-size: 1.5rem;
  margin-bottom: 0.75rem;
  color: #333;
}

.conversion-option p {
  color: #666;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.conversion-option button {
  width: 100%;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
}

/* Simple conversion button specific styles */
.btn-simple-conversion {
  background-color: #4caf50;
}

.btn-simple-conversion:hover {
  background-color: #45a049;
}

/* Responsive design for smaller screens */
@media (max-width: 768px) {
  .conversion-options {
    grid-template-columns: 1fr;
  }

  .conversion-page {
    padding: 1rem;
  }

  .conversion-page h1 {
    font-size: 1.5rem;
  }
}
```

### 3. Update Routing Configuration

**File**: `vulcanlab_ui/src/App.tsx` (MODIFIED - if routing needs update)

Ensure the route exists for `/simple-conversion`:

```typescript
import { SimpleConversionPage } from './components/simple-conversion/SimpleConversionPage';

// In your Routes configuration:
<Route path="/simple-conversion" element={<SimpleConversionPage />} />
```

**Note**: The actual `SimpleConversionPage` component will be created in T09. For this ticket, just ensure the route is defined even if it points to a placeholder component temporarily.

### 4. Placeholder Component (Temporary)

**File**: `vulcanlab_ui/src/components/simple-conversion/SimpleConversionPage.tsx` (NEW - TEMPORARY)

Create a minimal placeholder for T08 testing:

```typescript
/**
 * Simple Conversion Page (Placeholder)
 *
 * This is a temporary placeholder component for T08 testing.
 * Will be fully implemented in T09.
 */

import React from 'react';

export const SimpleConversionPage: React.FC = () => {
  return (
    <div style={{ padding: '2rem' }}>
      <h1>Simple Conversion</h1>
      <p>Coming soon... (Placeholder for T08 testing)</p>
    </div>
  );
};
```

## Manual Test Plan

### Setup
1. Start frontend development server
2. Navigate to Conversion page

### Test Cases

#### TC1: Button Visibility
**Steps**:
1. Navigate to `/conversion` page
2. Verify "Simple Conversion" button is visible
3. Verify it appears next to "Start Conversion" button
4. Verify both options displayed side-by-side (or stacked on mobile)

**Expected**: Both buttons visible and properly positioned

#### TC2: Button Styling
**Steps**:
1. Inspect "Simple Conversion" button
2. Verify green background color (#4caf50)
3. Verify consistent sizing with "Start Conversion" button
4. Verify border radius and padding match design

**Expected**: Button styled correctly

#### TC3: Hover State
**Steps**:
1. Hover mouse over "Simple Conversion" button
2. Verify background color changes to darker green (#45a049)
3. Verify smooth transition effect
4. Verify card has shadow effect on hover

**Expected**: Hover effects work correctly

#### TC4: Click Navigation
**Steps**:
1. Click "Simple Conversion" button
2. Verify navigation to `/simple-conversion` route
3. Verify placeholder page displays "Coming soon..." message
4. Verify URL changes to `/simple-conversion`

**Expected**: Navigates to placeholder page

#### TC5: Responsive Design - Desktop
**Steps**:
1. View page on desktop screen (>768px width)
2. Verify two options displayed side-by-side
3. Verify equal width columns
4. Verify adequate spacing between options

**Expected**: Desktop layout works correctly

#### TC6: Responsive Design - Mobile
**Steps**:
1. Resize browser to <768px width OR use mobile device
2. Verify options stack vertically
3. Verify full-width buttons
4. Verify readable text at smaller size

**Expected**: Mobile layout responsive

#### TC7: Back Navigation
**Steps**:
1. Click "Simple Conversion" button to navigate
2. Click browser back button
3. Verify returns to Conversion page
4. Verify button states are correct

**Expected**: Navigation history works

#### TC8: Comparison with Standard Conversion
**Steps**:
1. Click "Start Conversion" button
2. Note the navigation destination
3. Go back and click "Simple Conversion"
4. Verify different routes/pages

**Expected**: Two different workflows accessible

## Dependencies

- **Internal**: None (independent UI change)
- **External**: React, React Router, CSS
- **Testing**: Manual testing only (no unit tests required for simple button addition)

## Assumptions

1. Conversion page component exists and is accessible via routing
2. React Router is configured in the application
3. CSS styling follows existing project patterns
4. SimpleConversionPage component will be fully implemented in T09

## Notes

- This is a **frontend-only** ticket
- No backend changes required
- No unit tests required (simple UI addition)
- Placeholder component created for T08, fully implemented in T09
- Button styling uses green color to differentiate from standard conversion
- Responsive design supports both desktop and mobile views
- Grid layout automatically adjusts to screen size

## Definition of Done

- [ ] Button added to Conversion page
- [ ] Button navigates to `/simple-conversion` route
- [ ] Button styled with green color scheme
- [ ] Hover state implemented
- [ ] Responsive design works on desktop and mobile
- [ ] Manual test plan completed
- [ ] Placeholder page displays when button clicked
- [ ] Code follows existing project patterns
