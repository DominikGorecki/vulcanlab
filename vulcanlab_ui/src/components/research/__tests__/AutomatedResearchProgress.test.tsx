import React from 'react';
import { render, screen } from '@testing-library/react';
import { AutomatedResearchProgress } from '../AutomatedResearchProgress';
import { usePollSessionStatus } from '@/lib/polling';
import { useToast } from '@/hooks/use-toast';

// Mock the hook and toast
jest.mock('@/lib/polling');
jest.mock('@/hooks/use-toast');

// Mock UI components that might be tricky
jest.mock('@/components/ui/progress', () => ({
  Progress: ({ value }: any) => <div role="progressbar" aria-valuenow={value} />
}));

describe('AutomatedResearchProgress', () => {
  const sessionId = 123;
  const mockToast = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useToast as jest.Mock).mockReturnValue({ toast: mockToast });
  });

  it('renders nothing when no status', () => {
    (usePollSessionStatus as jest.Mock).mockReturnValue({
      status: null,
      currentPhase: null,
      sectionsCompleted: 0,
      totalSections: 0,
      error: null,
      isPolling: false
    });

    const { container } = render(<AutomatedResearchProgress sessionId={sessionId} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders progress correctly', () => {
    (usePollSessionStatus as jest.Mock).mockReturnValue({
      status: 'in_progress',
      currentPhase: 'researching',
      sectionsCompleted: 2,
      totalSections: 5,
      error: null,
      isPolling: true
    });

    render(<AutomatedResearchProgress sessionId={sessionId} />);

    expect(screen.getByText(`Automated Research Session #${sessionId}`)).toBeInTheDocument();
    expect(screen.getByText('researching')).toBeInTheDocument();
    expect(screen.getByText('2 / 5 sections')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '40');
  });

  it('shows success toast on completion', () => {
    const onComplete = jest.fn();
    (usePollSessionStatus as jest.Mock).mockReturnValue({
      status: 'completed',
      currentPhase: 'completed',
      sectionsCompleted: 5,
      totalSections: 5,
      error: null,
      isPolling: false
    });

    render(<AutomatedResearchProgress sessionId={sessionId} onComplete={onComplete} />);

    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
      title: "Deep research completed!"
    }));
    expect(onComplete).toHaveBeenCalled();
  });

  it('shows error message on failure', () => {
    (usePollSessionStatus as jest.Mock).mockReturnValue({
      status: 'failed',
      currentPhase: 'failed',
      sectionsCompleted: 2,
      totalSections: 5,
      error: 'Something went wrong',
      isPolling: false
    });

    render(<AutomatedResearchProgress sessionId={sessionId} />);

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
      title: "Research failed",
      variant: "destructive"
    }));
  });
});
