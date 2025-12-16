/**
 * Unit tests for SimpleConversionSummaryCard component
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SimpleConversionSummaryCard } from '../SimpleConversionSummaryCard';

describe('SimpleConversionSummaryCard', () => {
  const defaultProps = {
    title: 'Test Document',
    author: 'John Doe',
    classification: 'small' as const,
    mode: 'automatic' as const,
    status: 'success' as const,
    token_count: 5000,
    chunk_count: 25,
    heading_chunk_count: 10,
    content_chunk_count: 15,
  };

  it('renders summary card with all required fields', () => {
    render(<SimpleConversionSummaryCard {...defaultProps} />);

    expect(screen.getByTestId('summary-card')).toBeInTheDocument();
    expect(screen.getByTestId('title')).toHaveTextContent('Test Document');
    expect(screen.getByTestId('author')).toHaveTextContent('John Doe');
    expect(screen.getByTestId('token-count')).toHaveTextContent('5,000');
    expect(screen.getByTestId('chunk-count')).toHaveTextContent('25');
    expect(screen.getByTestId('heading-chunk-count')).toHaveTextContent('10');
    expect(screen.getByTestId('content-chunk-count')).toHaveTextContent('15');
  });

  it('displays classification badge with correct text for small classification', () => {
    render(<SimpleConversionSummaryCard {...defaultProps} classification="small" />);

    const badge = screen.getByTestId('classification-badge');
    expect(badge).toHaveTextContent('Small');
    expect(badge).toHaveClass('bg-blue-600');
  });

  it('displays classification badge with correct text for large classification', () => {
    render(<SimpleConversionSummaryCard {...defaultProps} classification="large" />);

    const badge = screen.getByTestId('classification-badge');
    expect(badge).toHaveTextContent('Large');
    expect(badge).toHaveClass('bg-purple-600');
  });

  it('displays mode badge with correct text for automatic mode', () => {
    render(<SimpleConversionSummaryCard {...defaultProps} mode="automatic" />);

    const badge = screen.getByTestId('mode-badge');
    expect(badge).toHaveTextContent('Automatic');
  });

  it('displays mode badge with correct text for manual mode', () => {
    render(<SimpleConversionSummaryCard {...defaultProps} mode="manual" />);

    const badge = screen.getByTestId('mode-badge');
    expect(badge).toHaveTextContent('Manual');
  });

  it('displays success status indicator', () => {
    render(<SimpleConversionSummaryCard {...defaultProps} status="success" />);

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveTextContent('Success');
    expect(indicator).toHaveClass('text-green-600');
  });

  it('displays failed status indicator', () => {
    render(<SimpleConversionSummaryCard {...defaultProps} status="failed" />);

    const indicator = screen.getByTestId('status-indicator');
    expect(indicator).toHaveTextContent('Failed');
    expect(indicator).toHaveClass('text-red-600');
  });

  it('shows error banner when status is failed and error_message is provided', () => {
    render(
      <SimpleConversionSummaryCard
        {...defaultProps}
        status="failed"
        error_message="Processing failed due to invalid input"
      />
    );

    const errorBanner = screen.getByTestId('error-banner');
    expect(errorBanner).toBeInTheDocument();
    expect(errorBanner).toHaveTextContent('Conversion Failed');
    expect(errorBanner).toHaveTextContent('Processing failed due to invalid input');
  });

  it('does not show error banner when status is success', () => {
    render(
      <SimpleConversionSummaryCard
        {...defaultProps}
        status="success"
        error_message={null}
      />
    );

    expect(screen.queryByTestId('error-banner')).not.toBeInTheDocument();
  });

  it('does not show error banner when status is failed but no error_message', () => {
    render(
      <SimpleConversionSummaryCard
        {...defaultProps}
        status="failed"
        error_message={null}
      />
    );

    expect(screen.queryByTestId('error-banner')).not.toBeInTheDocument();
  });

  it('formats token count with locale formatting', () => {
    render(<SimpleConversionSummaryCard {...defaultProps} token_count={123456} />);

    expect(screen.getByTestId('token-count')).toHaveTextContent('123,456');
  });

  it('displays chunk counts separately', () => {
    render(
      <SimpleConversionSummaryCard
        {...defaultProps}
        chunk_count={30}
        heading_chunk_count={12}
        content_chunk_count={18}
      />
    );

    expect(screen.getByTestId('chunk-count')).toHaveTextContent('30');
    expect(screen.getByTestId('heading-chunk-count')).toHaveTextContent('12');
    expect(screen.getByTestId('content-chunk-count')).toHaveTextContent('18');
  });

  it('handles zero chunk counts', () => {
    render(
      <SimpleConversionSummaryCard
        {...defaultProps}
        chunk_count={0}
        heading_chunk_count={0}
        content_chunk_count={0}
      />
    );

    expect(screen.getByTestId('chunk-count')).toHaveTextContent('0');
    expect(screen.getByTestId('heading-chunk-count')).toHaveTextContent('0');
    expect(screen.getByTestId('content-chunk-count')).toHaveTextContent('0');
  });
});
