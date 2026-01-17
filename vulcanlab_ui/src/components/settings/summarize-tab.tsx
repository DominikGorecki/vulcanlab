"use client";

import { useState, useCallback, useEffect } from "react";
import { useForm } from "react-hook-form";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2Icon } from "lucide-react";
import { usePageData } from "@/hooks";
import { PageLoadingState, PageErrorState, FormField } from "@/components";
import { useToast } from "@/hooks/use-toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SummarizeSettings {
  min_heading_word_count: number;
  max_total_heading_words: number;
  dense_top_k: number;
  lexical_top_k: number;
  rrf_k: number;
  rrf_top_k: number;
  mmr_lambda: number;
  mmr_top_n: number;
  max_llm_calls: number;
  max_tokens_per_call: number;
  tokens_per_word: number;
  h1_h2_min_chunks: number;
  h3_min_chunks: number;
}

export function SummarizeTab() {
  const { toast } = useToast();
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const fetchSettingsFn = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/summarize/settings`);
    if (!response.ok) throw new Error(`Failed to fetch settings: ${response.statusText}`);
    return response.json();
  }, []);

  const { data: settings, loading, error, refetch: fetchSettings } = usePageData<SummarizeSettings>(
    fetchSettingsFn
  );

  const { register, handleSubmit, reset, formState: { errors, isDirty } } = useForm<SummarizeSettings>();

  useEffect(() => {
    if (settings) {
      reset(settings);
    }
  }, [settings, reset]);

  const onSave = async (formData: SummarizeSettings) => {
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/summarize/settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error("Failed to save summarization settings");
      }

      setSaveSuccess(true);
      toast({
        title: "Settings saved",
        description: "Summarization parameters have been updated.",
      });
      setTimeout(() => setSaveSuccess(false), 2000);
      fetchSettings();
    } catch (err) {
      toast({
        title: "Save failed",
        description: err instanceof Error ? err.message : "An error occurred",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <PageLoadingState />;
  if (error) return <PageErrorState title="Settings Error" error={error} onRetry={fetchSettings} />;

  return (
    <div className="space-y-6 pb-12">
      <div className="grid gap-6 md:grid-cols-2">
        {/* Heading Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Heading Selection</CardTitle>
            <CardDescription>Configure how document headings are selected for summarization.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField 
              label="Min Heading Word Count" 
              description="Minimum words in heading content to include in summarization."
              error={errors.min_heading_word_count?.message}
            >
              <Input 
                type="number" 
                {...register("min_heading_word_count", { 
                  required: "Required",
                  min: { value: 1, message: "Must be positive" },
                  valueAsNumber: true 
                })} 
              />
            </FormField>
            <FormField 
              label="Max Total Heading Words" 
              description="Upper limit on words processed across all headings."
              error={errors.max_total_heading_words?.message}
            >
              <Input 
                type="number" 
                {...register("max_total_heading_words", { 
                  required: "Required",
                  min: { value: 1, message: "Must be positive" },
                  valueAsNumber: true 
                })} 
              />
            </FormField>
          </CardContent>
        </Card>

        {/* Search & Ranking */}
        <Card>
          <CardHeader>
            <CardTitle>Search & Ranking</CardTitle>
            <CardDescription>Tweak retrieval and diversity parameters.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField label="Dense Top K" error={errors.dense_top_k?.message}>
                <Input type="number" {...register("dense_top_k", { required: "Required", min: 1, valueAsNumber: true })} />
              </FormField>
              <FormField label="Lexical Top K" error={errors.lexical_top_k?.message}>
                <Input type="number" {...register("lexical_top_k", { required: "Required", min: 1, valueAsNumber: true })} />
              </FormField>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <FormField label="RRF K" description="Fusion constant" error={errors.rrf_k?.message}>
                <Input type="number" {...register("rrf_k", { required: "Required", min: 1, valueAsNumber: true })} />
              </FormField>
              <FormField label="RRF Top K" description="Candidates after fusion" error={errors.rrf_top_k?.message}>
                <Input type="number" {...register("rrf_top_k", { required: "Required", min: 1, valueAsNumber: true })} />
              </FormField>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <FormField 
                label="MMR Lambda" 
                description="Relevance (1.0) vs Diversity (0.0)"
                error={errors.mmr_lambda?.message}
              >
                <Input 
                  type="number" 
                  step="0.1" 
                  {...register("mmr_lambda", { 
                    required: "Required",
                    min: { value: 0, message: "Min 0" },
                    max: { value: 1, message: "Max 1" },
                    valueAsNumber: true 
                  })} 
                />
              </FormField>
              <FormField label="MMR Top N" description="Final chunk count" error={errors.mmr_top_n?.message}>
                <Input type="number" {...register("mmr_top_n", { required: "Required", min: 1, valueAsNumber: true })} />
              </FormField>
            </div>
          </CardContent>
        </Card>

        {/* Token Budget */}
        <Card>
          <CardHeader>
            <CardTitle>Token Budget</CardTitle>
            <CardDescription>Control LLM usage and cost.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField label="Max LLM Calls" error={errors.max_llm_calls?.message}>
              <Input type="number" {...register("max_llm_calls", { required: "Required", min: 1, valueAsNumber: true })} />
            </FormField>
            <FormField label="Max Tokens Per Call" error={errors.max_tokens_per_call?.message}>
              <Input type="number" {...register("max_tokens_per_call", { required: "Required", min: 1, valueAsNumber: true })} />
            </FormField>
            <FormField 
              label="Tokens Per Word" 
              description="Used for budget estimation."
              error={errors.tokens_per_word?.message}
            >
              <Input 
                type="number" 
                step="0.05" 
                {...register("tokens_per_word", { 
                  required: "Required",
                  min: { value: 0.1, message: "Min 0.1" },
                  valueAsNumber: true 
                })} 
              />
            </FormField>
          </CardContent>
        </Card>

        {/* Pruning Minimums */}
        <Card>
          <CardHeader>
            <CardTitle>Pruning Minimums</CardTitle>
            <CardDescription>Minimum chunks required to attempt summarization.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField label="H1/H2 Min Chunks" error={errors.h1_h2_min_chunks?.message}>
              <Input type="number" {...register("h1_h2_min_chunks", { required: "Required", min: 0, valueAsNumber: true })} />
            </FormField>
            <FormField label="H3 Min Chunks" error={errors.h3_min_chunks?.message}>
              <Input type="number" {...register("h3_min_chunks", { required: "Required", min: 0, valueAsNumber: true })} />
            </FormField>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6 flex justify-between">
          <div className="flex gap-2">
            <Button onClick={handleSubmit(onSave)} disabled={saving || !isDirty}>
              {saving && <Loader2Icon className="h-4 w-4 animate-spin mr-2" />}
              {saveSuccess ? "Saved!" : "Save Changes"}
            </Button>
            <Button variant="outline" onClick={() => reset()} disabled={saving || !isDirty}>Reset</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
