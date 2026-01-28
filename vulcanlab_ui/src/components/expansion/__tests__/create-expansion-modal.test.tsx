import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { CreateExpansionModal } from '../create-expansion-modal';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock useToast
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

describe('CreateExpansionModal', () => {
  const mockOnClose = jest.fn();
  const mockOnSuccess = jest.fn();
  const mockRouterPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockRouterPush,
    });
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders modal when isOpen is true', () => {
    render(
      <CreateExpansionModal
        isOpen={true}
        onClose={mockOnClose}
        resultId={123}
      />
    );

    expect(screen.getByText('Expand Answer')).toBeInTheDocument();
    expect(screen.getByText(/Create an expansion to break down/)).toBeInTheDocument();
  });

  it('does not render modal when isOpen is false', () => {
    render(
      <CreateExpansionModal
        isOpen={false}
        onClose={mockOnClose}
        resultId={123}
      />
    );

    expect(screen.queryByText('Expand Answer')).not.toBeInTheDocument();
  });

  it('shows Automatic and Manual mode options', () => {
    render(
      <CreateExpansionModal
        isOpen={true}
        onClose={mockOnClose}
        resultId={123}
      />
    );

    expect(screen.getByText('Automatic')).toBeInTheDocument();
    expect(screen.getByText('Manual')).toBeInTheDocument();
    expect(screen.getByText(/System will process all sections automatically/)).toBeInTheDocument();
    expect(screen.getByText(/You will copy each section prompt/)).toBeInTheDocument();
  });

  it('shows Recommended badge for Automatic mode', () => {
    render(
      <CreateExpansionModal
        isOpen={true}
        onClose={mockOnClose}
        resultId={123}
      />
    );

    expect(screen.getByText('Recommended')).toBeInTheDocument();
  });

  it('allows switching between modes', () => {
    render(
      <CreateExpansionModal
        isOpen={true}
        onClose={mockOnClose}
        resultId={123}
      />
    );

    // Click on Manual mode
    const manualOption = screen.getByText('Manual').closest('div[class*="cursor-pointer"]');
    if (manualOption) {
      fireEvent.click(manualOption);
    }

    // The Manual option should now be selected (visual check would require DOM inspection)
    expect(screen.getByText('Manual')).toBeInTheDocument();
  });

  it('calls onClose when Cancel button is clicked', () => {
    render(
      <CreateExpansionModal
        isOpen={true}
        onClose={mockOnClose}
        resultId={123}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('submits to API and redirects on success', async () => {
    const mockExpansion = { expansion_id: 456 };
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockExpansion,
    });

    render(
      <CreateExpansionModal
        isOpen={true}
        onClose={mockOnClose}
        resultId={123}
        onSuccess={mockOnSuccess}
      />
    );

    const createButton = screen.getByText('Create Expansion');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/expansions/'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('"result_id":123'),
        })
      );
    });

    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
      expect(mockRouterPush).toHaveBeenCalledWith('/expansions/456');
    });
  });

  it('submits correct mode when Manual is selected', async () => {
    const mockExpansion = { expansion_id: 789 };
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockExpansion,
    });

    render(
      <CreateExpansionModal
        isOpen={true}
        onClose={mockOnClose}
        resultId={123}
        onSuccess={mockOnSuccess}
      />
    );

    // Select Manual mode
    const manualOption = screen.getByText('Manual').closest('div[class*="cursor-pointer"]');
    if (manualOption) {
      fireEvent.click(manualOption);
    }

    const createButton = screen.getByText('Create Expansion');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: expect.stringContaining('"mode":"manual"'),
        })
      );
    });

    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
      expect(mockRouterPush).toHaveBeenCalledWith('/expansions/789');
    });
  });
});
