# T11: Manual Mode Workflow with Dual Execution Options

**Status**: PENDING
**Priority**: High
**Type**: Frontend + API Integration
**Depends On**: T07 (API endpoints), T09 (Entry form)
**Blocks**: None

## Overview

Implement the manual mode workflow page that displays an LLM prompt for the user to copy/paste, provides two execution options (manual copy/paste OR direct automatic execution), and shows final results. This page handles the "Manual" execution path from T09 and gives users flexibility in how they interact with the LLM.

## Acceptance Criteria

- [ ] Page receives work_id from URL parameter
- [ ] Fetches prompt via `/api/simple-conversion/manual-prompt` on mount
- [ ] Displays full prompt text in copyable code block
- [ ] Shows instructions for manual LLM usage
- [ ] Displays classification (small/large) and instructions specific to that type
- [ ] **Option 1**: Text area for user to paste LLM response
- [ ] **Option 1**: Submit button calls `/api/simple-conversion/manual-submit`
- [ ] **Option 2**: "Run Automatically" button calls `/api/simple-conversion/execute-auto`
- [ ] Both options lead to results display via `/api/simple-conversion/results`
- [ ] Copy button copies prompt to clipboard
- [ ] Error handling displays error messages
- [ ] Loading states for both execution options
- [ ] Unit tests for component logic
- [ ] Manual test plan completed successfully

## Technical Implementation

### 1. Main Component

**File**: `vulcanlab_ui/src/components/simple-conversion/ManualWorkflow.tsx` (NEW)

```typescript
/**
 * Manual Workflow Page
 *
 * Handles manual execution mode for simple conversion pipeline.
 * Displays LLM prompt for user to copy/paste, with options to:
 * 1. Paste manual LLM response and submit
 * 2. Run automatically via direct LLM call
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './ManualWorkflow.css';

interface PromptData {
  work_id: number;
  classification: string;
  prompt: string;
  instructions: string;
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

export const ManualWorkflow: React.FC = () => {
  const { workId } = useParams<{ workId: string }>();
  const navigate = useNavigate();

  const [promptData, setPromptData] = useState<PromptData | null>(null);
  const [manualResponse, setManualResponse] = useState('');
  const [results, setResults] = useState<ResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  const [completed, setCompleted] = useState(false);

  // Fetch prompt on mount
  useEffect(() => {
    if (!workId) {
      setError('No work ID provided');
      setLoading(false);
      return;
    }

    fetchPrompt();
  }, [workId]);

  const fetchPrompt = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get<PromptData>(
        `/api/simple-conversion/manual-prompt/${workId}`
      );

      setPromptData(response.data);

    } catch (err: any) {
      console.error('Failed to fetch prompt:', err);
      const message = err.response?.data?.detail || 'Failed to load prompt';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const copyPromptToClipboard = async () => {
    if (!promptData) return;

    try {
      await navigator.clipboard.writeText(promptData.prompt);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
      alert('Failed to copy to clipboard');
    }
  };

  const handleManualSubmit = async () => {
    if (!manualResponse.trim()) {
      setError('Please paste the LLM response before submitting');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      await axios.post(`/api/simple-conversion/manual-submit/${workId}`, {
        llm_response: manualResponse
      });

      setCompleted(true);
      await fetchResults();

    } catch (err: any) {
      console.error('Failed to submit manual result:', err);
      const message = err.response?.data?.detail || 'Failed to process result';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAutoExecute = async () => {
    try {
      setExecuting(true);
      setError(null);

      await axios.post(`/api/simple-conversion/execute-auto/${workId}`);

      // Poll for completion
      await pollForCompletion();

    } catch (err: any) {
      console.error('Failed to execute automatically:', err);
      const message = err.response?.data?.detail || 'Failed to execute pipeline';
      setError(message);
      setExecuting(false);
    }
  };

  const pollForCompletion = async () => {
    const maxAttempts = 60; // 2 minutes max (2s intervals)
    let attempts = 0;

    const poll = async (): Promise<void> => {
      try {
        const response = await axios.get(`/api/simple-conversion/status/${workId}`);
        const status = response.data.step;

        if (status === 'complete') {
          setExecuting(false);
          setCompleted(true);
          await fetchResults();
          return;
        }

        if (status === 'error') {
          setExecuting(false);
          setError(response.data.error_message || 'Pipeline execution failed');
          return;
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(() => poll(), 2000);
        } else {
          setExecuting(false);
          setError('Execution timeout - please check status');
        }

      } catch (err) {
        console.error('Polling error:', err);
        setExecuting(false);
      }
    };

    await poll();
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

  if (!workId) {
    return (
      <div className="manual-workflow error-state">
        <h1>Error</h1>
        <p>No work ID provided</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="manual-workflow loading-state">
        <h1>Loading...</h1>
        <p>Preparing prompt...</p>
      </div>
    );
  }

  return (
    <div className="manual-workflow">
      <h1>Manual Conversion</h1>

      {!completed && promptData && (
        <>
          {/* Classification Info */}
          <div className="classification-info">
            <strong>Document Classification:</strong>{' '}
            <span className={`classification-badge ${promptData.classification}`}>
              {promptData.classification.toUpperCase()}
            </span>
          </div>

          {/* Instructions */}
          <div className="instructions-section">
            <h2>Instructions</h2>
            <p>{promptData.instructions}</p>
          </div>

          {/* Prompt Display */}
          <div className="prompt-section">
            <div className="prompt-header">
              <h2>LLM Prompt</h2>
              <button
                onClick={copyPromptToClipboard}
                className="btn-copy"
              >
                {copySuccess ? '✓ Copied!' : 'Copy to Clipboard'}
              </button>
            </div>

            <pre className="prompt-display">
              <code>{promptData.prompt}</code>
            </pre>
          </div>

          {/* Execution Options */}
          <div className="execution-options">
            <h2>Choose Execution Method</h2>

            {/* Option 1: Manual Paste */}
            <div className="option-card">
              <h3>Option 1: Manual LLM Execution</h3>
              <p>
                Copy the prompt above, paste it into your preferred LLM
                (ChatGPT, Claude, etc.), then paste the response below.
              </p>

              <textarea
                className="manual-response-input"
                placeholder="Paste LLM response here (should be JSON format)..."
                value={manualResponse}
                onChange={(e) => setManualResponse(e.target.value)}
                disabled={submitting || executing}
                rows={10}
              />

              <button
                onClick={handleManualSubmit}
                disabled={submitting || executing || !manualResponse.trim()}
                className="btn-primary"
              >
                {submitting ? 'Processing...' : 'Submit LLM Response'}
              </button>
            </div>

            {/* Option 2: Automatic */}
            <div className="option-card">
              <h3>Option 2: Automatic Execution</h3>
              <p>
                Run the LLM automatically using the configured LLM client.
                No copy/paste required.
              </p>

              <button
                onClick={handleAutoExecute}
                disabled={submitting || executing}
                className="btn-secondary btn-auto"
              >
                {executing ? 'Executing...' : 'Run Automatically'}
              </button>

              {executing && (
                <div className="executing-indicator">
                  <div className="spinner" />
                  <span>Running pipeline automatically...</span>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-section">
          <h2>Error</h2>
          <p>{error}</p>
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

**File**: `vulcanlab_ui/src/components/simple-conversion/ManualWorkflow.css` (NEW)

```css
.manual-workflow {
  padding: 2rem;
  max-width: 1000px;
  margin: 0 auto;
}

.manual-workflow h1 {
  font-size: 2rem;
  margin-bottom: 1.5rem;
}

/* Classification Info */
.classification-info {
  background-color: #f9f9f9;
  border-left: 4px solid #4caf50;
  padding: 1rem;
  margin-bottom: 1.5rem;
  border-radius: 4px;
}

.classification-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.875rem;
}

.classification-badge.small {
  background-color: #e3f2fd;
  color: #1976d2;
}

.classification-badge.large {
  background-color: #fff3e0;
  color: #f57c00;
}

/* Instructions */
.instructions-section {
  background-color: #e8f5e9;
  border: 1px solid #4caf50;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.instructions-section h2 {
  margin-top: 0;
  color: #2e7d32;
}

.instructions-section p {
  margin-bottom: 0;
  line-height: 1.6;
  color: #1b5e20;
}

/* Prompt Section */
.prompt-section {
  margin-bottom: 2rem;
}

.prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.prompt-header h2 {
  margin: 0;
}

.btn-copy {
  padding: 0.5rem 1rem;
  background-color: #2196f3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}

.btn-copy:hover {
  background-color: #1976d2;
}

.prompt-display {
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 1.5rem;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

.prompt-display code {
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Execution Options */
.execution-options {
  margin-top: 2rem;
}

.execution-options h2 {
  margin-bottom: 1.5rem;
}

.execution-options {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}

.option-card {
  border: 2px solid #ddd;
  border-radius: 8px;
  padding: 1.5rem;
  background-color: #fafafa;
}

.option-card h3 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: #333;
}

.option-card p {
  color: #666;
  margin-bottom: 1rem;
  line-height: 1.6;
}

.manual-response-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  resize: vertical;
  margin-bottom: 1rem;
}

.manual-response-input:focus {
  outline: none;
  border-color: #4caf50;
}

.option-card button {
  width: 100%;
  padding: 0.75rem;
  font-size: 1rem;
  font-weight: 600;
}

.btn-auto {
  background-color: #2196f3 !important;
}

.btn-auto:hover:not(:disabled) {
  background-color: #1976d2 !important;
}

.executing-indicator {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 1rem;
  padding: 1rem;
  background-color: #e3f2fd;
  border-radius: 4px;
  color: #1976d2;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #2196f3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Error Section */
.error-section {
  background-color: #ffebee;
  border: 1px solid #d32f2f;
  border-left: 4px solid #d32f2f;
  border-radius: 4px;
  padding: 1.5rem;
  margin: 2rem 0;
}

.error-section h2 {
  color: #d32f2f;
  margin-top: 0;
}

.error-section p {
  color: #c62828;
  margin-bottom: 0;
}

/* Results Section - Reuse from AutomaticWorkflow */
.results-section {
  background-color: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 2rem;
  margin-top: 2rem;
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

.results-actions {
  margin-top: 2rem;
  display: flex;
  justify-content: flex-end;
}

/* Responsive Design */
@media (max-width: 768px) {
  .manual-workflow {
    padding: 1rem;
  }

  .prompt-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }

  .btn-copy {
    width: 100%;
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

Add route for manual workflow:

```typescript
import { ManualWorkflow } from './components/simple-conversion/ManualWorkflow';

// In your Routes configuration:
<Route path="/simple-conversion/manual/:workId" element={<ManualWorkflow />} />
```

## Unit Tests

**File**: `vulcanlab_ui/src/components/simple-conversion/__tests__/ManualWorkflow.test.tsx` (NEW)

```typescript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import { ManualWorkflow } from '../ManualWorkflow';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn()
  }
});

describe('ManualWorkflow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches and displays prompt on mount', async () => {
    mockedAxios.get.mockResolvedValue({
      data: {
        work_id: 123,
        classification: 'small',
        prompt: 'Test prompt text',
        instructions: 'Test instructions'
      }
    });

    render(
      <BrowserRouter>
        <ManualWorkflow />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Test instructions')).toBeInTheDocument();
      expect(screen.getByText('Test prompt text')).toBeInTheDocument();
    });
  });

  it('copies prompt to clipboard', async () => {
    mockedAxios.get.mockResolvedValue({
      data: {
        work_id: 123,
        classification: 'small',
        prompt: 'Test prompt',
        instructions: 'Instructions'
      }
    });

    render(
      <BrowserRouter>
        <ManualWorkflow />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Copy to Clipboard')).toBeInTheDocument();
    });

    const copyButton = screen.getByText('Copy to Clipboard');
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Test prompt');
      expect(screen.getByText('✓ Copied!')).toBeInTheDocument();
    });
  });

  it('submits manual LLM response', async () => {
    mockedAxios.get
      .mockResolvedValueOnce({
        data: {
          work_id: 123,
          classification: 'small',
          prompt: 'Prompt',
          instructions: 'Instructions'
        }
      })
      .mockResolvedValueOnce({
        data: {
          work_id: 123,
          title: 'Test',
          author: 'Author',
          classification: 'small',
          token_count: 1000,
          chunk_count: 2,
          chunks: []
        }
      });

    mockedAxios.post.mockResolvedValue({ data: {} });

    render(
      <BrowserRouter>
        <ManualWorkflow />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Paste LLM response/)).toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText(/Paste LLM response/);
    fireEvent.change(textarea, { target: { value: '{"sanitized": "test"}' } });

    const submitButton = screen.getByText('Submit LLM Response');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/simple-conversion/manual-submit/undefined',
        { llm_response: '{"sanitized": "test"}' }
      );
    });
  });

  it('executes automatically when auto button clicked', async () => {
    mockedAxios.get.mockResolvedValue({
      data: {
        work_id: 123,
        classification: 'small',
        prompt: 'Prompt',
        instructions: 'Instructions'
      }
    });

    mockedAxios.post.mockResolvedValue({ data: {} });

    render(
      <BrowserRouter>
        <ManualWorkflow />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Run Automatically')).toBeInTheDocument();
    });

    const autoButton = screen.getByText('Run Automatically');
    fireEvent.click(autoButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/simple-conversion/execute-auto/undefined');
    });
  });
});
```

## Manual Test Plan

### Setup
1. Complete T09 form submission with "Manual" mode
2. Backend API ready to serve prompts
3. LLM client configured for automatic option

### Test Cases

#### TC1: Prompt Display
**Steps**:
1. Submit form in T09 with "Manual" mode
2. Verify navigation to `/simple-conversion/manual/{work_id}`
3. Verify prompt loads and displays
4. Verify instructions appear
5. Verify classification badge shows (SMALL or LARGE)

**Expected**: Prompt displays correctly

#### TC2: Copy to Clipboard
**Steps**:
1. Click "Copy to Clipboard" button
2. Verify button changes to "✓ Copied!"
3. Open text editor and paste (Ctrl+V)
4. Verify prompt text pasted correctly

**Expected**: Clipboard copy works

#### TC3: Manual Execution - Submit Response
**Steps**:
1. Copy prompt from page
2. Paste into ChatGPT/Claude
3. Get JSON response from LLM
4. Paste JSON into textarea on page
5. Click "Submit LLM Response"
6. Verify processing message appears
7. Wait for completion
8. Verify results display with chunks

**Expected**: Manual submission works end-to-end

#### TC4: Automatic Execution from Manual Page
**Steps**:
1. On manual workflow page
2. Scroll to "Option 2: Automatic Execution"
3. Click "Run Automatically" button
4. Verify "Executing..." message shows
5. Verify spinner appears
6. Wait for completion
7. Verify results display

**Expected**: Auto execution works from manual page

#### TC5: Validation - Empty Response
**Steps**:
1. Leave textarea empty
2. Click "Submit LLM Response"
3. Verify error message about pasting response

**Expected**: Empty submission prevented

#### TC6: Error Handling - Invalid JSON
**Steps**:
1. Paste invalid JSON (not proper format)
2. Submit
3. Verify error message displays
4. Verify can retry

**Expected**: Error handled gracefully

#### TC7: Classification-Specific Instructions
**Steps**:
1. Test with SMALL document
2. Verify instructions mention full document
3. Test with LARGE document
4. Verify instructions mention condensed version

**Expected**: Instructions match classification

#### TC8: Results Display
**Steps**:
1. Complete either manual or auto execution
2. Verify results section appears
3. Verify summary shows all metadata
4. Verify chunks list displays
5. Click "Start Another Conversion"
6. Verify returns to start page

**Expected**: Results rendered correctly

## Dependencies

- **Internal**: T07 (API endpoints), T09 (entry form)
- **External**: React, React Router, Axios, TypeScript, Clipboard API
- **Testing**: Jest, React Testing Library

## Assumptions

1. `/api/simple-conversion/manual-prompt` returns formatted prompt
2. Users understand how to use ChatGPT/Claude interfaces
3. LLM responses will be valid JSON (with error handling for invalid)
4. Clipboard API supported in target browsers

## Notes

- This is a **frontend + API integration** ticket
- Provides two execution paths from same page
- Manual option gives users control/transparency
- Auto option provides convenience
- Clipboard copy improves UX
- Polling used for auto execution status
- Results display shared with T10

## Definition of Done

- [ ] All code implemented as specified
- [ ] All unit tests pass (4 tests)
- [ ] Manual test plan completed
- [ ] Prompt fetches and displays on mount
- [ ] Copy to clipboard works
- [ ] Manual LLM response submission works
- [ ] Automatic execution option works
- [ ] Both paths lead to results display
- [ ] Error handling shows messages
- [ ] Responsive design works on mobile and desktop
- [ ] Code follows React best practices
