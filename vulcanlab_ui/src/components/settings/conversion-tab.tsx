"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2Icon, CheckCircleIcon, AlertCircle } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ConversionSettingsData {
  token_threshold: number;
}

export function ConversionTab() {
  const [threshold, setThreshold] = useState<number>(15000);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

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
      <CardContent className="space-y-4">
        {error && (
          <div className="flex items-center gap-2 text-destructive bg-destructive/10 border border-destructive/20 px-4 py-3 rounded-md text-sm">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

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
