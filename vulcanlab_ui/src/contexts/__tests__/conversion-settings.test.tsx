/**
 * Unit tests for ConversionSettingsContext
 * Tests state management, API fetching, and context provider functionality
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { ConversionSettingsProvider, useConversionSettings } from '../conversion-settings';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Test component that consumes the context
function TestConsumer() {
  const { advancedModeEnabled, loading, error, updateAdvancedMode, refetchSettings } = useConversionSettings();

  return (
    <div>
      <div data-testid="advanced-mode-enabled">{String(advancedModeEnabled)}</div>
      <div data-testid="loading">{String(loading)}</div>
      <div data-testid="error">{error || 'null'}</div>
      <button onClick={() => updateAdvancedMode(true)}>Enable Advanced Mode</button>
      <button onClick={() => updateAdvancedMode(false)}>Disable Advanced Mode</button>
      <button onClick={() => refetchSettings()}>Refetch Settings</button>
    </div>
  );
}

describe('ConversionSettingsContext', () => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  beforeEach(() => {
    mockFetch.mockClear();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Provider Initialization', () => {
    it('fetches conversion settings on mount', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      await act(async () => {
        render(
          <ConversionSettingsProvider>
            <TestConsumer />
          </ConversionSettingsProvider>
        );
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/conversion/settings`);
      });
    });

    it('sets loading to true during initial fetch', () => {
      mockFetch.mockImplementationOnce(() => new Promise(() => {})); // Never resolves

      render(
        <ConversionSettingsProvider>
          <TestConsumer />
        </ConversionSettingsProvider>
      );

      expect(screen.getByTestId('loading').textContent).toBe('true');
    });

    it('sets loading to false after successful fetch', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      await act(async () => {
        render(
          <ConversionSettingsProvider>
            <TestConsumer />
          </ConversionSettingsProvider>
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });
    });
  });

  describe('Context Value Provision', () => {
    it('provides advancedModeEnabled as false when API returns false', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      await act(async () => {
        render(
          <ConversionSettingsProvider>
            <TestConsumer />
          </ConversionSettingsProvider>
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId('advanced-mode-enabled').textContent).toBe('false');
      });
    });

    it('provides advancedModeEnabled as true when API returns true', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: true,
        }),
      });

      await act(async () => {
        render(
          <ConversionSettingsProvider>
            <TestConsumer />
          </ConversionSettingsProvider>
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId('advanced-mode-enabled').textContent).toBe('true');
      });
    });

    it('defaults to false when advanced_mode_enabled is undefined in API response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
        }),
      });

      await act(async () => {
        render(
          <ConversionSettingsProvider>
            <TestConsumer />
          </ConversionSettingsProvider>
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId('advanced-mode-enabled').textContent).toBe('false');
      });
    });
  });

  describe('Error Handling', () => {
    it('defaults to false when fetch fails', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await act(async () => {
        render(
          <ConversionSettingsProvider>
            <TestConsumer />
          </ConversionSettingsProvider>
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId('advanced-mode-enabled').textContent).toBe('false');
      });
    });

    it('sets error message when fetch fails', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network timeout'));

      await act(async () => {
        render(
          <ConversionSettingsProvider>
            <TestConsumer />
          </ConversionSettingsProvider>
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId('error').textContent).toBe('Network timeout');
      });
    });

    it('defaults to false when API returns non-ok response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      });

      await act(async () => {
        render(
          <ConversionSettingsProvider>
            <TestConsumer />
          </ConversionSettingsProvider>
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId('advanced-mode-enabled').textContent).toBe('false');
      });
    });

    it('sets loading to false after fetch fails', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await act(async () => {
        render(
          <ConversionSettingsProvider>
            <TestConsumer />
          </ConversionSettingsProvider>
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });
    });
  });

  describe('Context State Updates', () => {
    it('updates advancedModeEnabled when updateAdvancedMode is called', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      await act(async () => {
        render(
          <ConversionSettingsProvider>
            <TestConsumer />
          </ConversionSettingsProvider>
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId('advanced-mode-enabled').textContent).toBe('false');
      });

      // Update to true
      await act(async () => {
        screen.getByText('Enable Advanced Mode').click();
      });

      expect(screen.getByTestId('advanced-mode-enabled').textContent).toBe('true');

      // Update to false
      await act(async () => {
        screen.getByText('Disable Advanced Mode').click();
      });

      expect(screen.getByTestId('advanced-mode-enabled').textContent).toBe('false');
    });

    it('refetches settings when refetchSettings is called', async () => {
      // Initial fetch
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      await act(async () => {
        render(
          <ConversionSettingsProvider>
            <TestConsumer />
          </ConversionSettingsProvider>
        );
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1);
      });

      // Refetch with new value
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: true,
        }),
      });

      await act(async () => {
        screen.getByText('Refetch Settings').click();
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2);
        expect(screen.getByTestId('advanced-mode-enabled').textContent).toBe('true');
      });
    });
  });

  describe('Hook Error Handling', () => {
    it('throws error when useConversionSettings is used outside provider', () => {
      // Suppress console.error for this test
      const originalError = console.error;
      console.error = jest.fn();

      expect(() => {
        render(<TestConsumer />);
      }).toThrow('useConversionSettings must be used within a ConversionSettingsProvider');

      console.error = originalError;
    });
  });
});
