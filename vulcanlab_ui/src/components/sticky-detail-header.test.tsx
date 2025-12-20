import { render, screen } from '@testing-library/react';
import { StickyDetailHeader } from './sticky-detail-header';

// Mock Next.js Link component
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => {
    return <a href={href}>{children}</a>;
  };
});

describe('StickyDetailHeader', () => {
  it('should render title', () => {
    render(
      <StickyDetailHeader
        title="Test Detail Page"
        backUrl="/test"
      />
    );
    expect(screen.getByText('Test Detail Page')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Test Detail Page');
  });

  it('should render back button with correct href', () => {
    render(
      <StickyDetailHeader
        title="Details"
        backUrl="/items"
      />
    );
    const backLink = screen.getByRole('link');
    expect(backLink).toHaveAttribute('href', '/items');
  });

  it('should render default back label', () => {
    render(
      <StickyDetailHeader
        title="Details"
        backUrl="/test"
      />
    );
    expect(screen.getByText('Back')).toBeInTheDocument();
  });

  it('should render custom backLabel when provided', () => {
    render(
      <StickyDetailHeader
        title="Details"
        backUrl="/test"
        backLabel="Back to List"
      />
    );
    expect(screen.getByText('Back to List')).toBeInTheDocument();
    expect(screen.queryByText('Back')).not.toBeInTheDocument();
  });

  it('should render subtitle when provided', () => {
    render(
      <StickyDetailHeader
        title="User Details"
        backUrl="/users"
        subtitle="user@example.com"
      />
    );
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
  });

  it('should not render subtitle when undefined', () => {
    const { container } = render(
      <StickyDetailHeader
        title="Details"
        backUrl="/test"
      />
    );
    const subtitle = container.querySelector('p');
    expect(subtitle).not.toBeInTheDocument();
  });

  it('should render actions when provided', () => {
    render(
      <StickyDetailHeader
        title="Details"
        backUrl="/test"
        actions={
          <button data-testid="action-button">Save</button>
        }
      />
    );
    expect(screen.getByTestId('action-button')).toBeInTheDocument();
    expect(screen.getByText('Save')).toBeInTheDocument();
  });

  it('should render multiple actions', () => {
    render(
      <StickyDetailHeader
        title="Details"
        backUrl="/test"
        actions={
          <>
            <button data-testid="cancel">Cancel</button>
            <button data-testid="save">Save</button>
          </>
        }
      />
    );
    expect(screen.getByTestId('cancel')).toBeInTheDocument();
    expect(screen.getByTestId('save')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <StickyDetailHeader
        title="Details"
        backUrl="/test"
        className="custom-sticky-class"
      />
    );
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('custom-sticky-class');
  });

  it('should have sticky positioning classes', () => {
    const { container } = render(
      <StickyDetailHeader
        title="Details"
        backUrl="/test"
      />
    );
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('sticky');
    expect(wrapper).toHaveClass('top-0');
  });

  it('should have appropriate z-index', () => {
    const { container } = render(
      <StickyDetailHeader
        title="Details"
        backUrl="/test"
      />
    );
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('z-40');
  });

  it('should have background and border classes', () => {
    const { container } = render(
      <StickyDetailHeader
        title="Details"
        backUrl="/test"
      />
    );
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('border-b');
    expect(wrapper).toHaveClass('bg-background/95');
    expect(wrapper).toHaveClass('backdrop-blur');
  });

  it('should render back icon', () => {
    const { container } = render(
      <StickyDetailHeader
        title="Details"
        backUrl="/test"
      />
    );
    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('should render all elements together', () => {
    render(
      <StickyDetailHeader
        title="Complete Header"
        subtitle="All props included"
        backUrl="/list"
        backLabel="Return to List"
        actions={<button>Action</button>}
      />
    );
    expect(screen.getByText('Complete Header')).toBeInTheDocument();
    expect(screen.getByText('All props included')).toBeInTheDocument();
    expect(screen.getByText('Return to List')).toBeInTheDocument();
    expect(screen.getByText('Action')).toBeInTheDocument();
  });
});
