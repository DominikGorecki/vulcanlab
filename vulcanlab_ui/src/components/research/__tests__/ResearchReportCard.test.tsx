import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ResearchReportCard } from '../ResearchReportCard';
import { ResearchSession } from '@/types/research';

describe('ResearchReportCard', () => {
  const mockSession: ResearchSession = {
    id: 1,
    collection_id: 123,
    thread_id: 'thread-1',
    session_type: 'automated',
    status: 'completed',
    created_at: '2026-01-08T12:00:00Z',
    updated_at: '2026-01-08T13:00:00Z',
    state_data: {
      executive_summary: 'This is a test executive summary that should be displayed on the card.',
      report_metadata: {
        word_count: 500,
        citation_count: 10
      }
    }
  };

  const mockOnClick = jest.fn();

  it('renders session information correctly', () => {
    render(<ResearchReportCard session={mockSession} onClick={mockOnClick} />);

    expect(screen.getByText(/automated/i)).toBeInTheDocument();
    expect(screen.getByText('Jan 8, 2026')).toBeInTheDocument();
    expect(screen.getByText(/This is a test executive summary/)).toBeInTheDocument();
    expect(screen.getByText(/500/)).toBeInTheDocument();
    expect(screen.getByText(/words/)).toBeInTheDocument();
    expect(screen.getByText(/10/)).toBeInTheDocument();
    expect(screen.getByText(/citations/)).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    render(<ResearchReportCard session={mockSession} onClick={mockOnClick} />);

    fireEvent.click(screen.getByRole('button', { name: /View Report/i }));
    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  it('truncates long executive summary', () => {
    const longSummary = 'A'.repeat(200);
    const sessionWithLongSummary = {
      ...mockSession,
      state_data: {
        ...mockSession.state_data,
        executive_summary: longSummary
      }
    };

    render(<ResearchReportCard session={sessionWithLongSummary} onClick={mockOnClick} />);
    
    const preview = screen.getByText(/A{150}\.\.\./);
    expect(preview).toBeInTheDocument();
  });

  it('handles missing metadata gracefully', () => {
    const sessionNoMetadata: ResearchSession = {
      ...mockSession,
      state_data: {}
    };

    render(<ResearchReportCard session={sessionNoMetadata} onClick={mockOnClick} />);
    
    expect(screen.getByText('No executive summary available.')).toBeInTheDocument();
    expect(screen.getByText('0 words')).toBeInTheDocument();
    expect(screen.getByText('0 citations')).toBeInTheDocument();
  });
});
