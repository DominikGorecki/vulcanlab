"use client";

import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Star, Trash2, Loader2Icon, AlertTriangle, Plus } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { usePageData } from "@/hooks";
import { PageLoadingState, PageErrorState, FormField, ConfirmDialog } from "@/components";
import { useForm, Controller } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type {
  RagConfig,
  RagConfigParams,
} from "@/types/rag-config";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function RagConfigTab() {
  const fetchPresetsFn = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/rag-config/`);
    if (!response.ok) throw new Error(`Failed to fetch presets: ${response.statusText}`);
    return response.json();
  }, []);

  const { data: presets, loading, error, refetch: fetchPresets } = usePageData<RagConfig[]>(
    fetchPresetsFn
  );

  const [selectedPresetName, setSelectedPresetName] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);

  const { register, handleSubmit, reset, control, getValues, formState: { isDirty } } = useForm<{
    description: string;
    config: RagConfigParams;
  }>();

  useEffect(() => {
    if (presets && presets.length > 0 && !selectedPresetName) {
      const defaultPreset = presets.find(p => p.is_default) || presets[0];
      setSelectedPresetName(defaultPreset.preset_name);
    }
  }, [presets, selectedPresetName]);

  useEffect(() => {
    if (presets && selectedPresetName) {
      const preset = presets.find(p => p.preset_name === selectedPresetName);
      if (preset) {
        reset({
          description: preset.description || "",
          config: JSON.parse(JSON.stringify(preset.config))
        });
      }
    }
  }, [selectedPresetName, presets, reset]);

  const onSave = async (formData: { description: string, config: RagConfigParams }) => {
    if (!selectedPresetName) return;
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE_URL}/api/rag-config/${encodeURIComponent(selectedPresetName)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!response.ok) throw new Error("Failed to save preset");
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
      fetchPresets();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleSetDefault = async () => {
    if (!selectedPresetName) return;
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE_URL}/api/rag-config/${encodeURIComponent(selectedPresetName)}/set-default`, { method: "PUT" });
      if (!response.ok) throw new Error("Failed to set default");
      fetchPresets();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedPresetName) return;
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE_URL}/api/rag-config/${encodeURIComponent(selectedPresetName)}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Failed to delete preset");
      setSelectedPresetName(null);
      fetchPresets();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleCreatePreset = async (data: { name: string, description: string }) => {
    try {
      setCreating(true);
      const currentConfig = getValues("config");
      const response = await fetch(`${API_BASE_URL}/api/rag-config/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preset_name: data.name,
          description: data.description,
          is_default: false,
          config: currentConfig
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to create preset");
      }

      const newPreset = await response.json();
      setShowCreateModal(false);
      await fetchPresets();
      setSelectedPresetName(newPreset.preset_name);
    } catch (err) {
      console.error(err);
      alert(err instanceof Error ? err.message : "Failed to create preset");
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <PageLoadingState />;
  if (error) return <PageErrorState title="RAG Config Error" error={error} onRetry={fetchPresets} />;

  const currentPreset = presets?.find(p => p.preset_name === selectedPresetName);
  const isDefault = currentPreset?.is_default || false;

  return (
    <div className="space-y-4 pb-12">
      <Card>
        <CardHeader>
          <CardTitle>RAG Presets</CardTitle>
          <CardDescription>Manage your RAG pipeline configurations.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <Label>Active Preset</Label>
              <Select value={selectedPresetName || ""} onValueChange={setSelectedPresetName}>
                <SelectTrigger className="mt-1.5">
                  <SelectValue placeholder="Select preset..." />
                </SelectTrigger>
                <SelectContent>
                  {presets?.map(p => (
                    <SelectItem key={p.id} value={p.preset_name}>
                      <div className="flex items-center gap-2">
                        {p.preset_name}
                        {p.is_default && <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="pt-6 flex gap-2">
              <Button variant="outline" size="icon" onClick={() => setShowCreateModal(true)} title="Create new preset">
                <Plus className="h-4 w-4" />
              </Button>
              {!isDefault && (
                <Button variant="outline" size="icon" onClick={handleSetDefault} title="Set as default">
                  <Star className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>

          <FormField label="Description">
            <Input {...register("description")} />
          </FormField>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Parameters</CardTitle>
          <CardDescription>Tweak the RAG pipeline behavior.</CardDescription>
        </CardHeader>
        <CardContent>
          <Accordion type="multiple" defaultValue={["retrieval", "consolidation", "augmentation"]}>
            <AccordionItem value="retrieval">
              <AccordionTrigger className="text-lg font-bold">Retrieval Stage</AccordionTrigger>
              <AccordionContent className="space-y-6 pt-4">
                {/* Search Parameters */}
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Search</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <FormField label="Dense Limit" description="Max results per dense vector query">
                      <Input type="number" {...register("config.retrieval.dense_limit", { valueAsNumber: true })} />
                    </FormField>
                    <FormField label="Lexical Limit" description="Max results per keyword query">
                      <Input type="number" {...register("config.retrieval.lexical_limit", { valueAsNumber: true })} />
                    </FormField>
                  </div>
                </div>

                {/* Fusion Parameters */}
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Rank Fusion (RRF)</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <FormField label="RRF K" description="Constant for Reciprocal Rank Fusion">
                      <Input type="number" {...register("config.retrieval.rrf_k", { valueAsNumber: true })} />
                    </FormField>
                    <FormField label="Top K RRF" description="Candidates to keep after fusion">
                      <Input type="number" {...register("config.retrieval.top_k_rrf", { valueAsNumber: true })} />
                    </FormField>
                  </div>
                </div>

                {/* Enrichment Parameters */}
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Context Enrichment</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <FormField label="Min Word Count" description="Trigger enrichment below this">
                      <Input type="number" {...register("config.retrieval.min_word_count", { valueAsNumber: true })} />
                    </FormField>
                    <FormField label="Max Word Count" description="Maximum words for enriched chunk">
                      <Input type="number" {...register("config.retrieval.max_word_count", { valueAsNumber: true })} />
                    </FormField>
                  </div>
                </div>

                {/* Reranking Parameters */}
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Reranking</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <FormField label="Batch Size" description="Parallel query-chunk pairs">
                      <Input type="number" {...register("config.retrieval.reranker_batch_size", { valueAsNumber: true })} />
                    </FormField>
                    <FormField label="Max Length" description="Max tokens for reranker input">
                      <Input type="number" {...register("config.retrieval.reranker_max_length", { valueAsNumber: true })} />
                    </FormField>
                  </div>
                </div>

                {/* Scoring & Diversity */}
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Scoring & Diversity</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <FormField label="MMR Lambda" description="Relevance (1.0) vs Diversity (0.0)">
                      <Input type="number" step="0.01" {...register("config.retrieval.mmr_lambda", { valueAsNumber: true })} />
                    </FormField>
                    <FormField label="Entity Boost" description="Score boost per entity match">
                      <Input type="number" step="0.01" {...register("config.retrieval.entity_boost", { valueAsNumber: true })} />
                    </FormField>
                  </div>
                </div>

                {/* Final Selection */}
                <div className="space-y-4 border-t pt-4">
                  <FormField label="Top N Final" description="Final chunks selected after reranking/MMR">
                    <Input type="number" {...register("config.retrieval.top_n_final", { valueAsNumber: true })} />
                  </FormField>
                </div>

                {/* Sentence Filtering */}
                <div className="space-y-4 border-t pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Min Sentence Filtering</Label>
                      <p className="text-xs text-muted-foreground">Filter short chunks at query time</p>
                    </div>
                    <Controller
                      name="config.retrieval.min_sentence_filter_enabled"
                      control={control}
                      render={({ field }) => (
                        <Switch checked={field.value} onCheckedChange={field.onChange} />
                      )}
                    />
                  </div>
                  {/* Min Sentence Count if enabled */}
                  <Controller 
                    name="config.retrieval.min_sentence_filter_enabled"
                    control={control}
                    render={({ field: { value: enabled } }) => (
                      enabled ? (
                        <FormField label="Min Sentence Count">
                           <Input type="number" {...register("config.retrieval.min_sentence_count", { valueAsNumber: true })} />
                        </FormField>
                      ) : <></>
                    )}
                  />
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="consolidation">
              <AccordionTrigger className="text-lg font-bold">Consolidation Stage</AccordionTrigger>
              <AccordionContent className="space-y-6 pt-4">
                <div className="space-y-4">
                  <Label>Coverage Threshold</Label>
                  <p className="text-xs text-muted-foreground">Percentage of parent content required for replacement (0.0-1.0)</p>
                  <Controller
                    name="config.consolidation.coverage_threshold"
                    control={control}
                    render={({ field }) => (
                      <Slider 
                        min={0} 
                        max={1} 
                        step={0.05} 
                        value={[field.value ?? 0.5]} 
                        onValueChange={([v]) => field.onChange(v)} 
                      />
                    )}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <FormField label="Line Gap" description="Max lines between chunks to merge">
                    <Input type="number" {...register("config.consolidation.line_gap", { valueAsNumber: true })} />
                  </FormField>
                  <FormField label="Min Group Length" description="Min characters for consolidated group">
                    <Input type="number" {...register("config.consolidation.min_content_length", { valueAsNumber: true })} />
                  </FormField>
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="augmentation">
              <AccordionTrigger className="text-lg font-bold">Augmentation Stage</AccordionTrigger>
              <AccordionContent className="space-y-4 pt-4">
                <FormField label="Top N Contexts" description="Number of source blocks in final prompt">
                  <Input type="number" {...register("config.augmentation.top_n_contexts", { valueAsNumber: true })} />
                </FormField>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6 flex justify-between">
          <div className="flex gap-2">
             <Button onClick={handleSubmit(onSave)} disabled={saving || !isDirty}>
               {saving && <Loader2Icon className="h-4 w-4 animate-spin mr-2" />}
               {saveSuccess ? "Saved!" : "Save Changes"}
             </Button>
             <Button variant="outline" onClick={() => reset()} disabled={saving || !isDirty}>Reset</Button>
          </div>
          {!isDefault && (
            <Button variant="destructive" onClick={() => setShowDeleteConfirm(true)}>
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Preset
            </Button>
          )}
        </CardContent>
      </Card>

      <ConfirmDialog
        open={showDeleteConfirm}
        onOpenChange={setShowDeleteConfirm}
        title="Delete Preset"
        message={`Are you sure you want to delete "${selectedPresetName}"?`}
        onConfirm={handleDelete}
        confirmLabel="Delete"
        variant="danger"
      />

      <CreatePresetModal 
        open={showCreateModal} 
        onOpenChange={setShowCreateModal} 
        onConfirm={handleCreatePreset}
        loading={creating}
      />
    </div>
  );
}

function CreatePresetModal({ 
  open, 
  onOpenChange, 
  onConfirm, 
  loading 
}: { 
  open: boolean, 
  onOpenChange: (open: boolean) => void, 
  onConfirm: (data: { name: string, description: string }) => void,
  loading: boolean
}) {
  const { register, handleSubmit, reset } = useForm<{ name: string, description: string }>();

  useEffect(() => {
    if (open) reset({ name: "", description: "" });
  }, [open, reset]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New RAG Preset</DialogTitle>
          <DialogDescription>
            This will create a new preset using the current parameter values.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onConfirm)} className="space-y-4 py-4">
          <FormField label="Preset Name">
            <Input {...register("name", { required: true })} placeholder="e.g. High Precision" />
          </FormField>
          <FormField label="Description">
            <Input {...register("description")} placeholder="e.g. Optimized for academic papers" />
          </FormField>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && <Loader2Icon className="h-4 w-4 animate-spin mr-2" />}
              Create Preset
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
