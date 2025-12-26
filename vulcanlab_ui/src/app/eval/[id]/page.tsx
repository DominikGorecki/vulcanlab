"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { Flask, Trash2, Calendar, ListChecks, AlertCircle } from "lucide-react";
import {
  StickyDetailHeader,
  PageLoadingState,
  PageErrorState,
  ConfirmDialog,
  EmptyState,
} from "@/components";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { usePageData } from "@/hooks/use-page-data";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription } from "@/components/ui/alert";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ExperimentDetail {
  id: number;
  name: string;
  description_x: string | null;
  description_y: string | null;
  model_x: string | null;
  model_y: string | null;
  judge_model: string | null;
  eval_template_id: number | null;
  created_at: string;
  updated_at: string;
}

interface PageProps {
  params: {
    id: string;
  };
}

export default function ExperimentDetailPage({ params }: PageProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const fetchData = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/eval/experiments/${params.id}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Experiment not found");
      }
      throw new Error("Failed to load experiment");
    }

    const experiment: ExperimentDetail = await response.json();
    return experiment;
  }, [params.id]);

  const { data, loading, error, refetch } = usePageData<ExperimentDetail>(fetchData);

  const handleDelete = async () => {
    setDeleting(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/eval/experiments/${params.id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete experiment");
      }

      toast({
        title: "Experiment deleted",
        description: "The experiment and all associated data have been deleted.",
      });

      router.push("/eval");
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to delete experiment",
        variant: "destructive",
      });
      setDeleting(false);
      setDeleteDialogOpen(false);
    }
  };

  if (loading) {
    return <PageLoadingState title="Loading experiment..." />;
  }

  if (error) {
    return <PageErrorState error={error} onRetry={refetch} />;
  }

  if (!data) {
    return null;
  }

  return (
    <div className="container mx-auto p-6">
      <StickyDetailHeader
        title={data.name}
        subtitle={`Created ${new Date(data.created_at).toLocaleDateString()}`}
        icon={<Flask className="h-6 w-6" />}
        backHref="/eval"
        backLabel="Back to Experiments"
        actions={[
          {
            label: "Delete",
            variant: "destructive",
            onClick: () => setDeleteDialogOpen(true),
            icon: <Trash2 className="h-4 w-4" />,
          },
        ]}
      />

      <div className="space-y-6">
        {/* Experiment Metadata */}
        <Card>
          <CardHeader>
            <CardTitle>Experiment Configuration</CardTitle>
            <CardDescription>
              Details about this evaluation experiment
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-1">Answer Set X</h3>
                  <p className="text-base">
                    {data.description_x || <span className="text-muted-foreground italic">Not specified</span>}
                  </p>
                  {data.model_x && (
                    <p className="text-sm text-muted-foreground mt-1">Model: {data.model_x}</p>
                  )}
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-1">Answer Set Y</h3>
                  <p className="text-base">
                    {data.description_y || <span className="text-muted-foreground italic">Not specified</span>}
                  </p>
                  {data.model_y && (
                    <p className="text-sm text-muted-foreground mt-1">Model: {data.model_y}</p>
                  )}
                </div>
              </div>
            </div>

            <div className="pt-4 border-t">
              <h3 className="text-sm font-medium text-muted-foreground mb-1">Judge Model</h3>
              <p className="text-base">
                {data.judge_model || <span className="text-muted-foreground italic">Not specified</span>}
              </p>
            </div>

            <div className="pt-4 border-t">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span>Created: {new Date(data.created_at).toLocaleString()}</span>
              </div>
              {data.updated_at !== data.created_at && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                  <Calendar className="h-4 w-4" />
                  <span>Updated: {new Date(data.updated_at).toLocaleString()}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Stats Placeholder (T05) */}
        <Card>
          <CardHeader>
            <CardTitle>Statistics</CardTitle>
            <CardDescription>
              Evaluation results and statistical analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Statistical analysis will be available after evaluations are completed (T05).
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>

        {/* Prompts Placeholder (T03) */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ListChecks className="h-5 w-5" />
              Prompts
            </CardTitle>
            <CardDescription>
              Test prompts for this experiment
            </CardDescription>
          </CardHeader>
          <CardContent>
            <EmptyState
              title="No prompts yet"
              description="Add prompts to start evaluating answers (T03)"
              compact
            />
          </CardContent>
        </Card>
      </div>

      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Experiment"
        description="Are you sure you want to delete this experiment? This will permanently delete all associated prompts, answers, and evaluations. This action cannot be undone."
        confirmLabel="Delete Experiment"
        variant="destructive"
        onConfirm={handleDelete}
        loading={deleting}
      />
    </div>
  );
}
