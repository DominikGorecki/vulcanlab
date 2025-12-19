import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import RAGPage from '../page';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock the usePageData hook
jest.mock('@/hooks/use-page-data', () => ({
  usePageData: jest.fn(),
}));

// Mock the components
jest.mock('@/components', () => ({
  PageHeader: ({ title, description }: any) => (
    <div data-testid="page-header">
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  ),
  PageLoadingState: () => <div data-testid="loading-state">Loading...</div>,
  PageErrorState: ({ error, onRetry }: any) => (
    <div data-testid="error-state">
      <p>{error.message}</p>
      <button onClick={onRetry}>Retry</button>
    </div>
  ),
  DataTable: ({ data, columns, emptyState }: any) => (
    <div data-testid="data-table">
      {data.length === 0 ? (
        <div data-testid="empty-state">{emptyState.title}</div>
      ) : (
        <table>
          <tbody>
            {data.map((row: any) => (
              <tr key={row.id}>
                <td>{row.original_query}</td>
                <td>{row.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  ),
  StatusBadge: ({ status }: any) => <span data-testid="status-badge">{status}</span>,
  StatsCardGrid: ({ stats }: any) => (
    <div data-testid="stats-card-grid">
      {stats.map((stat: any, idx: number) => (
        <div key={idx}>
          {stat.title}: {stat.value}
        </div>
      ))}
    </div>
  ),
}));

describe('RAGPage', () => {
  const mockPush = jest.fn();
  const mockRefetch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });
  });

  it('should display loading state initially', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refetch: mockRefetch,
    });

    render(<RAGPage />);
    expect(screen.getByTestId('loading-state')).toBeInTheDocument();
  });

  it('should display error state when fetch fails', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    const mockError = new Error('Failed to load queries');
    usePageData.mockReturnValue({
      data: null,
      loading: false,
      error: mockError,
      refetch: mockRefetch,
    });

    render(<RAGPage />);
    expect(screen.getByTestId('error-state')).toBeInTheDocument();
    expect(screen.getByText('Failed to load queries')).toBeInTheDocument();
  });

  it('should display queries when data is loaded', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    const mockData = {
      queries: [
        {
          id: 1,
          original_query: 'What is working memory?',
          created_at: '2024-01-01T00:00:00Z',
          status: 'ready',
          intent: 'DEFINITION',
          entities_count: 2,
        },
        {
          id: 2,
          original_query: 'How does attention work?',
          created_at: '2024-01-02T00:00:00Z',
          status: 'needs_embeddings',
          intent: 'EXPLANATION',
          entities_count: 1,
        },
      ],
      total: 2,
    };

    usePageData.mockReturnValue({
      data: mockData,
      loading: false,
      error: null,
      refetch: mockRefetch,
    });

    render(<RAGPage />);
    expect(screen.getByTestId('page-header')).toBeInTheDocument();
    expect(screen.getByText('RAG Queries')).toBeInTheDocument();
    expect(screen.getByTestId('data-table')).toBeInTheDocument();
    expect(screen.getByText('What is working memory?')).toBeInTheDocument();
    expect(screen.getByText('How does attention work?')).toBeInTheDocument();
  });

  it('should display stats correctly', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    const mockData = {
      queries: [
        { id: 1, original_query: 'Query 1', created_at: '2024-01-01T00:00:00Z', status: 'ready', intent: null, entities_count: 0 },
        { id: 2, original_query: 'Query 2', created_at: '2024-01-02T00:00:00Z', status: 'needs_embeddings', intent: null, entities_count: 0 },
        { id: 3, original_query: 'Query 3', created_at: '2024-01-03T00:00:00Z', status: 'ready', intent: null, entities_count: 0 },
      ],
      total: 3,
    };

    usePageData.mockReturnValue({
      data: mockData,
      loading: false,
      error: null,
      refetch: mockRefetch,
    });

    render(<RAGPage />);
    const statsGrid = screen.getByTestId('stats-card-grid');
    expect(statsGrid).toHaveTextContent('Total Queries: 3');
    expect(statsGrid).toHaveTextContent('Ready: 2');
    expect(statsGrid).toHaveTextContent('Pending: 1');
  });

  it('should display empty state when no queries exist', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    const mockData = {
      queries: [],
      total: 0,
    };

    usePageData.mockReturnValue({
      data: mockData,
      loading: false,
      error: null,
      refetch: mockRefetch,
    });

    render(<RAGPage />);
    expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    expect(screen.getByText('No queries found')).toBeInTheDocument();
  });

  it('should handle retry on error', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    const mockError = new Error('Network error');
    usePageData.mockReturnValue({
      data: null,
      loading: false,
      error: mockError,
      refetch: mockRefetch,
    });

    render(<RAGPage />);
    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);
    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });

  it('should navigate to new query page when manual button is clicked', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: { queries: [], total: 0 },
      loading: false,
      error: null,
      refetch: mockRefetch,
    });

    render(<RAGPage />);
    const textarea = screen.getByPlaceholderText(/Enter your query here/i);
    fireEvent.change(textarea, { target: { value: 'Test query' } });

    const manualButton = screen.getByText('Manual');
    fireEvent.click(manualButton);

    expect(mockPush).toHaveBeenCalledWith('/rag/new?q=Test%20query');
  });
});
