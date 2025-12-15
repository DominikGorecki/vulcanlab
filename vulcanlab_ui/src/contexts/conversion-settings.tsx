"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ConversionSettings {
  advanced_mode_enabled: boolean;
  token_threshold: number;
}

interface ConversionSettingsContextValue {
  advancedModeEnabled: boolean;
  loading: boolean;
  error: string | null;
  updateAdvancedMode: (enabled: boolean) => void;
  refetchSettings: () => Promise<void>;
}

const ConversionSettingsContext = createContext<ConversionSettingsContextValue | undefined>(
  undefined
);

export function ConversionSettingsProvider({ children }: { children: React.ReactNode }) {
  const [advancedModeEnabled, setAdvancedModeEnabled] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/api/conversion/settings`);

      if (!response.ok) {
        throw new Error(`Failed to load settings: ${response.statusText}`);
      }

      const data: ConversionSettings = await response.json();
      setAdvancedModeEnabled(data.advanced_mode_enabled ?? false);
    } catch (err) {
      console.error('Failed to load conversion settings:', err);
      setError(err instanceof Error ? err.message : 'Failed to load settings');
      // Default to false (hidden) on error
      setAdvancedModeEnabled(false);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch settings on mount
  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const updateAdvancedMode = useCallback((enabled: boolean) => {
    setAdvancedModeEnabled(enabled);
  }, []);

  const refetchSettings = useCallback(async () => {
    await fetchSettings();
  }, [fetchSettings]);

  const value = useMemo(
    () => ({
      advancedModeEnabled,
      loading,
      error,
      updateAdvancedMode,
      refetchSettings,
    }),
    [advancedModeEnabled, loading, error, updateAdvancedMode, refetchSettings]
  );

  return (
    <ConversionSettingsContext.Provider value={value}>
      {children}
    </ConversionSettingsContext.Provider>
  );
}

export function useConversionSettings() {
  const context = useContext(ConversionSettingsContext);
  if (context === undefined) {
    throw new Error('useConversionSettings must be used within a ConversionSettingsProvider');
  }
  return context;
}
