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

// Mock the DeepResearchModal
jest.mock('@/components/research/DeepResearchModal', () => ({
  DeepResearchModal: ({ isOpen, initialSessionId }: { isOpen: boolean; initialSessionId?: number }) => 
    isOpen ? (
      <div data-testid="deep-research-modal">
        Deep Research Modal Content
        {initialSessionId && <span data-testid="resume-id">{initialSessionId}</span>}
      </div>
    ) : null,
}));

describe('CollectionDetailPage - Session Resume', () => {
  const mockCollection = {
    id: 123,
    name: 'Test Collection',
    description: 'Test Description',
    tags: ['test'],
    item_count: 5,
    items: Array(5).fill({ id: 1, item_type: 'work', link: '/test', order: 1 }),
    created_at: '2023-01-01T00:00:00',
    updated_at: '2023-01-01T00:00:00',
  };

  const mockSessions = {
    sessions: [
      {
        id: 10,
        collection_id: 123,
        status: 'in_progress',
        session_type: 'manual',
        current_phase: 'research',
        created_at: '2023-01-02T00:00:00',
      }
    ]
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockImplementation((url) => {
      if (url.endsWith('/api/v1/collections/123')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockCollection,
        });
      }
      if (url.endsWith('/research-sessions')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockSessions,
        });
      }
      if (url.includes('/resume')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ session_id: 10, current_phase: 'research', next_step: {} }),
        });
      }
      return Promise.reject(new Error(`Unknown URL: ${url}`));
    });
  });

  it('renders in-progress sessions', async () => {
    render(<CollectionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('In-Progress Research')).toBeInTheDocument();
      expect(screen.getByText(/manual Research/i)).toBeInTheDocument();
      expect(screen.getByText('Resume Session')).toBeInTheDocument();
    });
  });

  it('calls resume API and opens modal with sessionId when Resume is clicked', async () => {
    render(<CollectionDetailPage />);

    await waitFor(() => {
      const resumeButton = screen.getByText('Resume Session');
      fireEvent.click(resumeButton);
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/api/v1/research-sessions/10/resume'), expect.anything());
      expect(screen.getByTestId('deep-research-modal')).toBeInTheDocument();
      expect(screen.getByTestId('resume-id')).toHaveTextContent('10');
    });
  });
});
