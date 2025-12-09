"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Loader2Icon, AlertCircle, ChevronLeft, Save, CheckCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

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

// Human-readable labels for function tags
const FUNCTION_LABELS: Record<string, string> = {
  query_expansion: "Query Expansion",
  rag_augmentation: "RAG Augmented Prompt",
  vectorization_suggestions: "Vectorization Suggestions",
  heading_hierarchy: "Heading Hierarchy Corrections",
};

export default function TemplateEditorPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const function_tag = params.function_tag as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [versions, setVersions] = useState<TemplateVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number | "new">("new");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isActive, setIsActive] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [activating, setActivating] = useState(false);
  const [variables, setVariables] = useState<PromptVariable[] | null>(null);

  useEffect(() => {
    fetchVersions();
  }, [function_tag]);

  useEffect(() => {
    if (selectedVersion === "new") {
      setTitle("");
      setContent("");
      setIsActive(false);
      setIsDirty(false);
    } else if (selectedVersion) {
      const version = versions.find((v) => v.version === selectedVersion);
      if (version) {
        setTitle(version.title);
        setContent(version.template_content);
        setIsActive(version.is_active);
        setIsDirty(false);
      }
    }
  }, [selectedVersion, versions]);

  const fetchVersions = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/settings/templates/${function_tag}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch templates: ${response.statusText}`);
      }
      const data: TemplateVersion[] = await response.json();
      setVersions(data);

      // Extract variables from the first template (all versions share same variables)
      if (data.length > 0 && data[0].variables) {
        setVariables(data[0].variables);
      }

      // Select the active version or the latest version
      const activeVersion = data.find((v) => v.is_active);
      if (activeVersion) {
        setSelectedVersion(activeVersion.version);
      } else if (data.length > 0) {
        setSelectedVersion(data[0].version);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load templates");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);

      if (selectedVersion === "new") {
        // Create new version
        const response = await fetch(`${API_BASE_URL}/settings/templates/${function_tag}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            title,
            template_content: content,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Failed to create template");
        }

        const newVersion: TemplateVersion = await response.json();

        toast({
          title: "Template created",
          description: `Version ${newVersion.version} created successfully`,
        });

        // Refresh versions and select the new one
        await fetchVersions();
        setSelectedVersion(newVersion.version);
      } else {
        // Update existing version
        const response = await fetch(
          `${API_BASE_URL}/settings/templates/${function_tag}/${selectedVersion}`,
          {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              title,
              template_content: content,
            }),
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Failed to update template");
        }

        toast({
          title: "Template updated",
          description: `Version ${selectedVersion} updated successfully`,
        });

        await fetchVersions();
      }

      setIsDirty(false);
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to save template",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleActivate = async () => {
    if (selectedVersion === "new") return;

    try {
      setActivating(true);

      const response = await fetch(
        `${API_BASE_URL}/settings/templates/${function_tag}/${selectedVersion}/activate`,
        {
          method: "PUT",
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to activate template");
      }

      toast({
        title: "Template activated",
        description: `Version ${selectedVersion} is now active`,
      });

      await fetchVersions();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to activate template",
        variant: "destructive",
      });
    } finally {
      setActivating(false);
    }
  };

  const handleTitleChange = (value: string) => {
    setTitle(value);
    setIsDirty(true);
  };

  const handleContentChange = (value: string) => {
    setContent(value);
    setIsDirty(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
          <Button onClick={fetchVersions} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const functionLabel = FUNCTION_LABELS[function_tag] || function_tag;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push("/settings?tab=templates")}
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          Back to Templates
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{functionLabel}</CardTitle>
          <CardDescription>
            Edit prompt templates for this function. Select a version or create a new one.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Two-card layout: Version/Title on left, Variables on right */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left Card: Version and Title */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Template Info</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Version Selector */}
                <div className="space-y-2">
                  <Label htmlFor="version">Version</Label>
                  <div className="flex items-center gap-4">
                    <Select
                      value={selectedVersion.toString()}
                      onValueChange={(value) =>
                        setSelectedVersion(value === "new" ? "new" : parseInt(value))
                      }
                    >
                      <SelectTrigger id="version" className="w-[200px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="new">Add New Version</SelectItem>
                        {versions.map((version) => (
                          <SelectItem key={version.version} value={version.version.toString()}>
                            <div className="flex items-center gap-2">
                              v{version.version}
                              {version.is_active && (
                                <Badge variant="default" className="ml-2 text-xs">
                                  Active
                                </Badge>
                              )}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {isActive && selectedVersion !== "new" && (
                      <Badge variant="default">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Active Version
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Title Input */}
                <div className="space-y-2">
                  <Label htmlFor="title">Title</Label>
                  <Input
                    id="title"
                    value={title}
                    onChange={(e) => handleTitleChange(e.target.value)}
                    placeholder="Enter template title"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Right Card: Variables */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Template Variables</CardTitle>
                <CardDescription>
                  Variables available in this template
                </CardDescription>
              </CardHeader>
              <CardContent>
                {variables && variables.length > 0 ? (
                  <div className="space-y-3">
                    {variables.map((variable, index) => (
                      <div key={index} className="border-l-2 border-primary pl-3">
                        <code className="text-sm font-mono font-semibold text-primary">
                          {`{${variable.variable_name}}`}
                        </code>
                        <p className="text-sm text-muted-foreground mt-1">
                          {variable.variable_description}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No variable metadata available for this template.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Template Content */}
          <div className="space-y-2">
            <Label htmlFor="content">Template Content</Label>
            <Textarea
              id="content"
              value={content}
              onChange={(e) => handleContentChange(e.target.value)}
              placeholder="Enter template content with {variable} placeholders"
              className="font-mono min-h-[300px]"
            />
            <p className="text-sm text-muted-foreground">
              Use curly braces for variables, e.g., {"{variable_name}"}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-4">
            <Button
              onClick={handleSave}
              disabled={saving || !title || !content || !isDirty}
            >
              {saving ? (
                <>
                  <Loader2Icon className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save
                </>
              )}
            </Button>

            {selectedVersion !== "new" && !isActive && (
              <Button
                variant="outline"
                onClick={handleActivate}
                disabled={activating || isDirty}
              >
                {activating ? (
                  <>
                    <Loader2Icon className="h-4 w-4 mr-2 animate-spin" />
                    Activating...
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Set as Active
                  </>
                )}
              </Button>
            )}

            {isDirty && (
              <span className="text-sm text-muted-foreground">
                Unsaved changes
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
