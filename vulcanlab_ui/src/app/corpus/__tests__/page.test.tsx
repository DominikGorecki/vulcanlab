/**
 * Unit tests for Corpus Page
 * Verifies rendering, navigation, and deletion functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CorpusPage from '../page';

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock useToast
const mockToast = jest.fn();
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('CorpusPage', () => {
  const mockWorks = [
    { id: 1, title: 'Test Work 1', authors: 'Author A', created_at: '2023-01-01T00:00:00', status: 'Standard', vectorized_chunks: 25, has_summary: true },
    { id: 2, title: 'Test Work 2', authors: 'Author B, Author C', created_at: '2023-01-02T00:00:00', status: 'Automatic', vectorized_chunks: 15, has_summary: false },
  ];

  const mockStats = {
    total_works: 2,
    chunk_stats: {
      no_vec: 111,
      to_vec: 222,
      vec: 333,
      vec_err: 444,
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock responses for stats and works fetches
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ works: mockWorks, total: 2 }),
      });
  });

  it('renders PageHeader with correct title', async () => {
    render(<CorpusPage />);
    await waitFor(() => {
      expect(screen.getByText('Corpus')).toBeInTheDocument();
    });
  });

  it('renders StatsCardGrid with correct data', async () => {
    render(<CorpusPage />);

    await waitFor(() => {
      expect(screen.getByText('Total Works')).toBeInTheDocument();
      // "2" appears in both the stats card and as the ID for Test Work 2
      expect(screen.getAllByText('2')).toHaveLength(2);
      expect(screen.getByText('To Vectorize')).toBeInTheDocument();
      expect(screen.getByText('222')).toBeInTheDocument();
      expect(screen.getByText('Not Queued')).toBeInTheDocument();
      expect(screen.getByText('111')).toBeInTheDocument();
      // "Vectorized" appears in both stats card and table header
      expect(screen.getAllByText('Vectorized')).toHaveLength(2);
      expect(screen.getByText('333')).toBeInTheDocument();
      expect(screen.getByText('Errors')).toBeInTheDocument();
      expect(screen.getByText('444')).toBeInTheDocument();
    });
  });

  it('renders DataTable with correct data', async () => {
    render(<CorpusPage />);

    await waitFor(() => {
      expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      expect(screen.getByText('Author A')).toBeInTheDocument();
      expect(screen.getByText('Test Work 2')).toBeInTheDocument();
      expect(screen.getByText('Author B, Author C')).toBeInTheDocument();
    });
  });

  it('navigates to detail page when a row is clicked', async () => {
    render(<CorpusPage />);

    await waitFor(() => {
      const row = screen.getByText('Test Work 1').closest('tr');
      expect(row).toBeInTheDocument();
      fireEvent.click(row!);
    });

    expect(mockPush).toHaveBeenCalledWith('/corpus/1');
  });

  it('renders Summarize button in each row', async () => {
    render(<CorpusPage />);

    await waitFor(() => {
      const summarizeButtons = screen.getAllByLabelText(/Summarize work/i);
      expect(summarizeButtons).toHaveLength(2);
    });
  });

  it('navigates to summarization workflow page when Summarize button is clicked', async () => {
    render(<CorpusPage />);

    await waitFor(() => {
      const summarizeButtons = screen.getAllByLabelText(/Summarize work/i);
      fireEvent.click(summarizeButtons[0]);
    });

    expect(mockPush).toHaveBeenCalledWith('/summaries/workflow/1');
  });

  it('shows summary indicator when work has a summary', async () => {
    render(<CorpusPage />);

    await waitFor(() => {
      const work1 = screen.getByText('Test Work 1').closest('div');
      // The indicator is a CheckCircle2 which is rendered as an svg or div with title "Summarized"
      expect(screen.getByTitle('Summarized')).toBeInTheDocument();
    });
  });

  it('hides summary indicator when work has no summary', async () => {
    render(<CorpusPage />);

    await waitFor(() => {
      const work2 = screen.getByText('Test Work 2');
      // Work 2 has has_summary: false, so it shouldn't have the indicator
      // In our mock, only one work has a summary
      const indicators = screen.queryAllByTitle('Summarized');
      expect(indicators).toHaveLength(1);
    });
  });

  it('opens ConfirmDialog when delete button is clicked', async () => {
    render(<CorpusPage />);

    await waitFor(() => {
      // Find the delete button within the actions cell
      const deleteButtons = screen.getAllByLabelText(/Delete work/i);
      fireEvent.click(deleteButtons[0]);
    });

    // Check if the confirmation dialog text appears
    await waitFor(() => {
      expect(screen.getByText(/Are you sure/i)).toBeInTheDocument();
    });
  });

  it('calls delete API and shows success toast when deletion is confirmed', async () => {
    render(<CorpusPage />);

    // 1. Trigger delete dialog
    await waitFor(() => {
      const deleteButtons = screen.getAllByLabelText(/Delete work/i);
      fireEvent.click(deleteButtons[0]);
    });

    // 2. Mock successful deletion and subsequent refetches
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });
    // Stats refetch after delete
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ ...mockStats, total_works: 1 }),
    });
    // Works refetch after delete
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ works: [mockWorks[1]], total: 1 }),
    });

    // 3. Confirm deletion
    const confirmButton = screen.getByRole('button', { name: /Delete/i });
    fireEvent.click(confirmButton);

    // 4. Verify API call and toast
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/corpus/works/1'),
        expect.objectContaining({ method: 'DELETE' })
      );
      expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
        title: 'Work deleted',
      }));
    });
  });

  it('shows error toast when deletion fails', async () => {
    render(<CorpusPage />);

    await waitFor(() => {
      const deleteButtons = screen.getAllByLabelText(/Delete work/i);
      fireEvent.click(deleteButtons[0]);
    });

    // Mock failed deletion
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Server Error' }),
    });

    const confirmButton = screen.getByRole('button', { name: /Delete/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
        title: 'Deletion failed',
        variant: 'destructive'
      }));
    });
  });
});
