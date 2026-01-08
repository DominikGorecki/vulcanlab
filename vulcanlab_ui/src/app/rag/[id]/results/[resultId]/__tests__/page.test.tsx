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

// Mock components
jest.mock('@/components', () => {
  const actual = jest.requireActual('@/components');
  return {
    ...actual,
    StickyDetailHeader: ({ title, actions }: any) => (
      <div data-testid="sticky-header">
        <h1>{title}</h1>
        <div data-testid="header-actions">{actions}</div>
      </div>
    ),
    PageLoadingState: () => <div data-testid="loading">Loading...</div>,
    PageErrorState: () => <div data-testid="error">Error</div>,
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
  };
});

// Mock MarkdownEditor to avoid issues with heavy components
jest.mock('@/components/markdown-editor', () => ({
  MarkdownEditor: () => <div data-testid="markdown-editor" />,
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
        result: { id: 1, response_text: 'test result', model_name: 'test-model' }
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
        result: { id: 1, response_text: 'test result', model_name: 'test-model' }
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

