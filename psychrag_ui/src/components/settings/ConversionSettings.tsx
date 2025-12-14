/**
 * Conversion settings component for simple conversion pipeline.
 *
 * Allows users to configure the token threshold that determines whether
 * documents are classified as "small" or "large" for processing.
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ConversionSettings.css';

interface ConversionSettingsData {
  token_threshold: number;
}

export const ConversionSettings: React.FC = () => {
  const [threshold, setThreshold] = useState<number>(15000);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load current settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get<ConversionSettingsData>(
        '/api/conversion/settings'
      );
      setThreshold(response.data.token_threshold);
    } catch (err) {
      console.error('Failed to load conversion settings:', err);
      setError('Failed to load settings. Using default value.');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      // Validate threshold
      if (threshold <= 0) {
        setError('Token threshold must be a positive number');
        return;
      }

      await axios.put<ConversionSettingsData>('/api/conversion/settings', {
        token_threshold: threshold,
      });

      setSuccessMessage('Settings saved successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      console.error('Failed to save conversion settings:', err);
      const message = err.response?.data?.detail || 'Failed to save settings';
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  const handleThresholdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value)) {
      setThreshold(value);
    }
  };

  if (loading) {
    return <div className="conversion-settings">Loading settings...</div>;
  }

  return (
    <div className="conversion-settings">
      <h3>Conversion Settings</h3>
      <p className="settings-description">
        Configure settings for the simple conversion pipeline. The token
        threshold determines whether a document is processed as "small"
        (full LLM sanitization) or "large" (condensed heading extraction).
      </p>

      <div className="setting-item">
        <label htmlFor="token-threshold">
          Token Threshold:
          <span className="setting-hint">
            Documents with fewer tokens use full LLM sanitization
          </span>
        </label>
        <input
          id="token-threshold"
          type="number"
          min="1"
          step="1000"
          value={threshold}
          onChange={handleThresholdChange}
          disabled={saving}
        />
      </div>

      {error && <div className="error-message">{error}</div>}
      {successMessage && <div className="success-message">{successMessage}</div>}

      <div className="settings-actions">
        <button
          onClick={saveSettings}
          disabled={saving}
          className="btn-primary"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
        <button
          onClick={loadSettings}
          disabled={saving || loading}
          className="btn-secondary"
        >
          Reset
        </button>
      </div>
    </div>
  );
};
