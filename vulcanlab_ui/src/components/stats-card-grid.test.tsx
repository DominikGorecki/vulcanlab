import { render, screen } from '@testing-library/react';
import { StatsCardGrid } from './stats-card-grid';
import type { StatsCardProps } from './stats-card';

// Mock icon component
const MockIcon = ({ className }: { className?: string }) => (
  <svg data-testid="mock-icon" className={className}>
    <circle cx="12" cy="12" r="10" />
  </svg>
);

const mockStats: StatsCardProps[] = [
  {
    label: 'Total Users',
    value: '1,234',
    icon: MockIcon,
    trend: { value: '+12%', direction: 'up' },
  },
  {
    label: 'Revenue',
    value: '$45,231',
    icon: MockIcon,
    trend: { value: '+8%', direction: 'up' },
  },
  {
    label: 'Orders',
    value: '543',
    trend: { value: '-3%', direction: 'down' },
  },
];

describe('StatsCardGrid', () => {
  it('should render correct number of StatsCard components', () => {
    render(<StatsCardGrid stats={mockStats} />);

    expect(screen.getByText('Total Users')).toBeInTheDocument();
    expect(screen.getByText('Revenue')).toBeInTheDocument();
    expect(screen.getByText('Orders')).toBeInTheDocument();
  });

  it('should apply grid layout classes', () => {
    const { container } = render(<StatsCardGrid stats={mockStats} />);

    const grid = container.firstChild;
    expect(grid).toHaveClass('grid');
    expect(grid).toHaveClass('grid-cols-1');
    expect(grid).toHaveClass('md:grid-cols-2');
    expect(grid).toHaveClass('lg:grid-cols-3');
  });

  it('should apply custom className', () => {
    const { container } = render(
      <StatsCardGrid stats={mockStats} className="custom-grid-class" />
    );

    const grid = container.firstChild;
    expect(grid).toHaveClass('custom-grid-class');
  });

  it('should handle empty stats array', () => {
    const { container } = render(<StatsCardGrid stats={[]} />);

    expect(container.firstChild).toBeNull();
  });

  it('should pass props correctly to each StatsCard', () => {
    render(<StatsCardGrid stats={mockStats} />);

    // Check that values are rendered
    expect(screen.getByText('1,234')).toBeInTheDocument();
    expect(screen.getByText('$45,231')).toBeInTheDocument();
    expect(screen.getByText('543')).toBeInTheDocument();

    // Check that trends are rendered
    expect(screen.getByText('+12%')).toBeInTheDocument();
    expect(screen.getByText('+8%')).toBeInTheDocument();
    expect(screen.getByText('-3%')).toBeInTheDocument();
  });

  it('should render single stat', () => {
    const singleStat: StatsCardProps[] = [
      { label: 'Users', value: 100 },
    ];

    render(<StatsCardGrid stats={singleStat} />);

    expect(screen.getByText('Users')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('should render multiple stats with different configurations', () => {
    const mixedStats: StatsCardProps[] = [
      { label: 'Stat 1', value: '100' },
      { label: 'Stat 2', value: 200, icon: MockIcon },
      { label: 'Stat 3', value: '300', trend: { value: '+5%', direction: 'up' } },
    ];

    render(<StatsCardGrid stats={mixedStats} />);

    expect(screen.getByText('Stat 1')).toBeInTheDocument();
    expect(screen.getByText('Stat 2')).toBeInTheDocument();
    expect(screen.getByText('Stat 3')).toBeInTheDocument();
  });

  it('should apply gap spacing between cards', () => {
    const { container } = render(<StatsCardGrid stats={mockStats} />);

    const grid = container.firstChild;
    expect(grid).toHaveClass('gap-4');
  });

  it('should render all cards in the grid', () => {
    const { container } = render(<StatsCardGrid stats={mockStats} />);

    const cards = container.querySelectorAll('[data-slot="card"]');
    expect(cards).toHaveLength(3);
  });
});
