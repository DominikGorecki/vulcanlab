"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Loader2Icon, AlertCircle, PenSquare } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface TemplateSummary {
  version: number;
  title: string;
  is_active: boolean;
  created_at: string;
}

interface FunctionTemplateSummary {
  function_tag: string;
  active_version: number | null;
  versions: TemplateSummary[];
}

interface TemplateListResponse {
  templates: FunctionTemplateSummary[];
}

// Human-readable labels for function tags
const FUNCTION_LABELS: Record<string, string> = {
  query_expansion: "Query Expansion",
  rag_augmentation: "RAG Augmented Prompt",
  vectorization_suggestions: "Vectorization Suggestions",
  heading_hierarchy: "Heading Hierarchy Corrections",
  toc_extraction: "Manual ToC Extraction",
};

export function TemplatesTabContent() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [templates, setTemplates] = useState<FunctionTemplateSummary[]>([]);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/settings/templates/`);
      if (!response.ok) {
        throw new Error(`Failed to fetch templates: ${response.statusText}`);
      }
      const data: TemplateListResponse = await response.json();
      setTemplates(data.templates);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load templates");
    } finally {
      setLoading(false);
    }
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
          <Button onClick={fetchTemplates} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Prompt Templates</CardTitle>
        <CardDescription>
          Manage versioned prompt templates for AI functions. Click a function to edit its templates.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Function</TableHead>
              <TableHead>Active Version</TableHead>
              <TableHead>Total Versions</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {templates.map((template) => (
              <TableRow key={template.function_tag}>
                <TableCell className="font-medium">
                  {FUNCTION_LABELS[template.function_tag] || template.function_tag}
                </TableCell>
                <TableCell>
                  {template.active_version ? (
                    <Badge variant="default">v{template.active_version}</Badge>
                  ) : (
                    <span className="text-muted-foreground text-sm">No active version</span>
                  )}
                </TableCell>
                <TableCell>
                  <span className="text-sm text-muted-foreground">
                    {template.versions.length} version{template.versions.length !== 1 ? 's' : ''}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push(`/settings/templates/${template.function_tag}`)}
                  >
                    <PenSquare className="h-4 w-4 mr-2" />
                    Edit
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
