import { render, screen } from '@testing-library/react';
import { PageHeader } from './page-header';

describe('PageHeader', () => {
  it('should render title', () => {
    render(<PageHeader title="Test Page" />);
    expect(screen.getByText('Test Page')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Test Page');
  });

  it('should render description when provided', () => {
    render(
      <PageHeader
        title="My Page"
        description="This is a test description"
      />
    );
    expect(screen.getByText('This is a test description')).toBeInTheDocument();
  });

  it('should not render description when undefined', () => {
    const { container } = render(<PageHeader title="Test" />);
    const description = container.querySelector('p');
    expect(description).not.toBeInTheDocument();
  });

  it('should render actions ReactNode when provided', () => {
    render(
      <PageHeader
        title="Test"
        actions={
          <button data-testid="action-button">Action</button>
        }
      />
    );
    expect(screen.getByTestId('action-button')).toBeInTheDocument();
    expect(screen.getByText('Action')).toBeInTheDocument();
  });

  it('should render multiple actions', () => {
    render(
      <PageHeader
        title="Test"
        actions={
          <>
            <button data-testid="action-1">Action 1</button>
            <button data-testid="action-2">Action 2</button>
          </>
        }
      />
    );
    expect(screen.getByTestId('action-1')).toBeInTheDocument();
    expect(screen.getByTestId('action-2')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <PageHeader title="Test" className="custom-header-class" />
    );
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('custom-header-class');
  });

  it('should have responsive layout classes', () => {
    const { container } = render(<PageHeader title="Test" />);
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('flex');
    expect(wrapper).toHaveClass('flex-col');
    expect(wrapper).toHaveClass('sm:flex-row');
  });

  it('should render title, description, and actions together', () => {
    render(
      <PageHeader
        title="Complete Header"
        description="With all props"
        actions={<button>Click Me</button>}
      />
    );
    expect(screen.getByText('Complete Header')).toBeInTheDocument();
    expect(screen.getByText('With all props')).toBeInTheDocument();
    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  it('should not render actions container when actions is undefined', () => {
    const { container } = render(<PageHeader title="Test" />);
    const actionsContainer = container.querySelector('[class*="items-center"]');
    // The main container has items-start, so we check if there's no second flex container
    const flexContainers = container.querySelectorAll('[class*="flex"]');
    // Should only have the main container and the space-y div, not an actions container
    expect(flexContainers.length).toBeLessThanOrEqual(2);
  });
});
