"use client";

import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2Icon, RotateCcwIcon, SaveIcon } from "lucide-react";
import { usePageData, useToast } from "@/hooks";
import { PageLoadingState, PageErrorState, FormField, ConfirmDialog } from "@/components";
import { useForm } from "react-hook-form";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SummarizeSettings {
  h1_always_summarize: boolean;
  h2_top_percent: number;
  h3_salience_threshold: number;
  h4_salience_threshold: number;
  definition_density_weight: number;
  list_density_weight: number;
  keyphrase_novelty_weight: number;
  location_prior_weight: number;
  heading_depth_weight: number;
}

const DEFAULT_SETTINGS: SummarizeSettings = {
  h1_always_summarize: true,
  h2_top_percent: 10,
  h3_salience_threshold: 0.5,
  h4_salience_threshold: 0.7,
  definition_density_weight: 0.2,
  list_density_weight: 0.2,
  keyphrase_novelty_weight: 0.2,
  location_prior_weight: 0.2,
  heading_depth_weight: 0.2,
};

export function SummarizeTab() {
  const { toast } = useToast();
  
  const fetchSettingsFn = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/settings/summarize`);
    if (!response.ok) throw new Error(`Failed to load settings: ${response.statusText}`);
    return response.json();
  }, []);

  const { data, loading, error, refetch: loadSettings } = usePageData<SummarizeSettings>(
    fetchSettingsFn
  );

  const { register, handleSubmit, reset, watch, setValue, formState: { isDirty, errors } } = useForm<SummarizeSettings>();
  const [saving, setSaving] = useState(false);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);

  useEffect(() => {
    if (data) {
      reset(data);
    }
  }, [data, reset]);

  const h1AlwaysSummarize = watch("h1_always_summarize");

  const onSave = async (formData: SummarizeSettings) => {
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/settings/summarize`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error(`Failed to save: ${response.statusText}`);
      }

      toast({
        title: "Settings Saved",
        description: "Summarization configuration has been updated.",
      });
      loadSettings();
    } catch (err) {
      console.error(err);
      toast({
        title: "Save Failed",
        description: err instanceof Error ? err.message : "Failed to save settings.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const onResetToDefaults = async () => {
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/settings/summarize`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(DEFAULT_SETTINGS),
      });

      if (!response.ok) {
        throw new Error(`Failed to reset: ${response.statusText}`);
      }

      toast({
        title: "Settings Reset",
        description: "Summarization configuration has been reset to defaults.",
      });
      loadSettings();
      setResetDialogOpen(false);
    } catch (err) {
      console.error(err);
      toast({
        title: "Reset Failed",
        description: err instanceof Error ? err.message : "Failed to reset settings.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <PageLoadingState />;
  if (error) return <PageErrorState title="Summarize Settings Error" error={error} onRetry={loadSettings} />;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Node Selection Thresholds</CardTitle>
          <CardDescription>
            Configure how nodes are selected for summarization based on their hierarchy and salience scores.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between pb-4 border-b">
            <div className="space-y-1">
              <Label htmlFor="h1_always_summarize" className="text-base font-medium">Always Summarize H1</Label>
              <p className="text-sm text-muted-foreground">Force include all level 1 headings in summaries.</p>
            </div>
            <Switch 
              id="h1_always_summarize"
              checked={h1AlwaysSummarize} 
              onCheckedChange={(checked) => setValue("h1_always_summarize", checked, { shouldDirty: true })} 
            />
          </div>

          <FormField 
            id="h2_top_percent"
            label="H2 Top Percent" 
            description="The percentage of top-salience level 2 nodes to include (0-100). Higher values mean more H2 sections are summarized."
            error={errors.h2_top_percent?.message}
          >
            <Input 
              id="h2_top_percent"
              type="number" 
              min="0" 
              max="100" 
              {...register("h2_top_percent", { 
                valueAsNumber: true,
                min: { value: 0, message: "Minimum value is 0" },
                max: { value: 100, message: "Maximum value is 100" }
              })} 
            />
          </FormField>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <FormField 
              id="h3_salience_threshold"
              label="H3 Salience Threshold" 
              description="Minimum salience score for level 3 nodes (0.0-1.0). Higher values mean fewer H3 sections are summarized."
              error={errors.h3_salience_threshold?.message}
            >
              <Input 
                id="h3_salience_threshold"
                type="number" 
                min="0" 
                max="1" 
                step="0.1"
                {...register("h3_salience_threshold", { 
                  valueAsNumber: true,
                  min: { value: 0, message: "Minimum value is 0.0" },
                  max: { value: 1, message: "Maximum value is 1.0" }
                })} 
              />
            </FormField>

            <FormField 
              id="h4_salience_threshold"
              label="H4 Salience Threshold" 
              description="Minimum salience score for level 4 nodes (0.0-1.0). Higher values mean fewer H4 sections are summarized."
              error={errors.h4_salience_threshold?.message}
            >
              <Input 
                id="h4_salience_threshold"
                type="number" 
                min="0" 
                max="1" 
                step="0.1"
                {...register("h4_salience_threshold", { 
                  valueAsNumber: true,
                  min: { value: 0, message: "Minimum value is 0.0" },
                  max: { value: 1, message: "Maximum value is 1.0" }
                })} 
              />
            </FormField>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Salience Weights</CardTitle>
          <CardDescription>
            Adjust the relative importance of different factors when calculating node salience scores. All weights should be between 0.0 and 1.0.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <FormField 
              id="definition_density_weight"
              label="Definition Density" 
              description="Weight for nodes containing many term definitions."
              error={errors.definition_density_weight?.message}
            >
              <Input 
                id="definition_density_weight"
                type="number" 
                min="0" 
                max="1" 
                step="0.05"
                {...register("definition_density_weight", { 
                  valueAsNumber: true,
                  min: { value: 0, message: "Minimum value is 0.0" },
                  max: { value: 1, message: "Maximum value is 1.0" }
                })} 
              />
            </FormField>

            <FormField 
              id="list_density_weight"
              label="List Density" 
              description="Weight for nodes containing lists or structured data."
              error={errors.list_density_weight?.message}
            >
              <Input 
                id="list_density_weight"
                type="number" 
                min="0" 
                max="1" 
                step="0.05"
                {...register("list_density_weight", { 
                  valueAsNumber: true,
                  min: { value: 0, message: "Minimum value is 0.0" },
                  max: { value: 1, message: "Maximum value is 1.0" }
                })} 
              />
            </FormField>

            <FormField 
              id="keyphrase_novelty_weight"
              label="Keyphrase Novelty" 
              description="Weight for nodes introducing new concepts or keyphrases."
              error={errors.keyphrase_novelty_weight?.message}
            >
              <Input 
                id="keyphrase_novelty_weight"
                type="number" 
                min="0" 
                max="1" 
                step="0.05"
                {...register("keyphrase_novelty_weight", { 
                  valueAsNumber: true,
                  min: { value: 0, message: "Minimum value is 0.0" },
                  max: { value: 1, message: "Maximum value is 1.0" }
                })} 
              />
            </FormField>

            <FormField 
              id="location_prior_weight"
              label="Location Prior" 
              description="Weight for nodes appearing at the beginning of sections."
              error={errors.location_prior_weight?.message}
            >
              <Input 
                id="location_prior_weight"
                type="number" 
                min="0" 
                max="1" 
                step="0.05"
                {...register("location_prior_weight", { 
                  valueAsNumber: true,
                  min: { value: 0, message: "Minimum value is 0.0" },
                  max: { value: 1, message: "Maximum value is 1.0" }
                })} 
              />
            </FormField>

            <FormField 
              id="heading_depth_weight"
              label="Heading Depth" 
              description="Weight for nodes higher in the document hierarchy."
              error={errors.heading_depth_weight?.message}
            >
              <Input 
                id="heading_depth_weight"
                type="number" 
                min="0" 
                max="1" 
                step="0.05"
                {...register("heading_depth_weight", { 
                  valueAsNumber: true,
                  min: { value: 0, message: "Minimum value is 0.0" },
                  max: { value: 1, message: "Maximum value is 1.0" }
                })} 
              />
            </FormField>
          </div>

          <div className="flex items-center gap-3 pt-6 border-t">
            <Button onClick={handleSubmit(onSave)} disabled={saving || !isDirty}>
              {saving ? <Loader2Icon className="h-4 w-4 animate-spin mr-2" /> : <SaveIcon className="h-4 w-4 mr-2" />}
              Save Changes
            </Button>
            <Button variant="outline" onClick={() => reset()} disabled={saving || !isDirty}>
              Cancel
            </Button>
            <div className="flex-1" />
            <Button variant="ghost" className="text-destructive hover:text-destructive" onClick={() => setResetDialogOpen(true)}>
              <RotateCcwIcon className="h-4 w-4 mr-2" />
              Reset to Defaults
            </Button>
          </div>
        </CardContent>
      </Card>

      <ConfirmDialog
        open={resetDialogOpen}
        onOpenChange={setResetDialogOpen}
        onConfirm={onResetToDefaults}
        title="Reset to Defaults?"
        message="This will overwrite all current summarization settings with their default values. This action cannot be undone."
        confirmLabel="Reset Settings"
        variant="danger"
      />
    </div>
  );
}
