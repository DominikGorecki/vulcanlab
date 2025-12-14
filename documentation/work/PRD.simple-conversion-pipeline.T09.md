# T09: Simple Conversion Page with Metadata Form

**Status**: PENDING
**Priority**: High
**Type**: Vertical Slice (Frontend + API Integration)
**Depends On**: T07 (API endpoints), T08 (Navigation button)
**Blocks**: T10, T11 (Workflow pages depend on this foundation)

## Overview

Implement the main Simple Conversion page with a form to collect file path and metadata (title, author, year), mode selection (Automatic/Manual), and submission to initiate the conversion pipeline. This page is the entry point to the simple conversion workflow.

## Acceptance Criteria

- [ ] Page fetches input files from `/conv/io-folder-data` endpoint
- [ ] Page displays form with file selector dropdown (from input folder)
- [ ] Form includes title, author, year (optional) metadata fields
- [ ] Radio buttons for mode selection (Automatic/Manual)
- [ ] Submit button calls `/api/simple-conversion/start` endpoint
- [ ] Form validation (file selected, required fields, valid year)
- [ ] Success: navigate to appropriate workflow page (T10 for auto, T11 for manual)
- [ ] Error handling displays error messages
- [ ] Loading state during submission and file fetch
- [ ] Responsive design for mobile and desktop
- [ ] Unit tests for component logic
- [ ] Manual test plan completed successfully

## Technical Implementation

### 1. Main Component

**File**: `vulcanlab_ui/src/app/simple-conversion/page.tsx` (REPLACE placeholder from T08)

```typescript
/**
 * Simple Conversion Page
 *
 * Entry point for the simple conversion workflow. Fetches available files
 * from input folder, collects metadata, and execution mode, then initiates
 * the conversion process.
 */

"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2Icon, AlertCircle } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FormData {
  selectedFile: string;
  title: string;
  author: string;
  year: string;
  mode: 'automatic' | 'manual';
}

interface FormErrors {
  selectedFile?: string;
  title?: string;
  author?: string;
  year?: string;
}

export default function SimpleConversionPage() {
  const router = useRouter();

  // File list state
  const [inputFiles, setInputFiles] = useState<string[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(true);
  const [filesFetchError, setFilesFetchError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState<FormData>({
    selectedFile: '',
    title: '',
    author: '',
    year: '',
    mode: 'automatic'
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch input files on mount
  useEffect(() => {
    fetchInputFiles();
  }, []);

  const fetchInputFiles = async () => {
    try {
      setLoadingFiles(true);
      setFilesFetchError(null);

      const response = await fetch(`${API_BASE_URL}/conv/io-folder-data`);
      if (!response.ok) {
        throw new Error(`Failed to fetch files: ${response.statusText}`);
      }

      const data = await response.json();
      setInputFiles(data.input_files || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load input files';
      setFilesFetchError(message);
    } finally {
      setLoadingFiles(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // Clear error for this field when user types
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleModeChange = (mode: 'automatic' | 'manual') => {
    setFormData(prev => ({ ...prev, mode }));
  };

  const handleFileSelect = (value: string) => {
    setFormData(prev => ({ ...prev, selectedFile: value }));
    if (errors.selectedFile) {
      setErrors(prev => ({ ...prev, selectedFile: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.selectedFile) {
      newErrors.selectedFile = 'Please select a file';
    }

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!formData.author.trim()) {
      newErrors.author = 'Author is required';
    }

    if (formData.year) {
      const yearNum = parseInt(formData.year, 10);
      if (isNaN(yearNum) || yearNum < 1000 || yearNum > new Date().getFullYear() + 1) {
        newErrors.year = 'Please enter a valid year';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/simple-conversion/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: formData.selectedFile,
          title: formData.title,
          author: formData.author,
          year: formData.year ? parseInt(formData.year, 10) : null,
          mode: formData.mode
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to start conversion');
      }

      const data = await response.json();
      const { work_id, mode } = data;

      // Navigate to appropriate workflow page
      if (mode === 'automatic') {
        router.push(`/simple-conversion/automatic/${work_id}`);
      } else {
        router.push(`/simple-conversion/manual/${work_id}`);
      }

    } catch (err) {
      console.error('Failed to start conversion:', err);
      const message = err instanceof Error ? err.message : 'Failed to start conversion';
      setErrorMessage(message);
    } finally {
      setSubmitting(false);
    }
  };

  // Loading state for file fetch
  if (loadingFiles) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Simple Conversion</h2>
          <p className="text-muted-foreground">Loading available files...</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  // Error state for file fetch
  if (filesFetchError) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Simple Conversion</h2>
          <p className="text-muted-foreground">Streamlined document conversion workflow.</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {filesFetchError}
          </AlertDescription>
        </Alert>
        <Button onClick={fetchInputFiles}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Simple Conversion</h2>
        <p className="text-muted-foreground">
          Convert your PDF or EPUB document in a streamlined single-page workflow.
          Select a file from the input folder and provide metadata.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Start Conversion</CardTitle>
          <CardDescription>
            Select a file and provide metadata to begin the conversion process.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* File Selection */}
            <div className="space-y-2">
              <Label htmlFor="selectedFile">
                Select File <span className="text-destructive">*</span>
              </Label>
              <Select
                value={formData.selectedFile}
                onValueChange={handleFileSelect}
                disabled={submitting || inputFiles.length === 0}
              >
                <SelectTrigger id="selectedFile" className={errors.selectedFile ? 'border-destructive' : ''}>
                  <SelectValue placeholder="Choose a file from input folder" />
                </SelectTrigger>
                <SelectContent>
                  {inputFiles.length === 0 ? (
                    <div className="text-sm text-muted-foreground p-2">
                      No files in input folder
                    </div>
                  ) : (
                    inputFiles.map((file) => (
                      <SelectItem key={file} value={file}>
                        {file}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {errors.selectedFile && (
                <p className="text-sm text-destructive">{errors.selectedFile}</p>
              )}
            </div>

            {/* Title */}
            <div className="space-y-2">
              <Label htmlFor="title">
                Title <span className="text-destructive">*</span>
              </Label>
              <Input
                id="title"
                name="title"
                type="text"
                value={formData.title}
                onChange={handleInputChange}
                placeholder="Document title"
                disabled={submitting}
                className={errors.title ? 'border-destructive' : ''}
              />
              {errors.title && (
                <p className="text-sm text-destructive">{errors.title}</p>
              )}
            </div>

            {/* Author */}
            <div className="space-y-2">
              <Label htmlFor="author">
                Author <span className="text-destructive">*</span>
              </Label>
              <Input
                id="author"
                name="author"
                type="text"
                value={formData.author}
                onChange={handleInputChange}
                placeholder="Author name"
                disabled={submitting}
                className={errors.author ? 'border-destructive' : ''}
              />
              {errors.author && (
                <p className="text-sm text-destructive">{errors.author}</p>
              )}
            </div>

            {/* Year (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="year">
                Publication Year <span className="text-muted-foreground text-sm font-normal">(optional)</span>
              </Label>
              <Input
                id="year"
                name="year"
                type="number"
                value={formData.year}
                onChange={handleInputChange}
                placeholder="2023"
                disabled={submitting}
                className={errors.year ? 'border-destructive' : ''}
              />
              {errors.year && (
                <p className="text-sm text-destructive">{errors.year}</p>
              )}
            </div>

            {/* Mode Selection */}
            <div className="space-y-3">
              <Label>Execution Mode</Label>
              <RadioGroup
                value={formData.mode}
                onValueChange={(value) => handleModeChange(value as 'automatic' | 'manual')}
                disabled={submitting}
                className="grid gap-4 md:grid-cols-2"
              >
                <div>
                  <RadioGroupItem value="automatic" id="mode-automatic" className="peer sr-only" />
                  <Label
                    htmlFor="mode-automatic"
                    className="flex flex-col items-start gap-2 rounded-md border-2 border-muted p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-green-600 [&:has([data-state=checked])]:border-green-600 cursor-pointer"
                  >
                    <div className="font-semibold">Automatic</div>
                    <div className="text-sm text-muted-foreground">
                      Pipeline runs automatically using LLM. No manual intervention required.
                    </div>
                  </Label>
                </div>
                <div>
                  <RadioGroupItem value="manual" id="mode-manual" className="peer sr-only" />
                  <Label
                    htmlFor="mode-manual"
                    className="flex flex-col items-start gap-2 rounded-md border-2 border-muted p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-green-600 [&:has([data-state=checked])]:border-green-600 cursor-pointer"
                  >
                    <div className="font-semibold">Manual</div>
                    <div className="text-sm text-muted-foreground">
                      Copy prompt, paste into your own LLM, and submit the result.
                    </div>
                  </Label>
                </div>
              </RadioGroup>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{errorMessage}</AlertDescription>
              </Alert>
            )}

            {/* Submit Button */}
            <div className="flex justify-end gap-2">
              <Button
                type="submit"
                disabled={submitting || inputFiles.length === 0}
                className="bg-green-600 hover:bg-green-700"
              >
                {submitting ? (
                  <>
                    <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                    Starting Conversion...
                  </>
                ) : (
                  'Start Conversion'
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

### 2. Styling

**Note**: This component uses Tailwind CSS and shadcn/ui components for styling, so no separate CSS file is needed. All styling is done via className props using Tailwind utility classes.

Key styling patterns:
- `space-y-6` for vertical spacing between sections
- `border-destructive` for error state borders
- `text-destructive` for error messages
- `bg-green-600 hover:bg-green-700` for green submit button
- `peer-data-[state=checked]:border-green-600` for selected radio card
- `md:grid-cols-2` for responsive two-column layout on desktop

### 3. Unit Tests (REMOVED OLD CSS)

The following CSS is NO LONGER NEEDED since we're using Tailwind/shadcn:

```css (DEPRECATED - DO NOT CREATE THIS FILE)
.simple-conversion-page {
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
}

.simple-conversion-page h1 {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.page-description {
  color: #666;
  font-size: 1rem;
  line-height: 1.6;
  margin-bottom: 2rem;
}

.conversion-form {
  background-color: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #333;
}

.required {
  color: #d32f2f;
}

.optional {
  color: #888;
  font-weight: normal;
  font-size: 0.9rem;
}

.form-group input[type="text"],
.form-group input[type="number"] {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input[type="text"]:focus,
.form-group input[type="number"]:focus {
  outline: none;
  border-color: #4caf50;
}

.form-group input.error {
  border-color: #d32f2f;
}

.error-message {
  display: block;
  color: #d32f2f;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

/* Mode Selection */
.mode-selection {
  margin-top: 2rem;
}

.mode-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 0.75rem;
}

.mode-option {
  border: 2px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  background-color: white;
}

.mode-option:hover {
  border-color: #4caf50;
  background-color: #f0f8f0;
}

.mode-option.selected {
  border-color: #4caf50;
  background-color: #e8f5e9;
}

.mode-option input[type="radio"] {
  margin-right: 0.5rem;
}

.mode-content h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: #333;
}

.mode-content p {
  margin: 0;
  font-size: 0.9rem;
  color: #666;
  line-height: 1.4;
}

/* Form Error Message */
.form-error-message {
  background-color: #ffebee;
  color: #d32f2f;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  border-left: 4px solid #d32f2f;
}

/* Form Actions */
.form-actions {
  margin-top: 2rem;
  display: flex;
  justify-content: flex-end;
}

.btn-submit {
  padding: 0.75rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  background-color: #4caf50;
}

.btn-submit:hover:not(:disabled) {
  background-color: #45a049;
}

.btn-submit:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

/* Responsive Design */
@media (max-width: 768px) {
  .simple-conversion-page {
    padding: 1rem;
  }

  .conversion-form {
    padding: 1.5rem;
  }

  .mode-options {
    grid-template-columns: 1fr;
  }

  .form-actions {
    justify-content: stretch;
  }

  .btn-submit {
    width: 100%;
  }
}
```

## Unit Tests

**Note**: Unit tests should be updated to:
1. Mock the `/conv/io-folder-data` endpoint to return test files
2. Test file selection from dropdown instead of text input
3. Use `fetch` instead of `axios` for API calls
4. Test Next.js `useRouter` instead of React Router's `useNavigate`

**File**: Tests should be created following Next.js testing patterns with Jest and React Testing Library.

Key test scenarios to cover:
1. **File list loading** - Mock `/conv/io-folder-data` and verify files populate dropdown
2. **File selection** - Select file from dropdown and verify form state updates
3. **Form validation** - Verify required field validation (file, title, author)
4. **Year validation** - Test invalid year format
5. **Mode selection** - Test automatic and manual mode radio buttons
6. **Form submission** - Mock API call and verify navigation
7. **Error handling** - Test API error display
8. **Loading states** - Test file loading and submission loading states

Sample test structure (to be fully implemented):

```typescript
/**
 * Unit tests for Simple Conversion Page
 *
 * NOTE: These are sample test outlines. Full implementation should follow
 * Next.js testing patterns with proper mocking of fetch and useRouter.
 */

describe('SimpleConversionPage', () => {
  beforeEach(() => {
    // Mock fetch for /conv/io-folder-data
    global.fetch = jest.fn((url) => {
      if (url.includes('/conv/io-folder-data')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            input_files: ['test1.pdf', 'test2.epub']
          })
        });
      }
      return Promise.reject(new Error('Unexpected URL'));
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('loads and displays input files in dropdown', async () => {
    // Test implementation here
  });

  it('validates required file selection', async () => {
    // Test "Please select a file" error message
  });

  it('validates required metadata fields', async () => {
    // Test title and author required validation
  });

  it('submits form with selected file', async () => {
    // Test full form submission with file from dropdown
  });

  // Additional tests for:
  // - Year field validation (invalid year < 1000 or > current year + 1)
  // - Form submission with automatic mode (verify fetch call and navigation)
  // - Form submission with manual mode (verify navigation to manual workflow)
  // - API error handling (verify error message display)
  // - Form disabled state during submission
  // - File dropdown selection updates selectedFile field
  // - File fetch error displays retry button
});
```

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

**Expected**: Manual mode submission navigates to manual workflow

#### TC9: Optional Year Field
**Steps**:
1. Select file from dropdown
2. Fill Title and Author
3. Leave Year field empty
4. Select mode (automatic or manual)
5. Submit form
6. Verify submission succeeds
7. Verify API receives `year: null`

**Expected**: Year field is optional, null sent when empty

#### TC10: API Error Handling
**Steps**:
1. Select file from dropdown: "invalid-file.pdf"
2. Fill all required fields
3. Submit
4. Verify API returns error (simulate by using non-existent file)
5. Verify error alert displays at top of form (red background)
6. Verify error message shows API error detail
7. Verify no navigation occurs
8. Verify form remains editable (not disabled)

**Expected**: API errors display without navigation

#### TC11: Form Disabled During Submission
**Steps**:
1. Fill all required fields
2. Click "Start Conversion"
3. Immediately verify:
   - Submit button is disabled
   - Submit button shows "Starting Conversion..."
   - File dropdown is disabled
   - All input fields are disabled
   - Mode selection radio buttons are disabled

**Expected**: All form controls disabled during API call

#### TC12: Responsive Design - Desktop
**Steps**:
1. View on desktop (>768px width)
2. Verify mode option cards display side-by-side (2 columns)
3. Verify adequate spacing between cards
4. Verify submit button positioned appropriately
5. Verify file dropdown full width

**Expected**: Desktop layout uses grid with 2 columns for mode cards

#### TC13: Responsive Design - Mobile
**Steps**:
1. Resize browser to <768px OR use mobile device
2. Verify mode option cards stack vertically (1 column)
3. Verify submit button full width
4. Verify readable text and adequate touch targets
5. Verify file dropdown full width

**Expected**: Mobile layout responsive, cards stack vertically

## Dependencies

- **Internal**:
  - T07 (API endpoints: `/api/simple-conversion/start`)
  - T08 (navigation button on conversion page)
  - Existing `/conv/io-folder-data` endpoint for file fetching
- **External**:
  - Next.js (App Router)
  - React
  - shadcn/ui components (Card, Button, Input, Label, RadioGroup, Select, Alert)
  - Tailwind CSS
  - lucide-react icons
  - TypeScript
- **Testing**: Jest, React Testing Library

## Assumptions

1. `/api/simple-conversion/start` endpoint implemented and working (T07)
2. `/conv/io-folder-data` endpoint returns `{ input_files: string[] }` format
3. Routes for `/simple-conversion/automatic/:id` and `/simple-conversion/manual/:id` will be created in T10/T11
4. Input folder contains PDF/EPUB files for conversion
5. NEXT_PUBLIC_API_URL environment variable configured
6. shadcn/ui components already installed in project

## Notes

- This is a **vertical slice** ticket (frontend + API integration)
- Uses existing input folder system (same as standard conversion workflow)
- File selection via dropdown (NOT manual text input, NOT file upload)
- Form validation happens client-side before API call
- Year field is optional but validated if provided (range: 1000 to current year + 1)
- Mode selection uses radio buttons with visual card selection
- Error messages display inline for field errors, alert banner for API/fetch errors
- Loading states: file fetch on mount, form submission
- All form fields disabled during submission
- Navigation happens after successful API response
- Uses Next.js App Router patterns (useRouter from next/navigation)
- Uses fetch API instead of axios
- Uses shadcn/ui components instead of custom CSS

## Definition of Done

- [ ] All code implemented as specified
- [ ] File dropdown fetches from `/conv/io-folder-data` endpoint
- [ ] File selection works correctly
- [ ] All unit tests pass
- [ ] Manual test plan completed (13 test cases)
- [ ] Form validation works for all fields
- [ ] Mode selection (automatic/manual) functional
- [ ] API integration successful with fetch API
- [ ] Navigation to workflow pages works (Next.js router)
- [ ] Error handling displays messages (fetch errors, API errors, validation errors)
- [ ] Loading states work (file fetch, form submission)
- [ ] Responsive design works on mobile and desktop
- [ ] Code follows Next.js and React best practices
- [ ] Uses shadcn/ui components consistently
