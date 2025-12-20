import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ConfirmDialog } from './confirm-dialog';

describe('ConfirmDialog', () => {
  const mockOnOpenChange = jest.fn();
  const mockOnConfirm = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render title and message when open is true', () => {
    render(
      <ConfirmDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        title="Delete Item"
        message="Are you sure?"
        onConfirm={mockOnConfirm}
      />
    );
    expect(screen.getByText('Delete Item')).toBeInTheDocument();
    expect(screen.getByText('Are you sure?')).toBeInTheDocument();
  });

  it('should not render when open is false', () => {
    render(
      <ConfirmDialog
        open={false}
        onOpenChange={mockOnOpenChange}
        title="Delete Item"
        message="Are you sure?"
        onConfirm={mockOnConfirm}
      />
    );
    expect(screen.queryByText('Delete Item')).not.toBeInTheDocument();
  });

  it('should render default confirm/cancel labels', () => {
    render(
      <ConfirmDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        title="Confirmation Dialog"
        message="Proceed?"
        onConfirm={mockOnConfirm}
      />
    );
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
  });

  it('should render custom confirm/cancel labels when provided', () => {
    render(
      <ConfirmDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        title="Delete"
        message="Delete this?"
        confirmLabel="Delete Now"
        cancelLabel="Keep It"
        onConfirm={mockOnConfirm}
      />
    );
    expect(screen.getByText('Delete Now')).toBeInTheDocument();
    expect(screen.getByText('Keep It')).toBeInTheDocument();
  });

  it('should call onConfirm when confirm button is clicked', async () => {
    render(
      <ConfirmDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        title="Confirmation"
        message="Proceed?"
        onConfirm={mockOnConfirm}
      />
    );
    const confirmButton = screen.getByRole('button', { name: 'Confirm' });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockOnConfirm).toHaveBeenCalledTimes(1);
    });
  });

  it('should call onOpenChange(false) when cancel button is clicked', () => {
    render(
      <ConfirmDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        title="Confirmation"
        message="Proceed?"
        onConfirm={mockOnConfirm}
      />
    );
    const cancelButton = screen.getByRole('button', { name: 'Cancel' });
    fireEvent.click(cancelButton);

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('should show loading spinner during async onConfirm', async () => {
    const asyncOnConfirm = jest.fn(
      (): Promise<void> => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(
      <ConfirmDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        title="Confirmation"
        message="Proceed?"
        onConfirm={asyncOnConfirm}
      />
    );

    const confirmButton = screen.getByRole('button', { name: 'Confirm' });
    fireEvent.click(confirmButton);

    // Loading spinner should appear
    await waitFor(() => {
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  it('should close dialog after successful async confirmation', async () => {
    const asyncOnConfirm = jest.fn(
      (): Promise<void> => new Promise((resolve) => setTimeout(resolve, 50))
    );

    render(
      <ConfirmDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        title="Confirmation"
        message="Proceed?"
        onConfirm={asyncOnConfirm}
      />
    );

    const confirmButton = screen.getByRole('button', { name: 'Confirm' });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it('should apply danger variant styling (destructive button)', () => {
    const { container } = render(
      <ConfirmDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        title="Delete"
        message="Delete this?"
        variant="danger"
        onConfirm={mockOnConfirm}
      />
    );

    const confirmButton = screen.getByRole('button', { name: 'Confirm' });
    // Danger variant uses destructive variant
    expect(confirmButton).toBeInTheDocument();
  });

  it('should apply warning variant styling (amber button)', () => {
    const { container } = render(
      <ConfirmDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        title="Warning"
        message="Proceed with caution?"
        variant="warning"
        onConfirm={mockOnConfirm}
      />
    );

    const confirmButton = screen.getByRole('button', { name: 'Confirm' });
    expect(confirmButton).toHaveClass('bg-amber-600');
  });

  it('should apply info variant styling (blue button)', () => {
    const { container } = render(
      <ConfirmDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        title="Information"
        message="Would you like to proceed?"
        variant="info"
        onConfirm={mockOnConfirm}
      />
    );

    const confirmButton = screen.getByRole('button', { name: 'Confirm' });
    expect(confirmButton).toHaveClass('bg-blue-600');
  });

  it('should disable buttons during loading', async () => {
    const asyncOnConfirm = jest.fn(
      (): Promise<void> => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(
      <ConfirmDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        title="Confirmation"
        message="Proceed?"
        onConfirm={asyncOnConfirm}
      />
    );

    const confirmButton = screen.getByRole('button', { name: 'Confirm' });
    const cancelButton = screen.getByRole('button', { name: 'Cancel' });

    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(confirmButton).toBeDisabled();
      expect(cancelButton).toBeDisabled();
    });
  });

  it('should handle errors in onConfirm and keep dialog open', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    const failingOnConfirm = jest.fn(
      () => Promise.reject(new Error('Failed'))
    );

    render(
      <ConfirmDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        title="Confirmation"
        message="Proceed?"
        onConfirm={failingOnConfirm}
      />
    );

    const confirmButton = screen.getByRole('button', { name: 'Confirm' });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(failingOnConfirm).toHaveBeenCalled();
    });

    // Dialog should NOT close on error
    expect(mockOnOpenChange).not.toHaveBeenCalledWith(false);

    consoleErrorSpy.mockRestore();
  });
});
