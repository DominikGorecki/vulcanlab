import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter, useSearchParams } from 'next/navigation';
import NewQueryPage from '../page';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

// Mock usePageData
jest.mock('@/hooks/use-page-data', () => ({
  usePageData: jest.fn(),
}));

// Mock components
jest.mock('@/components', () => ({
  PageLoadingState: () => <div data-testid="loading-state">Loading...</div>,
  PageErrorState: ({ error }: any) => <div data-testid="error-state">{error.message}</div>,
  StickyDetailHeader: ({ title, subtitle }: any) => (
    <div data-testid="sticky-header">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
  ),
}));

describe('NewQueryPage', () => {
  const mockPush = jest.fn();
  const mockGet = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
    (useSearchParams as jest.Mock).mockReturnValue({ get: mockGet });
  });

  it('should show error if no query provided', () => {
    mockGet.mockReturnValue(null);
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: null,
      loading: false,
      error: new Error("No query provided"),
      refetch: jest.fn(),
    });

    render(<NewQueryPage />);
    expect(screen.getByTestId('error-state')).toBeInTheDocument();
    expect(screen.getByText('No query provided')).toBeInTheDocument();
  });

  it('should load and display prompt', async () => {
    mockGet.mockReturnValue('test query');
    const { usePageData } = require('@/hooks/use-page-data');
    usePageData.mockReturnValue({
      data: 'Expanded prompt text',
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(<NewQueryPage />);
    
    expect(screen.getByTestId('sticky-header')).toBeInTheDocument();
    expect(screen.getByText('test query')).toBeInTheDocument();
    expect(screen.getByText('Expanded prompt text')).toBeInTheDocument();
  });
});
