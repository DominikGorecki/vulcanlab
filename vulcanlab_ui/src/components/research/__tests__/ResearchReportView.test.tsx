import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ResearchReportView } from '../ResearchReportView';
import { usePageData } from '@/hooks/use-page-data';

// Mock usePageData hook
jest.mock('@/hooks/use-page-data', () => ({
  usePageData: jest.fn(),
}));

// Mock components
jest.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open, onOpenChange }: any) => open ? <div role="dialog">{children}</div> : null,
  DialogContent: ({ children }: any) => <div>{children}</div>,
  DialogHeader: ({ children }: any) => <div>{children}</div>,
  DialogTitle: ({ children }: any) => <h2>{children}</h2>,
  DialogDescription: ({ children }: any) => <p>{children}</p>,
  DialogFooter: ({ children }: any) => <div>{children}</div>,
}));

jest.mock('@/components/markdown-renderer', () => ({
  MarkdownRenderer: ({ content, components }: any) => (
    <div data-testid="markdown-content">
      {content}
      {/* Simulate a link to test the custom renderer if needed, but here we just render content */}
    </div>
  ),
}));

jest.mock('@/components/collections/MetadataCard', () => ({
  MetadataCard: ({ collectionId, itemId }: any) => (
    <div data-testid={`metadata-card-${itemId}`}>Metadata for {itemId} in {collectionId}</div>
  ),
}));

describe('ResearchReportView', () => {
  const sessionId = 456;
  const collectionId = 123;
  const mockOnClose = jest.fn();

  const mockReport = {
    id: 1,
    session_id: sessionId,
    report_content: '# Test Report Content\n\nSee [Citation](link://collection-item/789)',
    executive_summary: 'Test summary',
    report_metadata: {
      word_count: 100,
      citation_count: 1
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    (usePageData as jest.Mock).mockReturnValue({
      data: null,
      loading: true,
      error: null,
    });

    render(<ResearchReportView sessionId={sessionId} collectionId={collectionId} onClose={mockOnClose} />);
    expect(screen.getByText(/Fetching report content/)).toBeInTheDocument();
  });

  it('renders error state', () => {
    const error = 'Report not found';
    (usePageData as jest.Mock).mockReturnValue({
      data: null,
      loading: false,
      error,
    });

    render(<ResearchReportView sessionId={sessionId} collectionId={collectionId} onClose={mockOnClose} />);
    expect(screen.getByText(error)).toBeInTheDocument();
  });

  it('renders report content correctly', () => {
    (usePageData as jest.Mock).mockReturnValue({
      data: mockReport,
      loading: false,
      error: null,
    });

    render(<ResearchReportView sessionId={sessionId} collectionId={collectionId} onClose={mockOnClose} />);
    
    expect(screen.getByText('Research Report')).toBeInTheDocument();
    expect(screen.getByText('Test summary')).toBeInTheDocument();
    expect(screen.getByTestId('markdown-content')).toBeInTheDocument();
    expect(screen.getByText(/Test Report Content/)).toBeInTheDocument();
    expect(screen.getByText(/100 words/)).toBeInTheDocument();
    expect(screen.getByText(/1 citation/)).toBeInTheDocument();
  });

  it('calls onClose when Close button is clicked', () => {
    (usePageData as jest.Mock).mockReturnValue({
      data: mockReport,
      loading: false,
      error: null,
    });

    render(<ResearchReportView sessionId={sessionId} collectionId={collectionId} onClose={mockOnClose} />);
    
    fireEvent.click(screen.getByRole('button', { name: /Close/i }));
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
});
