import { render, screen } from '@testing-library/react';
import { ExpansionStatusBadge, expansionStatusConfig } from '../expansion-status-badge';

describe('ExpansionStatusBadge', () => {
  it('renders correct label for "created" status', () => {
    render(<ExpansionStatusBadge status="created" />);
    expect(screen.getByText('Created')).toBeInTheDocument();
  });

  it('renders correct label for "breakdown_pending" status', () => {
    render(<ExpansionStatusBadge status="breakdown_pending" />);
    expect(screen.getByText('Breakdown Pending')).toBeInTheDocument();
  });

  it('renders correct label for "breakdown_complete" status', () => {
    render(<ExpansionStatusBadge status="breakdown_complete" />);
    expect(screen.getByText('Breakdown Complete')).toBeInTheDocument();
  });

  it('renders correct label for "sections_in_progress" status', () => {
    render(<ExpansionStatusBadge status="sections_in_progress" />);
    expect(screen.getByText('Processing Sections')).toBeInTheDocument();
  });

  it('renders correct label for "combining" status', () => {
    render(<ExpansionStatusBadge status="combining" />);
    expect(screen.getByText('Combining')).toBeInTheDocument();
  });

  it('renders correct label for "completed" status', () => {
    render(<ExpansionStatusBadge status="completed" />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('renders correct label for "failed" status', () => {
    render(<ExpansionStatusBadge status="failed" />);
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('falls back gracefully for unknown status', () => {
    render(<ExpansionStatusBadge status="unknown_status" />);
    expect(screen.getByText('unknown_status')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <ExpansionStatusBadge status="completed" className="custom-class" />
    );
    const badge = container.firstChild;
    expect(badge).toHaveClass('custom-class');
  });
});

describe('expansionStatusConfig', () => {
  it('has gray variant for created status', () => {
    expect(expansionStatusConfig.created.variant).toBe('secondary');
  });

  it('has gray variant for breakdown_pending status', () => {
    expect(expansionStatusConfig.breakdown_pending.variant).toBe('secondary');
  });

  it('has outline variant for breakdown_complete status', () => {
    expect(expansionStatusConfig.breakdown_complete.variant).toBe('outline');
  });

  it('has outline variant for sections_in_progress status', () => {
    expect(expansionStatusConfig.sections_in_progress.variant).toBe('outline');
  });

  it('has outline variant for combining status', () => {
    expect(expansionStatusConfig.combining.variant).toBe('outline');
  });

  it('has default variant for completed status', () => {
    expect(expansionStatusConfig.completed.variant).toBe('default');
  });

  it('has destructive variant for failed status', () => {
    expect(expansionStatusConfig.failed.variant).toBe('destructive');
  });
});
