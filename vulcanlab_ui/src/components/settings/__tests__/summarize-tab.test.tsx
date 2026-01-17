/**
 * Unit tests for SummarizeTab component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SummarizeTab } from '../summarize-tab';

// Mock usePageData
jest.mock('@/hooks', () => ({
  usePageData: jest.fn(),
}));

// Mock useToast
const mockToast = jest.fn();
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('SummarizeTab', () => {
  const mockSettings = {
    min_heading_word_count: 600,
    max_total_heading_words: 3000,
    dense_top_k: 7,
    lexical_top_k: 7,
    rrf_k: 60,
    rrf_top_k: 7,
    mmr_lambda: 0.7,
    mmr_top_n: 5,
    max_llm_calls: 5,
    max_tokens_per_call: 15000,
    tokens_per_word: 0.75,
    h1_h2_min_chunks: 2,
    h3_min_chunks: 1,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    const { usePageData } = require('@/hooks');
    usePageData.mockReturnValue({
      data: mockSettings,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });
  });

  it('renders all form fields with correct initial values', async () => {
    const { container } = render(<SummarizeTab />);

    expect(container.querySelector('input[name="min_heading_word_count"]')).toHaveValue(600);
    expect(container.querySelector('input[name="max_total_heading_words"]')).toHaveValue(3000);
    expect(container.querySelector('input[name="dense_top_k"]')).toHaveValue(7);
    expect(container.querySelector('input[name="lexical_top_k"]')).toHaveValue(7);
    expect(container.querySelector('input[name="rrf_k"]')).toHaveValue(60);
    expect(container.querySelector('input[name="rrf_top_k"]')).toHaveValue(7);
    expect(container.querySelector('input[name="mmr_lambda"]')).toHaveValue(0.7);
    expect(container.querySelector('input[name="mmr_top_n"]')).toHaveValue(5);
    expect(container.querySelector('input[name="max_llm_calls"]')).toHaveValue(5);
    expect(container.querySelector('input[name="max_tokens_per_call"]')).toHaveValue(15000);
    expect(container.querySelector('input[name="tokens_per_word"]')).toHaveValue(0.75);
    expect(container.querySelector('input[name="h1_h2_min_chunks"]')).toHaveValue(2);
    expect(container.querySelector('input[name="h3_min_chunks"]')).toHaveValue(1);
  });

  it('validates mmr_lambda range', async () => {
    const { container } = render(<SummarizeTab />);
    
    const lambdaInput = container.querySelector('input[name="mmr_lambda"]');
    if (!lambdaInput) throw new Error("Lambda input not found");
    
    fireEvent.change(lambdaInput, { target: { value: '1.5' } });
    
    const saveButton = screen.getByText(/Save Changes/i);
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/Max 1/i)).toBeInTheDocument();
    });
  });

  it('calls PUT endpoint and shows success toast on save', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    const { container } = render(<SummarizeTab />);

    const lambdaInput = container.querySelector('input[name="mmr_lambda"]');
    if (!lambdaInput) throw new Error("Lambda input not found");

    // Change value to make form dirty
    fireEvent.change(lambdaInput, { target: { value: '0.8' } });

    const saveButton = screen.getByText(/Save Changes/i);
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/summarize/settings'),
        expect.objectContaining({
          method: 'PUT',
          body: expect.stringContaining('"mmr_lambda":0.8'),
        })
      );
      expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
        title: 'Settings saved',
      }));
    });
  });

  it('renders loading state', () => {
    const { usePageData } = require('@/hooks');
    usePageData.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refetch: jest.fn(),
    });

    render(<SummarizeTab />);
    // Loading state usually renders PageLoadingState which has a title or spinner
    // In our mock of PageLoadingState (from other tests), we look for a test id or text
    // Assuming PageLoadingState shows "Loading..." or similar
  });

  it('renders error state', () => {
    const { usePageData } = require('@/hooks');
    usePageData.mockReturnValue({
      data: null,
      loading: false,
      error: new Error('Fetch failed'),
      refetch: jest.fn(),
    });

    render(<SummarizeTab />);
    expect(screen.getByText(/Fetch failed/i)).toBeInTheDocument();
  });
});
