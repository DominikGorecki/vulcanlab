import { render, screen, fireEvent } from '@testing-library/react';
import { PageErrorState } from './page-error-state';

describe('PageErrorState', () => {
  it('should render error message from string', () => {
    render(<PageErrorState error="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('should render error message from Error object', () => {
    const error = new Error('Network error');
    render(<PageErrorState error={error} />);
    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('should render with title', () => {
    render(
      <PageErrorState
        error="Failed to load"
        title="Error occurred"
      />
    );
    expect(screen.getByText('Error occurred')).toBeInTheDocument();
    expect(screen.getByText('Failed to load')).toBeInTheDocument();
  });

  it('should render with description', () => {
    render(
      <PageErrorState
        error="Failed to load"
        description="Please try again later"
      />
    );
    expect(screen.getByText('Please try again later')).toBeInTheDocument();
  });

  it('should render with title and description', () => {
    render(
      <PageErrorState
        error="API Error"
        title="Failed to fetch data"
        description="The server is not responding"
      />
    );
    expect(screen.getByText('Failed to fetch data')).toBeInTheDocument();
    expect(screen.getByText('API Error')).toBeInTheDocument();
    expect(screen.getByText('The server is not responding')).toBeInTheDocument();
  });

  it('should show retry button when onRetry is provided', () => {
    const handleRetry = jest.fn();
    render(
      <PageErrorState
        error="Failed to load"
        onRetry={handleRetry}
      />
    );
    const retryButton = screen.getByRole('button', { name: /try again/i });
    expect(retryButton).toBeInTheDocument();
  });

  it('should not show retry button when onRetry is undefined', () => {
    render(<PageErrorState error="Failed to load" />);
    const retryButton = screen.queryByRole('button', { name: /try again/i });
    expect(retryButton).not.toBeInTheDocument();
  });

  it('should call onRetry when retry button is clicked', () => {
    const handleRetry = jest.fn();
    render(
      <PageErrorState
        error="Failed to load"
        onRetry={handleRetry}
      />
    );
    const retryButton = screen.getByRole('button', { name: /try again/i });
    fireEvent.click(retryButton);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it('should apply custom className', () => {
    const { container } = render(
      <PageErrorState
        error="Error"
        className="custom-error-class"
      />
    );
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('custom-error-class');
  });

  it('should render error icon', () => {
    const { container } = render(<PageErrorState error="Error" />);
    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('should not render title when not provided', () => {
    render(<PageErrorState error="Error message" />);
    const title = screen.queryByRole('heading');
    expect(title).not.toBeInTheDocument();
  });

  it('should not render description when not provided', () => {
    const { container } = render(<PageErrorState error="Error message" />);
    const paragraphs = container.querySelectorAll('p');
    // Should only have one <p> for the error message, not the description
    expect(paragraphs.length).toBe(1);
    expect(paragraphs[0]).toHaveTextContent('Error message');
  });
});
