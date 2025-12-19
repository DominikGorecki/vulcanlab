import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { useParams, useRouter } from 'next/navigation';
import GeneratePage from '../page';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useParams: jest.fn(),
  useRouter: jest.fn(),
}));

// Mock the usePageData hook
jest.mock('@/hooks/use-page-data', () => ({
  usePageData: jest.fn(),
}));

// Mock the components
jest.mock('@/components', () => ({
  PageLoadingState: () => <div data-testid="loading-state">Loading...</div>,
  PageErrorState: ({ error, onRetry, actions }: any) => (
    <div data-testid="error-state">
      <p>{error.message}</p>
      <button onClick={onRetry}>Retry</button>
      {actions && actions.map((action: any, idx: number) => (
        <button key={idx} onClick={action.onClick}>{action.label}</button>
      ))}
    </div>
  ),
  StickyDetailHeader: ({ title, subtitle, onBack, actions }: any) => (
    <div data-testid="sticky-header">
      <button onClick={onBack}>Back</button>
      <h1>{title}</h1>
      <p>{subtitle}</p>
      {actions}
    </div>
  ),
}));

// Mock other components
jest.mock('@/components/markdown-renderer', () => ({
  MarkdownRenderer: ({ content }: any) => <div data-testid="markdown-renderer">{content}</div>,
}));

jest.mock('@/components/text-stats', () => ({
  TextStats: ({ text }: any) => <div data-testid="text-stats">{text.length} chars</div>,
}));

describe('GeneratePage', () => {
  const mockPush = jest.fn();
  const mockRefetch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useParams as jest.Mock).mockReturnValue({ id: '123' });
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });

    // Mock fetch globally
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('should display loading state initially', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refetch: mockRefetch,
    });

    render(<GeneratePage />);
    expect(screen.getByTestId('loading-state')).toBeInTheDocument();
  });

  it('should display error state when fetch fails', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    const mockError = new Error('Query not found');
    usePageData.mockReturnValue({
      data: null,
      loading: false,
      error: mockError,
      refetch: mockRefetch,
    });

    render(<GeneratePage />);
    expect(screen.getByTestId('error-state')).toBeInTheDocument();
    expect(screen.getByText('Query not found')).toBeInTheDocument();
  });

  it('should display prompt data when loaded', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    const mockPromptData = {
      query_id: 123,
      original_query: 'What is working memory?',
      prompt: 'This is a test prompt with context...',
      context_count: 5,
    };

    // First call for prompt data
    usePageData
      .mockReturnValueOnce({
        data: mockPromptData,
        loading: false,
        error: null,
        refetch: mockRefetch,
      })
      // Second call for query details
      .mockReturnValueOnce({
        data: { clean_retrieval_context: [{}, {}, {}, {}, {}] },
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

    render(<GeneratePage />);
    expect(screen.getByTestId('sticky-header')).toBeInTheDocument();
    expect(screen.getByText('Generate Response')).toBeInTheDocument();
    expect(screen.getByText('What is working memory?')).toBeInTheDocument();
  });

  it('should handle back navigation', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    const mockPromptData = {
      query_id: 123,
      original_query: 'Test query',
      prompt: 'Test prompt',
      context_count: 5,
    };

    usePageData
      .mockReturnValueOnce({
        data: mockPromptData,
        loading: false,
        error: null,
        refetch: mockRefetch,
      })
      .mockReturnValueOnce({
        data: { clean_retrieval_context: [] },
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

    render(<GeneratePage />);
    const backButton = screen.getByText('Back');
    fireEvent.click(backButton);
    expect(mockPush).toHaveBeenCalledWith('/rag');
  });

  it('should handle retry on error', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    const mockError = new Error('Failed to load prompt');
    usePageData.mockReturnValue({
      data: null,
      loading: false,
      error: mockError,
      refetch: mockRefetch,
    });

    render(<GeneratePage />);
    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);
    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });

  it('should navigate to inspect page when inspect button is clicked', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    const mockPromptData = {
      query_id: 123,
      original_query: 'Test query',
      prompt: 'Test prompt',
      context_count: 5,
    };

    usePageData
      .mockReturnValueOnce({
        data: mockPromptData,
        loading: false,
        error: null,
        refetch: mockRefetch,
      })
      .mockReturnValueOnce({
        data: { clean_retrieval_context: [] },
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

    render(<GeneratePage />);
    const inspectButton = screen.getByText('Inspect');
    fireEvent.click(inspectButton);
    expect(mockPush).toHaveBeenCalledWith('/rag/123/inspect');
  });
});
