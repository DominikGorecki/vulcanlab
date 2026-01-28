import { render, screen, fireEvent } from '@testing-library/react';
import { useParams, useRouter } from 'next/navigation';
import ResultDetailPage from '../page';
import { useAddToCollection } from '@/hooks/use-add-to-collection';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useParams: jest.fn(),
  useRouter: jest.fn(),
}));

// Mock usePageData
jest.mock('@/hooks/use-page-data', () => ({
  usePageData: jest.fn(),
}));

// Mock useAddToCollection
jest.mock('@/hooks/use-add-to-collection', () => ({
  useAddToCollection: jest.fn(),
}));

// Mock page-loading-state
jest.mock('@/components/page-loading-state', () => ({
  PageLoadingState: () => <div data-testid="loading">Loading...</div>,
}));

// Mock page-error-state
jest.mock('@/components/page-error-state', () => ({
  PageErrorState: () => <div data-testid="error">Error</div>,
}));

// Mock sticky-detail-header
jest.mock('@/components/sticky-detail-header', () => ({
  StickyDetailHeader: ({ title, actions }: any) => (
    <div data-testid="sticky-header">
      <h1>{title}</h1>
      <div data-testid="header-actions">{actions}</div>
    </div>
  ),
}));

// Mock AddToCollectionModal
jest.mock('@/components/collections/AddToCollectionModal', () => ({
  AddToCollectionModal: ({ isOpen, onClose, itemType, itemLink }: any) => (
    <div data-testid="add-to-collection-modal">
      {isOpen && (
        <>
          <span data-testid="modal-type">{itemType}</span>
          <span data-testid="modal-link">{itemLink}</span>
          <button onClick={onClose}>Close</button>
        </>
      )}
    </div>
  ),
}));

// Mock MarkdownEditor to avoid issues with heavy components
jest.mock('@/components/markdown-editor', () => ({
  MarkdownEditor: () => <div data-testid="markdown-editor" />,
}));

// Mock TextStats
jest.mock('@/components/text-stats', () => ({
  TextStats: () => <span data-testid="text-stats" />,
}));

// Mock CreateExpansionModal
jest.mock('@/components/expansion', () => ({
  CreateExpansionModal: ({ isOpen, onClose, resultId }: any) => (
    <div data-testid="create-expansion-modal">
      {isOpen && (
        <>
          <span data-testid="expansion-result-id">{resultId}</span>
          <button onClick={onClose}>Close Expansion Modal</button>
        </>
      )}
    </div>
  ),
}));

describe('ResultDetailPage Collections Integration', () => {
  const mockOpenAddToCollection = jest.fn();
  const mockCloseAddToCollection = jest.fn();
  const mockRouterPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useParams as jest.Mock).mockReturnValue({
      id: 'query-1',
      resultId: 'result-1',
    });
    (useRouter as jest.Mock).mockReturnValue({
      push: mockRouterPush,
    });
    (useAddToCollection as jest.Mock).mockReturnValue({
      isOpen: false,
      openAddToCollection: mockOpenAddToCollection,
      closeAddToCollection: mockCloseAddToCollection,
      itemType: '',
      itemLink: '',
    });
  });

  it('renders "Add to Collection" button in header', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: {
        query: { id: 1, original_query: 'test query' },
        result: { id: 1, response_text: 'test result', model_name: 'test-model' },
        expansion: null,
      },
      loading: false,
      error: null,
    });

    render(<ResultDetailPage />);

    expect(screen.getByText(/Add to Collection/i)).toBeInTheDocument();
  });

  it('calls openAddToCollection with correct props when clicked', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: {
        query: { id: 1, original_query: 'test query' },
        result: { id: 1, response_text: 'test result', model_name: 'test-model' },
        expansion: null,
      },
      loading: false,
      error: null,
    });

    render(<ResultDetailPage />);

    const addButton = screen.getByText(/Add to Collection/i);
    fireEvent.click(addButton);

    expect(mockOpenAddToCollection).toHaveBeenCalledWith(
      'research_result',
      '/rag/query-1/results/result-1'
    );
  });
});

describe('ResultDetailPage Expansion Integration', () => {
  const mockOpenAddToCollection = jest.fn();
  const mockCloseAddToCollection = jest.fn();
  const mockRouterPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useParams as jest.Mock).mockReturnValue({
      id: '1',
      resultId: '2',
    });
    (useRouter as jest.Mock).mockReturnValue({
      push: mockRouterPush,
    });
    (useAddToCollection as jest.Mock).mockReturnValue({
      isOpen: false,
      openAddToCollection: mockOpenAddToCollection,
      closeAddToCollection: mockCloseAddToCollection,
      itemType: '',
      itemLink: '',
    });
  });

  it('renders "Expand Answer" button when no expansion exists', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: {
        query: { id: 1, original_query: 'test query' },
        result: { id: 1, response_text: 'test result', model_name: 'test-model' },
        expansion: null,
      },
      loading: false,
      error: null,
    });

    render(<ResultDetailPage />);

    expect(screen.getByText(/Expand Answer/i)).toBeInTheDocument();
    expect(screen.queryByText(/View Expansion/i)).not.toBeInTheDocument();
  });

  it('renders "View Expansion" button when expansion exists', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: {
        query: { id: 1, original_query: 'test query' },
        result: { id: 1, response_text: 'test result', model_name: 'test-model' },
        expansion: { id: 123, status: 'completed' },
      },
      loading: false,
      error: null,
    });

    render(<ResultDetailPage />);

    expect(screen.getByText(/View Expansion/i)).toBeInTheDocument();
    expect(screen.queryByText(/Expand Answer/i)).not.toBeInTheDocument();
  });

  it('navigates to expansion detail when View Expansion is clicked', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: {
        query: { id: 1, original_query: 'test query' },
        result: { id: 1, response_text: 'test result', model_name: 'test-model' },
        expansion: { id: 456, status: 'completed' },
      },
      loading: false,
      error: null,
    });

    render(<ResultDetailPage />);

    const viewButton = screen.getByText(/View Expansion/i);
    fireEvent.click(viewButton);

    expect(mockRouterPush).toHaveBeenCalledWith('/expansions/456');
  });

  it('opens expansion modal when Expand Answer is clicked', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: {
        query: { id: 1, original_query: 'test query' },
        result: { id: 1, response_text: 'test result', model_name: 'test-model' },
        expansion: null,
      },
      loading: false,
      error: null,
    });

    render(<ResultDetailPage />);

    // Modal should not be visible initially
    expect(screen.queryByTestId('expansion-result-id')).not.toBeInTheDocument();

    // Click Expand Answer button
    const expandButton = screen.getByText(/Expand Answer/i);
    fireEvent.click(expandButton);

    // Modal should now be visible with correct resultId
    expect(screen.getByTestId('expansion-result-id')).toHaveTextContent('2');
  });
});
