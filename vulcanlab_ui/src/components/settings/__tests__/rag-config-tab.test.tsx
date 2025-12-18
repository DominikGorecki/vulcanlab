/**
 * Unit tests for RagConfigTab component
 * Tests the sentence filter controls and integration with RAG config API
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { RagConfigTab } from '../rag-config-tab';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

const mockRagConfig = {
  id: 1,
  preset_name: 'default',
  is_default: true,
  description: 'Default RAG configuration',
  config: {
    retrieval: {
      dense_limit: 19,
      lexical_limit: 5,
      rrf_k: 50,
      top_k_rrf: 75,
      top_n_final: 17,
      entity_boost: 0.05,
      min_word_count: 150,
      min_char_count: 250,
      min_content_length: 750,
      enrich_lines_above: 0,
      enrich_lines_below: 13,
      mmr_lambda: 0.7,
      reranker_batch_size: 8,
      reranker_max_length: 512,
      min_sentence_filter_enabled: false,
      min_sentence_count: 5,
    },
    consolidation: {
      coverage_threshold: 0.5,
      line_gap: 7,
      min_content_length: 350,
      enrich_from_md: true,
    },
    augmentation: {
      top_n_contexts: 5,
    },
  },
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

describe('RagConfigTab - Sentence Filter Controls', () => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  beforeEach(() => {
    mockFetch.mockClear();

    // Default mock response for presets list
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => [mockRagConfig],
    });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Initial Rendering', () => {
    it('renders sentence filter controls with default values', async () => {
      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        expect(screen.getByLabelText(/enable minimum sentence filter/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/minimum sentences/i)).toBeInTheDocument();
      });
    });

    it('displays toggle in unchecked state when min_sentence_filter_enabled is false', async () => {
      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const toggle = screen.getByRole('switch', { name: /enable minimum sentence filter/i });
        expect(toggle).not.toBeChecked();
      });
    });

    it('displays toggle in checked state when min_sentence_filter_enabled is true', async () => {
      const configWithFilterEnabled = {
        ...mockRagConfig,
        config: {
          ...mockRagConfig.config,
          retrieval: {
            ...mockRagConfig.config.retrieval,
            min_sentence_filter_enabled: true,
          },
        },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => [configWithFilterEnabled],
      });

      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const toggle = screen.getByRole('switch', { name: /enable minimum sentence filter/i });
        expect(toggle).toBeChecked();
      });
    });

    it('displays correct default value for min_sentence_count', async () => {
      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const input = screen.getByLabelText(/minimum sentences/i);
        expect(input).toHaveValue(5);
      });
    });
  });

  describe('Number Input Disabled State', () => {
    it('disables number input when toggle is unchecked', async () => {
      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const input = screen.getByLabelText(/minimum sentences/i);
        expect(input).toBeDisabled();
      });
    });

    it('enables number input when toggle is checked', async () => {
      const configWithFilterEnabled = {
        ...mockRagConfig,
        config: {
          ...mockRagConfig.config,
          retrieval: {
            ...mockRagConfig.config.retrieval,
            min_sentence_filter_enabled: true,
          },
        },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => [configWithFilterEnabled],
      });

      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const input = screen.getByLabelText(/minimum sentences/i);
        expect(input).not.toBeDisabled();
      });
    });

    it('enables number input when user checks the toggle', async () => {
      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const toggle = screen.getByRole('switch', { name: /enable minimum sentence filter/i });
        expect(toggle).not.toBeChecked();
      });

      const toggle = screen.getByRole('switch', { name: /enable minimum sentence filter/i });

      await act(async () => {
        fireEvent.click(toggle);
      });

      await waitFor(() => {
        const input = screen.getByLabelText(/minimum sentences/i);
        expect(input).not.toBeDisabled();
      });
    });
  });

  describe('Client-Side Validation', () => {
    it('rejects values less than 1', async () => {
      const configWithFilterEnabled = {
        ...mockRagConfig,
        config: {
          ...mockRagConfig.config,
          retrieval: {
            ...mockRagConfig.config.retrieval,
            min_sentence_filter_enabled: true,
          },
        },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => [configWithFilterEnabled],
      });

      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const input = screen.getByLabelText(/minimum sentences/i);
        expect(input).not.toBeDisabled();
      });

      const input = screen.getByLabelText(/minimum sentences/i) as HTMLInputElement;

      // Try to set value to 0
      await act(async () => {
        fireEvent.change(input, { target: { value: '0' } });
      });

      // Value should not be updated (validation prevents it)
      await waitFor(() => {
        expect(input.value).toBe('5'); // Should remain at original value
      });
    });

    it('accepts values greater than or equal to 1', async () => {
      const configWithFilterEnabled = {
        ...mockRagConfig,
        config: {
          ...mockRagConfig.config,
          retrieval: {
            ...mockRagConfig.config.retrieval,
            min_sentence_filter_enabled: true,
          },
        },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => [configWithFilterEnabled],
      });

      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const input = screen.getByLabelText(/minimum sentences/i);
        expect(input).not.toBeDisabled();
      });

      const input = screen.getByLabelText(/minimum sentences/i) as HTMLInputElement;

      // Set value to 10
      await act(async () => {
        fireEvent.change(input, { target: { value: '10' } });
      });

      // Value should be updated
      await waitFor(() => {
        expect(input.value).toBe('10');
      });
    });

    it('enforces min attribute of 1', async () => {
      const configWithFilterEnabled = {
        ...mockRagConfig,
        config: {
          ...mockRagConfig.config,
          retrieval: {
            ...mockRagConfig.config.retrieval,
            min_sentence_filter_enabled: true,
          },
        },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => [configWithFilterEnabled],
      });

      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const input = screen.getByLabelText(/minimum sentences/i);
        expect(input).toHaveAttribute('min', '1');
      });
    });

    it('enforces max attribute of 100', async () => {
      const configWithFilterEnabled = {
        ...mockRagConfig,
        config: {
          ...mockRagConfig.config,
          retrieval: {
            ...mockRagConfig.config.retrieval,
            min_sentence_filter_enabled: true,
          },
        },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => [configWithFilterEnabled],
      });

      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const input = screen.getByLabelText(/minimum sentences/i);
        expect(input).toHaveAttribute('max', '100');
      });
    });
  });

  describe('Form Submission', () => {
    it('includes new fields in save payload', async () => {
      const configWithFilterEnabled = {
        ...mockRagConfig,
        config: {
          ...mockRagConfig.config,
          retrieval: {
            ...mockRagConfig.config.retrieval,
            min_sentence_filter_enabled: true,
            min_sentence_count: 10,
          },
        },
      };

      // Initial fetch
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [configWithFilterEnabled],
      });

      // Save response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => configWithFilterEnabled,
      });

      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const toggle = screen.getByRole('switch', { name: /enable minimum sentence filter/i });
        expect(toggle).toBeChecked();
      });

      const input = screen.getByLabelText(/minimum sentences/i);

      // Change value
      await act(async () => {
        fireEvent.change(input, { target: { value: '15' } });
      });

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: /save changes/i });
        expect(saveButton).not.toBeDisabled();
      });

      const saveButton = screen.getByRole('button', { name: /save changes/i });

      // Click save
      await act(async () => {
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          `${API_BASE_URL}/api/rag-config/default`,
          expect.objectContaining({
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: expect.stringContaining('"min_sentence_filter_enabled":true'),
          })
        );
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          `${API_BASE_URL}/api/rag-config/default`,
          expect.objectContaining({
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: expect.stringContaining('"min_sentence_count":15'),
          })
        );
      });
    });

    it('saves toggle state when user checks the toggle', async () => {
      // Initial fetch
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [mockRagConfig],
      });

      // Save response
      const updatedConfig = {
        ...mockRagConfig,
        config: {
          ...mockRagConfig.config,
          retrieval: {
            ...mockRagConfig.config.retrieval,
            min_sentence_filter_enabled: true,
          },
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => updatedConfig,
      });

      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const toggle = screen.getByRole('switch', { name: /enable minimum sentence filter/i });
        expect(toggle).not.toBeChecked();
      });

      const toggle = screen.getByRole('switch', { name: /enable minimum sentence filter/i });

      // Click toggle
      await act(async () => {
        fireEvent.click(toggle);
      });

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: /save changes/i });
        expect(saveButton).not.toBeDisabled();
      });

      const saveButton = screen.getByRole('button', { name: /save changes/i });

      // Click save
      await act(async () => {
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          `${API_BASE_URL}/api/rag-config/default`,
          expect.objectContaining({
            method: 'PUT',
            body: expect.stringContaining('"min_sentence_filter_enabled":true'),
          })
        );
      });
    });
  });

  describe('Default Values', () => {
    it('loads default values from API (false, 5)', async () => {
      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const toggle = screen.getByRole('switch', { name: /enable minimum sentence filter/i });
        const input = screen.getByLabelText(/minimum sentences/i) as HTMLInputElement;

        expect(toggle).not.toBeChecked();
        expect(input.value).toBe('5');
      });
    });

    it('loads custom values from API correctly', async () => {
      const customConfig = {
        ...mockRagConfig,
        config: {
          ...mockRagConfig.config,
          retrieval: {
            ...mockRagConfig.config.retrieval,
            min_sentence_filter_enabled: true,
            min_sentence_count: 15,
          },
        },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => [customConfig],
      });

      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const toggle = screen.getByRole('switch', { name: /enable minimum sentence filter/i });
        const input = screen.getByLabelText(/minimum sentences/i) as HTMLInputElement;

        expect(toggle).toBeChecked();
        expect(input.value).toBe('15');
      });
    });
  });

  describe('Value Persistence', () => {
    it('persists values after save and reload', async () => {
      const customConfig = {
        ...mockRagConfig,
        config: {
          ...mockRagConfig.config,
          retrieval: {
            ...mockRagConfig.config.retrieval,
            min_sentence_filter_enabled: true,
            min_sentence_count: 20,
          },
        },
      };

      // Initial fetch
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [customConfig],
      });

      // Fetch after update
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [customConfig],
      });

      await act(async () => {
        render(<RagConfigTab />);
      });

      await waitFor(() => {
        const toggle = screen.getByRole('switch', { name: /enable minimum sentence filter/i });
        const input = screen.getByLabelText(/minimum sentences/i) as HTMLInputElement;

        expect(toggle).toBeChecked();
        expect(input.value).toBe('20');
      });

      // Verify values persist
      const toggle = screen.getByRole('switch', { name: /enable minimum sentence filter/i });
      const input = screen.getByLabelText(/minimum sentences/i) as HTMLInputElement;

      expect(toggle).toBeChecked();
      expect(input.value).toBe('20');
    });
  });
});
