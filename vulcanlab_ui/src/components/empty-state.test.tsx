import { render, screen, fireEvent } from '@testing-library/react';
import { EmptyState } from './empty-state';

// Mock icon component
const MockIcon = ({ className }: { className?: string }) => (
  <svg data-testid="mock-icon" className={className}>
    <circle cx="12" cy="12" r="10" />
  </svg>
);

describe('EmptyState', () => {
  it('should render title', () => {
    render(<EmptyState title="No items found" />);
    expect(screen.getByText('No items found')).toBeInTheDocument();
  });

  it('should render with icon component', () => {
    render(<EmptyState title="No data" icon={MockIcon} />);
    const icon = screen.getByTestId('mock-icon');
    expect(icon).toBeInTheDocument();
  });

  it('should render with description', () => {
    render(
      <EmptyState
        title="No results"
        description="Try adjusting your filters"
      />
    );
    expect(screen.getByText('Try adjusting your filters')).toBeInTheDocument();
  });

  it('should render with title, icon, and description', () => {
    render(
      <EmptyState
        title="Empty folder"
        icon={MockIcon}
        description="This folder contains no files"
      />
    );
    expect(screen.getByText('Empty folder')).toBeInTheDocument();
    expect(screen.getByTestId('mock-icon')).toBeInTheDocument();
    expect(screen.getByText('This folder contains no files')).toBeInTheDocument();
  });

  it('should show action button when action is provided', () => {
    const handleClick = jest.fn();
    render(
      <EmptyState
        title="No items"
        action={{ label: 'Add Item', onClick: handleClick }}
      />
    );
    const button = screen.getByRole('button', { name: 'Add Item' });
    expect(button).toBeInTheDocument();
  });

  it('should not show action button when action is undefined', () => {
    render(<EmptyState title="No items" />);
    const button = screen.queryByRole('button');
    expect(button).not.toBeInTheDocument();
  });

  it('should call onClick when action button is clicked', () => {
    const handleClick = jest.fn();
    render(
      <EmptyState
        title="No data"
        action={{ label: 'Create New', onClick: handleClick }}
      />
    );
    const button = screen.getByRole('button', { name: 'Create New' });
    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should apply custom className', () => {
    const { container } = render(
      <EmptyState
        title="Empty"
        className="custom-empty-class"
      />
    );
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('custom-empty-class');
  });

  it('should not render icon when not provided', () => {
    const { container } = render(<EmptyState title="No items" />);
    const icon = container.querySelector('[data-testid="mock-icon"]');
    expect(icon).not.toBeInTheDocument();
  });

  it('should not render description when not provided', () => {
    render(<EmptyState title="Empty state" />);
    const paragraphs = screen.queryAllByRole('paragraph');
    expect(paragraphs.length).toBe(0);
  });

  it('should apply correct className to icon', () => {
    render(<EmptyState title="No data" icon={MockIcon} />);
    const icon = screen.getByTestId('mock-icon');
    expect(icon).toHaveClass('size-16');
    expect(icon).toHaveClass('text-muted-foreground/50');
  });
});
