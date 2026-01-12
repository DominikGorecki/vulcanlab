import { renderHook, act } from '@testing-library/react';
import { usePollSessionStatus } from '../polling';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('usePollSessionStatus', () => {
  const sessionId = 123;
  const mockSession = {
    id: sessionId,
    status: 'in_progress',
    current_phase: 'researching',
    state_data: {
      sections_completed: 2,
      total_sections: 5
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('starts polling when sessionId is provided', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockSession,
    });

    const { result } = renderHook(() => usePollSessionStatus(sessionId, 5000));

    // Initial state
    expect(result.current.isPolling).toBe(true);

    // Wait for initial fetch
    await act(async () => {
      jest.advanceTimersByTime(0);
    });

    expect(mockFetch).toHaveBeenCalledWith(`/api/v1/research-sessions/${sessionId}`);
    expect(result.current.status).toBe('in_progress');
    expect(result.current.currentPhase).toBe('researching');
    expect(result.current.sectionsCompleted).toBe(2);
    expect(result.current.totalSections).toBe(5);
  });

  it('polls every interval', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockSession,
    });

    renderHook(() => usePollSessionStatus(sessionId, 5000));

    await act(async () => {
      jest.advanceTimersByTime(5000);
    });

    expect(mockFetch).toHaveBeenCalledTimes(2); // Initial + 1st poll

    await act(async () => {
      jest.advanceTimersByTime(5000);
    });

    expect(mockFetch).toHaveBeenCalledTimes(3); // Initial + 2nd poll
  });

  it('stops polling when terminal status is reached', async () => {
    const completedSession = { ...mockSession, status: 'completed' };
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => completedSession,
    });

    const { result } = renderHook(() => usePollSessionStatus(sessionId, 5000));

    await act(async () => {
      jest.advanceTimersByTime(0);
    });

    expect(result.current.status).toBe('completed');
    expect(result.current.isPolling).toBe(false);

    await act(async () => {
      jest.advanceTimersByTime(5000);
    });

    expect(mockFetch).toHaveBeenCalledTimes(1); // Should not poll again
  });

  it('handles errors and stops polling', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => usePollSessionStatus(sessionId, 5000));

    await act(async () => {
      jest.advanceTimersByTime(0);
    });

    expect(result.current.error).toBe('Network error');
    expect(result.current.isPolling).toBe(false);
  });

  it('cleans up on unmount', () => {
    const clearIntervalSpy = jest.spyOn(global, 'clearInterval');
    const { unmount } = renderHook(() => usePollSessionStatus(sessionId, 5000));
    
    unmount();
    expect(clearIntervalSpy).toHaveBeenCalled();
    clearIntervalSpy.mockRestore();
  });
});
