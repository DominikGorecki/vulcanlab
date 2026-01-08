import { renderHook, act } from '@testing-library/react';
import { useDebounce } from '../use-debounce';

describe('useDebounce', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should return the initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 300));
    expect(result.current).toBe('initial');
  });

  it('should update the value after the specified delay', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 300 },
      }
    );

    // Update the value
    rerender({ value: 'updated', delay: 300 });

    // Should still be initial before delay
    expect(result.current).toBe('initial');

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Should now be updated
    expect(result.current).toBe('updated');
  });

  it('should reset the timer if the value changes again within the delay', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 300 },
      }
    );

    // First update
    rerender({ value: 'update1', delay: 300 });
    act(() => {
      jest.advanceTimersByTime(150);
    });
    expect(result.current).toBe('initial');

    // Second update before timer finished
    rerender({ value: 'update2', delay: 300 });
    act(() => {
      jest.advanceTimersByTime(150);
    });
    // Still initial because the 300ms timer for 'update2' hasn't finished
    expect(result.current).toBe('initial');

    // Finish the timer for 'update2'
    act(() => {
      jest.advanceTimersByTime(150);
    });
    expect(result.current).toBe('update2');
  });
});

