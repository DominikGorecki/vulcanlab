import { renderHook, act, waitFor } from '@testing-library/react';
import { usePageData } from './use-page-data';

describe('usePageData', () => {
  it('should initialize with loading state when autoFetch is true', () => {
    const mockFetch = jest.fn(() => Promise.resolve({ id: 1, name: 'Test' }));
    const { result } = renderHook(() => usePageData(mockFetch));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBe(null);
    expect(result.current.error).toBe(null);
  });

  it('should not auto-fetch when autoFetch is false', () => {
    const mockFetch = jest.fn(() => Promise.resolve({ id: 1, name: 'Test' }));
    const { result } = renderHook(() =>
      usePageData(mockFetch, { autoFetch: false })
    );

    expect(result.current.loading).toBe(false);
    expect(result.current.data).toBe(null);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('should handle successful data fetch', async () => {
    const mockData = { id: 1, name: 'Test User' };
    const mockFetch = jest.fn(() => Promise.resolve(mockData));
    const { result } = renderHook(() => usePageData(mockFetch));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBe(null);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('should handle fetch errors', async () => {
    const mockError = new Error('Fetch failed');
    const mockFetch = jest.fn(() => Promise.reject(mockError));
    const { result } = renderHook(() => usePageData(mockFetch));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBe(null);
    expect(result.current.error).toEqual(mockError);
  });

  it('should call onError callback when fetch fails', async () => {
    const mockError = new Error('Fetch failed');
    const mockFetch = jest.fn(() => Promise.reject(mockError));
    const onError = jest.fn();

    renderHook(() => usePageData(mockFetch, { onError }));

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(mockError);
    });
  });

  it('should handle non-Error rejections', async () => {
    const mockFetch = jest.fn(() => Promise.reject('String error'));
    const { result } = renderHook(() => usePageData(mockFetch));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe('String error');
  });

  it('should refetch data when refetch is called', async () => {
    const mockData1 = { id: 1, name: 'First' };
    const mockData2 = { id: 2, name: 'Second' };
    const mockFetch = jest
      .fn()
      .mockResolvedValueOnce(mockData1)
      .mockResolvedValueOnce(mockData2);

    const { result } = renderHook(() => usePageData(mockFetch));

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData1);
    });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data).toEqual(mockData2);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it('should clear error state when refetch succeeds after error', async () => {
    const mockError = new Error('First fetch failed');
    const mockData = { id: 1, name: 'Success' };
    const mockFetch = jest
      .fn()
      .mockRejectedValueOnce(mockError)
      .mockResolvedValueOnce(mockData);

    const { result } = renderHook(() => usePageData(mockFetch));

    await waitFor(() => {
      expect(result.current.error).toEqual(mockError);
    });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.error).toBe(null);
    expect(result.current.data).toEqual(mockData);
  });

  it('should set loading to true during refetch', async () => {
    const mockFetch = jest.fn(
      () => new Promise((resolve) => setTimeout(() => resolve({ id: 1 }), 100))
    );

    const { result } = renderHook(() =>
      usePageData(mockFetch, { autoFetch: false })
    );

    act(() => {
      result.current.refetch();
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });
});
