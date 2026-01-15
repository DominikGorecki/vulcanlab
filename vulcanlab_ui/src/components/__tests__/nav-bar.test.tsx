/**
 * Unit tests for NavBar component
 * Tests conditional rendering of navigation items based on advanced mode setting
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { NavBar } from '../nav-bar';
import { ConversionSettingsProvider } from '@/contexts/conversion-settings';
import { usePathname } from 'next/navigation';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('NavBar', () => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  beforeEach(() => {
    mockFetch.mockClear();
    (usePathname as jest.Mock).mockReturnValue('/');
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Advanced Mode OFF', () => {
    it('hides Conversion nav item when advanced mode is disabled', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      // Wait for loading to complete
      await screen.findByText('Simple Conversion');

      expect(screen.queryByTestId('nav-item-conversion')).not.toBeInTheDocument();
    });

    it('hides Sanitization nav item when advanced mode is disabled', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('Simple Conversion');

      expect(screen.queryByTestId('nav-item-sanitization')).not.toBeInTheDocument();
    });

    it('hides Chunking nav item when advanced mode is disabled', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('Simple Conversion');

      expect(screen.queryByTestId('nav-item-chunking')).not.toBeInTheDocument();
    });
  });

  describe('Advanced Mode ON', () => {
    it('shows Conversion nav item when advanced mode is enabled', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: true,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByTestId('nav-item-conversion');

      expect(screen.getByTestId('nav-item-conversion')).toBeInTheDocument();
    });

    it('shows Sanitization nav item when advanced mode is enabled', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: true,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByTestId('nav-item-sanitization');

      expect(screen.getByTestId('nav-item-sanitization')).toBeInTheDocument();
    });

    it('shows Chunking nav item when advanced mode is enabled', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: true,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByTestId('nav-item-chunking');

      expect(screen.getByTestId('nav-item-chunking')).toBeInTheDocument();
    });
  });

  describe('MD Import/Export Navigation Item', () => {
    it('includes MD Import/Export nav item', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('MD Import/Export');
      expect(screen.getByTestId('nav-item-md-import/export')).toBeInTheDocument();
    });

    it('MD Import/Export nav item is always visible (not filtered by advanced mode)', async () => {
      // Test with advanced mode OFF
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      const { rerender } = render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('MD Import/Export');
      expect(screen.getByTestId('nav-item-md-import/export')).toBeInTheDocument();

      // Test with advanced mode ON
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: true,
        }),
      });

      rerender(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('MD Import/Export');
      expect(screen.getByTestId('nav-item-md-import/export')).toBeInTheDocument();
    });

    it('MD Import/Export nav item links to /markdown/export', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('MD Import/Export');
      const navItem = screen.getByTestId('nav-item-md-import/export');
      expect(navItem).toHaveAttribute('href', '/markdown/export');
    });

    it('MD Import/Export nav item uses FileUp icon', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('MD Import/Export');
      const navItem = screen.getByTestId('nav-item-md-import/export');

      // Check that the icon is rendered (lucide icons render as SVG)
      const icon = navItem.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('Summarize Navigation Item', () => {
    it('includes Summarize nav item', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('Summarize');
      expect(screen.getByTestId('nav-item-summarize')).toBeInTheDocument();
    });

    it('Summarize nav item is always visible', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('Summarize');
      expect(screen.getByTestId('nav-item-summarize')).toBeInTheDocument();
    });

    it('Summarize nav item links to /summarize', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('Summarize');
      const navItem = screen.getByTestId('nav-item-summarize');
      expect(navItem).toHaveAttribute('href', '/summarize');
    });
  });

  describe('Always Visible Items', () => {
    it('shows Simple Conversion nav item regardless of toggle state', async () => {
      // Test with OFF
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      const { rerender } = render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('Simple Conversion');
      expect(screen.getByTestId('nav-item-simple-conversion')).toBeInTheDocument();

      // Test with ON
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: true,
        }),
      });

      rerender(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('Simple Conversion');
      expect(screen.getByTestId('nav-item-simple-conversion')).toBeInTheDocument();
    });

    it('shows Corpus nav item regardless of toggle state', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('Corpus');
      expect(screen.getByTestId('nav-item-corpus')).toBeInTheDocument();
    });

    it('shows Vectorization nav item regardless of toggle state', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('Vectorization');
      expect(screen.getByTestId('nav-item-vectorization')).toBeInTheDocument();
    });

    it('shows Research (RAG) nav item regardless of toggle state', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('Research (RAG)');
      expect(screen.getByTestId('nav-item-research-(rag)')).toBeInTheDocument();
    });

    it('shows Settings nav item regardless of toggle state', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('Settings');
      expect(screen.getByTestId('nav-item-settings')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('hides advanced items during initial load (defaults to simplified view)', () => {
      // Make fetch hang to test loading state
      mockFetch.mockImplementationOnce(() => new Promise(() => {}));

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      // Advanced items should be hidden during loading
      expect(screen.queryByTestId('nav-item-conversion')).not.toBeInTheDocument();
      expect(screen.queryByTestId('nav-item-sanitization')).not.toBeInTheDocument();
      expect(screen.queryByTestId('nav-item-chunking')).not.toBeInTheDocument();

      // Simple items should be visible
      expect(screen.getByTestId('nav-item-simple-conversion')).toBeInTheDocument();
      expect(screen.getByTestId('nav-item-corpus')).toBeInTheDocument();
      expect(screen.getByTestId('nav-item-settings')).toBeInTheDocument();
    });
  });

  describe('Fetch Failure Handling', () => {
    it('defaults to hidden state when fetch fails', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      // Wait for error to be handled
      await new Promise(resolve => setTimeout(resolve, 100));

      // Advanced items should be hidden on error
      expect(screen.queryByTestId('nav-item-conversion')).not.toBeInTheDocument();
      expect(screen.queryByTestId('nav-item-sanitization')).not.toBeInTheDocument();
      expect(screen.queryByTestId('nav-item-chunking')).not.toBeInTheDocument();

      // Simple items should still be visible
      expect(screen.getByTestId('nav-item-simple-conversion')).toBeInTheDocument();
      expect(screen.getByTestId('nav-item-corpus')).toBeInTheDocument();
    });
  });

  describe('Nav Item Ordering', () => {
    it('maintains correct nav item order when advanced mode is ON', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: true,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByTestId('nav-item-conversion');

      const navItems = screen.getAllByRole('link');
      const labels = navItems.map(item => item.textContent);

      // Expected order from navItems array
      expect(labels).toEqual([
        'Research (RAG)',
        'Collections',
        'Corpus',
        'Summarize',
        'Simple Conversion',
        'Conversion',
        'Sanitization',
        'Chunking',
        'Vectorization',
        'Search',
        'Cleanup',
        'Eval',
        'MD Import/Export',
        'Settings',
      ]);
    });

    it('maintains correct nav item order when advanced mode is OFF', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          token_threshold: 15000,
          advanced_mode_enabled: false,
        }),
      });

      render(
        <ConversionSettingsProvider>
          <NavBar />
        </ConversionSettingsProvider>
      );

      await screen.findByText('Simple Conversion');

      const navItems = screen.getAllByRole('link');
      const labels = navItems.map(item => item.textContent);

      // Expected order without advanced items
      expect(labels).toEqual([
        'Research (RAG)',
        'Collections',
        'Corpus',
        'Summarize',
        'Simple Conversion',
        'Vectorization',
        'Search',
        'Cleanup',
        'Eval',
        'MD Import/Export',
        'Settings',
      ]);
    });
  });
});
