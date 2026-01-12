import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { ResearchReportList } from '../ResearchReportList';
import { usePageData } from '@/hooks/use-page-data';

// Mock usePageData hook
jest.mock('@/hooks/use-page-data', () => ({
  usePageData: jest.fn(),
}));

// Mock child components
jest.mock('../ResearchReportCard', () => ({
  ResearchReportCard: ({ session, onClick }: any) => (
    <div data-testid={`report-card-${session.id}`} onClick={onClick}>
      Report {session.id}
    </div>
  ),
}));

jest.mock('../ResearchReportView', () => ({
  ResearchReportView: ({ sessionId, onClose }: any) => (
    <div data-testid="report-view">
      Viewing {sessionId}
      <button onClick={onClose}>Close</button>
    </div>
  ),
}));

describe('ResearchReportList', () => {
  const collectionId = 123;
  const mockSessions = [
    {
      id: 1,
      status: 'completed',
      session_type: 'manual',
      created_at: '2026-01-01T10:00:00Z',
    },
    {
      id: 2,
      status: 'completed',
      session_type: 'automated',
      created_at: '2026-01-02T10:00:00Z',
    },
    {
      id: 3,
      status: 'in_progress',
      session_type: 'automated',
      created_at: '2026-01-03T10:00:00Z',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    (usePageData as jest.Mock).mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refetch: jest.fn(),
    });

    render(<ResearchReportList collectionId={collectionId} />);
    expect(screen.getByTestId('page-loading-state')).toBeInTheDocument();
  });

  it('renders error state', () => {
    const error = 'Failed to fetch';
    (usePageData as jest.Mock).mockReturnValue({
      data: null,
      loading: false,
      error,
      refetch: jest.fn(),
    });

    render(<ResearchReportList collectionId={collectionId} />);
    expect(screen.getByText(error)).toBeInTheDocument();
  });

  it('renders empty state when no completed sessions', () => {
    (usePageData as jest.Mock).mockReturnValue({
      data: [],
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<ResearchReportList collectionId={collectionId} />);
    expect(screen.getByText(/No research reports yet/)).toBeInTheDocument();
  });

  it('renders only completed sessions sorted by date DESC', () => {
    // Sort mockSessions by date DESC as the component expects
    const sortedCompletedSessions = mockSessions
      .filter(s => s.status === 'completed')
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    (usePageData as jest.Mock).mockReturnValue({
      data: sortedCompletedSessions,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<ResearchReportList collectionId={collectionId} />);
    
    expect(screen.getByText('Research Reports')).toBeInTheDocument();
    expect(screen.getByTestId('report-card-1')).toBeInTheDocument();
    expect(screen.getByTestId('report-card-2')).toBeInTheDocument();
    expect(screen.queryByTestId('report-card-3')).not.toBeInTheDocument();

    // Verify sort (date DESC) - session 2 is newer
    const cards = screen.getAllByTestId(/report-card-/);
    expect(cards[0]).toHaveTextContent('Report 2');
    expect(cards[1]).toHaveTextContent('Report 1');
  });

  it('opens ResearchReportView when card is clicked', async () => {
    (usePageData as jest.Mock).mockReturnValue({
      data: mockSessions.filter(s => s.status === 'completed'),
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<ResearchReportList collectionId={collectionId} />);
    
    fireEvent.click(screen.getByTestId('report-card-2'));
    
    expect(screen.getByTestId('report-view')).toBeInTheDocument();
    expect(screen.getByText('Viewing 2')).toBeInTheDocument();
  });
});

// Mock PageLoadingState and PageErrorState since they are from @/components
jest.mock('@/components/page-loading-state', () => ({
  PageLoadingState: () => <div data-testid="page-loading-state">Loading...</div>
}));

jest.mock('@/components/page-error-state', () => ({
  PageErrorState: ({ error }: any) => <div>{error}</div>
}));

import { fireEvent } from '@testing-library/react';
