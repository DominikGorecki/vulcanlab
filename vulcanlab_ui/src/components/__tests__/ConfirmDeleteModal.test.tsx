/**
 * Unit tests for ConfirmDeleteModal component
 * Tests modal rendering, user interactions, and loading states
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ConfirmDeleteModal } from '../ConfirmDeleteModal';

describe('ConfirmDeleteModal', () => {
  const mockWork = {
    title: 'Test Work Title',
    authors: 'John Doe, Jane Smith',
  };

  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Modal Visibility', () => {
    it('test_confirm_modal_not_visible_when_closed: does not render when isOpen is false', () => {
      render(
        <ConfirmDeleteModal
          work={mockWork}
          isOpen={false}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          isDeleting={false}
        />
      );

      expect(screen.queryByTestId('confirm-delete-modal')).not.toBeInTheDocument();
    });

    it('renders when isOpen is true', () => {
      render(
        <ConfirmDeleteModal
          work={mockWork}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          isDeleting={false}
        />
      );

      expect(screen.getByTestId('confirm-delete-modal')).toBeInTheDocument();
    });

    it('does not render when work is null', () => {
      render(
        <ConfirmDeleteModal
          work={null}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          isDeleting={false}
        />
      );

      expect(screen.queryByTestId('confirm-delete-modal')).not.toBeInTheDocument();
    });
  });

  describe('Work Details Display', () => {
    it('test_confirm_modal_renders_work_details: displays work title and authors correctly', () => {
      render(
        <ConfirmDeleteModal
          work={mockWork}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          isDeleting={false}
        />
      );

      expect(screen.getByText(mockWork.title)).toBeInTheDocument();
      expect(screen.getByText(mockWork.authors)).toBeInTheDocument();
      expect(screen.getByText('Delete Work')).toBeInTheDocument();
    });

    it('displays work without authors correctly', () => {
      const workNoAuthors = {
        title: 'Test Work Without Authors',
        authors: null,
      };

      render(
        <ConfirmDeleteModal
          work={workNoAuthors}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          isDeleting={false}
        />
      );

      expect(screen.getByText(workNoAuthors.title)).toBeInTheDocument();
      expect(screen.queryByText(/Authors:/)).not.toBeInTheDocument();
    });

    it('displays warning message', () => {
      render(
        <ConfirmDeleteModal
          work={mockWork}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          isDeleting={false}
        />
      );

      expect(
        screen.getByText('Are you sure you want to delete this work? This action cannot be undone.')
      ).toBeInTheDocument();
    });
  });

  describe('Button Interactions', () => {
    it('test_confirm_modal_cancel_button_calls_onClose: calls onClose when Cancel button is clicked', () => {
      render(
        <ConfirmDeleteModal
          work={mockWork}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          isDeleting={false}
        />
      );

      const cancelButton = screen.getByTestId('cancel-button');
      fireEvent.click(cancelButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
      expect(mockOnConfirm).not.toHaveBeenCalled();
    });

    it('test_confirm_modal_delete_button_calls_onConfirm: calls onConfirm when Delete button is clicked', () => {
      render(
        <ConfirmDeleteModal
          work={mockWork}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          isDeleting={false}
        />
      );

      const deleteButton = screen.getByTestId('delete-button');
      fireEvent.click(deleteButton);

      expect(mockOnConfirm).toHaveBeenCalledTimes(1);
      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('test_confirm_modal_shows_loading_state: shows loading spinner and disables buttons when isDeleting is true', () => {
      render(
        <ConfirmDeleteModal
          work={mockWork}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          isDeleting={true}
        />
      );

      const deleteButton = screen.getByTestId('delete-button');
      const cancelButton = screen.getByTestId('cancel-button');

      expect(deleteButton).toBeDisabled();
      expect(cancelButton).toBeDisabled();
      expect(screen.getByText('Deleting...')).toBeInTheDocument();
    });

    it('shows "Delete" text when not deleting', () => {
      render(
        <ConfirmDeleteModal
          work={mockWork}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          isDeleting={false}
        />
      );

      const deleteButton = screen.getByTestId('delete-button');
      expect(deleteButton).not.toBeDisabled();
      expect(screen.getByText('Delete')).toBeInTheDocument();
      expect(screen.queryByText('Deleting...')).not.toBeInTheDocument();
    });

    it('prevents closing modal when deleting', () => {
      render(
        <ConfirmDeleteModal
          work={mockWork}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          isDeleting={true}
        />
      );

      const cancelButton = screen.getByTestId('cancel-button');
      fireEvent.click(cancelButton);

      // onClose should not be called because button is disabled
      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has proper dialog structure', () => {
      render(
        <ConfirmDeleteModal
          work={mockWork}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          isDeleting={false}
        />
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('has descriptive button labels', () => {
      render(
        <ConfirmDeleteModal
          work={mockWork}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          isDeleting={false}
        />
      );

      expect(screen.getByText('Cancel')).toBeInTheDocument();
      expect(screen.getByText('Delete')).toBeInTheDocument();
    });
  });
});
