import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ExpansionDetailPage from '../page';
import { useParams, useRouter } from 'next/navigation';
import { usePageData } from '@/hooks/use-page-data';

// Mock the hooks
jest.mock('next/navigation', () => ({
  useParams: jest.fn(),
  useRouter: jest.fn(),
}));

jest.mock('@/hooks/use-page-data', () => ({
  usePageData: jest.fn(),
}));

// Mock the components
jest.mock('@/components/expansion', () => ({
  ExpansionStatusBadge: ({ status }: { status: string }) => <div data-testid="expansion-status">{status}</div>,
  SectionsList: ({ onRetry, onSaveManual }: any) => (
    <div data-testid="sections-list">
      <button onClick={() => onRetry(1)}>Retry Section</button>
      <button onClick={() => onSaveManual(1, 'Manual text')}>Save Manual</button>
    </div>
  ),
  CombinedReport: ({ report }: { report: string }) => <div data-testid="combined-report">{report}</div>,
}));

jest.mock('@/components/sticky-detail-header', () => ({
  StickyDetailHeader: ({ title, subtitle, actions }: any) => (
    <div data-testid="sticky-header">
      <h1>{title}</h1>
      <div>{subtitle}</div>
      <div>{actions}</div>
    </div>
  ),
}));

// Mock toast
jest.mock('@/hooks/use-toast', () => ({
  toast: jest.fn(),
}));

describe('ExpansionDetailPage', () => {
  const mockRouter = { push: jest.fn() };
  const mockParams = { id: '456' };
  const mockRefetch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useParams as jest.Mock).mockReturnValue(mockParams);
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    
    // Default fetch mock
    global.fetch = jest.fn(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    ) as jest.Mock;
  });

  it('renders loading state', () => {
    (usePageData as jest.Mock).mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refetch: mockRefetch,
    });

    render(<ExpansionDetailPage />);
    expect(screen.getByText(/loading expansion detail/i)).toBeInTheDocument();
  });

  it('renders error state', () => {
    (usePageData as jest.Mock).mockReturnValue({
      data: null,
      loading: false,
      error: new Error('Failed to load'),
      refetch: mockRefetch,
    });

    render(<ExpansionDetailPage />);
    expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
  });

  it('renders expansion detail with sections', () => {
    const mockData = {
      id: 456,
      result_id: 123,
      query_id: 100,
      mode: 'automatic',
      status: 'sections_in_progress',
      sections: [{ id: 1, order: 1, heading: 'S1', summary: 'Summary 1', status: 'completed' }],
      combined_report: null,
    };

    (usePageData as jest.Mock).mockReturnValue({
      data: mockData,
      loading: false,
      error: null,
      refetch: mockRefetch,
    });

    render(<ExpansionDetailPage />);

    expect(screen.getByText('Expansion #456')).toBeInTheDocument();
    expect(screen.getByTestId('expansion-status')).toHaveTextContent('sections_in_progress');
    expect(screen.getByTestId('sections-list')).toBeInTheDocument();
  });

  it('renders combined report when completed', () => {
    const mockData = {
      id: 456,
      result_id: 123,
      query_id: 100,
      mode: 'automatic',
      status: 'completed',
      sections: [{ id: 1, order: 1, heading: 'S1', summary: 'Summary 1', status: 'completed' }],
      combined_report: 'Final Report Content',
    };

    (usePageData as jest.Mock).mockReturnValue({
      data: mockData,
      loading: false,
      error: null,
      refetch: mockRefetch,
    });

    render(<ExpansionDetailPage />);

    expect(screen.getByTestId('combined-report')).toHaveTextContent('Final Report Content');
  });

  it('calls run automatic API when "Run All" is clicked', async () => {
    const mockData = {
      id: 456,
      result_id: 123,
      query_id: 100,
      mode: 'automatic',
      status: 'breakdown_complete',
      sections: [{ id: 1, order: 1, heading: 'S1', summary: 'Summary 1', status: 'pending' }],
    };

    (usePageData as jest.Mock).mockReturnValue({
      data: mockData,
      loading: false,
      error: null,
      refetch: mockRefetch,
    });

    render(<ExpansionDetailPage />);

    const runAllBtn = screen.getByRole('button', { name: /run all/i });
    fireEvent.click(runAllBtn);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/expansions/456/run'),
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('calls combine API when "Combine Report" is clicked', async () => {
    const mockData = {
      id: 456,
      result_id: 123,
      query_id: 100,
      mode: 'manual',
      status: 'breakdown_complete',
      sections: [{ id: 1, order: 1, heading: 'S1', summary: 'Summary 1', status: 'completed' }],
    };

    (usePageData as jest.Mock).mockReturnValue({
      data: mockData,
      loading: false,
      error: null,
      refetch: mockRefetch,
    });

    render(<ExpansionDetailPage />);

    const combineBtn = screen.getByRole('button', { name: /combine report/i });
    fireEvent.click(combineBtn);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/expansions/456/combine'),
      expect.objectContaining({ method: 'POST' })
    );
  });
});
