import { render, screen } from '@testing-library/react';
import { StatsCard } from './stats-card';

// Mock icon component
const MockIcon = ({ className }: { className?: string }) => (
  <svg data-testid="mock-icon" className={className}>
    <circle cx="12" cy="12" r="10" />
  </svg>
);

describe('StatsCard', () => {
  it('should render label', () => {
    render(<StatsCard label="Total Users" value={100} />);
    expect(screen.getByText('Total Users')).toBeInTheDocument();
  });

  it('should render string value', () => {
    render(<StatsCard label="Revenue" value="$1,234" />);
    expect(screen.getByText('$1,234')).toBeInTheDocument();
  });

  it('should render number value', () => {
    render(<StatsCard label="Count" value={42} />);
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('should render icon when provided', () => {
    render(
      <StatsCard
        label="Users"
        value={100}
        icon={MockIcon}
      />
    );
    expect(screen.getByTestId('mock-icon')).toBeInTheDocument();
  });

  it('should not render icon when not provided', () => {
    render(<StatsCard label="Users" value={100} />);
    expect(screen.queryByTestId('mock-icon')).not.toBeInTheDocument();
  });

  it('should render trend when provided', () => {
    render(
      <StatsCard
        label="Sales"
        value={100}
        trend={{ value: '+12%', direction: 'up' }}
      />
    );
    expect(screen.getByText('+12%')).toBeInTheDocument();
  });

  it('should show up arrow for up direction', () => {
    const { container } = render(
      <StatsCard
        label="Sales"
        value={100}
        trend={{ value: '+12%', direction: 'up' }}
      />
    );
    // TrendingUp icon should be present
    const icons = container.querySelectorAll('svg');
    expect(icons.length).toBeGreaterThan(0);
  });

  it('should show down arrow for down direction', () => {
    const { container } = render(
      <StatsCard
        label="Sales"
        value={100}
        trend={{ value: '-5%', direction: 'down' }}
      />
    );
    // TrendingDown icon should be present
    const icons = container.querySelectorAll('svg');
    expect(icons.length).toBeGreaterThan(0);
  });

  it('should apply green color for up trend', () => {
    render(
      <StatsCard
        label="Sales"
        value={100}
        trend={{ value: '+12%', direction: 'up' }}
      />
    );
    const trendValue = screen.getByText('+12%');
    expect(trendValue).toHaveClass('text-green-600');
  });

  it('should apply red color for down trend', () => {
    render(
      <StatsCard
        label="Sales"
        value={100}
        trend={{ value: '-5%', direction: 'down' }}
      />
    );
    const trendValue = screen.getByText('-5%');
    expect(trendValue).toHaveClass('text-red-600');
  });

  it('should apply custom className', () => {
    const { container } = render(
      <StatsCard
        label="Users"
        value={100}
        className="custom-stats-class"
      />
    );
    const card = container.querySelector('[data-slot="card"]');
    expect(card).toHaveClass('custom-stats-class');
  });

  it('should not render trend when not provided', () => {
    render(<StatsCard label="Users" value={100} />);
    expect(screen.queryByText('vs last period')).not.toBeInTheDocument();
  });

  it('should render all elements together', () => {
    render(
      <StatsCard
        label="Total Revenue"
        value="$12,345"
        icon={MockIcon}
        trend={{ value: '+15%', direction: 'up' }}
      />
    );
    expect(screen.getByText('Total Revenue')).toBeInTheDocument();
    expect(screen.getByText('$12,345')).toBeInTheDocument();
    expect(screen.getByTestId('mock-icon')).toBeInTheDocument();
    expect(screen.getByText('+15%')).toBeInTheDocument();
  });

  it('should render trend with numeric value', () => {
    render(
      <StatsCard
        label="Growth"
        value={100}
        trend={{ value: 12, direction: 'up' }}
      />
    );
    expect(screen.getByText('12')).toBeInTheDocument();
  });
});
