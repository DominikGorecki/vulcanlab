import { render, screen, fireEvent } from '@testing-library/react';
import { useParams, useRouter } from 'next/navigation';
import DocumentViewerPage from '../page';
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

describe('DocumentViewerPage Collections Integration', () => {
  const mockOpenAddToCollection = jest.fn();
  const mockCloseAddToCollection = jest.fn();
  const mockRouterPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useParams as jest.Mock).mockReturnValue({
      work_id: '1',
      start_line: '10',
      end_line: '20',
    });
    (useRouter as jest.Mock).mockReturnValue({
      push: mockRouterPush,
      back: jest.fn(),
    });
    (useAddToCollection as jest.Mock).mockReturnValue({
      isOpen: false,
      openAddToCollection: mockOpenAddToCollection,
      closeAddToCollection: mockCloseAddToCollection,
      itemType: '',
      itemLink: '',
    });
  });

  it('renders "Add to Collection" button', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: { work_id: 1, work_title: 'Test Work', content: 'test', filename: 'test.md' },
      loading: false,
      error: null,
    });

    render(<DocumentViewerPage />);
    
    expect(screen.getByText(/Add to Collection/i)).toBeInTheDocument();
  });

  it('calls openAddToCollection with correct props when clicked', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: { work_id: 1, work_title: 'Test Work', content: 'test', filename: 'test.md' },
      loading: false,
      error: null,
    });

    render(<DocumentViewerPage />);
    
    const addButton = screen.getByText(/Add to Collection/i);
    fireEvent.click(addButton);

    expect(mockOpenAddToCollection).toHaveBeenCalledWith(
      'excerpt',
      '/search/result/1/10/20'
    );
  });

  it('renders AddToCollectionModal with correct props when open', () => {
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: { work_id: 1, work_title: 'Test Work', content: 'test', filename: 'test.md' },
      loading: false,
      error: null,
    });
    
    (useAddToCollection as jest.Mock).mockReturnValue({
      isOpen: true,
      openAddToCollection: mockOpenAddToCollection,
      closeAddToCollection: mockCloseAddToCollection,
      itemType: 'excerpt',
      itemLink: '/search/result/1/10/20',
    });

    render(<DocumentViewerPage />);
    
    expect(screen.getByTestId('add-to-collection-modal')).toBeInTheDocument();
    expect(screen.getByTestId('modal-type')).toHaveTextContent('excerpt');
    expect(screen.getByTestId('modal-link')).toHaveTextContent('/search/result/1/10/20');
  });
});

