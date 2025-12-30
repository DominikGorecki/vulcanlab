"use client";

import { use, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import {
  FlaskConical,
  Trash2,
  Download,
  Calendar,
  ListChecks,
  AlertCircle,
  Plus,
  Send,
  TrendingUp,
  TrendingDown,
  Target,
  BarChart3,
  Equal,
  AlertTriangle,
} from "lucide-react";
import {
  StickyDetailHeader,
  PageLoadingState,
  PageErrorState,
  ConfirmDialog,
  EmptyState,
  DataTable,
  StatsCardGrid,
  type DataTableColumn,
} from "@/components";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { usePageData } from "@/hooks/use-page-data";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AutoModeToggle } from "./auto-mode-toggle";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ExperimentStats {
  eval_count: number;
  x_win_rate: number;
  mean_score: number;
  median_score: number;
  tie_percentage: number;
  harm_rate: number;
  wilcoxon_p_value: number | null;
}

interface ExperimentDimension {
  id: number;
  experiment_id: number;
  dimension_name: string;
  display_order: number;
}

interface ExperimentDetail {
  id: number;
  name: string;
  description_x: string | null;
  description_y: string | null;
  model_x: string | null;
  model_y: string | null;
  judge_model: string | null;
  eval_template_id: number | null;
  auto_mode_enabled: boolean;
  auto_answer_provider: string | null;
  auto_judge_provider: string | null;
  created_at: string;
  updated_at: string;
  dimensions: ExperimentDimension[];
  stats?: ExperimentStats;
}

interface PromptListItem {
  id: number;
  experiment_id: number;
  prompt_text: string;
  created_at: string;
  eval_count: number;
}

interface PageProps {
  params: Promise<{
    id: string;
  }>;
}

interface PromptsTableProps {
  prompts: PromptListItem[];
  loading: boolean;
  onPromptClick: (prompt: PromptListItem) => void;
  onDeletePrompt: (prompt: PromptListItem) => void;
}

function PromptsTable({ prompts, loading, onPromptClick, onDeletePrompt }: PromptsTableProps) {
  const columns: DataTableColumn<PromptListItem>[] = [
    {
      key: "prompt_text",
      header: "Prompt",
      cell: (prompt) => (
        <div className="max-w-2xl">
          <p className="line-clamp-2">{prompt.prompt_text}</p>
        </div>
      ),
    },
    {
      key: "eval_count",
      header: "Evaluations",
      cell: (prompt) => (
        <div className="text-center">
          <span className="inline-flex items-center justify-center px-2 py-1 text-xs font-medium rounded-full bg-primary/10 text-primary">
            {prompt.eval_count}
          </span>
        </div>
      ),
      className: "w-32 text-center",
    },
    {
      key: "created_at",
      header: "Created",
      cell: (prompt) => new Date(prompt.created_at).toLocaleDateString(),
      sortable: true,
      className: "w-40",
    },
    {
      key: "actions",
      header: "",
      cell: (prompt) => (
        <Button
          variant="ghost"
          size="icon"
          onClick={(e) => {
            e.stopPropagation();
            onDeletePrompt(prompt);
          }}
          className="text-muted-foreground hover:text-destructive"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      ),
      className: "w-12",
    },
  ];

  return (
    <DataTable
      data={prompts}
      columns={columns}
      onRowClick={onPromptClick}
      loading={loading}
      emptyState={{
        title: "No prompts yet",
        description: "Add your first prompt above to get started",
        icon: ListChecks,
      }}
    />
  );
}

export default function ExperimentDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportingJsonl, setExportingJsonl] = useState(false);
  const [promptText, setPromptText] = useState("");
  const [submittingPrompt, setSubmittingPrompt] = useState(false);
  const [promptToDelete, setPromptPromptToDelete] = useState<PromptListItem | null>(null);
  const [deletePromptDialogOpen, setDeletePromptDialogOpen] = useState(false);
  const [deletingPrompt, setDeletingPrompt] = useState(false);

  const fetchData = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/eval/experiments/${id}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Experiment not found");
      }
      throw new Error("Failed to load experiment");
    }

    const experiment: ExperimentDetail = await response.json();
    return experiment;
  }, [id]);

  const { data, loading, error, refetch } = usePageData<ExperimentDetail>(fetchData);

  const fetchPrompts = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/eval/experiments/${id}/prompts`);

    if (!response.ok) {
      throw new Error("Failed to load prompts");
    }

    const prompts: PromptListItem[] = await response.json();
    return prompts;
  }, [id]);

  const { data: prompts, loading: promptsLoading, error: promptsError, refetch: refetchPrompts } = usePageData<PromptListItem[]>(fetchPrompts);

  const handleExportCSV = () => {
    setExporting(true);
    try {
      const url = `${API_BASE_URL}/api/v1/eval/experiments/${id}/export-csv`;

      // Create a temporary link and trigger download
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `experiment_${id}_evaluations.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      toast({
        title: "Export started",
        description: "Your CSV export is being generated and will download shortly.",
      });
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to start export.",
        variant: "destructive",
      });
    } finally {
      // We set exporting to false after a short delay since the browser download
      // doesn't give us a callback when finished.
      setTimeout(() => setExporting(false), 2000);
    }
  };

  const handleExportJsonl = () => {
    setExportingJsonl(true);
    try {
      const url = `${API_BASE_URL}/api/v1/eval/experiments/${id}/export-jsonl`;

      // Create a temporary link and trigger download
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `experiment_${id}_answers.jsonl`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      toast({
        title: "Export started",
        description: "Your JSONL export is being generated and will download shortly.",
      });
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to start export.",
        variant: "destructive",
      });
    } finally {
      // We set exportingJsonl to false after a short delay since the browser download
      // doesn't give us a callback when finished.
      setTimeout(() => setExportingJsonl(false), 2000);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/eval/experiments/${id}`, {
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

  const handleAddPrompt = async () => {
    if (!promptText.trim()) {
      toast({
        title: "Validation error",
        description: "Prompt text cannot be empty",
        variant: "destructive",
      });
      return;
    }

    setSubmittingPrompt(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/eval/experiments/${id}/prompts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt_text: promptText.trim(),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create prompt");
      }

      toast({
        title: "Prompt added",
        description: "The prompt has been added to the experiment.",
      });

      setPromptText("");
      refetchPrompts();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to create prompt",
        variant: "destructive",
      });
    } finally {
      setSubmittingPrompt(false);
    }
  };

  const handlePromptClick = (prompt: PromptListItem) => {
    router.push(`/eval/${id}/prompts/${prompt.id}`);
  };

  const handleDeletePrompt = async () => {
    if (!promptToDelete) return;

    setDeletingPrompt(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/eval/prompts/${promptToDelete.id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete prompt");
      }

      toast({
        title: "Prompt deleted",
        description: "The prompt and all associated data have been deleted.",
      });

      refetchPrompts();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to delete prompt",
        variant: "destructive",
      });
    } finally {
      setDeletingPrompt(false);
      setDeletePromptDialogOpen(false);
      setPromptPromptToDelete(null);
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
        backUrl="/eval"
        backLabel="Back to Experiments"
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleExportCSV}
              disabled={exporting}
            >
              <Download className="mr-2 h-4 w-4" />
              {exporting ? "Exporting..." : "Export CSV"}
            </Button>
            <Button
              variant="outline"
              onClick={handleExportJsonl}
              disabled={exportingJsonl}
            >
              <Download className="mr-2 h-4 w-4" />
              {exportingJsonl ? "Exporting..." : "Export JSONL"}
            </Button>
            <Button
              variant="destructive"
              onClick={() => setDeleteDialogOpen(true)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </Button>
          </div>
        }
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

            {/* Automatic Mode Toggle */}
            <div className="pt-4 border-t">
              <AutoModeToggle
                experimentId={data.id}
                enabled={data.auto_mode_enabled}
                answerProvider={data.auto_answer_provider}
                judgeProvider={data.auto_judge_provider}
                onUpdate={refetch}
                onError={(error) => {
                  toast({
                    title: "Error",
                    description: error,
                    variant: "destructive",
                  });
                }}
              />
            </div>

            {/* Evaluation Dimensions */}
            {data.dimensions && data.dimensions.length > 0 && (
              <div className="pt-4 border-t">
                <h3 className="text-sm font-medium text-muted-foreground mb-3">Evaluation Dimensions</h3>
                <div className="flex flex-wrap gap-2">
                  {data.dimensions.map((dimension) => (
                    <div
                      key={dimension.id}
                      className="inline-flex items-center px-3 py-1.5 rounded-md bg-primary/10 text-primary text-sm font-mono"
                    >
                      {dimension.dimension_name}
                    </div>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  {data.dimensions.length} dimension{data.dimensions.length !== 1 ? "s" : ""} configured for this experiment
                </p>
              </div>
            )}

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

        {/* Statistics */}
        {data.stats && data.stats.eval_count > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>Statistical Analysis</CardTitle>
              <CardDescription>
                Aggregate results from {data.stats.eval_count} evaluation
                {data.stats.eval_count !== 1 ? "s" : ""}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <StatsCardGrid
                stats={[
                  {
                    label: "Evaluations",
                    value: data.stats.eval_count,
                    icon: BarChart3,
                  },
                  {
                    label: "X Win Rate",
                    value: `${data.stats.x_win_rate.toFixed(1)}%`,
                    icon: TrendingUp,
                  },
                  {
                    label: "Mean Score",
                    value: data.stats.mean_score.toFixed(2),
                    icon: Target,
                  },
                  {
                    label: "Median Score",
                    value: data.stats.median_score.toFixed(2),
                    icon: BarChart3,
                  },
                  {
                    label: "Tie Rate",
                    value: `${data.stats.tie_percentage.toFixed(1)}%`,
                    icon: Equal,
                  },
                  {
                    label: "Harm Rate",
                    value: `${data.stats.harm_rate.toFixed(1)}%`,
                    icon: data.stats.harm_rate > 50 ? AlertTriangle : TrendingDown,
                  },
                ]}
              />
              {data.stats.wilcoxon_p_value !== null && (
                <div className="mt-4 pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">
                      Wilcoxon Signed-Rank Test
                    </span>
                    <span className="text-sm font-mono">
                      p = {data.stats.wilcoxon_p_value.toFixed(4)}
                      {data.stats.wilcoxon_p_value < 0.05 && (
                        <span className="ml-2 text-green-600 dark:text-green-500">
                          (significant)
                        </span>
                      )}
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
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
                  Statistics will be available after evaluations are completed.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        )}

        {/* Prompts Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ListChecks className="h-5 w-5" />
              Prompts
            </CardTitle>
            <CardDescription>
              Add test prompts and submit answer pairs for evaluation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Add Prompt Form */}
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <Textarea
                  placeholder="Enter a prompt to test (e.g., 'What is the capital of France?')"
                  value={promptText}
                  onChange={(e) => setPromptText(e.target.value)}
                  className="flex-1 min-h-[80px]"
                  disabled={submittingPrompt}
                />
                <Button
                  onClick={handleAddPrompt}
                  disabled={!promptText.trim() || submittingPrompt}
                  size="lg"
                >
                  <Send className="mr-2 h-4 w-4" />
                  Add Prompt
                </Button>
              </div>
            </div>

            {/* Prompts Table */}
            {promptsError ? (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Failed to load prompts. {promptsError.message}
                </AlertDescription>
              </Alert>
            ) : (
              <PromptsTable
                prompts={prompts || []}
                loading={promptsLoading}
                onPromptClick={handlePromptClick}
                onDeletePrompt={(prompt) => {
                  setPromptPromptToDelete(prompt);
                  setDeletePromptDialogOpen(true);
                }}
              />
            )}
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

      <ConfirmDialog
        open={deletePromptDialogOpen}
        onOpenChange={setDeletePromptDialogOpen}
        title="Delete Prompt"
        description="Are you sure you want to delete this prompt? This will permanently delete all associated answer pairs and evaluations. This action cannot be undone."
        confirmLabel="Delete Prompt"
        variant="destructive"
        onConfirm={handleDeletePrompt}
        loading={deletingPrompt}
      />
    </div>
  );
}
