import { render, screen } from '@testing-library/react';
import { SectionStatusBadge, sectionStatusConfig } from '../section-status-badge';

describe('SectionStatusBadge', () => {
  it('renders correct label for "pending" status', () => {
    render(<SectionStatusBadge status="pending" />);
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('renders correct label for "expanding" status', () => {
    render(<SectionStatusBadge status="expanding" />);
    expect(screen.getByText('Expanding')).toBeInTheDocument();
  });

  it('renders correct label for "ready" status', () => {
    render(<SectionStatusBadge status="ready" />);
    expect(screen.getByText('Ready')).toBeInTheDocument();
  });

  it('renders correct label for "generating" status', () => {
    render(<SectionStatusBadge status="generating" />);
    expect(screen.getByText('Generating')).toBeInTheDocument();
  });

  it('renders correct label for "completed" status', () => {
    render(<SectionStatusBadge status="completed" />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('renders correct label for "failed" status', () => {
    render(<SectionStatusBadge status="failed" />);
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('falls back gracefully for unknown status', () => {
    render(<SectionStatusBadge status="unknown_status" />);
    expect(screen.getByText('unknown_status')).toBeInTheDocument();
  });
});

describe('sectionStatusConfig', () => {
  it('has secondary variant for pending status', () => {
    expect(sectionStatusConfig.pending.variant).toBe('secondary');
  });

  it('has outline variant for expanding status', () => {
    expect(sectionStatusConfig.expanding.variant).toBe('outline');
  });

  it('has outline variant for ready status', () => {
    expect(sectionStatusConfig.ready.variant).toBe('outline');
  });

  it('has outline variant for generating status', () => {
    expect(sectionStatusConfig.generating.variant).toBe('outline');
  });

  it('has default variant for completed status', () => {
    expect(sectionStatusConfig.completed.variant).toBe('default');
  });

  it('has destructive variant for failed status', () => {
    expect(sectionStatusConfig.failed.variant).toBe('destructive');
  });
});
