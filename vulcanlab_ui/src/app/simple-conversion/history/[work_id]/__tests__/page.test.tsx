/**
 * Unit tests for Conversion Detail Page
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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

  it('extracts work_id from params correctly', () => {
    (useParams as jest.Mock).mockReturnValue({ work_id: '456' });
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockResultsData,
    });

    render(<ConversionDetailPage />);

    expect(useParams).toHaveBeenCalled();
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
        'http://localhost:8000/api/simple-conversion/results/123'
      );
    });
  });

  it('shows loading state while fetching', () => {
    (global.fetch as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<ConversionDetailPage />);

    expect(screen.getByTestId('loading-state')).toBeInTheDocument();
    expect(screen.getByText('Loading conversion results...')).toBeInTheDocument();
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
      expect(screen.getByTestId('chunks-list')).toBeInTheDocument();
    });

    const chunks = screen.getAllByTestId('chunk-item');
    expect(chunks).toHaveLength(3);
  });

  it('calculates heading chunk count correctly from chunks array', async () => {
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
      expect(screen.getByTestId('heading-chunk-count')).toBeInTheDocument();
    });

    // Should be 2 (H1 and H2)
    expect(screen.getByTestId('heading-chunk-count')).toHaveTextContent('2');
  });

  it('calculates content chunk count correctly from chunks array', async () => {
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
      expect(screen.getByTestId('content-chunk-count')).toBeInTheDocument();
    });

    // Should be 1 (content-chunk)
    expect(screen.getByTestId('content-chunk-count')).toHaveTextContent('1');
  });

  it('shows error banner when conversion failed with error_message', async () => {
    const failedHistoryData = {
      items: [
        {
          work_id: 123,
          mode: 'automatic',
          status: 'failed',
          error_message: 'Processing failed due to timeout',
        },
      ],
    };

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockResultsData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => failedHistoryData,
      });

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('error-banner')).toBeInTheDocument();
    });

    expect(screen.getByText('Processing failed due to timeout')).toBeInTheDocument();
  });

  it('shows 404 state when work_id does not exist', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    });

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('error-state')).toBeInTheDocument();
    });

    expect(screen.getByText('Work not found')).toBeInTheDocument();
  });

  it('shows error state when fetch fails', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('error-state')).toBeInTheDocument();
    });

    expect(screen.getByText('Network error')).toBeInTheDocument();
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

    const user = userEvent.setup();
    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('back-button')).toBeInTheDocument();
    });

    const backButton = screen.getByTestId('back-button');
    await user.click(backButton);

    expect(mockRouter.push).toHaveBeenCalledWith('/simple-conversion');
  });

  it('"Start New Conversion" button navigates to /simple-conversion', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockResultsData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistoryData,
      });

    const user = userEvent.setup();
    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('start-new-conversion')).toBeInTheDocument();
    });

    const startButton = screen.getByTestId('start-new-conversion');
    await user.click(startButton);

    expect(mockRouter.push).toHaveBeenCalledWith('/simple-conversion');
  });

  it('mode badge shows automatic mode', async () => {
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
      expect(screen.getByTestId('mode-badge')).toBeInTheDocument();
    });

    expect(screen.getByTestId('mode-badge')).toHaveTextContent('Automatic');
  });

  it('mode badge shows manual mode', async () => {
    const manualHistoryData = {
      items: [
        {
          work_id: 123,
          mode: 'manual',
          status: 'complete',
          error_message: null,
        },
      ],
    };

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockResultsData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => manualHistoryData,
      });

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('mode-badge')).toBeInTheDocument();
    });

    expect(screen.getByTestId('mode-badge')).toHaveTextContent('Manual');
  });

  it('status indicator shows success state', async () => {
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
      expect(screen.getByTestId('status-indicator')).toBeInTheDocument();
    });

    expect(screen.getByTestId('status-indicator')).toHaveTextContent('Success');
  });

  it('status indicator shows failed state', async () => {
    const failedHistoryData = {
      items: [
        {
          work_id: 123,
          mode: 'automatic',
          status: 'failed',
          error_message: 'Error occurred',
        },
      ],
    };

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockResultsData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => failedHistoryData,
      });

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('status-indicator')).toBeInTheDocument();
    });

    expect(screen.getByTestId('status-indicator')).toHaveTextContent('Failed');
  });

  it('classification badge shows correct value (small)', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockResultsData, classification: 'small' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistoryData,
      });

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('classification-badge')).toBeInTheDocument();
    });

    expect(screen.getByTestId('classification-badge')).toHaveTextContent('Small');
  });

  it('classification badge shows correct value (large)', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockResultsData, classification: 'large' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistoryData,
      });

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('classification-badge')).toBeInTheDocument();
    });

    expect(screen.getByTestId('classification-badge')).toHaveTextContent('Large');
  });

  it('handles invalid work_id', async () => {
    (useParams as jest.Mock).mockReturnValue({ work_id: null });

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('error-state')).toBeInTheDocument();
    });

    expect(screen.getByText('Invalid work ID')).toBeInTheDocument();
  });

  it('shows error state for 400 status (not a simple conversion)', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
    });

    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('error-state')).toBeInTheDocument();
    });

    expect(
      screen.getByText('This work has not been processed or is not a simple conversion')
    ).toBeInTheDocument();
  });

  it('back to simple conversion button in error state navigates correctly', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    const user = userEvent.setup();
    render(<ConversionDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId('back-to-simple-conversion')).toBeInTheDocument();
    });

    const backButton = screen.getByTestId('back-to-simple-conversion');
    await user.click(backButton);

    expect(mockRouter.push).toHaveBeenCalledWith('/simple-conversion');
  });

  it('handles history fetch failure gracefully', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockResultsData,
      })
      .mockRejectedValueOnce(new Error('History fetch failed'));

    render(<ConversionDetailPage />);

    // Should still render results with default mode/status
    await waitFor(() => {
      expect(screen.getByTestId('summary-card')).toBeInTheDocument();
    });

    expect(screen.getByTestId('mode-badge')).toHaveTextContent('Automatic');
    expect(screen.getByTestId('status-indicator')).toHaveTextContent('Success');
  });
});
