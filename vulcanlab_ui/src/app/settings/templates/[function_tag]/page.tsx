"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Loader2Icon, ChevronLeft, Save, CheckCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { usePageData } from "@/hooks";
import { PageHeader, PageLoadingState, PageErrorState, FormField } from "@/components";
import { useForm } from "react-hook-form";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PromptVariable {
  variable_name: string;
  variable_description: string;
}

interface TemplateVersion {
  id: number;
  function_tag: string;
  version: number;
  title: string;
  template_content: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  variables?: PromptVariable[] | null;
}

const FUNCTION_LABELS: Record<string, string> = {
  query_expansion: "Query Expansion",
  rag_augmentation: "RAG Augmented Prompt",
  vectorization_suggestions: "Vectorization Suggestions",
  heading_hierarchy: "Heading Hierarchy Corrections",
  summarize_node: "Summarization - Node Summary",
  synthesize_abstract: "Summarization - Abstract",
  organize_key_concepts: "Summarization - Key Concepts",
};

export default function TemplateEditorPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const function_tag = params.function_tag as string;

  const fetchVersionsFn = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/settings/templates/${function_tag}`);
    if (!response.ok) throw new Error(`Failed to fetch templates: ${response.statusText}`);
    return response.json();
  }, [function_tag]);

  const { data: versions, loading, error, refetch: fetchVersions } = usePageData<TemplateVersion[]>(
    fetchVersionsFn
  );

  const [selectedVersion, setSelectedVersion] = useState<number | "new">("new");
  const [saving, setSaving] = useState(false);
  const [activating, setActivating] = useState(false);

  const { register, handleSubmit, reset, watch, formState: { isDirty } } = useForm({
    defaultValues: {
      title: "",
      template_content: ""
    }
  });

  useEffect(() => {
    if (versions && versions.length > 0 && selectedVersion === "new") {
      const active = versions.find(v => v.is_active) || versions[0];
      setSelectedVersion(active.version);
    }
  }, [versions]);

  useEffect(() => {
    if (selectedVersion === "new") {
      reset({ title: "", template_content: "" });
    } else if (versions) {
      const v = versions.find(ver => ver.version === selectedVersion);
      if (v) reset({ title: v.title, template_content: v.template_content });
    }
  }, [selectedVersion, versions, reset]);

  const onSave = async (formData: { title: string, template_content: string }) => {
    try {
      setSaving(true);
      const url = selectedVersion === "new" 
        ? `${API_BASE_URL}/settings/templates/${function_tag}` 
        : `${API_BASE_URL}/settings/templates/${function_tag}/${selectedVersion}`;
      const method = selectedVersion === "new" ? "POST" : "PUT";

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error("Failed to save template");
      
      const saved = await response.json();
      toast({ title: "Success", description: "Template saved successfully" });
      await fetchVersions();
      if (selectedVersion === "new") setSelectedVersion(saved.version);
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Save failed", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const handleActivate = async () => {
    if (selectedVersion === "new") return;
    try {
      setActivating(true);
      const response = await fetch(`${API_BASE_URL}/settings/templates/${function_tag}/${selectedVersion}/activate`, { method: "PUT" });
      if (!response.ok) throw new Error("Activation failed");
      toast({ title: "Success", description: "Template activated" });
      fetchVersions();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Activation failed", variant: "destructive" });
    } finally {
      setActivating(false);
    }
  };

  if (loading) return <PageLoadingState />;
  if (error) return <PageErrorState title="Templates Error" error={error} onRetry={fetchVersions} />;

  const functionLabel = FUNCTION_LABELS[function_tag] || function_tag;
  const currentV = versions?.find(v => v.version === selectedVersion);
  const variables = versions?.[0]?.variables || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/settings?tab=templates")}>
          <ChevronLeft className="h-4 w-4 mr-2" />
          Back to Templates
        </Button>
      </div>

      <PageHeader 
        title={functionLabel} 
        description="Edit prompt templates for this function."
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Template Editor</CardTitle>
                <Select value={selectedVersion.toString()} onValueChange={v => setSelectedVersion(v === "new" ? "new" : parseInt(v))}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="new">Add New Version</SelectItem>
                    {versions?.map(v => (
                      <SelectItem key={v.version} value={v.version.toString()}>
                        v{v.version} {v.is_active ? "(Active)" : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField label="Title">
                <Input {...register("title")} />
              </FormField>
              <div className="space-y-2">
                <Label>Template Content</Label>
                <Textarea 
                  {...register("template_content")} 
                  className="font-mono min-h-[400px]" 
                  placeholder="Enter template with {variable} placeholders"
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={handleSubmit(onSave)} disabled={saving || !isDirty}>
                  {saving && <Loader2Icon className="h-4 w-4 animate-spin mr-2" />}
                  Save Version
                </Button>
                {selectedVersion !== "new" && !currentV?.is_active && (
                  <Button variant="outline" onClick={handleActivate} disabled={activating || isDirty}>
                    {activating && <Loader2Icon className="h-4 w-4 animate-spin mr-2" />}
                    Set as Active
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Variables</CardTitle>
              <CardDescription>Available placeholders</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {variables.length > 0 ? (
                variables.map((v, i) => (
                  <div key={i} className="border-l-2 border-primary pl-3">
                    <code className="text-sm font-mono font-semibold text-primary">{`{${v.variable_name}}`}</code>
                    <p className="text-xs text-muted-foreground mt-1">{v.variable_description}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No variables defined.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
