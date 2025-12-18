/**
 * Unit tests for Markdown Import Page
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MarkdownImportPage from '../page';

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('MarkdownImportPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockReset();
  });

  const mockFilesResponse = {
    files: [
      {
        filename: 'test.md',
        file_path: '/input/test.md',
        has_metadata: true,
        metadata: {
          title: 'Test Document',
          author: 'Test Author',
          year: 2024,
        },
      },
      {
        filename: 'no-metadata.md',
        file_path: '/input/no-metadata.md',
        has_metadata: false,
        metadata: null,
      },
    ],
  };

  it('redirects to status page after successful import', async () => {
    // 1. Files list
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockFilesResponse,
    });

    await act(async () => {
      render(<MarkdownImportPage />);
    });

    await waitFor(() => {
      expect(screen.getByText('test.md')).toBeInTheDocument();
    });

    // Click import button
    const importButtons = screen.getAllByText('Import');
    await act(async () => {
      importButtons[0].click();
    });

    // Metadata modal should appear
    await waitFor(() => {
      expect(screen.getByText('Enter Metadata')).toBeInTheDocument();
    });

    // Click Next (metadata is pre-populated)
    const nextButton = screen.getByText('Next');
    await act(async () => {
      nextButton.click();
    });

    // 2. Duplicate check - no duplicate
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ exists: false }),
    });

    // Sanitization modal should appear
    await waitFor(() => {
      expect(screen.getByText('Markdown Sanitization')).toBeInTheDocument();
    });

    // 3. Import request
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        work_id: 456,
        status: 'importing',
        duplicate_warning: null,
      }),
    });

    // Click "Yes, it's sanitized"
    const sanitizedButton = screen.getByText("Yes, it's sanitized");
    await act(async () => {
      sanitizedButton.click();
    });

    // Should redirect to status page
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/simple-conversion/automatic/456');
    });
  });

  it('redirects to status page with correct work_id', async () => {
    const testWorkId = 789;

    // 1. Files list
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockFilesResponse,
    });

    await act(async () => {
      render(<MarkdownImportPage />);
    });

    await waitFor(() => {
      expect(screen.getByText('test.md')).toBeInTheDocument();
    });

    // Click import button
    const importButtons = screen.getAllByText('Import');
    await act(async () => {
      importButtons[0].click();
    });

    await waitFor(() => {
      expect(screen.getByText('Enter Metadata')).toBeInTheDocument();
    });

    const nextButton = screen.getByText('Next');
    await act(async () => {
      nextButton.click();
    });

    // 2. Duplicate check
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ exists: false }),
    });

    await waitFor(() => {
      expect(screen.getByText('Markdown Sanitization')).toBeInTheDocument();
    });

    // 3. Import request with specific work_id
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        work_id: testWorkId,
        status: 'importing',
        duplicate_warning: null,
      }),
    });

    const sanitizedButton = screen.getByText("Yes, it's sanitized");
    await act(async () => {
      sanitizedButton.click();
    });

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(`/simple-conversion/automatic/${testWorkId}`);
    });
  });

  it('redirects for unsanitized markdown import', async () => {
    // 1. Files list
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockFilesResponse,
    });

    await act(async () => {
      render(<MarkdownImportPage />);
    });

    await waitFor(() => {
      expect(screen.getByText('test.md')).toBeInTheDocument();
    });

    const importButtons = screen.getAllByText('Import');
    await act(async () => {
      importButtons[0].click();
    });

    await waitFor(() => {
      expect(screen.getByText('Enter Metadata')).toBeInTheDocument();
    });

    const nextButton = screen.getByText('Next');
    await act(async () => {
      nextButton.click();
    });

    // 2. Duplicate check
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ exists: false }),
    });

    await waitFor(() => {
      expect(screen.getByText('Markdown Sanitization')).toBeInTheDocument();
    });

    // 3. Import request (unsanitized)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        work_id: 999,
        status: 'importing',
        duplicate_warning: null,
      }),
    });

    // Click "No, needs sanitization"
    const unsanitizedButton = screen.getByText('No, needs sanitization');
    await act(async () => {
      unsanitizedButton.click();
    });

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/simple-conversion/automatic/999');
    });
  });

  it('does not redirect on import error', async () => {
    // 1. Files list
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockFilesResponse,
    });

    await act(async () => {
      render(<MarkdownImportPage />);
    });

    await waitFor(() => {
      expect(screen.getByText('test.md')).toBeInTheDocument();
    });

    const importButtons = screen.getAllByText('Import');
    await act(async () => {
      importButtons[0].click();
    });

    await waitFor(() => {
      expect(screen.getByText('Enter Metadata')).toBeInTheDocument();
    });

    const nextButton = screen.getByText('Next');
    await act(async () => {
      nextButton.click();
    });

    // 2. Duplicate check
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ exists: false }),
    });

    await waitFor(() => {
      expect(screen.getByText('Markdown Sanitization')).toBeInTheDocument();
    });

    // 3. Import request fails
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'File not found' }),
    });

    const sanitizedButton = screen.getByText("Yes, it's sanitized");
    await act(async () => {
      sanitizedButton.click();
    });

    // Should NOT redirect
    await waitFor(() => {
      expect(screen.getByText('Import Failed')).toBeInTheDocument();
    });

    expect(mockPush).not.toHaveBeenCalled();
  });
});
