# T10: Automatic Mode Workflow with Status Tracking

**Status**: PENDING
**Priority**: High
**Type**: Frontend + API Integration
**Depends On**: T07 (API endpoints), T09 (Entry form)
**Blocks**: None

## Overview

Implement the automatic mode workflow page that executes the full conversion pipeline automatically, displays real-time status updates via polling, and shows final results with chunk preview. This page handles the "Automatic" execution path from T09.

## Acceptance Criteria

- [ ] Page receives work_id from URL parameter
- [ ] Auto-executes pipeline on mount via `/api/simple-conversion/execute-auto`
- [ ] Polls `/api/simple-conversion/status` every 2 seconds during execution
- [ ] Displays current step (converting, parsing, sanitizing, chunking, complete)
- [ ] Shows progress indicator for each step
- [ ] Displays classification (small/large) when available
- [ ] Shows token count and chunk count when available
- [ ] On completion, fetches and displays results via `/api/simple-conversion/results`
- [ ] Shows chunk preview list (heading + content preview)
- [ ] Error handling displays error messages
- [ ] "View Full Results" button navigates to results page (if exists) or displays inline
- [ ] Unit tests for component logic
- [ ] Manual test plan completed successfully

## Technical Implementation

### 1. Main Component

**File**: `vulcanlab_ui/src/components/simple-conversion/AutomaticWorkflow.tsx` (NEW)

```typescript
/**
 * Automatic Workflow Page
 *
 * Handles automatic execution of the simple conversion pipeline.
 * Executes the pipeline, polls for status updates, and displays results.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './AutomaticWorkflow.css';

interface StatusData {
  work_id: number;
  step: string;
  classification?: string;
  token_count?: number;
  chunk_count?: number;
  mode?: string;
  error_message?: string;
}

interface ChunkResult {
  id: number;
  heading_level: number;
  heading_text: string;
  start_line: number;
  end_line: number;
  content_preview: string;
}

interface ResultsData {
  work_id: number;
  title: string;
  author: string;
  classification: string;
  token_count: number;
  chunk_count: number;
  chunks: ChunkResult[];
}

type ExecutionStep = 'executing' | 'parsing' | 'parsed' | 'sanitizing' | 'sanitized' | 'chunking' | 'chunked' | 'complete' | 'error';

export const AutomaticWorkflow: React.FC = () => {
  const { workId } = useParams<{ workId: string }>();
  const navigate = useNavigate();

  const [status, setStatus] = useState<StatusData | null>(null);
  const [results, setResults] = useState<ResultsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [executing, setExecuting] = useState(false);
  const [completed, setCompleted] = useState(false);

  // Start automatic execution on mount
  useEffect(() => {
    if (!workId) {
      setError('No work ID provided');
      return;
    }

    executeAutomatic();
  }, [workId]);

  // Poll for status while executing
  useEffect(() => {
    if (!executing || completed) return;

    const interval = setInterval(async () => {
      await fetchStatus();
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [executing, completed, workId]);

  const executeAutomatic = async () => {
    try {
      setExecuting(true);
      setError(null);

      await axios.post(`/api/simple-conversion/execute-auto/${workId}`);

      // Execution started, begin polling
      await fetchStatus();

    } catch (err: any) {
      console.error('Failed to execute automatic pipeline:', err);
      const message = err.response?.data?.detail || 'Failed to execute pipeline';
      setError(message);
      setExecuting(false);
    }
  };

  const fetchStatus = async () => {
    try {
      const response = await axios.get<StatusData>(
        `/api/simple-conversion/status/${workId}`
      );

      const statusData = response.data;
      setStatus(statusData);

      // Check if complete
      if (statusData.step === 'complete') {
        setExecuting(false);
        setCompleted(true);
        await fetchResults();
      } else if (statusData.step === 'error') {
        setExecuting(false);
        setError(statusData.error_message || 'Pipeline execution failed');
      }

    } catch (err: any) {
      console.error('Failed to fetch status:', err);
      // Don't stop polling on status fetch errors - might be temporary
    }
  };

  const fetchResults = async () => {
    try {
      const response = await axios.get<ResultsData>(
        `/api/simple-conversion/results/${workId}`
      );

      setResults(response.data);

    } catch (err: any) {
      console.error('Failed to fetch results:', err);
      const message = err.response?.data?.detail || 'Failed to load results';
      setError(message);
    }
  };

  const getStepLabel = (step: string): string => {
    const labels: Record<string, string> = {
      executing: 'Starting pipeline...',
      parsing: 'Parsing and classifying document...',
      parsed: 'Document parsed and classified',
      sanitizing: 'Sanitizing markdown...',
      sanitized: 'Markdown sanitized',
      chunking: 'Creating chunks...',
      chunked: 'Chunks created',
      complete: 'Pipeline complete!',
      error: 'Error occurred'
    };

    return labels[step] || step;
  };

  const isStepComplete = (stepName: string): boolean => {
    if (!status) return false;

    const stepOrder = ['parsing', 'parsed', 'sanitizing', 'sanitized', 'chunking', 'chunked', 'complete'];
    const currentIndex = stepOrder.indexOf(status.step);
    const checkIndex = stepOrder.indexOf(stepName);

    return currentIndex >= checkIndex;
  };

  const isStepActive = (stepName: string): boolean => {
    return status?.step === stepName;
  };

  if (!workId) {
    return (
      <div className="automatic-workflow error-state">
        <h1>Error</h1>
        <p>No work ID provided</p>
      </div>
    );
  }

  return (
    <div className="automatic-workflow">
      <h1>Automatic Conversion</h1>

      {/* Status Display */}
      {status && !completed && (
        <div className="status-section">
          <h2>Pipeline Status</h2>

          <div className="current-step">
            <div className="spinner" />
            <p>{getStepLabel(status.step)}</p>
          </div>

          {/* Progress Steps */}
          <div className="progress-steps">
            <div className={`step ${isStepComplete('parsed') ? 'complete' : ''} ${isStepActive('parsing') ? 'active' : ''}`}>
              <div className="step-icon">1</div>
              <div className="step-label">Parse & Classify</div>
            </div>

            <div className={`step ${isStepComplete('sanitized') ? 'complete' : ''} ${isStepActive('sanitizing') ? 'active' : ''}`}>
              <div className="step-icon">2</div>
              <div className="step-label">Sanitize</div>
            </div>

            <div className={`step ${isStepComplete('chunked') ? 'complete' : ''} ${isStepActive('chunking') ? 'active' : ''}`}>
              <div className="step-icon">3</div>
              <div className="step-label">Chunk</div>
            </div>

            <div className={`step ${isStepComplete('complete') ? 'complete' : ''}`}>
              <div className="step-icon">✓</div>
              <div className="step-label">Complete</div>
            </div>
          </div>

          {/* Metadata Display */}
          {status.classification && (
            <div className="metadata-display">
              <div className="metadata-item">
                <strong>Classification:</strong> {status.classification.toUpperCase()}
              </div>
              {status.token_count && (
                <div className="metadata-item">
                  <strong>Token Count:</strong> {status.token_count.toLocaleString()}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-section">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/simple-conversion')} className="btn-secondary">
            Back to Start
          </button>
        </div>
      )}

      {/* Results Display */}
      {completed && results && (
        <div className="results-section">
          <h2>Conversion Complete!</h2>

          <div className="results-summary">
            <div className="summary-item">
              <strong>Title:</strong> {results.title}
            </div>
            <div className="summary-item">
              <strong>Author:</strong> {results.author}
            </div>
            <div className="summary-item">
              <strong>Classification:</strong> {results.classification.toUpperCase()}
            </div>
            <div className="summary-item">
              <strong>Token Count:</strong> {results.token_count.toLocaleString()}
            </div>
            <div className="summary-item">
              <strong>Chunks Created:</strong> {results.chunk_count}
            </div>
          </div>

          <h3>Chunks</h3>
          <div className="chunks-list">
            {results.chunks.map((chunk) => (
              <div key={chunk.id} className="chunk-item">
                <div className="chunk-header">
                  <span className="chunk-level">H{chunk.heading_level}</span>
                  <span className="chunk-heading">{chunk.heading_text}</span>
                  <span className="chunk-lines">
                    Lines {chunk.start_line}-{chunk.end_line}
                  </span>
                </div>
                <div className="chunk-preview">
                  {chunk.content_preview}
                </div>
              </div>
            ))}
          </div>

          <div className="results-actions">
            <button onClick={() => navigate('/simple-conversion')} className="btn-secondary">
              Start Another Conversion
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
```

### 2. CSS Styling

**File**: `vulcanlab_ui/src/components/simple-conversion/AutomaticWorkflow.css` (NEW)

```css
.automatic-workflow {
  padding: 2rem;
  max-width: 1000px;
  margin: 0 auto;
}

.automatic-workflow h1 {
  font-size: 2rem;
  margin-bottom: 2rem;
}

/* Status Section */
.status-section {
  background-color: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
}

.status-section h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
}

.current-step {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  font-size: 1.1rem;
  color: #333;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #4caf50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Progress Steps */
.progress-steps {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin: 2rem 0;
}

.step {
  text-align: center;
  opacity: 0.4;
  transition: opacity 0.3s;
}

.step.active {
  opacity: 1;
}

.step.complete {
  opacity: 1;
}

.step-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: #ddd;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 0.5rem;
  font-weight: bold;
  font-size: 1.2rem;
  transition: all 0.3s;
}

.step.active .step-icon {
  background-color: #4caf50;
  color: white;
  box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
}

.step.complete .step-icon {
  background-color: #4caf50;
  color: white;
}

.step-label {
  font-size: 0.9rem;
  color: #666;
}

.step.active .step-label {
  color: #333;
  font-weight: 600;
}

/* Metadata Display */
.metadata-display {
  background-color: white;
  border-radius: 4px;
  padding: 1rem;
  margin-top: 1.5rem;
}

.metadata-item {
  padding: 0.5rem 0;
  border-bottom: 1px solid #eee;
}

.metadata-item:last-child {
  border-bottom: none;
}

.metadata-item strong {
  margin-right: 0.5rem;
  color: #333;
}

/* Error Section */
.error-section {
  background-color: #ffebee;
  border: 1px solid #d32f2f;
  border-left: 4px solid #d32f2f;
  border-radius: 4px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.error-section h2 {
  color: #d32f2f;
  margin-top: 0;
}

.error-section p {
  color: #c62828;
  margin-bottom: 1rem;
}

/* Results Section */
.results-section {
  background-color: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 2rem;
}

.results-section h2 {
  color: #4caf50;
  margin-top: 0;
}

.results-summary {
  background-color: white;
  border-radius: 4px;
  padding: 1.5rem;
  margin: 1.5rem 0;
}

.summary-item {
  padding: 0.75rem 0;
  border-bottom: 1px solid #eee;
}

.summary-item:last-child {
  border-bottom: none;
}

.summary-item strong {
  display: inline-block;
  width: 150px;
  color: #333;
}

/* Chunks List */
.results-section h3 {
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.chunks-list {
  max-height: 500px;
  overflow-y: auto;
  background-color: white;
  border-radius: 4px;
  padding: 1rem;
}

.chunk-item {
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 1rem;
  margin-bottom: 1rem;
  transition: box-shadow 0.2s;
}

.chunk-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chunk-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.chunk-level {
  background-color: #4caf50;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 600;
}

.chunk-heading {
  flex: 1;
  font-weight: 600;
  color: #333;
}

.chunk-lines {
  font-size: 0.875rem;
  color: #888;
}

.chunk-preview {
  color: #666;
  font-size: 0.9rem;
  line-height: 1.5;
  padding-left: 3rem;
}

/* Results Actions */
.results-actions {
  margin-top: 2rem;
  display: flex;
  justify-content: flex-end;
}

/* Responsive Design */
@media (max-width: 768px) {
  .automatic-workflow {
    padding: 1rem;
  }

  .progress-steps {
    grid-template-columns: repeat(2, 1fr);
  }

  .summary-item strong {
    display: block;
    width: auto;
    margin-bottom: 0.25rem;
  }

  .chunk-header {
    flex-wrap: wrap;
  }

  .chunk-preview {
    padding-left: 0;
  }

  .results-actions {
    justify-content: stretch;
  }

  .results-actions button {
    width: 100%;
  }
}
```

### 3. Routing Setup

**File**: `vulcanlab_ui/src/App.tsx` (MODIFIED)

Add route for automatic workflow:

```typescript
import { AutomaticWorkflow } from './components/simple-conversion/AutomaticWorkflow';

// In your Routes configuration:
<Route path="/simple-conversion/automatic/:workId" element={<AutomaticWorkflow />} />
```

## Unit Tests

**File**: `vulcanlab_ui/src/components/simple-conversion/__tests__/AutomaticWorkflow.test.tsx` (NEW)

```typescript
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import axios from 'axios';
import { AutomaticWorkflow } from '../AutomaticWorkflow';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

const renderComponent = (workId: string = '123') => {
  return render(
    <BrowserRouter>
      <Routes>
        <Route path="/simple-conversion/automatic/:workId" element={<AutomaticWorkflow />} />
      </Routes>
    </BrowserRouter>,
    { initialEntries: [`/simple-conversion/automatic/${workId}`] }
  );
};

describe('AutomaticWorkflow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('executes automatic pipeline on mount', async () => {
    mockedAxios.post.mockResolvedValue({ data: {} });
    mockedAxios.get.mockResolvedValue({
      data: { work_id: 123, step: 'parsing' }
    });

    renderComponent();

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/simple-conversion/execute-auto/123');
    });
  });

  it('polls status during execution', async () => {
    mockedAxios.post.mockResolvedValue({ data: {} });
    mockedAxios.get.mockResolvedValue({
      data: { work_id: 123, step: 'parsing' }
    });

    renderComponent();

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/simple-conversion/status/123');
    });

    // Advance time to trigger next poll
    jest.advanceTimersByTime(2000);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledTimes(2);
    });
  });

  it('displays classification and token count when available', async () => {
    mockedAxios.post.mockResolvedValue({ data: {} });
    mockedAxios.get.mockResolvedValue({
      data: {
        work_id: 123,
        step: 'sanitizing',
        classification: 'small',
        token_count: 5000
      }
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/Classification:/)).toBeInTheDocument();
      expect(screen.getByText(/SMALL/)).toBeInTheDocument();
      expect(screen.getByText(/5,000/)).toBeInTheDocument();
    });
  });

  it('fetches and displays results when complete', async () => {
    mockedAxios.post.mockResolvedValue({ data: {} });
    mockedAxios.get
      .mockResolvedValueOnce({
        data: { work_id: 123, step: 'complete' }
      })
      .mockResolvedValueOnce({
        data: {
          work_id: 123,
          title: 'Test Book',
          author: 'Test Author',
          classification: 'small',
          token_count: 5000,
          chunk_count: 3,
          chunks: [
            {
              id: 1,
              heading_level: 1,
              heading_text: 'Chapter 1',
              start_line: 1,
              end_line: 10,
              content_preview: 'Preview text...'
            }
          ]
        }
      });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Conversion Complete!')).toBeInTheDocument();
      expect(screen.getByText('Test Book')).toBeInTheDocument();
      expect(screen.getByText('Chapter 1')).toBeInTheDocument();
    });
  });

  it('displays error message on failure', async () => {
    mockedAxios.post.mockRejectedValue({
      response: { data: { detail: 'Pipeline failed' } }
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Pipeline failed')).toBeInTheDocument();
    });
  });
});
```

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

**Expected**: Metadata shows after parsing

#### TC4: Completion and Results
**Steps**:
1. Wait for pipeline to complete
2. Verify "Conversion Complete!" message
3. Verify summary shows: title, author, classification, token count, chunk count
4. Verify chunks list displays with headings
5. Verify chunk preview text shown

**Expected**: Full results displayed after completion

#### TC5: Chunk List Rendering
**Steps**:
1. Examine chunks list
2. Verify each chunk shows:
   - Heading level badge (H1, H2, etc.)
   - Heading text
   - Line numbers
   - Content preview
3. Verify scrollable if many chunks

**Expected**: Chunks rendered correctly

#### TC6: Error Handling
**Steps**:
1. Trigger an error (e.g., invalid work_id or backend failure)
2. Verify error section displays with message
3. Verify "Back to Start" button appears
4. Click button, verify returns to start page

**Expected**: Errors handled gracefully

#### TC7: Polling Stops on Completion
**Steps**:
1. Monitor network tab during execution
2. Verify status polling happens every 2 seconds
3. Wait for completion
4. Verify polling stops after completion

**Expected**: Polling ceases when done

#### TC8: Responsive Design
**Steps**:
1. View on mobile device (<768px)
2. Verify progress steps adapt to smaller screen
3. Verify chunks list readable on mobile
4. Verify summary items stack properly

**Expected**: Mobile layout responsive

## Dependencies

- **Internal**: T07 (API endpoints), T09 (entry form)
- **External**: React, React Router, Axios, TypeScript
- **Testing**: Jest, React Testing Library

## Assumptions

1. `/api/simple-conversion/execute-auto` runs full pipeline
2. Status polling necessary because execution is async
3. 2-second poll interval balances responsiveness and server load
4. Results endpoint returns chunks in order

## Notes

- This is a **frontend + API integration** ticket
- Polling mechanism updates UI in real-time
- Progress visualization helps user understand pipeline stages
- Error handling allows recovery by returning to start
- Chunk preview limited to 200 chars (from API)
- No manual intervention required in this workflow

## Definition of Done

- [ ] All code implemented as specified
- [ ] All unit tests pass (5 tests)
- [ ] Manual test plan completed
- [ ] Pipeline executes automatically on page load
- [ ] Status polling works every 2 seconds
- [ ] Progress steps update in real-time
- [ ] Results display on completion
- [ ] Error handling shows messages
- [ ] Polling stops after completion or error
- [ ] Responsive design works on mobile and desktop
- [ ] Code follows React best practices
