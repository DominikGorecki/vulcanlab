import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DeepResearchModal } from '../DeepResearchModal';

// Mock useToast
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

// Mock Radix UI Dialog because it can be tricky in tests
jest.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open, onOpenChange }: any) => open ? <div role="dialog" onClick={() => onOpenChange?.(false)}>{children}</div> : null,
  DialogContent: ({ children }: any) => <div onClick={(e) => e.stopPropagation()}>{children}</div>,
  DialogHeader: ({ children }: any) => <div>{children}</div>,
  DialogTitle: ({ children }: any) => <h2>{children}</h2>,
  DialogDescription: ({ children }: any) => <p>{children}</p>,
}));

jest.mock('../ManualResearchWizard', () => ({
  ManualResearchWizard: () => <div data-testid="manual-wizard">Manual Wizard</div>,
}));

describe('DeepResearchModal', () => {
  const mockOnClose = jest.fn();
  const collectionId = 123;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly when open', () => {
    render(
      <DeepResearchModal 
        isOpen={true} 
        onClose={mockOnClose} 
        collectionId={collectionId} 
      />
    );

    expect(screen.getByText('Start Deep Research')).toBeInTheDocument();
    expect(screen.getByText('Manual Research')).toBeInTheDocument();
    expect(screen.getByText('Automated Research')).toBeInTheDocument();
    expect(screen.getByText('Start Manual')).toBeInTheDocument();
    expect(screen.getByText('Start Automated')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <DeepResearchModal 
        isOpen={false} 
        onClose={mockOnClose} 
        collectionId={collectionId} 
      />
    );

    expect(screen.queryByText('Start Deep Research')).not.toBeInTheDocument();
  });

  it('calls start-manual endpoint when Start Manual is clicked', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 456, status: 'in_progress' })
    });
    global.fetch = mockFetch;

    render(
      <DeepResearchModal 
        isOpen={true} 
        onClose={mockOnClose} 
        collectionId={collectionId} 
      />
    );

    fireEvent.click(screen.getByText('Start Manual'));
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/research-sessions', expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ collection_id: collectionId, session_type: 'manual' })
      }));
    });
  });

  it('calls start-automated endpoint when Start Automated is clicked', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ session_id: 456, status: 'in_progress' })
    });
    global.fetch = mockFetch;

    render(
      <DeepResearchModal 
        isOpen={true} 
        onClose={mockOnClose} 
        collectionId={collectionId} 
      />
    );

    fireEvent.click(screen.getByText('Start Automated'));
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/research-sessions/start-automated', expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ collection_id: collectionId })
      }));
    });
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('calls onClose when dialog is closed', () => {
    render(
      <DeepResearchModal 
        isOpen={true} 
        onClose={mockOnClose} 
        collectionId={collectionId} 
      />
    );

    // Clicking the "dialog" backdrop (mocked) should trigger onOpenChange(false) which calls onClose()
    fireEvent.click(screen.getByRole('dialog'));
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
});
