import { render, screen, fireEvent } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import ExpansionsPage from '../page';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock usePageData
jest.mock('@/hooks/use-page-data', () => ({
  usePageData: jest.fn(),
}));

// Mock page-header component
jest.mock('@/components/page-header', () => ({
  PageHeader: ({ title, description }: any) => (
    <div data-testid="page-header">
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  ),
}));

// Mock page-loading-state component
jest.mock('@/components/page-loading-state', () => ({
  PageLoadingState: ({ title }: any) => <div data-testid="loading">{title || 'Loading...'}</div>,
}));

// Mock page-error-state component
jest.mock('@/components/page-error-state', () => ({
  PageErrorState: ({ onRetry }: any) => (
    <div data-testid="error">
      <button onClick={onRetry}>Retry</button>
    </div>
  ),
}));

// Mock empty-state component
jest.mock('@/components/empty-state', () => ({
  EmptyState: ({ title, description }: any) => (
    <div data-testid="empty-state">
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  ),
}));

// Mock data-table component
jest.mock('@/components/data-table', () => ({
  DataTable: ({ data, onRowClick }: any) => (
    <div data-testid="data-table">
      {data.map((row: any) => (
        <div
          key={row.id}
          data-testid={`row-${row.id}`}
          onClick={() => onRowClick?.(row)}
        >
          <span data-testid={`query-${row.id}`}>{row.original_query}</span>
          <span data-testid={`status-${row.id}`}>{row.status}</span>
          <span data-testid={`mode-${row.id}`}>{row.mode}</span>
        </div>
      ))}
    </div>
  ),
}));

// Mock expansion status badge
jest.mock('@/components/expansion', () => ({
  ExpansionStatusBadge: ({ status }: any) => (
    <span data-testid="status-badge">{status}</span>
  ),
}));

describe('ExpansionsPage', () => {
  const mockRouterPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockRouterPush,
    });
  });

  it('shows loading state', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refetch: jest.fn(),
    });

    render(<ExpansionsPage />);

    expect(screen.getByTestId('loading')).toBeInTheDocument();
    expect(screen.getByText('Loading expansions...')).toBeInTheDocument();
  });

  it('shows error state', () => {
    const mockRefetch = jest.fn();
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: null,
      loading: false,
      error: new Error('Failed to load'),
      refetch: mockRefetch,
    });

    render(<ExpansionsPage />);

    expect(screen.getByTestId('error')).toBeInTheDocument();

    // Test retry button
    fireEvent.click(screen.getByText('Retry'));
    expect(mockRefetch).toHaveBeenCalled();
  });

  it('shows empty state when no expansions', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: [],
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<ExpansionsPage />);

    expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    expect(screen.getByText('No expansions yet')).toBeInTheDocument();
  });

  it('renders expansions data in table', () => {
    const mockExpansions = [
      {
        id: 1,
        result_id: 10,
        original_query: 'Test query 1',
        mode: 'automatic',
        status: 'completed',
        section_count: 5,
        created_at: '2024-01-15T10:00:00Z',
      },
      {
        id: 2,
        result_id: 20,
        original_query: 'Test query 2',
        mode: 'manual',
        status: 'sections_in_progress',
        section_count: 3,
        created_at: '2024-01-16T12:00:00Z',
      },
    ];

    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: mockExpansions,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<ExpansionsPage />);

    expect(screen.getByTestId('data-table')).toBeInTheDocument();
    expect(screen.getByText('Test query 1')).toBeInTheDocument();
    expect(screen.getByText('Test query 2')).toBeInTheDocument();
  });

  it('navigates to expansion detail page on row click', () => {
    const mockExpansions = [
      {
        id: 1,
        result_id: 10,
        original_query: 'Test query',
        mode: 'automatic',
        status: 'completed',
        section_count: 5,
        created_at: '2024-01-15T10:00:00Z',
      },
    ];

    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: mockExpansions,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<ExpansionsPage />);

    const row = screen.getByTestId('row-1');
    fireEvent.click(row);

    expect(mockRouterPush).toHaveBeenCalledWith('/expansions/1');
  });

  it('renders page header with correct title', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: [],
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<ExpansionsPage />);

    expect(screen.getByTestId('page-header')).toBeInTheDocument();
    expect(screen.getByText('Expansions')).toBeInTheDocument();
  });
});
