import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CollectionDetailPage from '../page';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useParams: () => ({ id: '123' }),
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

// Mock useToast
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock the DeepResearchModal to avoid testing its internals here
jest.mock('@/components/research/DeepResearchModal', () => ({
  DeepResearchModal: ({ isOpen }: { isOpen: boolean }) => 
    isOpen ? <div data-testid="deep-research-modal">Deep Research Modal Content</div> : null,
}));

describe('CollectionDetailPage - Deep Research Button', () => {
  const mockCollection = (itemCount: number) => ({
    id: 123,
    name: 'Test Collection',
    description: 'Test Description',
    tags: ['test'],
    item_count: itemCount,
    items: Array(itemCount).fill({ id: 1, item_type: 'work', link: '/test', order: 1 }),
    created_at: '2023-01-01T00:00:00',
    updated_at: '2023-01-01T00:00:00',
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders "Deep Research" button when item count >= 5', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockCollection(5),
    });

    render(<CollectionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Deep Research')).toBeInTheDocument();
    });
  });

  it('does NOT render "Deep Research" button when item count < 5', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockCollection(4),
    });

    render(<CollectionDetailPage />);

    await waitFor(() => {
      // We expect PageHeader to be rendered but without the button in actions
      expect(screen.queryByText('Deep Research')).not.toBeInTheDocument();
    });
  });

  it('opens DeepResearchModal when button is clicked', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockCollection(5),
    });

    render(<CollectionDetailPage />);

    await waitFor(() => {
      const button = screen.getByText('Deep Research');
      fireEvent.click(button);
    });

    expect(screen.getByTestId('deep-research-modal')).toBeInTheDocument();
  });
});
