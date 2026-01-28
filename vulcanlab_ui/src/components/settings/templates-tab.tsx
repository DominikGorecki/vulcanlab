"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { PenSquare } from "lucide-react";
import { usePageData } from "@/hooks";
import { PageLoadingState, PageErrorState } from "@/components";

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

const FUNCTION_LABELS: Record<string, string> = {
  query_expansion: "Query Expansion",
  rag_augmentation: "RAG Augmented Prompt",
  vectorization_suggestions: "Vectorization Suggestions",
  heading_hierarchy: "Heading Hierarchy Corrections",
  toc_extraction: "Manual ToC Extraction",
  summarize_sections: "Section Summarization",
  answer_breakdown: "Answer Breakdown",
  expansion_section_generation: "Expansion Section Generation",
};

export function TemplatesTabContent() {
  const router = useRouter();
  const fetchTemplatesFn = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/settings/templates/`);
    if (!response.ok) throw new Error(`Failed to fetch templates: ${response.statusText}`);
    return response.json();
  }, []);

  const { data, loading, error, refetch: fetchTemplates } = usePageData<TemplateListResponse>(
    fetchTemplatesFn
  );

  if (loading) return <PageLoadingState />;
  if (error) return <PageErrorState title="Failed to load templates" error={error} onRetry={fetchTemplates} />;

  const templates = data?.templates || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Prompt Templates</CardTitle>
        <CardDescription>
          Manage versioned prompt templates for AI functions.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Function</TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Active Version</TableHead>
              <TableHead>Total Versions</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {templates.map((template) => {
              const activeTemplate = template.versions.find(v => v.is_active);
              return (
                <TableRow key={template.function_tag}>
                  <TableCell className="font-medium">
                    {FUNCTION_LABELS[template.function_tag] || template.function_tag}
                  </TableCell>
                  <TableCell>
                    {activeTemplate ? (
                      <span className="text-sm">{activeTemplate.title}</span>
                    ) : (
                      <span className="text-muted-foreground text-sm">No active template</span>
                    )}
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
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
