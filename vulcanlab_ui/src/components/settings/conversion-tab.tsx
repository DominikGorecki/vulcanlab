"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2Icon, CheckCircleIcon, AlertCircle } from "lucide-react";
import { useConversionSettings } from "@/contexts/conversion-settings";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ConversionSettingsData {
  token_threshold: number;
  advanced_mode_enabled: boolean;
}

export function ConversionTab() {
  const { updateAdvancedMode } = useConversionSettings();
  const [threshold, setThreshold] = useState<number>(15000);
  const [advancedMode, setAdvancedMode] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [savingToggle, setSavingToggle] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  const [toggleSaveSuccess, setToggleSaveSuccess] = useState<boolean>(false);

  // Load current settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/conversion/settings`);

      if (!response.ok) {
        throw new Error(`Failed to load settings: ${response.statusText}`);
      }

      const data: ConversionSettingsData = await response.json();
      setThreshold(data.token_threshold);
      setAdvancedMode(data.advanced_mode_enabled ?? false);
    } catch (err) {
      console.error('Failed to load conversion settings:', err);
      setError(err instanceof Error ? err.message : 'Failed to load settings. Using default value.');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    // Validate threshold
    if (threshold <= 0) {
      setError('Token threshold must be a positive number');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      setSaveSuccess(false);

      const response = await fetch(`${API_BASE_URL}/api/conversion/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token_threshold: threshold }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to save: ${response.statusText}`);
      }

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err: any) {
      console.error('Failed to save conversion settings:', err);
      const message = err instanceof Error ? err.message : 'Failed to save settings';
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  const handleThresholdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value)) {
      setThreshold(value);
      setError(null);
    }
  };

  const handleToggleChange = async (checked: boolean) => {
    try {
      setSavingToggle(true);
      setError(null);
      setToggleSaveSuccess(false);

      const response = await fetch(`${API_BASE_URL}/api/conversion/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token_threshold: threshold,
          advanced_mode_enabled: checked
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to save: ${response.statusText}`);
      }

      setAdvancedMode(checked);
      // Update context to immediately reflect in navigation
      updateAdvancedMode(checked);
      setToggleSaveSuccess(true);
      setTimeout(() => setToggleSaveSuccess(false), 2000);
    } catch (err: any) {
      console.error('Failed to save advanced mode toggle:', err);
      const message = err instanceof Error ? err.message : 'Failed to save toggle setting';
      setError(message);
    } finally {
      setSavingToggle(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Conversion Settings</CardTitle>
        <CardDescription>
          Configure settings for the simple conversion pipeline. The token
          threshold determines whether a document is processed as &quot;small&quot;
          (full LLM sanitization) or &quot;large&quot; (condensed heading extraction).
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <div className="flex items-center gap-2 text-destructive bg-destructive/10 border border-destructive/20 px-4 py-3 rounded-md text-sm">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

        {toggleSaveSuccess && (
          <div className="flex items-center gap-2 text-emerald-600 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900 px-4 py-3 rounded-md text-sm">
            <CheckCircleIcon className="h-4 w-4" />
            <span>Advanced mode setting saved successfully</span>
          </div>
        )}

        <div className="space-y-4 pb-4 border-b">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="advanced-mode" className="text-base font-medium">
                Advanced Conversion
              </Label>
              <p className="text-sm text-muted-foreground">
                Show advanced workflow pages (Conversion, Sanitization, Chunking) in navigation
              </p>
            </div>
            <Switch
              id="advanced-mode"
              checked={advancedMode}
              onCheckedChange={handleToggleChange}
              disabled={savingToggle}
            />
          </div>
          {savingToggle && (
            <div className="flex items-center gap-2 text-muted-foreground text-sm">
              <Loader2Icon className="h-3 w-3 animate-spin" />
              <span>Saving...</span>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="token-threshold">Token Threshold</Label>
          <Input
            id="token-threshold"
            type="number"
            min="1"
            step="1000"
            value={threshold}
            onChange={handleThresholdChange}
            disabled={saving}
            className="max-w-xs"
          />
          <p className="text-xs text-muted-foreground">
            Documents with fewer tokens use full LLM sanitization. Documents above this threshold
            use condensed heading extraction for processing.
          </p>
        </div>

        <div className="flex items-center gap-3 pt-2">
          <Button onClick={saveSettings} disabled={saving}>
            {saving ? (
              <>
                <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                Saving...
              </>
            ) : saveSuccess ? (
              <>
                <CheckCircleIcon className="h-4 w-4 mr-2 text-emerald-500" />
                Save Changes
              </>
            ) : (
              "Save Changes"
            )}
          </Button>
          <Button
            variant="outline"
            onClick={loadSettings}
            disabled={saving || loading}
          >
            Reset
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
