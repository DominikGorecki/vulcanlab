/**
 * Unit tests for Automatic Workflow Page
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import AutomaticWorkflowPage from '../page';

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useParams: () => ({ work_id: '123' }),
  useRouter: () => ({ push: mockPush }),
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('AutomaticWorkflowPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockFetch.mockReset();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  const mockSuccessfulExecution = () => {
    // 1. Initial status check
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ work_id: 123, step: 'converting' }),
    });
    // 2. Initial execution call
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'started' }),
    });

    // 3. Status poll (parsing)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ work_id: 123, step: 'parsing' }),
    });
  };

  it('executes automatic pipeline on mount', async () => {
    mockSuccessfulExecution();

    await act(async () => {
      render(<AutomaticWorkflowPage />);
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/simple-conversion/execute-auto/123'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  it('polls status during execution', async () => {
    // 1. Status check
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ work_id: 123, step: 'converting' }) });
    // 2. Execute
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    // 3. Status 1 (parsing)
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ work_id: 123, step: 'parsing' }) });
    
    await act(async () => {
      render(<AutomaticWorkflowPage />);
    });

    // Verify initial load
    await waitFor(() => {
      expect(screen.getByText('Parse & Classify')).toBeInTheDocument();
    });

    // Status 2 (sanitizing) - from polling
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ work_id: 123, step: 'sanitizing' }) });

    // Advance time for poll
    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    await waitFor(() => {
        // execute + 3 status calls
        expect(mockFetch).toHaveBeenCalledTimes(4); 
    });
  });

  it('displays completion and fetches results when complete', async () => {
    // 1. Status check
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ work_id: 123, step: 'converting' }) });
    // 2. Execute
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    // 3. Status (complete)
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ work_id: 123, step: 'complete' }) });
    // 4. Results fetch
    mockFetch.mockResolvedValueOnce({ 
      ok: true, 
      json: async () => ({ 
        work_id: 123, 
        title: 'Test Doc', 
        author: 'Author',
        classification: 'small',
        token_count: 100,
        chunk_count: 1,
        chunks: [{
            id: 1,
            heading_level: '1',
            heading_text: 'Intro',
            start_line: 1,
            end_line: 5,
            content_preview: 'Preview' 
        }]
      }) 
    });

    await act(async () => {
      render(<AutomaticWorkflowPage />);
    });

    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument();
      expect(screen.getByText('Test Doc')).toBeInTheDocument();
      expect(screen.getByText('Generated Chunks')).toBeInTheDocument();
    });
  });

  it('displays error if execution fails', async () => {
    // 1. Status check
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ work_id: 123, step: 'converting' }) });
    // 2. Execute fail
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Something exploded' }),
    });

    await act(async () => {
      render(<AutomaticWorkflowPage />);
    });

    await waitFor(() => {
      expect(screen.getByText('Something exploded')).toBeInTheDocument();
    });
  });

  it('displays "Start Another Conversion" button on success', async () => {
    // 1. Status check
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ work_id: 123, step: 'converting' }) });
    // 2. Execute
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    // 3. Status (complete)
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ work_id: 123, step: 'complete' }) });
    // 4. Results fetch
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        work_id: 123,
        title: 'Test Doc',
        author: 'Author',
        classification: 'small',
        token_count: 100,
        chunk_count: 1,
        chunks: []
      })
    });

    await act(async () => {
      render(<AutomaticWorkflowPage />);
    });

    await waitFor(() => {
      expect(screen.getByText('Start Another Conversion')).toBeInTheDocument();
    });
  });

  it('navigates to corpus page when "View in Corpus" is clicked', async () => {
    // 1. Status check
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ work_id: 123, step: 'converting' }) });
    // 2. Execute
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    // 3. Status (complete)
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ work_id: 123, step: 'complete' }) });
    // 4. Results fetch
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        work_id: 123,
        title: 'Test Doc',
        author: 'Author',
        classification: 'small',
        token_count: 100,
        chunk_count: 1,
        chunks: []
      })
    });

    await act(async () => {
      render(<AutomaticWorkflowPage />);
    });

    await waitFor(() => {
      expect(screen.getByText('View in Corpus')).toBeInTheDocument();
    });

    const viewButton = screen.getByText('View in Corpus');
    await act(async () => {
      viewButton.click();
    });

    expect(mockPush).toHaveBeenCalledWith('/corpus/123');
  });
});
