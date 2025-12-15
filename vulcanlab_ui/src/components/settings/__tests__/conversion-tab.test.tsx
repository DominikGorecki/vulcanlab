/**
 * Unit tests for ConversionTab component
 * Tests the Advanced Conversion toggle and token threshold settings
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { ConversionTab } from '../conversion-tab';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('ConversionTab', () => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  beforeEach(() => {
    mockFetch.mockClear();

    // Default mock response for settings
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        token_threshold: 15000,
        advanced_mode_enabled: false,
      }),
    });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Initial Rendering', () => {
    it('renders with toggle in OFF position by default (before API response)', () => {
      render(<ConversionTab />);

      // Should show loading state initially
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('fetches conversion settings on mount', async () => {
      await act(async () => {
        render(<ConversionTab />);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/conversion/settings`);
      });
    });

    it('displays toggle in ON position when API returns advanced_mode_enabled: true', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: true,
        }),
      });

      await act(async () => {
        render(<ConversionTab />);
      });

      await waitFor(() => {
        const toggle = screen.getByRole('switch', { name: /advanced conversion/i });
        expect(toggle).toBeChecked();
      });
    });

    it('displays toggle in OFF position when API returns advanced_mode_enabled: false', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      await act(async () => {
        render(<ConversionTab />);
      });

      await waitFor(() => {
        const toggle = screen.getByRole('switch', { name: /advanced conversion/i });
        expect(toggle).not.toBeChecked();
      });
    });

    it('shows loading state while fetching initial data', () => {
      // Make fetch hang to test loading state
      mockFetch.mockImplementation(() => new Promise(() => {}));

      render(<ConversionTab />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });

  describe('Toggle Interaction', () => {
    it('calls PUT endpoint with updated value when clicking toggle', async () => {
      // Initial load
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      // Toggle update
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: true,
        }),
      });

      await act(async () => {
        render(<ConversionTab />);
      });

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByRole('switch', { name: /advanced conversion/i })).not.toBeChecked();
      });

      const toggle = screen.getByRole('switch', { name: /advanced conversion/i });

      // Click toggle
      await act(async () => {
        fireEvent.click(toggle);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          `${API_BASE_URL}/api/conversion/settings`,
          expect.objectContaining({
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              token_threshold: 15000,
              advanced_mode_enabled: true,
            }),
          })
        );
      });
    });

    it('disables toggle during save operation', async () => {
      // Initial load
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      // Toggle update - make it hang to test disabled state
      mockFetch.mockImplementationOnce(() => new Promise(() => {}));

      await act(async () => {
        render(<ConversionTab />);
      });

      await waitFor(() => {
        expect(screen.getByRole('switch', { name: /advanced conversion/i })).not.toBeChecked();
      });

      const toggle = screen.getByRole('switch', { name: /advanced conversion/i });

      // Click toggle
      await act(async () => {
        fireEvent.click(toggle);
      });

      // Check toggle is disabled during save
      await waitFor(() => {
        expect(toggle).toBeDisabled();
        expect(screen.getByText(/saving\.\.\./i)).toBeInTheDocument();
      });
    });

    it('displays error message when save fails', async () => {
      // Initial load
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      // Toggle update fails
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Database connection failed' }),
      });

      await act(async () => {
        render(<ConversionTab />);
      });

      await waitFor(() => {
        expect(screen.getByRole('switch', { name: /advanced conversion/i })).not.toBeChecked();
      });

      const toggle = screen.getByRole('switch', { name: /advanced conversion/i });

      // Click toggle
      await act(async () => {
        fireEvent.click(toggle);
      });

      await waitFor(() => {
        expect(screen.getByText(/Database connection failed/i)).toBeInTheDocument();
      });
    });

    it('shows success state after successful save', async () => {
      // Initial load
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      // Toggle update succeeds
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: true,
        }),
      });

      await act(async () => {
        render(<ConversionTab />);
      });

      await waitFor(() => {
        expect(screen.getByRole('switch', { name: /advanced conversion/i })).not.toBeChecked();
      });

      const toggle = screen.getByRole('switch', { name: /advanced conversion/i });

      // Click toggle
      await act(async () => {
        fireEvent.click(toggle);
      });

      await waitFor(() => {
        expect(screen.getByText(/advanced mode setting saved successfully/i)).toBeInTheDocument();
      });
    });
  });

  describe('Toggle Description', () => {
    it('displays correct description text', async () => {
      await act(async () => {
        render(<ConversionTab />);
      });

      await waitFor(() => {
        expect(
          screen.getByText(/show advanced workflow pages \(conversion, sanitization, chunking\) in navigation/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Toggle Label', () => {
    it('displays correct label text', async () => {
      await act(async () => {
        render(<ConversionTab />);
      });

      await waitFor(() => {
        expect(screen.getByText(/advanced conversion/i)).toBeInTheDocument();
      });
    });
  });

  describe('State Persistence', () => {
    it('toggle state persists across component re-renders', async () => {
      // Initial load with ON state
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: true,
        }),
      });

      const { rerender } = await act(async () => {
        return render(<ConversionTab />);
      });

      await waitFor(() => {
        expect(screen.getByRole('switch', { name: /advanced conversion/i })).toBeChecked();
      });

      // Re-render component
      await act(async () => {
        rerender(<ConversionTab />);
      });

      // State should still be ON after re-render (fetched from backend)
      await waitFor(() => {
        expect(screen.getByRole('switch', { name: /advanced conversion/i })).toBeChecked();
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error when initial fetch fails', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await act(async () => {
        render(<ConversionTab />);
      });

      await waitFor(() => {
        expect(screen.getByText(/failed to load settings/i)).toBeInTheDocument();
      });
    });

    it('handles network errors gracefully during toggle save', async () => {
      // Initial load
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      // Toggle update fails with network error
      mockFetch.mockRejectedValueOnce(new Error('Network timeout'));

      await act(async () => {
        render(<ConversionTab />);
      });

      await waitFor(() => {
        expect(screen.getByRole('switch', { name: /advanced conversion/i })).not.toBeChecked();
      });

      const toggle = screen.getByRole('switch', { name: /advanced conversion/i });

      // Click toggle
      await act(async () => {
        fireEvent.click(toggle);
      });

      await waitFor(() => {
        expect(screen.getByText(/network timeout/i)).toBeInTheDocument();
      });
    });
  });

  describe('Token Threshold Integration', () => {
    it('includes current token threshold in toggle PUT request', async () => {
      // Initial load with specific threshold
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 20000,
          advanced_mode_enabled: false,
        }),
      });

      // Toggle update
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 20000,
          advanced_mode_enabled: true,
        }),
      });

      await act(async () => {
        render(<ConversionTab />);
      });

      await waitFor(() => {
        expect(screen.getByRole('switch', { name: /advanced conversion/i })).not.toBeChecked();
      });

      const toggle = screen.getByRole('switch', { name: /advanced conversion/i });

      // Click toggle
      await act(async () => {
        fireEvent.click(toggle);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          `${API_BASE_URL}/api/conversion/settings`,
          expect.objectContaining({
            method: 'PUT',
            body: JSON.stringify({
              token_threshold: 20000,
              advanced_mode_enabled: true,
            }),
          })
        );
      });
    });
  });
});
