import { render, screen } from '@testing-library/react';
import { StatusBadge } from './status-badge';

// Mock icon component
const MockIcon = ({ className }: { className?: string }) => (
  <svg data-testid="mock-icon" className={className}>
    <circle cx="12" cy="12" r="10" />
  </svg>
);

const testStatusConfig = {
  completed: {
    label: 'Completed',
    variant: 'default' as const,
    icon: MockIcon,
  },
  pending: {
    label: 'Pending',
    variant: 'secondary' as const,
  },
  failed: {
    label: 'Failed',
    variant: 'destructive' as const,
    icon: MockIcon,
  },
};

describe('StatusBadge', () => {
  it('should render label from statusConfig', () => {
    render(
      <StatusBadge
        status="completed"
        statusConfig={testStatusConfig}
      />
    );
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('should render icon when provided in config', () => {
    render(
      <StatusBadge
        status="completed"
        statusConfig={testStatusConfig}
      />
    );
    expect(screen.getByTestId('mock-icon')).toBeInTheDocument();
  });

  it('should not render icon when not provided in config', () => {
    render(
      <StatusBadge
        status="pending"
        statusConfig={testStatusConfig}
      />
    );
    expect(screen.queryByTestId('mock-icon')).not.toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <StatusBadge
        status="completed"
        statusConfig={testStatusConfig}
        className="custom-badge-class"
      />
    );
    const badge = container.firstChild;
    expect(badge).toHaveClass('custom-badge-class');
  });

  it('should handle unknown status with default variant', () => {
    render(
      <StatusBadge
        status="unknown"
        statusConfig={testStatusConfig}
      />
    );
    // Should render the status as the label
    expect(screen.getByText('unknown')).toBeInTheDocument();
  });

  it('should fall back gracefully when statusConfig is missing status key', () => {
    render(
      <StatusBadge
        status="missing"
        statusConfig={testStatusConfig}
      />
    );
    // Should render the status value as fallback
    expect(screen.getByText('missing')).toBeInTheDocument();
  });

  it('should render different statuses with different labels', () => {
    const { rerender } = render(
      <StatusBadge
        status="completed"
        statusConfig={testStatusConfig}
      />
    );
    expect(screen.getByText('Completed')).toBeInTheDocument();

    rerender(
      <StatusBadge
        status="pending"
        statusConfig={testStatusConfig}
      />
    );
    expect(screen.getByText('Pending')).toBeInTheDocument();

    rerender(
      <StatusBadge
        status="failed"
        statusConfig={testStatusConfig}
      />
    );
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('should apply correct icon className', () => {
    render(
      <StatusBadge
        status="completed"
        statusConfig={testStatusConfig}
      />
    );
    const icon = screen.getByTestId('mock-icon');
    expect(icon).toHaveClass('size-3');
  });

  it('should render badge with gap when icon is present', () => {
    const { container } = render(
      <StatusBadge
        status="completed"
        statusConfig={testStatusConfig}
      />
    );
    const badge = container.firstChild;
    expect(badge).toHaveClass('gap-1');
  });
});
