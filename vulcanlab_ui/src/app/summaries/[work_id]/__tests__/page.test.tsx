/**
 * Unit tests for Summary Viewer Page
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SummaryViewerPage from '../page';
import { useParams, useRouter } from 'next/navigation';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useParams: jest.fn(),
}));

// Mock components
jest.mock('@/components', () => ({
  StickyDetailHeader: ({ title, subtitle, actions, backUrl }: any) => (
    <div data-testid="sticky-header">
      <h1>{title}</h1>
      <h2>{subtitle}</h2>
      <div data-testid="header-actions">{actions}</div>
      <a href={backUrl}>Back</a>
    </div>
  ),
  PageLoadingState: ({ title }: any) => <div data-testid="loading-state">{title}</div>,
  PageErrorState: ({ error, onRetry }: any) => (
    <div data-testid="error-state">
      {error instanceof Error ? error.message : error}
      <button onClick={onRetry}>Retry</button>
    </div>
  ),
  MarkdownRenderer: ({ content }: { content: string }) => <div data-testid="markdown-content">{content}</div>,
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('SummaryViewerPage', () => {
  const mockWorkId = '123';
  const mockPush = jest.fn();
  
  const mockSummary = {
    work_id: 123,
    work_title: 'Test Document Title',
    sections: [
      {
        heading_title: 'Introduction',
        summary_content: 'This is the intro summary.',
        start_line: 1,
      },
      {
        heading_title: 'Methodology',
        summary_content: 'This is the methodology summary.',
        start_line: 50,
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useParams as jest.Mock).mockReturnValue({ work_id: mockWorkId });
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
  });

  it('renders loading state initially', async () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<SummaryViewerPage />);
    expect(screen.getByTestId('loading-state')).toBeInTheDocument();
  });

  it('fetches and displays the summary content', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSummary,
    });

    render(<SummaryViewerPage />);

    await waitFor(() => {
      expect(screen.getByText('Test Document Title')).toBeInTheDocument();
      expect(screen.getByText('Introduction')).toBeInTheDocument();
      expect(screen.getByText('Methodology')).toBeInTheDocument();
      
      const contents = screen.getAllByTestId('markdown-content');
      expect(contents).toHaveLength(2);
      expect(contents[0]).toHaveTextContent('This is the intro summary.');
      expect(contents[1]).toHaveTextContent('This is the methodology summary.');
    });
  });

  it('renders line references for sections', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSummary,
    });

    render(<SummaryViewerPage />);

    await waitFor(() => {
      expect(screen.getByText('Line 1')).toBeInTheDocument();
      expect(screen.getByText('Line 50')).toBeInTheDocument();
    });
  });

  it('navigates to original work when "View Original" is clicked', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSummary,
    });

    render(<SummaryViewerPage />);

    await waitFor(() => {
      const viewOriginalBtn = screen.getByText('View Original');
      fireEvent.click(viewOriginalBtn);
    });

    expect(mockPush).toHaveBeenCalledWith(`/corpus/${mockWorkId}`);
  });

  it('navigates to workflow when "Re-summarize" is clicked', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSummary,
    });

    render(<SummaryViewerPage />);

    await waitFor(() => {
      const resummarizeBtn = screen.getByText('Re-summarize');
      fireEvent.click(resummarizeBtn);
    });

    expect(mockPush).toHaveBeenCalledWith(`/summaries/workflow/${mockWorkId}`);
  });

  it('renders error state when fetch fails', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    });

    render(<SummaryViewerPage />);

    await waitFor(() => {
      expect(screen.getByTestId('error-state')).toBeInTheDocument();
      expect(screen.getByText('Summary not found for this work.')).toBeInTheDocument();
    });
  });

  it('renders empty state when there are no sections', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ ...mockSummary, sections: [] }),
    });

    render(<SummaryViewerPage />);

    await waitFor(() => {
      expect(screen.getByText('No summary content available')).toBeInTheDocument();
    });
    
    const workflowBtn = screen.getByText('Go to Workflow');
    fireEvent.click(workflowBtn);
    expect(mockPush).toHaveBeenCalledWith(`/summaries/workflow/${mockWorkId}`);
  });
});
