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
    { id: 1, title: 'Test Work 1', authors: 'Author A', created_at: '2023-01-01T00:00:00', status: 'Standard' },
    { id: 2, title: 'Test Work 2', authors: 'Author B, Author C', created_at: '2023-01-02T00:00:00', status: 'Automatic' },
  ];

  const mockStats = {
    total_works: 2,
    chunk_stats: {
      no_vec: 10,
      to_vec: 5,
      vec: 20,
      vec_err: 1,
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
      expect(screen.getAllByText('2')).toHaveLength(1); // One for total works
      expect(screen.getByText('To Vectorize')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
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
