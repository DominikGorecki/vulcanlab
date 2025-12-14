# T09: Simple Conversion Page with Metadata Form

**Status**: PENDING
**Priority**: High
**Type**: Vertical Slice (Frontend + API Integration)
**Depends On**: T07 (API endpoints), T08 (Navigation button)
**Blocks**: T10, T11 (Workflow pages depend on this foundation)

## Overview

Implement the main Simple Conversion page with a form to collect file path and metadata (title, author, year), mode selection (Automatic/Manual), and submission to initiate the conversion pipeline. This page is the entry point to the simple conversion workflow.

## Acceptance Criteria

- [ ] Page displays form with file path input
- [ ] Form includes title, author, year (optional) metadata fields
- [ ] Radio buttons for mode selection (Automatic/Manual)
- [ ] Submit button calls `/api/simple-conversion/start` endpoint
- [ ] Form validation (required fields, valid year)
- [ ] Success: navigate to appropriate workflow page (T10 for auto, T11 for manual)
- [ ] Error handling displays error messages
- [ ] Loading state during submission
- [ ] Responsive design for mobile and desktop
- [ ] Unit tests for component logic
- [ ] Manual test plan completed successfully

## Technical Implementation

### 1. Main Component

**File**: `vulcanlab_ui/src/components/simple-conversion/SimpleConversionPage.tsx` (REPLACE placeholder from T08)

```typescript
/**
 * Simple Conversion Page
 *
 * Entry point for the simple conversion workflow. Collects file path,
 * metadata, and execution mode, then initiates the conversion process.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './SimpleConversionPage.css';

interface FormData {
  filePath: string;
  title: string;
  author: string;
  year: string;
  mode: 'automatic' | 'manual';
}

interface FormErrors {
  filePath?: string;
  title?: string;
  author?: string;
  year?: string;
}

export const SimpleConversionPage: React.FC = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState<FormData>({
    filePath: '',
    title: '',
    author: '',
    year: '',
    mode: 'automatic'
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.filePath.trim()) {
      newErrors.filePath = 'File path is required';
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
      const response = await axios.post('/api/simple-conversion/start', {
        file_path: formData.filePath,
        title: formData.title,
        author: formData.author,
        year: formData.year ? parseInt(formData.year, 10) : null,
        mode: formData.mode
      });

      const { work_id, mode } = response.data;

      // Navigate to appropriate workflow page
      if (mode === 'automatic') {
        navigate(`/simple-conversion/automatic/${work_id}`);
      } else {
        navigate(`/simple-conversion/manual/${work_id}`);
      }

    } catch (err: any) {
      console.error('Failed to start conversion:', err);
      const message = err.response?.data?.detail || 'Failed to start conversion';
      setErrorMessage(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="simple-conversion-page">
      <h1>Simple Conversion</h1>

      <p className="page-description">
        Convert your PDF or EPUB document in a streamlined single-page workflow.
        Provide the file path and metadata, then choose automatic or manual execution.
      </p>

      <form onSubmit={handleSubmit} className="conversion-form">
        {/* File Path */}
        <div className="form-group">
          <label htmlFor="filePath">
            File Path <span className="required">*</span>
          </label>
          <input
            id="filePath"
            name="filePath"
            type="text"
            value={formData.filePath}
            onChange={handleInputChange}
            placeholder="/path/to/document.pdf"
            disabled={submitting}
            className={errors.filePath ? 'error' : ''}
          />
          {errors.filePath && (
            <span className="error-message">{errors.filePath}</span>
          )}
        </div>

        {/* Title */}
        <div className="form-group">
          <label htmlFor="title">
            Title <span className="required">*</span>
          </label>
          <input
            id="title"
            name="title"
            type="text"
            value={formData.title}
            onChange={handleInputChange}
            placeholder="Document title"
            disabled={submitting}
            className={errors.title ? 'error' : ''}
          />
          {errors.title && (
            <span className="error-message">{errors.title}</span>
          )}
        </div>

        {/* Author */}
        <div className="form-group">
          <label htmlFor="author">
            Author <span className="required">*</span>
          </label>
          <input
            id="author"
            name="author"
            type="text"
            value={formData.author}
            onChange={handleInputChange}
            placeholder="Author name"
            disabled={submitting}
            className={errors.author ? 'error' : ''}
          />
          {errors.author && (
            <span className="error-message">{errors.author}</span>
          )}
        </div>

        {/* Year (Optional) */}
        <div className="form-group">
          <label htmlFor="year">
            Publication Year <span className="optional">(optional)</span>
          </label>
          <input
            id="year"
            name="year"
            type="number"
            value={formData.year}
            onChange={handleInputChange}
            placeholder="2023"
            disabled={submitting}
            className={errors.year ? 'error' : ''}
          />
          {errors.year && (
            <span className="error-message">{errors.year}</span>
          )}
        </div>

        {/* Mode Selection */}
        <div className="form-group mode-selection">
          <label>Execution Mode</label>

          <div className="mode-options">
            <label className={`mode-option ${formData.mode === 'automatic' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="mode"
                value="automatic"
                checked={formData.mode === 'automatic'}
                onChange={() => handleModeChange('automatic')}
                disabled={submitting}
              />
              <div className="mode-content">
                <h3>Automatic</h3>
                <p>
                  Pipeline runs automatically using LLM. No manual intervention required.
                </p>
              </div>
            </label>

            <label className={`mode-option ${formData.mode === 'manual' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="mode"
                value="manual"
                checked={formData.mode === 'manual'}
                onChange={() => handleModeChange('manual')}
                disabled={submitting}
              />
              <div className="mode-content">
                <h3>Manual</h3>
                <p>
                  Copy prompt, paste into your own LLM, and submit the result.
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Error Message */}
        {errorMessage && (
          <div className="form-error-message">
            {errorMessage}
          </div>
        )}

        {/* Submit Button */}
        <div className="form-actions">
          <button
            type="submit"
            disabled={submitting}
            className="btn-primary btn-submit"
          >
            {submitting ? 'Starting Conversion...' : 'Start Conversion'}
          </button>
        </div>
      </form>
    </div>
  );
};
```

### 2. CSS Styling

**File**: `vulcanlab_ui/src/components/simple-conversion/SimpleConversionPage.css` (NEW)

```css
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

**File**: `vulcanlab_ui/src/components/simple-conversion/__tests__/SimpleConversionPage.test.tsx` (NEW)

```typescript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import { SimpleConversionPage } from '../SimpleConversionPage';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate
}));

describe('SimpleConversionPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <SimpleConversionPage />
      </BrowserRouter>
    );
  };

  it('renders form with all required fields', () => {
    renderComponent();

    expect(screen.getByLabelText(/File Path/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Title/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Author/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Publication Year/)).toBeInTheDocument();
    expect(screen.getByText(/Automatic/)).toBeInTheDocument();
    expect(screen.getByText(/Manual/)).toBeInTheDocument();
  });

  it('validates required fields on submit', async () => {
    renderComponent();

    const submitButton = screen.getByRole('button', { name: /Start Conversion/ });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('File path is required')).toBeInTheDocument();
      expect(screen.getByText('Title is required')).toBeInTheDocument();
      expect(screen.getByText('Author is required')).toBeInTheDocument();
    });

    expect(mockedAxios.post).not.toHaveBeenCalled();
  });

  it('validates year field format', async () => {
    renderComponent();

    const yearInput = screen.getByLabelText(/Publication Year/);
    fireEvent.change(yearInput, { target: { value: '999' } });

    const submitButton = screen.getByRole('button', { name: /Start Conversion/ });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Please enter a valid year/)).toBeInTheDocument();
    });
  });

  it('submits form with automatic mode', async () => {
    mockedAxios.post.mockResolvedValue({
      data: { work_id: 123, mode: 'automatic' }
    });

    renderComponent();

    fireEvent.change(screen.getByLabelText(/File Path/), {
      target: { value: '/test/file.pdf' }
    });
    fireEvent.change(screen.getByLabelText(/Title/), {
      target: { value: 'Test Book' }
    });
    fireEvent.change(screen.getByLabelText(/Author/), {
      target: { value: 'Test Author' }
    });

    const submitButton = screen.getByRole('button', { name: /Start Conversion/ });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/simple-conversion/start', {
        file_path: '/test/file.pdf',
        title: 'Test Book',
        author: 'Test Author',
        year: null,
        mode: 'automatic'
      });
    });

    expect(mockNavigate).toHaveBeenCalledWith('/simple-conversion/automatic/123');
  });

  it('submits form with manual mode', async () => {
    mockedAxios.post.mockResolvedValue({
      data: { work_id: 456, mode: 'manual' }
    });

    renderComponent();

    fireEvent.change(screen.getByLabelText(/File Path/), {
      target: { value: '/test/file.pdf' }
    });
    fireEvent.change(screen.getByLabelText(/Title/), {
      target: { value: 'Test Book' }
    });
    fireEvent.change(screen.getByLabelText(/Author/), {
      target: { value: 'Test Author' }
    });

    // Select manual mode
    const manualRadio = screen.getByLabelText(/Manual/);
    fireEvent.click(manualRadio);

    const submitButton = screen.getByRole('button', { name: /Start Conversion/ });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/simple-conversion/manual/456');
    });
  });

  it('displays error message on API failure', async () => {
    mockedAxios.post.mockRejectedValue({
      response: { data: { detail: 'File not found' } }
    });

    renderComponent();

    fireEvent.change(screen.getByLabelText(/File Path/), {
      target: { value: '/invalid/path.pdf' }
    });
    fireEvent.change(screen.getByLabelText(/Title/), {
      target: { value: 'Test' }
    });
    fireEvent.change(screen.getByLabelText(/Author/), {
      target: { value: 'Author' }
    });

    const submitButton = screen.getByRole('button', { name: /Start Conversion/ });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('File not found')).toBeInTheDocument();
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('disables form during submission', async () => {
    mockedAxios.post.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

    renderComponent();

    fireEvent.change(screen.getByLabelText(/File Path/), {
      target: { value: '/test.pdf' }
    });
    fireEvent.change(screen.getByLabelText(/Title/), {
      target: { value: 'Test' }
    });
    fireEvent.change(screen.getByLabelText(/Author/), {
      target: { value: 'Author' }
    });

    const submitButton = screen.getByRole('button', { name: /Start Conversion/ });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(submitButton).toBeDisabled();
      expect(screen.getByLabelText(/File Path/)).toBeDisabled();
    });
  });
});
```

## Manual Test Plan

### Setup
1. Start frontend dev server
2. Start backend API server
3. Navigate to `/simple-conversion` page

### Test Cases

#### TC1: Form Rendering
**Steps**:
1. Navigate to `/simple-conversion`
2. Verify all fields render: File Path, Title, Author, Year, Mode
3. Verify "Automatic" mode is selected by default
4. Verify submit button displays "Start Conversion"

**Expected**: Form renders correctly with all fields

#### TC2: Required Field Validation
**Steps**:
1. Leave all required fields empty
2. Click "Start Conversion"
3. Verify error messages appear for File Path, Title, Author
4. Verify form does not submit

**Expected**: Validation prevents submission

#### TC3: Year Field Validation
**Steps**:
1. Fill required fields correctly
2. Enter invalid year (e.g., "999" or "3000")
3. Submit form
4. Verify error message about valid year

**Expected**: Year validation works

#### TC4: Mode Selection - Automatic
**Steps**:
1. Select "Automatic" mode (default)
2. Verify card highlights with green border
3. Fill all required fields
4. Submit
5. Verify navigates to `/simple-conversion/automatic/{work_id}`

**Expected**: Automatic mode selected and navigates correctly

#### TC5: Mode Selection - Manual
**Steps**:
1. Click "Manual" mode radio button
2. Verify card highlights
3. Fill all required fields
4. Submit
5. Verify navigates to `/simple-conversion/manual/{work_id}`

**Expected**: Manual mode selected and navigates correctly

#### TC6: Successful Submission
**Steps**:
1. Fill form:
   - File Path: `/test/sample.pdf`
   - Title: "Sample Book"
   - Author: "Test Author"
   - Year: 2023
   - Mode: Automatic
2. Click submit
3. Verify button shows "Starting Conversion..."
4. Wait for API response
5. Verify navigation occurs

**Expected**: Form submits successfully

#### TC7: API Error Handling
**Steps**:
1. Fill form with invalid file path
2. Submit
3. Verify error message displays (red box at bottom of form)
4. Verify no navigation occurs
5. Verify form remains editable

**Expected**: Error handled gracefully

#### TC8: Responsive Design - Desktop
**Steps**:
1. View on desktop (>768px width)
2. Verify mode options display side-by-side
3. Verify submit button aligned right

**Expected**: Desktop layout correct

#### TC9: Responsive Design - Mobile
**Steps**:
1. Resize to <768px OR use mobile device
2. Verify mode options stack vertically
3. Verify submit button full width

**Expected**: Mobile layout responsive

## Dependencies

- **Internal**: T07 (API endpoints), T08 (navigation button)
- **External**: React, React Router, Axios, TypeScript
- **Testing**: Jest, React Testing Library

## Assumptions

1. `/api/simple-conversion/start` endpoint implemented (T07)
2. Routes for `/simple-conversion/automatic/:id` and `/simple-conversion/manual/:id` will be created in T10/T11
3. Axios configured with proper base URL

## Notes

- This is a **vertical slice** ticket (frontend + API integration)
- Form validation happens client-side before API call
- Year field is optional but validated if provided
- Mode selection uses radio buttons with visual card selection
- Error messages display inline for field errors, banner for API errors
- Loading state disables all form fields during submission
- Navigation happens after successful API response

## Definition of Done

- [ ] All code implemented as specified
- [ ] All unit tests pass (7 tests)
- [ ] Manual test plan completed
- [ ] Form validation works for all fields
- [ ] Mode selection (automatic/manual) functional
- [ ] API integration successful
- [ ] Navigation to workflow pages works
- [ ] Error handling displays messages
- [ ] Responsive design works on mobile and desktop
- [ ] Code follows React best practices
