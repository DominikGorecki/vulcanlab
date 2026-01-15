import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SummarizePage from '../page';

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

describe('SummarizePage', () => {
  const mockSummarizedWorks = {
    works: [
      {
        work_id: 1,
        title: 'Test Work 1',
        node_count: 10,
        summaries: ['abstract', 'outline'],
      },
      {
        work_id: 2,
        title: 'Test Work 2',
        node_count: 25,
        summaries: ['key_concepts'],
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders PageHeader with correct title', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSummarizedWorks,
    });

    render(<SummarizePage />);

    expect(screen.getByText('Summarize')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('View and manage work summaries')).toBeInTheDocument();
    });
  });

  it('renders loading state initially', () => {
    mockFetch.mockReturnValue(new Promise(() => {})); // Never resolves
    render(<SummarizePage />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('displays table after data loads', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSummarizedWorks,
    });

    render(<SummarizePage />);

    await waitFor(() => {
      expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      expect(screen.getByText('Test Work 2')).toBeInTheDocument();
    });

    // Check columns
    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Nodes')).toBeInTheDocument();
    expect(screen.getByText('Summaries')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();
  });

  it('shows node counts correctly', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSummarizedWorks,
    });

    render(<SummarizePage />);

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument();
    });
  });

  it('renders summary type badges correctly', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSummarizedWorks,
    });

    render(<SummarizePage />);

    await waitFor(() => {
      expect(screen.getByText('Abstract')).toBeInTheDocument();
      expect(screen.getByText('Outline')).toBeInTheDocument();
      expect(screen.getByText('Key Concepts')).toBeInTheDocument();
    });
  });

  it('navigates to detail page when a row is clicked', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSummarizedWorks,
    });

    render(<SummarizePage />);

    await waitFor(() => {
      const row = screen.getByText('Test Work 1').closest('tr');
      expect(row).toBeInTheDocument();
      fireEvent.click(row!);
    });

    expect(mockPush).toHaveBeenCalledWith('/summarize/1');
  });

  it('navigates to detail page when View button is clicked', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSummarizedWorks,
    });

    render(<SummarizePage />);

    await waitFor(() => {
      const viewButtons = screen.getAllByRole('button', { name: /View/i });
      fireEvent.click(viewButtons[0]);
    });

    expect(mockPush).toHaveBeenCalledWith('/summarize/1');
  });

  it('shows empty state when no works have summaries', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ works: [] }),
    });

    render(<SummarizePage />);

    await waitFor(() => {
      expect(screen.getByText('No summarized works')).toBeInTheDocument();
      expect(screen.getByText(/No works have been summarized yet/i)).toBeInTheDocument();
    });
  });

  it('shows error state on fetch failure', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    render(<SummarizePage />);

    await waitFor(() => {
      expect(screen.getByText('Error loading summaries')).toBeInTheDocument();
    });
  });

  it('retry button triggers refetch', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockSummarizedWorks,
      });

    render(<SummarizePage />);

    await waitFor(() => {
      expect(screen.getByText('Error loading summaries')).toBeInTheDocument();
    });

    const retryButton = screen.getByRole('button', { name: /Try Again/i });
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText('Test Work 1')).toBeInTheDocument();
    });
  });
});
