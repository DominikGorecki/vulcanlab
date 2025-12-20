import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Options for configuring the usePageData hook
 */
export interface UsePageDataOptions {
  /**
   * Whether to automatically fetch data on mount
   * @default true
   */
  autoFetch?: boolean;
  /**
   * Callback function called when an error occurs
   */
  onError?: (error: Error) => void;
}

/**
 * Return type for the usePageData hook
 */
export interface UsePageDataReturn<TData> {
  /**
   * The fetched data, or null if not yet loaded or an error occurred
   */
  data: TData | null;
  /**
   * Whether data is currently being fetched
   */
  loading: boolean;
  /**
   * Error object if fetch failed, null otherwise
   */
  error: Error | null;
  /**
   * Function to manually trigger a data fetch
   */
  refetch: () => Promise<void>;
}

/**
 * Custom hook for fetching and managing page data with loading and error states
 *
 * @param fetchFn - Async function that fetches the data
 * @param options - Configuration options
 * @returns Object containing data, loading state, error state, and refetch function
 */
export function usePageData<TData>(
  fetchFn: () => Promise<TData>,
  options: UsePageDataOptions = {}
): UsePageDataReturn<TData> {
  const { autoFetch = true, onError } = options;

  // Use a ref for onError to avoid unnecessary refetch recreations
  // when an inline function is passed to options.
  const onErrorRef = useRef(onError);
  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  const [data, setData] = useState<TData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await fetchFn();
      setData(result);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      if (onErrorRef.current) {
        onErrorRef.current(error);
      }
    } finally {
      setLoading(false);
    }
  }, [fetchFn]); // No longer depends on onError

  useEffect(() => {
    if (autoFetch) {
      refetch();
    }
  }, [autoFetch, refetch]);

  return {
    data,
    loading,
    error,
    refetch,
  };
}
