/**
 * Unit tests for Simple Conversion Page
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import SimpleConversionPage from '../page';

// Mock useRouter
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useParams: () => ({}),
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('SimpleConversionPage', () => {
  beforeEach(() => {
    mockPush.mockClear();
    mockFetch.mockClear();

    // Default mock responses for file list and history
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ input_files: ['test1.pdf', 'test2.epub'] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [] }),
      });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('loads and displays input files in dropdown', async () => {
    await act(async () => {
      render(<SimpleConversionPage />);
    });
    
    // Check loading state gone
    expect(screen.queryByText(/loading available files/i)).not.toBeInTheDocument();
    
    // Check fetch was called
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/conv/io-folder-data'));
  });

  it('displays error if file list fetch fails', async () => {
    mockFetch.mockReset();
    mockFetch.mockRejectedValueOnce(new Error('Network error'));
    
    await act(async () => {
      render(<SimpleConversionPage />);
    });
    
    expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    expect(screen.getByText(/Try Again/i)).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    await act(async () => {
      render(<SimpleConversionPage />);
    });

    const submitBtn = screen.getByRole('button', { name: /Start Conversion/i });
    
    fireEvent.click(submitBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/Please select a file/i)).toBeInTheDocument();
      expect(screen.getByText(/Title is required/i)).toBeInTheDocument();
      expect(screen.getByText(/Author is required/i)).toBeInTheDocument();
    });
  });

  it('validates year format', async () => {
    await act(async () => {
      render(<SimpleConversionPage />);
    });

    const titleInput = screen.getByPlaceholderText(/Document title/i);
    const authorInput = screen.getByPlaceholderText(/Author name/i);
    const yearInput = screen.getByPlaceholderText(/2023/i);

    fireEvent.change(titleInput, { target: { value: 'My Title' } });
    fireEvent.change(authorInput, { target: { value: 'My Author' } });
    fireEvent.change(yearInput, { target: { value: '999' } }); // Invalid year

    const submitBtn = screen.getByRole('button', { name: /Start Conversion/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Please enter a valid year/i)).toBeInTheDocument();
    });
  });

  describe('History Section', () => {
    it('fetches history data on mount', async () => {
      await act(async () => {
        render(<SimpleConversionPage />);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/simple-conversion/history')
        );
      });
    });

    it('displays empty state when no history exists', async () => {
      mockFetch.mockReset();
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ input_files: ['test1.pdf'] }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ items: [] }),
        });

      await act(async () => {
        render(<SimpleConversionPage />);
      });

      await waitFor(() => {
        expect(screen.getByText(/No past conversions yet/i)).toBeInTheDocument();
      });
    });

    it('renders history table when data is available', async () => {
      const mockHistoryData = {
        items: [
          {
            work_id: 1,
            title: 'Test Doc 1',
            author: 'Author 1',
            classification: 'small',
            mode: 'automatic',
            status: 'complete',
            created_at: '2025-01-15T10:00:00Z',
          },
          {
            work_id: 2,
            title: 'Test Doc 2',
            author: 'Author 2',
            classification: 'large',
            mode: 'manual',
            status: 'failed',
            created_at: '2025-01-14T10:00:00Z',
          },
        ],
      };

      mockFetch.mockReset();
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ input_files: ['test1.pdf'] }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockHistoryData,
        });

      await act(async () => {
        render(<SimpleConversionPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Doc 1')).toBeInTheDocument();
        expect(screen.getByText('Test Doc 2')).toBeInTheDocument();
        expect(screen.getByText('Author 1')).toBeInTheDocument();
        expect(screen.getByText('Author 2')).toBeInTheDocument();
      });
    });

    it('clicking history row navigates to detail page', async () => {
      const mockHistoryData = {
        items: [
          {
            work_id: 123,
            title: 'Test Doc',
            author: 'Test Author',
            classification: 'small',
            mode: 'automatic',
            status: 'complete',
            created_at: '2025-01-15T10:00:00Z',
          },
        ],
      };

      mockFetch.mockReset();
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ input_files: ['test1.pdf'] }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockHistoryData,
        });

      await act(async () => {
        render(<SimpleConversionPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Doc')).toBeInTheDocument();
      });

      const row = screen.getByText('Test Doc').closest('tr');
      if (row) fireEvent.click(row);

      expect(mockPush).toHaveBeenCalledWith('/simple-conversion/history/123');
    });
  });
});
