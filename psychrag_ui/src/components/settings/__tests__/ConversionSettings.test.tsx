import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import { ConversionSettings } from '../ConversionSettings';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('ConversionSettings', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('loads and displays current threshold on mount', async () => {
    mockedAxios.get.mockResolvedValue({
      data: { token_threshold: 20000 }
    });

    render(<ConversionSettings />);

    await waitFor(() => {
      const input = screen.getByLabelText(/Token Threshold/) as HTMLInputElement;
      expect(input.value).toBe('20000');
    });

    expect(mockedAxios.get).toHaveBeenCalledWith('/api/conversion/settings');
  });

  it('displays error when loading fails', async () => {
    mockedAxios.get.mockRejectedValue(new Error('Network error'));

    render(<ConversionSettings />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load settings/)).toBeInTheDocument();
    });
  });

  it('saves updated threshold successfully', async () => {
    mockedAxios.get.mockResolvedValue({
      data: { token_threshold: 15000 }
    });
    mockedAxios.put.mockResolvedValue({
      data: { token_threshold: 18000 }
    });

    render(<ConversionSettings />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Token Threshold/)).toBeInTheDocument();
    });

    const input = screen.getByLabelText(/Token Threshold/) as HTMLInputElement;
    fireEvent.change(input, { target: { value: '18000' } });

    const saveButton = screen.getByText('Save Settings');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockedAxios.put).toHaveBeenCalledWith('/api/conversion/settings', {
        token_threshold: 18000
      });
      expect(screen.getByText(/Settings saved successfully/)).toBeInTheDocument();
    });
  });

  it('displays error when saving fails', async () => {
    mockedAxios.get.mockResolvedValue({
      data: { token_threshold: 15000 }
    });
    mockedAxios.put.mockRejectedValue({
      response: { data: { detail: 'Invalid value' } }
    });

    render(<ConversionSettings />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Token Threshold/)).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Save Settings');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/Invalid value/)).toBeInTheDocument();
    });
  });

  it('validates positive threshold values', async () => {
    mockedAxios.get.mockResolvedValue({
      data: { token_threshold: 15000 }
    });

    render(<ConversionSettings />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Token Threshold/)).toBeInTheDocument();
    });

    const input = screen.getByLabelText(/Token Threshold/) as HTMLInputElement;
    fireEvent.change(input, { target: { value: '-100' } });

    const saveButton = screen.getByText('Save Settings');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/must be a positive number/)).toBeInTheDocument();
    });

    expect(mockedAxios.put).not.toHaveBeenCalled();
  });

  it('resets to current value on Reset button click', async () => {
    mockedAxios.get.mockResolvedValue({
      data: { token_threshold: 15000 }
    });

    render(<ConversionSettings />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Token Threshold/)).toBeInTheDocument();
    });

    const input = screen.getByLabelText(/Token Threshold/) as HTMLInputElement;
    fireEvent.change(input, { target: { value: '25000' } });
    expect(input.value).toBe('25000');

    const resetButton = screen.getByText('Reset');
    fireEvent.click(resetButton);

    await waitFor(() => {
      expect(input.value).toBe('15000');
    });

    expect(mockedAxios.get).toHaveBeenCalledTimes(2);
  });
});
