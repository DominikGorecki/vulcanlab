/**
 * Unit tests for Conversion Detail Page
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
// import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { useRouter, useParams } from 'next/navigation';
import ConversionDetailPage from '../page';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useParams: jest.fn(),
}));

// Mock fetch
global.fetch = jest.fn();

describe('ConversionDetailPage', () => {
  const mockRouter = {
    push: jest.fn(),
  };

  const mockResultsData = {
    work_id: 123,
    title: 'Test Document',
    author: 'John Doe',
    classification: 'small',
    token_count: 5000,
    chunk_count: 3,
    chunks: [
      {
        id: 1,
        heading_level: 'H1',
        heading_text: 'Introduction',
        start_line: 1,
        end_line: 10,
        content_preview: 'This is the introduction...',
      },
      {
        id: 2,
        heading_level: 'H2',
        heading_text: 'Background',
        start_line: 11,
        end_line: 25,
        content_preview: 'Background information...',
      },
      {
        id: 3,
        heading_level: 'content-chunk',
        heading_text: '',
        start_line: 26,
        end_line: 50,
        content_preview: 'Main content here...',
      },
    ],
  };

  const mockHistoryData = {
    items: [
      {
        work_id: 123,
        mode: 'automatic',
        status: 'complete',
        error_message: null,
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useParams as jest.Mock).mockReturnValue({ work_id: '123' });
    (global.fetch as jest.Mock).mockClear();
  });

  it('fetches results on mount', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockResultsData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistoryData,
      });

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/simple-conversion/results/123')
      );
    });
  });

  it('renders summary card with correct data when fetch succeeds', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockResultsData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistoryData,
      });

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('summary-card')).toBeInTheDocument();
    });

    expect(screen.getByTestId('title')).toHaveTextContent('Test Document');
    expect(screen.getByTestId('author')).toHaveTextContent('John Doe');
  });

  it('renders chunks list with all chunks from response', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockResultsData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistoryData,
      });

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Introduction')).toBeInTheDocument();
      expect(screen.getByText('Background')).toBeInTheDocument();
    });
  });

  it('shows error state when fetch fails', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('back button navigates to /simple-conversion', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockResultsData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistoryData,
      });

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Back to Simple Conversion')).toBeInTheDocument();
    });

    const backButton = screen.getByText('Back to Simple Conversion');
    fireEvent.click(backButton);

    expect(mockRouter.push).toHaveBeenCalledWith('/simple-conversion');
  });
});
