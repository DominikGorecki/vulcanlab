"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Loader2Icon, AlertCircle, CheckCircle2, Star, Copy, Trash2 } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import type {
  RagConfig,
  RagConfigParams,
  RagConfigCreateRequest,
  RagConfigUpdateRequest,
  RetrievalParams,
  ConsolidationParams,
  AugmentationParams,
} from "@/types/rag-config";
import { PARAM_CONSTRAINTS, getDefaultConfig } from "@/types/rag-config";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function RagConfigTab() {
  // State management
  const [presets, setPresets] = useState<RagConfig[]>([]);
  const [selectedPresetName, setSelectedPresetName] = useState<string | null>(null);
  const [currentConfig, setCurrentConfig] = useState<RagConfigParams | null>(null);
  const [originalConfig, setOriginalConfig] = useState<RagConfigParams | null>(null);
  const [description, setDescription] = useState<string>("");
  const [originalDescription, setOriginalDescription] = useState<string>("");

  // UI state
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Dialog state
  const [showNewPresetDialog, setShowNewPresetDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [newPresetName, setNewPresetName] = useState("");
  const [newPresetDescription, setNewPresetDescription] = useState("");

  // Fetch presets on mount
  useEffect(() => {
    fetchPresets();
  }, []);

  // Fetch all presets
  const fetchPresets = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/rag-config/`);
      if (!response.ok) {
        throw new Error(`Failed to fetch presets: ${response.statusText}`);
      }
      const data: RagConfig[] = await response.json();
      setPresets(data);

      // Select default preset if none selected
      if (!selectedPresetName && data.length > 0) {
        const defaultPreset = data.find((p) => p.is_default) || data[0];
        loadPreset(defaultPreset);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load presets");
    } finally {
      setLoading(false);
    }
  };

  // Load a preset into the form
  const loadPreset = (preset: RagConfig) => {
    setSelectedPresetName(preset.preset_name);
    setCurrentConfig(preset.config);
    setOriginalConfig(JSON.parse(JSON.stringify(preset.config))); // Deep copy
    setDescription(preset.description || "");
    setOriginalDescription(preset.description || "");
    setSaveSuccess(false);
  };

  // Handle preset selection change
  const handlePresetChange = (presetName: string) => {
    const preset = presets.find((p) => p.preset_name === presetName);
    if (preset) {
      loadPreset(preset);
    }
  };

  // Create new preset
  const handleCreatePreset = async () => {
    if (!newPresetName.trim()) {
      setError("Preset name is required");
      return;
    }

    try {
      setSaving(true);
      setError(null);

      const createRequest: RagConfigCreateRequest = {
        preset_name: newPresetName,
        description: newPresetDescription || undefined,
        is_default: false,
        config: currentConfig || getDefaultConfig(),
      };

      const response = await fetch(`${API_BASE_URL}/api/rag-config/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(createRequest),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create preset: ${response.statusText}`);
      }

      const newPreset: RagConfig = await response.json();

      // Refresh and select new preset
      await fetchPresets();
      loadPreset(newPreset);

      // Reset dialog
      setShowNewPresetDialog(false);
      setNewPresetName("");
      setNewPresetDescription("");
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create preset");
    } finally {
      setSaving(false);
    }
  };

  // Save current preset
  const handleSavePreset = async () => {
    if (!selectedPresetName || !currentConfig) return;

    try {
      setSaving(true);
      setError(null);

      const updateRequest: RagConfigUpdateRequest = {
        description: description || undefined,
        config: currentConfig,
      };

      const response = await fetch(
        `${API_BASE_URL}/api/rag-config/${encodeURIComponent(selectedPresetName)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updateRequest),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to save preset: ${response.statusText}`);
      }

      const updatedPreset: RagConfig = await response.json();

      // Update local state
      setOriginalConfig(JSON.parse(JSON.stringify(currentConfig)));
      setOriginalDescription(description);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);

      // Refresh preset list
      await fetchPresets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save preset");
    } finally {
      setSaving(false);
    }
  };

  // Set preset as default
  const handleSetDefault = async () => {
    if (!selectedPresetName) return;

    try {
      setSaving(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/rag-config/${encodeURIComponent(selectedPresetName)}/set-default`,
        { method: "PUT" }
      );

      if (!response.ok) {
        throw new Error(`Failed to set default: ${response.statusText}`);
      }

      await fetchPresets();
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to set default");
    } finally {
      setSaving(false);
    }
  };

  // Delete preset
  const handleDeletePreset = async () => {
    if (!selectedPresetName) return;

    try {
      setSaving(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/rag-config/${encodeURIComponent(selectedPresetName)}`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete preset: ${response.statusText}`);
      }

      // Refresh and select default
      await fetchPresets();
      setShowDeleteDialog(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete preset");
    } finally {
      setSaving(false);
    }
  };

  // Reset to original values
  const handleReset = () => {
    if (originalConfig) {
      setCurrentConfig(JSON.parse(JSON.stringify(originalConfig)));
      setDescription(originalDescription);
    }
  };

  // Check if form has unsaved changes
  const hasUnsavedChanges = () => {
    if (!originalConfig || !currentConfig) return false;
    return (
      JSON.stringify(currentConfig) !== JSON.stringify(originalConfig) ||
      description !== originalDescription
    );
  };

  // Update retrieval parameter
  const updateRetrievalParam = <K extends keyof RetrievalParams>(
    key: K,
    value: RetrievalParams[K]
  ) => {
    if (!currentConfig) return;
    setCurrentConfig({
      ...currentConfig,
      retrieval: { ...currentConfig.retrieval, [key]: value },
    });
  };

  // Update consolidation parameter
  const updateConsolidationParam = <K extends keyof ConsolidationParams>(
    key: K,
    value: ConsolidationParams[K]
  ) => {
    if (!currentConfig) return;
    setCurrentConfig({
      ...currentConfig,
      consolidation: { ...currentConfig.consolidation, [key]: value },
    });
  };

  // Update augmentation parameter
  const updateAugmentationParam = <K extends keyof AugmentationParams>(
    key: K,
    value: AugmentationParams[K]
  ) => {
    if (!currentConfig) return;
    setCurrentConfig({
      ...currentConfig,
      augmentation: { ...currentConfig.augmentation, [key]: value },
    });
  };

  // Get current preset
  const currentPreset = presets.find((p) => p.preset_name === selectedPresetName);
  const isDefault = currentPreset?.is_default || false;

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6 flex items-center justify-center">
          <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header Card - Preset Selector */}
      <Card>
        <CardHeader>
          <CardTitle>RAG Configuration Presets</CardTitle>
          <CardDescription>
            Manage retrieval, consolidation, and augmentation parameters. Changes affect how the RAG
            pipeline processes queries.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {saveSuccess && (
            <Alert className="border-emerald-500/20 bg-emerald-500/10">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <AlertDescription className="text-emerald-500">
                Changes saved successfully
              </AlertDescription>
            </Alert>
          )}

          <div className="flex items-center gap-3">
            <div className="flex-1">
              <Label htmlFor="preset-select">Active Preset</Label>
              <div className="flex items-center gap-2 mt-1.5">
                <Select value={selectedPresetName || ""} onValueChange={handlePresetChange}>
                  <SelectTrigger id="preset-select" className="w-full">
                    <SelectValue placeholder="Select preset..." />
                  </SelectTrigger>
                  <SelectContent>
                    {presets.map((preset) => (
                      <SelectItem key={preset.id} value={preset.preset_name}>
                        <div className="flex items-center gap-2">
                          {preset.preset_name}
                          {preset.is_default && (
                            <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex gap-2 pt-6">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setShowNewPresetDialog(true)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Duplicate current preset</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              {!isDefault && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button variant="outline" size="icon" onClick={handleSetDefault}>
                        <Star className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Set as default preset</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe this preset's purpose..."
            />
          </div>
        </CardContent>
      </Card>

      {/* Parameters Card */}
      {currentConfig && (
        <Card>
          <CardHeader>
            <CardTitle>Parameters</CardTitle>
            <CardDescription>Configure RAG pipeline behavior</CardDescription>
          </CardHeader>
          <CardContent>
            <Accordion type="multiple" defaultValue={["retrieval"]} className="w-full">
              {/* Retrieval Section */}
              <AccordionItem value="retrieval">
                <AccordionTrigger className="text-lg font-semibold">
                  Retrieval Parameters
                </AccordionTrigger>
                <AccordionContent className="space-y-4 pt-4">
                  {/* Number inputs for retrieval params */}
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(PARAM_CONSTRAINTS.retrieval).map(([key, constraint]) => {
                      const typedKey = key as keyof RetrievalParams;
                      const value = currentConfig.retrieval[typedKey];

                      // Float parameters use slider + input
                      if ("step" in constraint && constraint.step) {
                        return (
                          <div key={key} className="space-y-2 col-span-2">
                            <div className="flex justify-between">
                              <Label htmlFor={`retrieval-${key}`}>
                                {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                              </Label>
                              <span className="text-sm text-muted-foreground">
                                {typeof value === "number" ? value.toFixed(2) : "0.00"}
                              </span>
                            </div>
                            <Slider
                              id={`retrieval-${key}`}
                              min={constraint.min}
                              max={constraint.max}
                              step={constraint.step}
                              value={[typeof value === "number" ? value : constraint.default]}
                              onValueChange={([v]) => updateRetrievalParam(typedKey, v as never)}
                            />
                            <p className="text-xs text-muted-foreground">
                              {constraint.description}
                            </p>
                          </div>
                        );
                      }

                      // Integer parameters use number input
                      return (
                        <div key={key} className="space-y-2">
                          <Label htmlFor={`retrieval-${key}`}>
                            {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                          </Label>
                          <Input
                            id={`retrieval-${key}`}
                            type="number"
                            min={constraint.min}
                            max={constraint.max}
                            value={value ?? ""}
                            onChange={(e) => {
                              const val = parseInt(e.target.value);
                              if (!isNaN(val)) {
                                updateRetrievalParam(typedKey, val as never);
                              }
                            }}
                          />
                          <p className="text-xs text-muted-foreground">
                            {constraint.description}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Consolidation Section */}
              <AccordionItem value="consolidation">
                <AccordionTrigger className="text-lg font-semibold">
                  Consolidation Parameters
                </AccordionTrigger>
                <AccordionContent className="space-y-4 pt-4">
                  <div className="grid grid-cols-2 gap-4">
                    {/* coverage_threshold - slider */}
                    <div className="space-y-2 col-span-2">
                      <div className="flex justify-between">
                        <Label>Coverage Threshold</Label>
                        <span className="text-sm text-muted-foreground">
                          {typeof currentConfig.consolidation.coverage_threshold === "number"
                            ? currentConfig.consolidation.coverage_threshold.toFixed(2)
                            : "0.00"}
                        </span>
                      </div>
                      <Slider
                        min={PARAM_CONSTRAINTS.consolidation.coverage_threshold.min}
                        max={PARAM_CONSTRAINTS.consolidation.coverage_threshold.max}
                        step={PARAM_CONSTRAINTS.consolidation.coverage_threshold.step}
                        value={[typeof currentConfig.consolidation.coverage_threshold === "number"
                          ? currentConfig.consolidation.coverage_threshold
                          : PARAM_CONSTRAINTS.consolidation.coverage_threshold.default]}
                        onValueChange={([v]) => updateConsolidationParam("coverage_threshold", v)}
                      />
                      <p className="text-xs text-muted-foreground">
                        {PARAM_CONSTRAINTS.consolidation.coverage_threshold.description}
                      </p>
                    </div>

                    {/* line_gap */}
                    <div className="space-y-2">
                      <Label>Line Gap</Label>
                      <Input
                        type="number"
                        min={PARAM_CONSTRAINTS.consolidation.line_gap.min}
                        max={PARAM_CONSTRAINTS.consolidation.line_gap.max}
                        value={currentConfig.consolidation.line_gap ?? ""}
                        onChange={(e) => {
                          const val = parseInt(e.target.value);
                          if (!isNaN(val)) {
                            updateConsolidationParam("line_gap", val);
                          }
                        }}
                      />
                      <p className="text-xs text-muted-foreground">
                        {PARAM_CONSTRAINTS.consolidation.line_gap.description}
                      </p>
                    </div>

                    {/* min_content_length */}
                    <div className="space-y-2">
                      <Label>Min Content Length</Label>
                      <Input
                        type="number"
                        min={PARAM_CONSTRAINTS.consolidation.min_content_length.min}
                        max={PARAM_CONSTRAINTS.consolidation.min_content_length.max}
                        value={currentConfig.consolidation.min_content_length ?? ""}
                        onChange={(e) => {
                          const val = parseInt(e.target.value);
                          if (!isNaN(val)) {
                            updateConsolidationParam("min_content_length", val);
                          }
                        }}
                      />
                      <p className="text-xs text-muted-foreground">
                        {PARAM_CONSTRAINTS.consolidation.min_content_length.description}
                      </p>
                    </div>

                    {/* enrich_from_md - toggle */}
                    <div className="space-y-2 col-span-2">
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <Label>Enrich From Markdown</Label>
                          <p className="text-xs text-muted-foreground">
                            {PARAM_CONSTRAINTS.consolidation.enrich_from_md.description}
                          </p>
                        </div>
                        <Switch
                          checked={currentConfig.consolidation.enrich_from_md}
                          onCheckedChange={(checked) =>
                            updateConsolidationParam("enrich_from_md", checked)
                          }
                        />
                      </div>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Augmentation Section */}
              <AccordionItem value="augmentation">
                <AccordionTrigger className="text-lg font-semibold">
                  Augmentation Parameters
                </AccordionTrigger>
                <AccordionContent className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label>Top N Contexts</Label>
                    <Input
                      type="number"
                      min={PARAM_CONSTRAINTS.augmentation.top_n_contexts.min}
                      max={PARAM_CONSTRAINTS.augmentation.top_n_contexts.max}
                      value={currentConfig.augmentation.top_n_contexts ?? ""}
                      onChange={(e) => {
                        const val = parseInt(e.target.value);
                        if (!isNaN(val)) {
                          updateAugmentationParam("top_n_contexts", val);
                        }
                      }}
                    />
                    <p className="text-xs text-muted-foreground">
                      {PARAM_CONSTRAINTS.augmentation.top_n_contexts.description}
                    </p>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <Button onClick={handleSavePreset} disabled={saving || !hasUnsavedChanges()}>
                {saving ? (
                  <>
                    <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                    Saving...
                  </>
                ) : (
                  "Save Changes"
                )}
              </Button>
              <Button
                variant="outline"
                onClick={handleReset}
                disabled={!hasUnsavedChanges()}
              >
                Reset
              </Button>
            </div>

            {!isDefault && (
              <Button
                variant="destructive"
                onClick={() => setShowDeleteDialog(true)}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete Preset
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* New Preset Dialog */}
      <AlertDialog open={showNewPresetDialog} onOpenChange={setShowNewPresetDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Create New Preset</AlertDialogTitle>
            <AlertDialogDescription>
              Create a new preset based on the current configuration.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="new-preset-name">Preset Name</Label>
              <Input
                id="new-preset-name"
                value={newPresetName}
                onChange={(e) => setNewPresetName(e.target.value)}
                placeholder="e.g., Fast Retrieval"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-preset-description">Description</Label>
              <Input
                id="new-preset-description"
                value={newPresetDescription}
                onChange={(e) => setNewPresetDescription(e.target.value)}
                placeholder="Describe the preset..."
              />
            </div>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleCreatePreset}>Create</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Preset</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &quot;{selectedPresetName}&quot;? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeletePreset} className="bg-destructive">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
