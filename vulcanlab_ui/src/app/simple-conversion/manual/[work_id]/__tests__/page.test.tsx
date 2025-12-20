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
    mockFetch.mockReset();
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
        expect(screen.getByText('small')).toBeInTheDocument();
    });
  });

  it('copies prompt to clipboard', async () => {
    mockPromptLoad();

    await act(async () => {
      render(<ManualWorkflowPage />);
    });

    await waitFor(() => {
      expect(screen.getByText('Copy to Clipboard')).toBeInTheDocument();
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

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Paste sanitized markdown here/i)).toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText(/Paste sanitized markdown here/i);
    fireEvent.change(textarea, { target: { value: '{"foo":"bar"}' } });
    
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
    
    // For polling, we'll use a real timer but speed it up if possible or just mock the status
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

    await waitFor(() => {
      expect(screen.getByText('Automatic Execution')).toBeInTheDocument();
    });

    // Switch to auto tab
    const autoTab = screen.getByRole('tab', { name: /Automatic Execution/i });
    fireEvent.click(autoTab);
    fireEvent.keyDown(autoTab, { key: ' ', code: 'Space' });

    // Wait for the content to appear
    const autoBtn = await screen.findByRole('button', { name: /Run Automatically/i }, { timeout: 5000 });
    fireEvent.click(autoBtn);
    
    await waitFor(() => {
       expect(mockFetch).toHaveBeenCalledWith(
           expect.stringContaining('/api/simple-conversion/execute-auto/123'),
           expect.objectContaining({ method: 'POST' })
       );
    }, { timeout: 3000 });

    await waitFor(() => {
       expect(screen.getByText('Success')).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('displays errors properly', async () => {
    mockFetch.mockReset();
    mockFetch.mockRejectedValueOnce(new Error('Network blew up'));

    await act(async () => {
        render(<ManualWorkflowPage />);
    });

    await waitFor(() => {
        expect(screen.getByText('Network blew up')).toBeInTheDocument();
    });
  });
});
