"use client";

import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2Icon, CheckCircleIcon } from "lucide-react";
import { useConversionSettings } from "@/contexts/conversion-settings";
import { usePageData } from "@/hooks";
import { PageLoadingState, PageErrorState, FormField } from "@/components";
import { useForm } from "react-hook-form";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ConversionSettingsData {
  token_threshold: number;
  advanced_mode_enabled: boolean;
  use_full_model: boolean;
}

export function ConversionTab() {
  const { updateAdvancedMode } = useConversionSettings();
  
  const fetchSettingsFn = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/conversion/settings`);
    if (!response.ok) throw new Error(`Failed to load settings: ${response.statusText}`);
    return response.json();
  }, []);

  const { data, loading, error, refetch: loadSettings } = usePageData<ConversionSettingsData>(
    fetchSettingsFn
  );

  const { register, handleSubmit, reset, watch, setValue, formState: { isDirty } } = useForm<ConversionSettingsData>();
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (data) {
      reset(data);
    }
  }, [data, reset]);

  const advancedMode = watch("advanced_mode_enabled");
  const useFullModel = watch("use_full_model");

  const onSave = async (formData: ConversionSettingsData) => {
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE_URL}/api/conversion/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error(`Failed to save: ${response.statusText}`);
      }

      const updated = await response.json();
      updateAdvancedMode(updated.advanced_mode_enabled);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
      loadSettings();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <PageLoadingState />;
  if (error) return <PageErrorState title="Conversion Settings Error" error={error} onRetry={loadSettings} />;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Conversion Settings</CardTitle>
        <CardDescription>
          Configure settings for the simple conversion pipeline.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center justify-between pb-4 border-b">
          <div className="space-y-1">
            <Label className="text-base font-medium">Advanced Conversion</Label>
            <p className="text-sm text-muted-foreground">Show advanced workflow pages in navigation</p>
          </div>
          <Switch 
            checked={advancedMode} 
            onCheckedChange={(checked) => setValue("advanced_mode_enabled", checked, { shouldDirty: true })} 
          />
        </div>

        <div className="flex items-center justify-between pb-4 border-b">
          <div className="space-y-1">
            <Label className="text-base font-medium">Use Full LLM Models</Label>
            <p className="text-sm text-muted-foreground">Use full model tier for all processing</p>
          </div>
          <Switch 
            checked={useFullModel} 
            onCheckedChange={(checked) => setValue("use_full_model", checked, { shouldDirty: true })} 
          />
        </div>

        <FormField 
          label="Token Threshold" 
          description="Documents above this threshold use condensed extraction."
        >
          <Input 
            type="number" 
            min="1" 
            step="1000" 
            {...register("token_threshold", { valueAsNumber: true })} 
          />
        </FormField>

        <div className="flex items-center gap-3 pt-2">
          <Button onClick={handleSubmit(onSave)} disabled={saving || !isDirty}>
            {saving ? <Loader2Icon className="h-4 w-4 animate-spin mr-2" /> : null}
            {saveSuccess ? <CheckCircleIcon className="h-4 w-4 mr-2 text-emerald-500" /> : null}
            Save Changes
          </Button>
          <Button variant="outline" onClick={() => reset()} disabled={saving || !isDirty}>
            Reset
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
