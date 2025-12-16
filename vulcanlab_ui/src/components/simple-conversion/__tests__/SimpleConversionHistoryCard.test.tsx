/**
 * Unit tests for SimpleConversionHistoryCard component
 * Tests rendering of history card with various states and navigation behavior
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { SimpleConversionHistoryCard, SimpleConversionHistoryCardProps } from '../SimpleConversionHistoryCard';

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

describe('SimpleConversionHistoryCard', () => {
  const baseProps: SimpleConversionHistoryCardProps = {
    work_id: 123,
    title: 'Test Document',
    author: 'Test Author',
    classification: 'small',
    mode: 'automatic',
    status: 'success',
    created_at: '2025-01-15T10:30:00Z',
  };

  beforeEach(() => {
    mockPush.mockClear();
  });

  describe('Basic Rendering', () => {
    it('renders card with title and author', () => {
      render(<SimpleConversionHistoryCard {...baseProps} />);

      expect(screen.getByText('Test Document')).toBeInTheDocument();
      expect(screen.getByText('Test Author')).toBeInTheDocument();
    });

    it('renders with correct work_id in test id', () => {
      render(<SimpleConversionHistoryCard {...baseProps} />);

      expect(screen.getByTestId('history-card-123')).toBeInTheDocument();
    });
  });

  describe('Classification Badge', () => {
    it('displays "Small" badge for small classification', () => {
      render(<SimpleConversionHistoryCard {...baseProps} classification="small" />);

      const badge = screen.getByTestId('classification-badge');
      expect(badge).toHaveTextContent('Small');
    });

    it('displays "Large" badge for large classification', () => {
      render(<SimpleConversionHistoryCard {...baseProps} classification="large" />);

      const badge = screen.getByTestId('classification-badge');
      expect(badge).toHaveTextContent('Large');
    });

    it('applies blue styling for small classification', () => {
      render(<SimpleConversionHistoryCard {...baseProps} classification="small" />);

      const badge = screen.getByTestId('classification-badge');
      expect(badge).toHaveClass('bg-blue-600');
    });

    it('applies purple styling for large classification', () => {
      render(<SimpleConversionHistoryCard {...baseProps} classification="large" />);

      const badge = screen.getByTestId('classification-badge');
      expect(badge).toHaveClass('bg-purple-600');
    });
  });

  describe('Mode Badge', () => {
    it('displays "Automatic" badge for automatic mode', () => {
      render(<SimpleConversionHistoryCard {...baseProps} mode="automatic" />);

      const badge = screen.getByTestId('mode-badge');
      expect(badge).toHaveTextContent('Automatic');
    });

    it('displays "Manual" badge for manual mode', () => {
      render(<SimpleConversionHistoryCard {...baseProps} mode="manual" />);

      const badge = screen.getByTestId('mode-badge');
      expect(badge).toHaveTextContent('Manual');
    });

    it('shows play icon for automatic mode', () => {
      const { container } = render(<SimpleConversionHistoryCard {...baseProps} mode="automatic" />);

      const badge = screen.getByTestId('mode-badge');
      expect(badge.querySelector('svg')).toBeInTheDocument();
    });

    it('shows hand icon for manual mode', () => {
      const { container } = render(<SimpleConversionHistoryCard {...baseProps} mode="manual" />);

      const badge = screen.getByTestId('mode-badge');
      expect(badge.querySelector('svg')).toBeInTheDocument();
    });
  });

  describe('Status Indicator', () => {
    it('shows success icon for success status', () => {
      render(<SimpleConversionHistoryCard {...baseProps} status="success" />);

      const successIcon = screen.getByTestId('status-success');
      expect(successIcon).toBeInTheDocument();
      expect(successIcon).toHaveClass('text-green-600');
    });

    it('shows error icon for error status', () => {
      render(<SimpleConversionHistoryCard {...baseProps} status="error" />);

      const errorIcon = screen.getByTestId('status-error');
      expect(errorIcon).toBeInTheDocument();
      expect(errorIcon).toHaveClass('text-red-600');
    });

    it('does not show success icon when status is error', () => {
      render(<SimpleConversionHistoryCard {...baseProps} status="error" />);

      expect(screen.queryByTestId('status-success')).not.toBeInTheDocument();
    });

    it('does not show error icon when status is success', () => {
      render(<SimpleConversionHistoryCard {...baseProps} status="success" />);

      expect(screen.queryByTestId('status-error')).not.toBeInTheDocument();
    });
  });

  describe('Date Formatting', () => {
    it('formats date in human-readable format', () => {
      render(<SimpleConversionHistoryCard {...baseProps} created_at="2025-01-15T10:30:00Z" />);

      const dateElement = screen.getByTestId('created-date');
      expect(dateElement).toHaveTextContent('Jan 15, 2025');
    });

    it('formats different date correctly', () => {
      render(<SimpleConversionHistoryCard {...baseProps} created_at="2024-12-25T00:00:00Z" />);

      const dateElement = screen.getByTestId('created-date');
      expect(dateElement).toHaveTextContent('Dec 25, 2024');
    });
  });

  describe('Navigation', () => {
    it('navigates to detail page when card is clicked', () => {
      render(<SimpleConversionHistoryCard {...baseProps} work_id={456} />);

      const card = screen.getByTestId('history-card-456');
      fireEvent.click(card);

      expect(mockPush).toHaveBeenCalledWith('/simple-conversion/history/456');
    });

    it('navigates with correct work_id for different cards', () => {
      render(<SimpleConversionHistoryCard {...baseProps} work_id={789} />);

      const card = screen.getByTestId('history-card-789');
      fireEvent.click(card);

      expect(mockPush).toHaveBeenCalledWith('/simple-conversion/history/789');
    });

    it('has cursor-pointer class for clickable affordance', () => {
      render(<SimpleConversionHistoryCard {...baseProps} />);

      const card = screen.getByTestId('history-card-123');
      expect(card).toHaveClass('cursor-pointer');
    });

    it('has hover effect classes', () => {
      render(<SimpleConversionHistoryCard {...baseProps} />);

      const card = screen.getByTestId('history-card-123');
      expect(card).toHaveClass('hover:shadow-md');
      expect(card).toHaveClass('hover:border-primary/50');
    });
  });

  describe('Combined States', () => {
    it('renders correctly with large classification, manual mode, and error status', () => {
      render(
        <SimpleConversionHistoryCard
          {...baseProps}
          classification="large"
          mode="manual"
          status="error"
        />
      );

      expect(screen.getByTestId('classification-badge')).toHaveTextContent('Large');
      expect(screen.getByTestId('mode-badge')).toHaveTextContent('Manual');
      expect(screen.getByTestId('status-error')).toBeInTheDocument();
    });

    it('renders correctly with small classification, automatic mode, and success status', () => {
      render(
        <SimpleConversionHistoryCard
          {...baseProps}
          classification="small"
          mode="automatic"
          status="success"
        />
      );

      expect(screen.getByTestId('classification-badge')).toHaveTextContent('Small');
      expect(screen.getByTestId('mode-badge')).toHaveTextContent('Automatic');
      expect(screen.getByTestId('status-success')).toBeInTheDocument();
    });
  });

  describe('Error Message Prop', () => {
    it('accepts error_message prop without breaking', () => {
      render(
        <SimpleConversionHistoryCard
          {...baseProps}
          status="error"
          error_message="Test error message"
        />
      );

      // Error message is passed but not displayed in card (only on detail page)
      expect(screen.queryByText('Test error message')).not.toBeInTheDocument();
    });

    it('accepts null error_message', () => {
      render(
        <SimpleConversionHistoryCard
          {...baseProps}
          error_message={null}
        />
      );

      expect(screen.getByTestId('history-card-123')).toBeInTheDocument();
    });
  });
});
