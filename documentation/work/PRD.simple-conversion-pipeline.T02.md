# T02: Configuration System for Token Threshold

**Status**: PENDING
**Priority**: High
**Type**: Vertical Slice (Backend + Frontend + API)
**Depends On**: None
**Blocks**: T03 (Parse & classify module needs to read threshold)

## Overview

Implement a configuration system for the simple conversion pipeline token threshold setting. This includes backend config file updates, API endpoints to read/write the setting, and a frontend UI in Settings to allow users to configure the threshold that determines whether a document is classified as "small" or "large".

## Acceptance Criteria

- [ ] Backend config file (`vulcanlab.config.json`) includes `conversion.token_threshold` setting
- [ ] Backend config loader can read and write token threshold value
- [ ] API endpoints exist to GET and PUT conversion settings
- [ ] Frontend Settings page has "Conversion Settings" section with token threshold input
- [ ] Changes to threshold are saved to config file and persist across restarts
- [ ] Default value is 15000 tokens
- [ ] All unit tests pass and use mocks (no database access)
- [ ] Manual test plan completed successfully

## Technical Implementation

### 1. Backend: Config File Schema

**File**: `vulcanlab.config.json`

Add new section to config schema:

```json
{
  "database": { ... },
  "llm": { ... },
  "paths": { ... },
  "conversion": {
    "token_threshold": 15000
  }
}
```

**Default Value**: 15000 tokens (distinguishes small vs large documents)

### 2. Backend: Config Loader Module

**File**: `src/vulcanlab/config/conversion_config.py` (NEW)

```python
"""
Configuration loader for simple conversion pipeline settings.

Provides functions to read and write conversion-related configuration values
from vulcanlab.config.json.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_TOKEN_THRESHOLD = 15000

def get_config_path() -> Path:
    """Get path to vulcanlab.config.json."""
    # Look for config in standard locations
    candidates = [
        Path.cwd() / "vulcanlab.config.json",
        Path.home() / ".vulcanlab" / "vulcanlab.config.json",
    ]

    for path in candidates:
        if path.exists():
            return path

    # Return default location if none exist
    return Path.cwd() / "vulcanlab.config.json"


def load_config() -> dict:
    """Load configuration from JSON file."""
    config_path = get_config_path()

    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}, using defaults")
        return {}

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}


def save_config(config: dict) -> None:
    """Save configuration to JSON file."""
    config_path = get_config_path()

    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Config saved to {config_path}")
    except Exception as e:
        logger.error(f"Failed to save config to {config_path}: {e}")
        raise


def get_token_threshold() -> int:
    """
    Get the token threshold for document classification.

    Returns:
        Token threshold value (defaults to 15000)
    """
    config = load_config()

    # Navigate nested structure: conversion.token_threshold
    conversion = config.get('conversion', {})
    threshold = conversion.get('token_threshold', DEFAULT_TOKEN_THRESHOLD)

    if not isinstance(threshold, int) or threshold <= 0:
        logger.warning(
            f"Invalid token threshold value: {threshold}, using default {DEFAULT_TOKEN_THRESHOLD}"
        )
        return DEFAULT_TOKEN_THRESHOLD

    return threshold


def set_token_threshold(threshold: int) -> None:
    """
    Set the token threshold for document classification.

    Args:
        threshold: New threshold value (must be positive integer)

    Raises:
        ValueError: If threshold is not a positive integer
    """
    if not isinstance(threshold, int) or threshold <= 0:
        raise ValueError("Token threshold must be a positive integer")

    config = load_config()

    # Ensure conversion section exists
    if 'conversion' not in config:
        config['conversion'] = {}

    config['conversion']['token_threshold'] = threshold
    save_config(config)
    logger.info(f"Token threshold updated to {threshold}")
```

### 3. Backend: API Endpoints

**File**: `src/vulcanlab/api/conversion_settings.py` (NEW)

```python
"""
API endpoints for simple conversion configuration.

Provides REST endpoints to read and update conversion settings including
the token threshold for document classification.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging

from vulcanlab.config.conversion_config import (
    get_token_threshold,
    set_token_threshold
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/conversion", tags=["conversion_settings"])


class ConversionSettings(BaseModel):
    """Conversion settings response/request model."""
    token_threshold: int = Field(
        ...,
        gt=0,
        description="Token threshold for small vs large document classification"
    )


@router.get("/settings", response_model=ConversionSettings)
async def get_conversion_settings():
    """
    Get current conversion settings.

    Returns:
        Current token threshold setting
    """
    try:
        threshold = get_token_threshold()
        return ConversionSettings(token_threshold=threshold)
    except Exception as e:
        logger.error(f"Failed to get conversion settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to load settings")


@router.put("/settings", response_model=ConversionSettings)
async def update_conversion_settings(settings: ConversionSettings):
    """
    Update conversion settings.

    Args:
        settings: New settings values

    Returns:
        Updated settings
    """
    try:
        set_token_threshold(settings.token_threshold)
        return settings
    except ValueError as e:
        logger.warning(f"Invalid settings update: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update conversion settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to save settings")
```

**File**: `src/vulcanlab/api/__init__.py` (MODIFIED)

Add router registration:

```python
from .conversion_settings import router as conversion_settings_router

# In app initialization
app.include_router(conversion_settings_router)
```

### 4. Frontend: Settings Page UI

**File**: `psychrag_ui/src/components/settings/ConversionSettings.tsx` (NEW)

```typescript
/**
 * Conversion settings component for simple conversion pipeline.
 *
 * Allows users to configure the token threshold that determines whether
 * documents are classified as "small" or "large" for processing.
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

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
```

**File**: `psychrag_ui/src/components/settings/Settings.tsx` (MODIFIED)

Add ConversionSettings component to existing settings page:

```typescript
import { ConversionSettings } from './ConversionSettings';

// In render:
<div className="settings-page">
  {/* Existing settings sections */}

  <section className="settings-section">
    <ConversionSettings />
  </section>

  {/* Other settings sections */}
</div>
```

### 5. Frontend: CSS Styling

**File**: `psychrag_ui/src/components/settings/ConversionSettings.css` (NEW)

```css
.conversion-settings {
  padding: 1rem;
}

.conversion-settings h3 {
  margin-bottom: 0.5rem;
  font-size: 1.2rem;
}

.settings-description {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

.setting-item {
  margin-bottom: 1.5rem;
}

.setting-item label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.setting-hint {
  display: block;
  font-size: 0.85rem;
  color: #888;
  font-weight: normal;
  margin-top: 0.25rem;
}

.setting-item input[type="number"] {
  width: 200px;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
}

.setting-item input[type="number"]:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.settings-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.error-message {
  color: #d32f2f;
  background-color: #ffebee;
  padding: 0.75rem;
  border-radius: 4px;
  margin: 1rem 0;
}

.success-message {
  color: #388e3c;
  background-color: #e8f5e9;
  padding: 0.75rem;
  border-radius: 4px;
  margin: 1rem 0;
}
```

## Unit Tests

### Backend Tests

**File**: `tests/unit/test_conversion_config.py` (NEW)

```python
"""Unit tests for conversion config loader."""

import pytest
from unittest.mock import patch, mock_open, MagicMock
import json

from vulcanlab.config.conversion_config import (
    get_token_threshold,
    set_token_threshold,
    load_config,
    save_config,
    DEFAULT_TOKEN_THRESHOLD
)


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('builtins.open', new_callable=mock_open, read_data='{"conversion": {"token_threshold": 20000}}')
def test_get_token_threshold_from_config(mock_file, mock_path):
    """Test reading token threshold from config file."""
    mock_path.return_value = MagicMock(exists=lambda: True)

    threshold = get_token_threshold()

    assert threshold == 20000


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('builtins.open', new_callable=mock_open, read_data='{}')
def test_get_token_threshold_default(mock_file, mock_path):
    """Test default token threshold when not in config."""
    mock_path.return_value = MagicMock(exists=lambda: True)

    threshold = get_token_threshold()

    assert threshold == DEFAULT_TOKEN_THRESHOLD


@patch('vulcanlab.config.conversion_config.get_config_path')
def test_get_token_threshold_missing_file(mock_path):
    """Test default threshold when config file doesn't exist."""
    mock_path.return_value = MagicMock(exists=lambda: False)

    threshold = get_token_threshold()

    assert threshold == DEFAULT_TOKEN_THRESHOLD


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('builtins.open', new_callable=mock_open, read_data='{"conversion": {"token_threshold": -100}}')
def test_get_token_threshold_invalid_value(mock_file, mock_path):
    """Test default threshold when config has invalid value."""
    mock_path.return_value = MagicMock(exists=lambda: True)

    threshold = get_token_threshold()

    assert threshold == DEFAULT_TOKEN_THRESHOLD


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('vulcanlab.config.conversion_config.load_config')
@patch('vulcanlab.config.conversion_config.save_config')
def test_set_token_threshold_success(mock_save, mock_load, mock_path):
    """Test setting token threshold successfully."""
    mock_load.return_value = {}

    set_token_threshold(25000)

    mock_save.assert_called_once()
    saved_config = mock_save.call_args[0][0]
    assert saved_config['conversion']['token_threshold'] == 25000


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('vulcanlab.config.conversion_config.load_config')
@patch('vulcanlab.config.conversion_config.save_config')
def test_set_token_threshold_preserves_existing_config(mock_save, mock_load, mock_path):
    """Test that setting threshold preserves other config sections."""
    mock_load.return_value = {
        'database': {'host': 'localhost'},
        'llm': {'model': 'gpt-4'}
    }

    set_token_threshold(18000)

    saved_config = mock_save.call_args[0][0]
    assert saved_config['database']['host'] == 'localhost'
    assert saved_config['llm']['model'] == 'gpt-4'
    assert saved_config['conversion']['token_threshold'] == 18000


def test_set_token_threshold_invalid_zero():
    """Test that zero threshold raises ValueError."""
    with pytest.raises(ValueError, match="positive integer"):
        set_token_threshold(0)


def test_set_token_threshold_invalid_negative():
    """Test that negative threshold raises ValueError."""
    with pytest.raises(ValueError, match="positive integer"):
        set_token_threshold(-5000)


def test_set_token_threshold_invalid_type():
    """Test that non-integer threshold raises ValueError."""
    with pytest.raises(ValueError, match="positive integer"):
        set_token_threshold("15000")  # String instead of int
```

**File**: `tests/unit/test_conversion_settings_api.py` (NEW)

```python
"""Unit tests for conversion settings API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from vulcanlab.api.conversion_settings import router


# Mock app for testing
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@patch('vulcanlab.api.conversion_settings.get_token_threshold')
def test_get_conversion_settings_success(mock_get):
    """Test GET /api/conversion/settings returns current threshold."""
    mock_get.return_value = 20000

    response = client.get('/api/conversion/settings')

    assert response.status_code == 200
    data = response.json()
    assert data['token_threshold'] == 20000


@patch('vulcanlab.api.conversion_settings.get_token_threshold')
def test_get_conversion_settings_error(mock_get):
    """Test GET /api/conversion/settings handles errors."""
    mock_get.side_effect = Exception("Config error")

    response = client.get('/api/conversion/settings')

    assert response.status_code == 500


@patch('vulcanlab.api.conversion_settings.set_token_threshold')
def test_update_conversion_settings_success(mock_set):
    """Test PUT /api/conversion/settings updates threshold."""
    response = client.put(
        '/api/conversion/settings',
        json={'token_threshold': 18000}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['token_threshold'] == 18000
    mock_set.assert_called_once_with(18000)


@patch('vulcanlab.api.conversion_settings.set_token_threshold')
def test_update_conversion_settings_invalid_value(mock_set):
    """Test PUT /api/conversion/settings rejects invalid values."""
    mock_set.side_effect = ValueError("Token threshold must be a positive integer")

    response = client.put(
        '/api/conversion/settings',
        json={'token_threshold': -100}
    )

    assert response.status_code == 400


def test_update_conversion_settings_missing_field():
    """Test PUT /api/conversion/settings rejects missing fields."""
    response = client.put(
        '/api/conversion/settings',
        json={}
    )

    assert response.status_code == 422  # Pydantic validation error


@patch('vulcanlab.api.conversion_settings.set_token_threshold')
def test_update_conversion_settings_save_error(mock_set):
    """Test PUT /api/conversion/settings handles save errors."""
    mock_set.side_effect = Exception("Disk full")

    response = client.put(
        '/api/conversion/settings',
        json={'token_threshold': 15000}
    )

    assert response.status_code == 500
```

### Frontend Tests

**File**: `psychrag_ui/src/components/settings/__tests__/ConversionSettings.test.tsx` (NEW)

```typescript
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
```

## Manual Test Plan

### Setup
1. Ensure database is running
2. Ensure `vulcanlab.config.json` exists or can be created
3. Start backend API server
4. Start frontend dev server

### Test Cases

#### TC1: Load Default Settings
**Steps**:
1. Remove `conversion` section from `vulcanlab.config.json` if present
2. Navigate to Settings page in UI
3. Verify Conversion Settings section appears
4. Verify token threshold shows 15000 (default)

**Expected**: Default value of 15000 displayed

#### TC2: Load Existing Settings
**Steps**:
1. Manually edit `vulcanlab.config.json` to set `conversion.token_threshold = 20000`
2. Restart backend server
3. Navigate to Settings page in UI
4. Verify token threshold shows 20000

**Expected**: Custom value of 20000 displayed

#### TC3: Update Settings Successfully
**Steps**:
1. Navigate to Settings page
2. Change token threshold to 18000
3. Click "Save Settings"
4. Verify success message appears
5. Check `vulcanlab.config.json` file
6. Verify `conversion.token_threshold` is now 18000

**Expected**: Settings saved and persisted to file

#### TC4: Invalid Value Validation
**Steps**:
1. Navigate to Settings page
2. Try to set threshold to -100
3. Click "Save Settings"
4. Verify error message appears
5. Verify settings were NOT saved

**Expected**: Error message, no save operation

#### TC5: Settings Persist Across Restarts
**Steps**:
1. Set token threshold to 25000 and save
2. Restart backend server
3. Navigate to Settings page
4. Verify threshold still shows 25000

**Expected**: Value persists after restart

#### TC6: Reset Button
**Steps**:
1. Navigate to Settings page (currently 15000)
2. Change threshold to 30000 (don't save)
3. Click "Reset" button
4. Verify threshold returns to 15000

**Expected**: Unsaved changes discarded

#### TC7: API Endpoint Directly
**Steps**:
1. Use curl or Postman to GET `/api/conversion/settings`
2. Verify JSON response contains `token_threshold`
3. PUT new value: `{"token_threshold": 22000}`
4. Verify response shows updated value
5. GET again to confirm persistence

**Expected**: API works independently of UI

## Dependencies

- **Backend**: SQLAlchemy, FastAPI, Pydantic
- **Frontend**: React, Axios, TypeScript
- **Testing**: pytest, pytest-mock (backend); Jest, React Testing Library (frontend)

## Assumptions

1. `vulcanlab.config.json` is writable by the backend process
2. Config file location follows existing pattern (cwd or ~/.vulcanlab/)
3. Settings page already has router and component structure
4. Axios is configured with proper base URL for API calls

## Notes

- This is a **vertical slice** ticket covering full stack (config → API → UI)
- Default value of 15000 tokens is based on PRD requirements
- Changes are saved to file immediately (no batch/commit pattern needed)
- Frontend uses controlled component pattern for input
- Success message auto-dismisses after 3 seconds
- Config loader includes validation to prevent invalid values from breaking system
- All tests use mocks - no actual file I/O or database access

## Definition of Done

- [ ] All code implemented as specified
- [ ] All unit tests pass (13 tests: 10 backend, 3 frontend)
- [ ] Manual test plan executed and passed
- [ ] No database access in unit tests (mocks only)
- [ ] Code follows existing project patterns
- [ ] Frontend component renders without console errors
- [ ] API endpoints respond with correct status codes
- [ ] Config file updates persist correctly
