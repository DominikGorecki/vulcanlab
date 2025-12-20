import { render, screen } from '@testing-library/react';
import { PageLoadingState } from './page-loading-state';

describe('PageLoadingState', () => {
  it('should render with default spinner', () => {
    const { container } = render(<PageLoadingState />);
    const spinner = container.querySelector('svg');
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('animate-spin');
  });

  it('should render with title', () => {
    render(<PageLoadingState title="Loading data" />);
    expect(screen.getByText('Loading data')).toBeInTheDocument();
  });

  it('should render with description', () => {
    render(<PageLoadingState description="Please wait..." />);
    expect(screen.getByText('Please wait...')).toBeInTheDocument();
  });

  it('should render with both title and description', () => {
    render(
      <PageLoadingState
        title="Loading"
        description="Fetching your data"
      />
    );
    expect(screen.getByText('Loading')).toBeInTheDocument();
    expect(screen.getByText('Fetching your data')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <PageLoadingState className="custom-class" />
    );
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('custom-class');
  });

  it('should not render title when not provided', () => {
    const { container } = render(<PageLoadingState />);
    const title = container.querySelector('h3');
    expect(title).not.toBeInTheDocument();
  });

  it('should not render description when not provided', () => {
    const { container } = render(<PageLoadingState />);
    const description = container.querySelector('p');
    expect(description).not.toBeInTheDocument();
  });
});
