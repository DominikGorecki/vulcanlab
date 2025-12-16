/**
 * Unit tests for History Error Boundary
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { HistoryErrorBoundary } from '../HistoryErrorBoundary';

// Component that throws an error
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div data-testid="child-component">Child content</div>;
};

describe('HistoryErrorBoundary', () => {
  // Suppress console.error for these tests since we're intentionally throwing errors
  const originalError = console.error;
  beforeAll(() => {
    console.error = jest.fn();
  });

  afterAll(() => {
    console.error = originalError;
  });

  it('renders children when there is no error', () => {
    render(
      <HistoryErrorBoundary>
        <ThrowError shouldThrow={false} />
      </HistoryErrorBoundary>
    );

    expect(screen.getByTestId('child-component')).toBeInTheDocument();
    expect(screen.getByText('Child content')).toBeInTheDocument();
  });

  it('renders error fallback UI when child component throws', () => {
    render(
      <HistoryErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HistoryErrorBoundary>
    );

    expect(screen.getByTestId('history-error-boundary')).toBeInTheDocument();
    expect(screen.getByText(/Unable to load conversion history/i)).toBeInTheDocument();
    expect(screen.getByText(/An error occurred while displaying the conversion history/i)).toBeInTheDocument();
  });

  it('displays error message in fallback UI', () => {
    render(
      <HistoryErrorBoundary>
        <ThrowError shouldThrow={true} />
      </HistoryErrorBoundary>
    );

    expect(screen.getByText(/Test error/i)).toBeInTheDocument();
  });

  it('prevents error from bubbling up and crashing parent', () => {
    // This test verifies the error boundary catches the error
    expect(() => {
      render(
        <HistoryErrorBoundary>
          <ThrowError shouldThrow={true} />
        </HistoryErrorBoundary>
      );
    }).not.toThrow();
  });
});
