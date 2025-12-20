import { render, screen } from '@testing-library/react';
import { FormField } from './form-field';

describe('FormField', () => {
  it('should render label', () => {
    render(
      <FormField label="Email">
        <input type="email" />
      </FormField>
    );
    expect(screen.getByText('Email')).toBeInTheDocument();
  });

  it('should show required asterisk when required is true', () => {
    render(
      <FormField label="Username" required>
        <input type="text" />
      </FormField>
    );
    const asterisk = screen.getByText('*');
    expect(asterisk).toBeInTheDocument();
    expect(asterisk).toHaveClass('text-destructive');
  });

  it('should not show required asterisk when required is false', () => {
    render(
      <FormField label="Username" required={false}>
        <input type="text" />
      </FormField>
    );
    expect(screen.queryByText('*')).not.toBeInTheDocument();
  });

  it('should not show required asterisk by default', () => {
    render(
      <FormField label="Username">
        <input type="text" />
      </FormField>
    );
    expect(screen.queryByText('*')).not.toBeInTheDocument();
  });

  it('should render children input element', () => {
    render(
      <FormField label="Name">
        <input type="text" data-testid="test-input" />
      </FormField>
    );
    expect(screen.getByTestId('test-input')).toBeInTheDocument();
  });

  it('should display error message in red when error provided', () => {
    render(
      <FormField label="Email" error="Email is required">
        <input type="email" />
      </FormField>
    );
    const error = screen.getByText('Email is required');
    expect(error).toBeInTheDocument();
    expect(error).toHaveClass('text-destructive');
  });

  it('should not display error when error is undefined', () => {
    const { container } = render(
      <FormField label="Email">
        <input type="email" />
      </FormField>
    );
    const errorElements = container.querySelectorAll('.text-destructive');
    // Should only have the asterisk if required, no error message
    expect(errorElements.length).toBe(0);
  });

  it('should display description when provided', () => {
    render(
      <FormField
        label="Password"
        description="Must be at least 8 characters"
      >
        <input type="password" />
      </FormField>
    );
    expect(screen.getByText('Must be at least 8 characters')).toBeInTheDocument();
  });

  it('should not display description when not provided', () => {
    const { container } = render(
      <FormField label="Email">
        <input type="email" />
      </FormField>
    );
    const description = container.querySelector('.text-muted-foreground');
    expect(description).not.toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <FormField label="Email" className="custom-form-field">
        <input type="email" />
      </FormField>
    );
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('custom-form-field');
  });

  it('should render all elements together', () => {
    render(
      <FormField
        label="Email"
        required
        description="Enter your email address"
        error="Invalid email format"
      >
        <input type="email" data-testid="email-input" />
      </FormField>
    );
    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('*')).toBeInTheDocument();
    expect(screen.getByText('Enter your email address')).toBeInTheDocument();
    expect(screen.getByText('Invalid email format')).toBeInTheDocument();
    expect(screen.getByTestId('email-input')).toBeInTheDocument();
  });

  it('should render with any child component', () => {
    render(
      <FormField label="Custom">
        <select data-testid="select-input">
          <option>Option 1</option>
        </select>
      </FormField>
    );
    expect(screen.getByTestId('select-input')).toBeInTheDocument();
  });
});
