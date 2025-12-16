/**
 * Unit tests for Corpus Page - Delete Functionality
 * Tests delete icon appearance, modal opening, and delete flow
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import CorpusPage from '../page';

// Mock useRouter
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('CorpusPage - Delete Functionality', () => {
  const mockWorks = [
    { id: 1, title: 'Test Work 1', authors: 'Author A' },
    { id: 2, title: 'Test Work 2', authors: 'Author B, Author C' },
    { id: 3, title: 'Test Work 3', authors: null },
  ];

  const mockStats = {
    total_works: 3,
    chunk_stats: {
      no_vec: 10,
      to_vec: 5,
      vec: 20,
      vec_err: 1,
    },
  };

  beforeEach(() => {
    mockPush.mockClear();
    mockFetch.mockClear();

    // Default mock responses for stats and works
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ works: mockWorks, total: mockWorks.length }),
      });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Delete Icon Display', () => {
    it('test_delete_icon_appears_in_table: renders delete icon in each work row', async () => {
      await act(async () => {
        render(<CorpusPage />);
      });

      await waitFor(() => {
        const deleteIcons = screen.getAllByTestId('delete-icon');
        expect(deleteIcons).toHaveLength(mockWorks.length);
      });
    });

    it('renders Actions column header', async () => {
      await act(async () => {
        render(<CorpusPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Actions')).toBeInTheDocument();
      });
    });
  });

  describe('Delete Icon Interaction', () => {
    it('test_delete_icon_opens_modal: opens confirmation modal when delete icon is clicked', async () => {
      await act(async () => {
        render(<CorpusPage />);
      });

      await waitFor(() => {
        expect(screen.getAllByTestId('delete-icon')).toHaveLength(mockWorks.length);
      });

      const deleteIcons = screen.getAllByTestId('delete-icon');
      fireEvent.click(deleteIcons[0]);

      await waitFor(() => {
        expect(screen.getByTestId('confirm-delete-modal')).toBeInTheDocument();
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
        expect(screen.getByText('Author A')).toBeInTheDocument();
      });
    });

    it('test_delete_icon_stops_propagation: does not navigate to work detail when delete icon is clicked', async () => {
      await act(async () => {
        render(<CorpusPage />);
      });

      await waitFor(() => {
        expect(screen.getAllByTestId('delete-icon')).toHaveLength(mockWorks.length);
      });

      const deleteIcons = screen.getAllByTestId('delete-icon');
      fireEvent.click(deleteIcons[0]);

      // Router push should not be called when clicking delete icon
      expect(mockPush).not.toHaveBeenCalled();

      // Modal should open instead
      await waitFor(() => {
        expect(screen.getByTestId('confirm-delete-modal')).toBeInTheDocument();
      });
    });

    it('navigates to work detail when row is clicked (not delete icon)', async () => {
      await act(async () => {
        render(<CorpusPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });

      // Click on the title cell, not the delete icon
      const titleCell = screen.getByText('Test Work 1');
      fireEvent.click(titleCell);

      expect(mockPush).toHaveBeenCalledWith('/corpus/1');
    });
  });

  describe('Delete Confirmation Flow', () => {
    it('closes modal when Cancel button is clicked', async () => {
      await act(async () => {
        render(<CorpusPage />);
      });

      await waitFor(() => {
        expect(screen.getAllByTestId('delete-icon')).toHaveLength(mockWorks.length);
      });

      // Open modal
      const deleteIcons = screen.getAllByTestId('delete-icon');
      fireEvent.click(deleteIcons[0]);

      await waitFor(() => {
        expect(screen.getByTestId('confirm-delete-modal')).toBeInTheDocument();
      });

      // Click Cancel
      const cancelButton = screen.getByTestId('cancel-button');
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByTestId('confirm-delete-modal')).not.toBeInTheDocument();
      });

      // No delete API call should be made
      expect(mockFetch).toHaveBeenCalledTimes(2); // Only initial stats and works fetch
    });

    it('calls DELETE API and refreshes data when Delete button is clicked', async () => {
      await act(async () => {
        render(<CorpusPage />);
      });

      await waitFor(() => {
        expect(screen.getAllByTestId('delete-icon')).toHaveLength(mockWorks.length);
      });

      // Open modal
      const deleteIcons = screen.getAllByTestId('delete-icon');
      fireEvent.click(deleteIcons[0]);

      await waitFor(() => {
        expect(screen.getByTestId('confirm-delete-modal')).toBeInTheDocument();
      });

      // Mock successful deletion response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      // Mock refresh data responses
      const updatedWorks = mockWorks.filter((w) => w.id !== 1);
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...mockStats, total_works: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ works: updatedWorks, total: updatedWorks.length }),
        });

      // Click Delete
      const deleteButton = screen.getByTestId('delete-button');
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      // Verify DELETE API was called
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/corpus/works/1'),
          expect.objectContaining({ method: 'DELETE' })
        );
      });

      // Verify modal closes and data is refreshed
      await waitFor(() => {
        expect(screen.queryByTestId('confirm-delete-modal')).not.toBeInTheDocument();
      });
    });

    it('shows loading state during deletion', async () => {
      await act(async () => {
        render(<CorpusPage />);
      });

      await waitFor(() => {
        expect(screen.getAllByTestId('delete-icon')).toHaveLength(mockWorks.length);
      });

      // Open modal
      const deleteIcons = screen.getAllByTestId('delete-icon');
      fireEvent.click(deleteIcons[0]);

      await waitFor(() => {
        expect(screen.getByTestId('confirm-delete-modal')).toBeInTheDocument();
      });

      // Mock slow deletion response
      let resolveDelete: (value: any) => void;
      const deletePromise = new Promise((resolve) => {
        resolveDelete = resolve;
      });
      mockFetch.mockReturnValueOnce(deletePromise as any);

      // Click Delete
      const deleteButton = screen.getByTestId('delete-button');
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      // Check loading state
      await waitFor(() => {
        expect(screen.getByText('Deleting...')).toBeInTheDocument();
        expect(screen.getByTestId('delete-button')).toBeDisabled();
        expect(screen.getByTestId('cancel-button')).toBeDisabled();
      });

      // Resolve the delete
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockStats,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ works: mockWorks, total: mockWorks.length }),
        });

      await act(async () => {
        resolveDelete!({ ok: true, json: async () => ({}) });
      });

      // Loading state should be gone
      await waitFor(() => {
        expect(screen.queryByText('Deleting...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Delete Error Handling', () => {
    it('handles deletion errors gracefully', async () => {
      await act(async () => {
        render(<CorpusPage />);
      });

      await waitFor(() => {
        expect(screen.getAllByTestId('delete-icon')).toHaveLength(mockWorks.length);
      });

      // Open modal
      const deleteIcons = screen.getAllByTestId('delete-icon');
      fireEvent.click(deleteIcons[0]);

      await waitFor(() => {
        expect(screen.getByTestId('confirm-delete-modal')).toBeInTheDocument();
      });

      // Mock failed deletion response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      });

      // Click Delete
      const deleteButton = screen.getByTestId('delete-button');
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      // Modal should remain open on error (for now, until T04)
      await waitFor(() => {
        expect(screen.getByTestId('confirm-delete-modal')).toBeInTheDocument();
      });

      // Console error should be logged
      // (T04 will handle proper error display)
    });
  });

  describe('Multiple Works', () => {
    it('can delete different works independently', async () => {
      await act(async () => {
        render(<CorpusPage />);
      });

      await waitFor(() => {
        expect(screen.getAllByTestId('delete-icon')).toHaveLength(mockWorks.length);
      });

      // Click delete icon for second work
      const deleteIcons = screen.getAllByTestId('delete-icon');
      fireEvent.click(deleteIcons[1]);

      await waitFor(() => {
        expect(screen.getByTestId('confirm-delete-modal')).toBeInTheDocument();
        expect(screen.getByText('Test Work 2')).toBeInTheDocument();
        expect(screen.getByText('Author B, Author C')).toBeInTheDocument();
      });
    });

    it('displays work with null authors correctly in modal', async () => {
      await act(async () => {
        render(<CorpusPage />);
      });

      await waitFor(() => {
        expect(screen.getAllByTestId('delete-icon')).toHaveLength(mockWorks.length);
      });

      // Click delete icon for work with no authors
      const deleteIcons = screen.getAllByTestId('delete-icon');
      fireEvent.click(deleteIcons[2]);

      await waitFor(() => {
        expect(screen.getByTestId('confirm-delete-modal')).toBeInTheDocument();
        expect(screen.getByText('Test Work 3')).toBeInTheDocument();
        // Authors section should not be shown
        expect(screen.queryByText(/Authors:/)).not.toBeInTheDocument();
      });
    });
  });
});
