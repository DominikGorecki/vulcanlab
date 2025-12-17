/**
 * Unit tests for MarkdownTabs component
 * Tests tab rendering, navigation, and active state determination
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MarkdownTabs } from '../MarkdownTabs';
import { usePathname, useRouter } from 'next/navigation';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
  useRouter: jest.fn(),
}));

describe('MarkdownTabs', () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });
  });

  describe('Tab Rendering', () => {
    it('renders two tabs: Export and Import', () => {
      (usePathname as jest.Mock).mockReturnValue('/markdown/export');

      render(<MarkdownTabs />);

      expect(screen.getByTestId('markdown-tab-export')).toBeInTheDocument();
      expect(screen.getByTestId('markdown-tab-import')).toBeInTheDocument();
    });

    it('Export tab links to /markdown/export', () => {
      (usePathname as jest.Mock).mockReturnValue('/markdown/export');

      render(<MarkdownTabs />);

      const exportTab = screen.getByTestId('markdown-tab-export');
      expect(exportTab).toHaveAttribute('data-state', 'active');
    });

    it('Import tab links to /markdown/import', () => {
      (usePathname as jest.Mock).mockReturnValue('/markdown/import');

      render(<MarkdownTabs />);

      const importTab = screen.getByTestId('markdown-tab-import');
      expect(importTab).toHaveAttribute('data-state', 'active');
    });
  });

  describe('Active Tab Determination', () => {
    it('Export tab is active when on /markdown/export', () => {
      (usePathname as jest.Mock).mockReturnValue('/markdown/export');

      render(<MarkdownTabs />);

      const exportTab = screen.getByTestId('markdown-tab-export');
      const importTab = screen.getByTestId('markdown-tab-import');

      expect(exportTab).toHaveAttribute('data-state', 'active');
      expect(importTab).toHaveAttribute('data-state', 'inactive');
    });

    it('Import tab is active when on /markdown/import', () => {
      (usePathname as jest.Mock).mockReturnValue('/markdown/import');

      render(<MarkdownTabs />);

      const exportTab = screen.getByTestId('markdown-tab-export');
      const importTab = screen.getByTestId('markdown-tab-import');

      expect(exportTab).toHaveAttribute('data-state', 'inactive');
      expect(importTab).toHaveAttribute('data-state', 'active');
    });

    it('defaults to export tab when pathname does not match', () => {
      (usePathname as jest.Mock).mockReturnValue('/some/other/route');

      render(<MarkdownTabs />);

      const exportTab = screen.getByTestId('markdown-tab-export');
      expect(exportTab).toHaveAttribute('data-state', 'active');
    });
  });

  describe('Tab Navigation', () => {
    it('clicking Export tab navigates to /markdown/export', () => {
      (usePathname as jest.Mock).mockReturnValue('/markdown/import');

      render(<MarkdownTabs />);

      const exportTab = screen.getByTestId('markdown-tab-export');
      fireEvent.click(exportTab);

      expect(mockPush).toHaveBeenCalledWith('/markdown/export');
    });

    it('clicking Import tab navigates to /markdown/import', () => {
      (usePathname as jest.Mock).mockReturnValue('/markdown/export');

      render(<MarkdownTabs />);

      const importTab = screen.getByTestId('markdown-tab-import');
      fireEvent.click(importTab);

      expect(mockPush).toHaveBeenCalledWith('/markdown/import');
    });
  });

  describe('Pathname Edge Cases', () => {
    it('handles /markdown/import/nested routes as import tab active', () => {
      (usePathname as jest.Mock).mockReturnValue('/markdown/import/some/nested/route');

      render(<MarkdownTabs />);

      const importTab = screen.getByTestId('markdown-tab-import');
      expect(importTab).toHaveAttribute('data-state', 'active');
    });

    it('handles /markdown/export/nested routes as export tab active', () => {
      (usePathname as jest.Mock).mockReturnValue('/markdown/export/some/nested/route');

      render(<MarkdownTabs />);

      const exportTab = screen.getByTestId('markdown-tab-export');
      expect(exportTab).toHaveAttribute('data-state', 'active');
    });
  });
});
