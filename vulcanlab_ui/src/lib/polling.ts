import { useState, useEffect, useCallback, useRef } from 'react';
import { ResearchSession } from '@/types/research';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function usePollSessionStatus(sessionId: number | null, interval: number = 5000) {
  const [status, setStatus] = useState<string | null>(null);
  const [currentPhase, setCurrentPhase] = useState<string | null>(null);
  const [sectionsCompleted, setSectionsCompleted] = useState<number>(0);
  const [totalSections, setTotalSections] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch session status');
      }
      const data: ResearchSession = await response.json();
      
      setStatus(data.status);
      setCurrentPhase(data.current_phase || null);
      
      // Parse state_data for progress if it exists
      if (data.state_data) {
        const state = data.state_data;
        if (state.sections_completed !== undefined) {
          setSectionsCompleted(state.sections_completed);
        }
        if (state.total_sections !== undefined) {
          setTotalSections(state.total_sections);
        }
        if (data.status === 'failed' && state.error) {
          setError(state.error);
        }
      }

      // Stop polling if terminal state
      if (['completed', 'failed', 'cancelled'].includes(data.status)) {
        setIsPolling(false);
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      }
    } catch (err: any) {
      console.error('Polling error:', err);
      setError(err.message);
      setIsPolling(false);
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) {
      setIsPolling(false);
      setStatus(null);
      setCurrentPhase(null);
      setSectionsCompleted(0);
      setTotalSections(0);
      setError(null);
      return;
    }

    setIsPolling(true);
    fetchStatus();

    pollIntervalRef.current = setInterval(fetchStatus, interval);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [sessionId, interval, fetchStatus]);

  return {
    status,
    currentPhase,
    sectionsCompleted,
    totalSections,
    error,
    isPolling,
    refetch: fetchStatus
  };
}
