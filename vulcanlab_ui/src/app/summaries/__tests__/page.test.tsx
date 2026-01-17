/**
 * Unit tests for Summaries Page
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SummariesPage from '../page';

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('SummariesPage', () => {
  const mockSummaries = [
    {
      work_id: 1,
      title: 'Test Work 1',
      summary_count: 3,
      last_updated: '2023-01-01T12:00:00Z',
    },
    {
      work_id: 2,
      title: 'Test Work 2',
      summary_count: 5,
      last_updated: '2023-01-02T15:30:00Z',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders PageHeader with correct title', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ works: mockSummaries }),
    });

    render(<SummariesPage />);
    
    expect(screen.getByText('Summaries')).toBeInTheDocument();
    expect(screen.getByText('View generated summaries for your works.')).toBeInTheDocument();
  });

  it('renders DataTable with correct data', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ works: mockSummaries }),
    });

    render(<SummariesPage />);

    await waitFor(() => {
      expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      expect(screen.getByText('Test Work 2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });

  it('navigates to summary detail page when a row is clicked', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ works: mockSummaries }),
    });

    render(<SummariesPage />);

    await waitFor(() => {
      const row = screen.getByText('Test Work 1').closest('tr');
      expect(row).toBeInTheDocument();
      fireEvent.click(row!);
    });

    expect(mockPush).toHaveBeenCalledWith('/summaries/1');
  });

  it('renders empty state when no summaries are found', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ works: [] }),
    });

    render(<SummariesPage />);

    await waitFor(() => {
      expect(screen.getByText('No summaries yet')).toBeInTheDocument();
      expect(screen.getByText('Start summarizing your works from the Corpus page.')).toBeInTheDocument();
    });

    const corpusLink = screen.getByText('Go to Corpus');
    fireEvent.click(corpusLink);
    expect(mockPush).toHaveBeenCalledWith('/corpus');
  });

  it('renders error state when fetch fails', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    render(<SummariesPage />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load summaries')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });
  });

  it('retries fetch when retry button is clicked', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ works: mockSummaries }),
      });

    render(<SummariesPage />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load summaries')).toBeInTheDocument();
    });

    const retryButton = screen.getByText('Try Again');
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText('Test Work 1')).toBeInTheDocument();
    });
    
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});
