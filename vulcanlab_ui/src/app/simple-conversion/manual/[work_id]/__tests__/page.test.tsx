/**
 * Unit tests for Manual Workflow Page
 */

import React from 'react';
import { render, screen, waitFor, act, fireEvent } from '@testing-library/react';
import ManualWorkflowPage from '../page';

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useParams: () => ({ work_id: '123' }),
  useRouter: () => ({ push: mockPush }),
}));

// Mock clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(),
  },
});

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('ManualWorkflowPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockFetch.mockReset();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  const mockPromptLoad = () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        work_id: 123,
        classification: 'small',
        prompt: 'TEST PROMPT',
        instructions: 'TEST INSTRUCTION'
      }),
    });
  };

  it('fetches and displays prompt on mount', async () => {
    mockPromptLoad();

    await act(async () => {
      render(<ManualWorkflowPage />);
    });

    await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/api/simple-conversion/manual-prompt/123'));
        expect(screen.getByText('TEST PROMPT')).toBeInTheDocument();
        expect(screen.getByText('TEST INSTRUCTION')).toBeInTheDocument();
        expect(screen.getByText('SMALL')).toBeInTheDocument();
    });
  });

  it('copies prompt to clipboard', async () => {
    mockPromptLoad();

    await act(async () => {
      render(<ManualWorkflowPage />);
    });

    const copyBtn = screen.getByText('Copy to Clipboard');
    fireEvent.click(copyBtn);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('TEST PROMPT');
      expect(screen.getByText('Copied!')).toBeInTheDocument();
    });
  });

  it('submits manual response correctly', async () => {
    mockPromptLoad();
    // Manual submit success response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'complete' }),
    });
    // Results after submit
     mockFetch.mockResolvedValueOnce({ 
      ok: true, 
      json: async () => ({ 
        work_id: 123, 
        title: 'Title', 
        author: 'Auth',
        classification: 'small',
        token_count: 50,
        chunk_count: 1,
        chunks: []
      }) 
    });

    await act(async () => {
      render(<ManualWorkflowPage />);
    });

    const textarea = screen.getByPlaceholderText('Paste LLM response here (JSON format)...');
    fireEvent.change(textarea, { target: { value: '{"foo":"bar"}' } });
    
    // Have to select the manual tab content button
    const submitBtn = screen.getByText('Submit Response');
    fireEvent.click(submitBtn);

    await waitFor(() => {
       expect(mockFetch).toHaveBeenCalledWith(
           expect.stringContaining('/api/simple-conversion/manual-submit/123'),
           expect.objectContaining({
               method: 'POST',
               body: JSON.stringify({ llm_response: '{"foo":"bar"}' })
           })
       );
       expect(screen.getByText('Success')).toBeInTheDocument();
    });
  });

  it('executes automatic mode correctly', async () => {
    mockPromptLoad();
    // Auto execute call
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    // Poll status: complete
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ step: 'complete' }) });
    // Fetch result
    mockFetch.mockResolvedValueOnce({ 
      ok: true, 
      json: async () => ({ 
        work_id: 123, 
        title: 'Title', 
        author: 'Auth',
        classification: 'small',
        token_count: 50,
        chunk_count: 1,
        chunks: []
      }) 
    });

    await act(async () => {
      render(<ManualWorkflowPage />);
    });

    // Switch to auto tab
    const autoTab = screen.getByText('Option 2: Automatic Execution');
    fireEvent.click(autoTab);

    const autoBtn = screen.getByText('Run Automatically');
    fireEvent.click(autoBtn);
    
    // Advance timer for polling
    await act(async () => {
        jest.advanceTimersByTime(2000);
    });

    await waitFor(() => {
       expect(mockFetch).toHaveBeenCalledWith(
           expect.stringContaining('/api/simple-conversion/execute-auto/123'),
           expect.objectContaining({ method: 'POST' })
       );
       expect(screen.getByText('Success')).toBeInTheDocument();
    });
  });

  it('displays errors properly', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network blew up'));

    await act(async () => {
        render(<ManualWorkflowPage />);
    });

    await waitFor(() => {
        expect(screen.getByText('Network blew up')).toBeInTheDocument();
    });
  });
});
