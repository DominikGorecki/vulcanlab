import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { SummarizeTab } from '../summarize-tab';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock hooks
const mockToast = jest.fn();
jest.mock('@/hooks', () => ({
  ...jest.requireActual('@/hooks'),
  useToast: () => ({ toast: mockToast }),
}));

describe('SummarizeTab', () => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  const mockSettings = {
    h1_always_summarize: true,
    h2_top_percent: 10,
    h3_salience_threshold: 0.5,
    h4_salience_threshold: 0.7,
    definition_density_weight: 0.2,
    list_density_weight: 0.2,
    keyphrase_novelty_weight: 0.2,
    location_prior_weight: 0.2,
    heading_depth_weight: 0.2,
  };

  beforeEach(() => {
    mockFetch.mockClear();
    mockToast.mockClear();

    // Default mock response for settings
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockSettings,
    });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('renders loading state initially', () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));
    render(<SummarizeTab />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders form with data after loading', async () => {
    await act(async () => {
      render(<SummarizeTab />);
    });

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
      expect(screen.getByText(/Node Selection Thresholds/i)).toBeInTheDocument();
      expect(screen.getByText(/Salience Weights/i)).toBeInTheDocument();
    });

    const h2Input = screen.getByLabelText(/H2 Top Percent/i) as HTMLInputElement;
    expect(h2Input.value).toBe('10');

    const h1Switch = screen.getByRole('switch', { name: /Always Summarize H1/i });
    expect(h1Switch).toBeChecked();
  });

  it('validates h2_top_percent range (0-100)', async () => {
    await act(async () => {
      render(<SummarizeTab />);
    });

    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument());

    const h2Input = screen.getByLabelText(/H2 Top Percent/i);
    
    await act(async () => {
      fireEvent.change(h2Input, { target: { value: '150' } });
      fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/Maximum value is 100/i)).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.change(h2Input, { target: { value: '-10' } });
    });

    await waitFor(() => {
      expect(screen.getByText(/Minimum value is 0/i)).toBeInTheDocument();
    });
  });

  it('validates threshold range (0.0-1.0)', async () => {
    await act(async () => {
      render(<SummarizeTab />);
    });

    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument());

    const h3Input = screen.getByLabelText(/H3 Salience Threshold/i);
    
    await act(async () => {
      fireEvent.change(h3Input, { target: { value: '1.5' } });
      fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/Maximum value is 1.0/i)).toBeInTheDocument();
    });
  });

  it('calls PUT endpoint with form values on save', async () => {
    await act(async () => {
      render(<SummarizeTab />);
    });

    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument());

    const h2Input = screen.getByLabelText(/H2 Top Percent/i);
    
    await act(async () => {
      fireEvent.change(h2Input, { target: { value: '20' } });
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ ...mockSettings, h2_top_percent: 20 }),
    });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/v1/settings/summarize`,
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ ...mockSettings, h2_top_percent: 20 }),
        })
      );
      expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
        title: "Settings Saved",
      }));
    });
  });

  it('shows error toast when save fails', async () => {
    await act(async () => {
      render(<SummarizeTab />);
    });

    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument());

    const h2Input = screen.getByLabelText(/H2 Top Percent/i);
    await act(async () => {
      fireEvent.change(h2Input, { target: { value: '20' } });
    });

    mockFetch.mockResolvedValueOnce({
      ok: false,
      statusText: 'Internal Server Error',
    });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));
    });

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
        title: "Save Failed",
        variant: "destructive",
      }));
    });
  });

  it('shows confirmation dialog and resets to defaults on reset', async () => {
    await act(async () => {
      render(<SummarizeTab />);
    });

    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument());

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Reset to Defaults/i }));
    });

    expect(screen.getByText(/Reset to Defaults\?/i)).toBeInTheDocument();

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings, // Assuming mockSettings ARE the defaults
    });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Reset Settings/i }));
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/v1/settings/summarize`,
        expect.objectContaining({
          method: 'PUT',
        })
      );
      expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
        title: "Settings Reset",
      }));
    });
  });
});
