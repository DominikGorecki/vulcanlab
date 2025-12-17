/**
 * Unit tests for Markdown Export Page
 * Tests work listing, export functionality, loading states, and error handling
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import MarkdownExportPage from '../page';

// Mock useRouter
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
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

describe('MarkdownExportPage', () => {
  const mockWorks = [
    { id: 1, title: 'Test Work 1', authors: 'Author A' },
    { id: 2, title: 'Test Work 2', authors: 'Author B, Author C' },
    { id: 3, title: 'Test Work 3', authors: null },
  ];

  beforeEach(() => {
    mockPush.mockClear();
    mockToast.mockClear();
    mockFetch.mockClear();

    // Default mock response for works
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ works: mockWorks, total: mockWorks.length }),
    });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Page Rendering', () => {
    it('test_page_renders_with_loading_state: displays loading spinner initially', async () => {
      mockFetch.mockImplementationOnce(
        () => new Promise(() => {}) // Never resolves
      );

      render(<MarkdownExportPage />);

      expect(screen.getByText('Export Markdown')).toBeInTheDocument();
      expect(screen.getByText('Export corpus works as markdown files with metadata.')).toBeInTheDocument();

      // Check for loading spinner
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('test_page_fetches_works_on_mount: fetches works from API on mount', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/corpus/works')
        );
      });
    });

    it('test_works_displayed_in_table: renders works in table correctly', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
        expect(screen.getByText('Test Work 2')).toBeInTheDocument();
        expect(screen.getByText('Test Work 3')).toBeInTheDocument();
        expect(screen.getByText('Author A')).toBeInTheDocument();
        expect(screen.getByText('Author B, Author C')).toBeInTheDocument();
      });
    });

    it('displays table headers correctly', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('ID')).toBeInTheDocument();
        expect(screen.getByText('Title')).toBeInTheDocument();
        expect(screen.getByText('Authors')).toBeInTheDocument();
        expect(screen.getByText('Actions')).toBeInTheDocument();
      });
    });

    it('displays dash for null authors', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        const rows = screen.getAllByRole('row');
        const work3Row = rows.find(row => row.textContent?.includes('Test Work 3'));
        expect(work3Row?.textContent).toContain('-');
      });
    });

    it('displays empty state when no works', async () => {
      mockFetch.mockReset();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ works: [], total: 0 }),
      });

      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('No corpus works found.')).toBeInTheDocument();
        expect(screen.getByText('Works must complete chunking before appearing here.')).toBeInTheDocument();
      });
    });
  });

  describe('Export Functionality', () => {
    it('test_export_button_calls_api: calls export API with correct work ID', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });

      // Mock export API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          message: 'Export successful',
          export_path: '/exports/test_work_1.md',
        }),
      });

      const exportButtons = screen.getAllByTestId(/export-button-/);
      fireEvent.click(exportButtons[0]);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/markdown/export/1'),
          expect.objectContaining({ method: 'POST' })
        );
      });
    });

    it('test_success_toast_appears: displays success toast after successful export', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });

      // Mock export API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          message: 'Export successful',
          export_path: '/exports/test_work_1.md',
        }),
      });

      const exportButtons = screen.getAllByTestId(/export-button-/);
      await act(async () => {
        fireEvent.click(exportButtons[0]);
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Export Successful',
            description: expect.stringContaining('test_work_1.md'),
          })
        );
      });
    });

    it('truncates long export paths in toast', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });

      // Mock export API response with long path
      const longPath = '/very/long/path/to/exports/with/many/directories/test_work_1.md';
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          message: 'Export successful',
          export_path: longPath,
        }),
      });

      const exportButtons = screen.getAllByTestId(/export-button-/);
      await act(async () => {
        fireEvent.click(exportButtons[0]);
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            description: expect.stringContaining('.../'),
          })
        );
      });
    });

    it('test_export_button_disabled_during_export: disables export button while export in progress', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });

      // Mock export API with delayed response
      mockFetch.mockImplementationOnce(
        () => new Promise(resolve => {
          setTimeout(() => {
            resolve({
              ok: true,
              json: async () => ({ success: true, export_path: '/exports/test.md' }),
            });
          }, 100);
        })
      );

      const exportButton = screen.getByTestId('export-button-1');

      await act(async () => {
        fireEvent.click(exportButton);
      });

      // Button should be disabled
      expect(exportButton).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(exportButton).not.toBeDisabled();
      }, { timeout: 500 });
    });

    it('shows loading spinner in button during export', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });

      // Mock export API with delayed response
      mockFetch.mockImplementationOnce(
        () => new Promise(resolve => {
          setTimeout(() => {
            resolve({
              ok: true,
              json: async () => ({ success: true, export_path: '/exports/test.md' }),
            });
          }, 100);
        })
      );

      const exportButton = screen.getByTestId('export-button-1');

      await act(async () => {
        fireEvent.click(exportButton);
      });

      // Check for spinner (Loader2Icon has animate-spin class)
      const spinner = exportButton.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();

      // Wait for completion
      await waitFor(() => {
        expect(exportButton).not.toBeDisabled();
      }, { timeout: 500 });
    });
  });

  describe('Error Handling', () => {
    it('test_error_modal_appears_on_failure: displays error modal after failed export', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });

      // Mock failed export
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'Work has no sanitized markdown' }),
      });

      const exportButtons = screen.getAllByTestId(/export-button-/);
      await act(async () => {
        fireEvent.click(exportButtons[0]);
      });

      await waitFor(() => {
        expect(screen.getByTestId('error-modal')).toBeInTheDocument();
        expect(screen.getByText('Export Failed')).toBeInTheDocument();
      });
    });

    it('handles 404 error correctly', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });

      // Mock 404 response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        headers: new Headers(),
      });

      const exportButtons = screen.getAllByTestId(/export-button-/);
      await act(async () => {
        fireEvent.click(exportButtons[0]);
      });

      await waitFor(() => {
        expect(screen.getByText('Work Not Found')).toBeInTheDocument();
      });
    });

    it('handles 500 error correctly', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });

      // Mock 500 response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'Database error at /path/to/file.py:123' }),
      });

      const exportButtons = screen.getAllByTestId(/export-button-/);
      await act(async () => {
        fireEvent.click(exportButtons[0]);
      });

      await waitFor(() => {
        expect(screen.getByTestId('error-modal')).toBeInTheDocument();
        // File paths should be sanitized
        expect(screen.getByTestId('error-details').textContent).toContain('[file]');
      });
    });

    it('handles network errors', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });

      // Mock network error
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const exportButtons = screen.getAllByTestId(/export-button-/);
      await act(async () => {
        fireEvent.click(exportButtons[0]);
      });

      await waitFor(() => {
        expect(screen.getByText('Connection Error')).toBeInTheDocument();
      });
    });

    it('displays error modal when works fetch fails', async () => {
      mockFetch.mockReset();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      });

      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText(/Failed to load works/)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('test_row_click_navigates_to_corpus_detail: navigates to corpus detail on row click', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });

      // Click on a row (but not the button)
      const rows = screen.getAllByRole('row');
      const work1Row = rows.find(row => row.textContent?.includes('Test Work 1'));

      if (work1Row) {
        fireEvent.click(work1Row);
      }

      expect(mockPush).toHaveBeenCalledWith('/corpus/1');
    });

    it('does not navigate when export button is clicked', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });

      // Mock export API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          export_path: '/exports/test.md',
        }),
      });

      const exportButtons = screen.getAllByTestId(/export-button-/);
      await act(async () => {
        fireEvent.click(exportButtons[0]);
      });

      // Navigation should not be triggered
      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  describe('Error Modal Interaction', () => {
    it('closes error modal when close button clicked', async () => {
      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });

      // Trigger error
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        headers: new Headers(),
      });

      const exportButtons = screen.getAllByTestId(/export-button-/);
      await act(async () => {
        fireEvent.click(exportButtons[0]);
      });

      await waitFor(() => {
        expect(screen.getByTestId('error-modal')).toBeInTheDocument();
      });

      // Close modal
      const closeButton = screen.getByTestId('close-button');
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByTestId('error-modal')).not.toBeInTheDocument();
      });
    });
  });

  describe('Retry Functionality', () => {
    it('allows retrying after fetch error', async () => {
      mockFetch.mockReset();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Server Error',
      });

      await act(async () => {
        render(<MarkdownExportPage />);
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
      });

      // Mock successful retry
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ works: mockWorks, total: mockWorks.length }),
      });

      const retryButton = screen.getByRole('button', { name: 'Retry' });
      await act(async () => {
        fireEvent.click(retryButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Test Work 1')).toBeInTheDocument();
      });
    });
  });
});
