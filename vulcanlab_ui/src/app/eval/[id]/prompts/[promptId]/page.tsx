"use client";

import { use, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { MessageSquare, Trash2, Calendar, Plus, AlertCircle } from "lucide-react";
import {
  StickyDetailHeader,
  PageLoadingState,
  PageErrorState,
  ConfirmDialog,
  DataTable,
  type DataTableColumn,
} from "@/components";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { usePageData } from "@/hooks/use-page-data";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AddAnswersDialog } from "./add-answers-dialog";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PromptDetail {
  id: number;
  experiment_id: number;
  prompt_text: string;
  created_at: string;
  updated_at: string;
}

interface ExperimentDetail {
  id: number;
  name: string;
  description_x: string | null;
  description_y: string | null;
  model_x: string | null;
  model_y: string | null;
}

interface AnswerListItem {
  id: number;
  prompt_id: number;
  created_at: string;
  has_evaluation: boolean;
}

interface PageProps {
  params: Promise<{
    id: string;
    promptId: string;
  }>;
}

interface AnswersTableProps {
  answers: AnswerListItem[];
  loading: boolean;
}

function AnswersTable({ answers, loading }: AnswersTableProps) {
  const columns: DataTableColumn<AnswerListItem>[] = [
    {
      key: "id",
      header: "Answer ID",
      cell: (answer) => <span className="font-mono text-sm">#{answer.id}</span>,
      className: "w-32",
    },
    {
      key: "has_evaluation",
      header: "Status",
      cell: (answer) => (
        <span
          className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${
            answer.has_evaluation
              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
              : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
          }`}
        >
          {answer.has_evaluation ? "Evaluated" : "Pending"}
        </span>
      ),
      className: "w-40",
    },
    {
      key: "created_at",
      header: "Created",
      cell: (answer) => new Date(answer.created_at).toLocaleString(),
      sortable: true,
      className: "w-48",
    },
  ];

  return (
    <DataTable
      data={answers}
      columns={columns}
      loading={loading}
      emptyState={{
        title: "No answers yet",
        description: "Add answer pairs to evaluate this prompt",
        icon: MessageSquare,
      }}
    />
  );
}

export default function PromptDetailPage({ params }: PageProps) {
  const { id: experimentId, promptId } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [addAnswersDialogOpen, setAddAnswersDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const fetchPrompt = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/eval/prompts/${promptId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Prompt not found");
      }
      throw new Error("Failed to load prompt");
    }

    const prompt: PromptDetail = await response.json();
    return prompt;
  }, [promptId]);

  const fetchExperiment = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/eval/experiments/${experimentId}`);

    if (!response.ok) {
      throw new Error("Failed to load experiment");
    }

    const experiment: ExperimentDetail = await response.json();
    return experiment;
  }, [experimentId]);

  const fetchAnswers = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/eval/prompts/${promptId}/answers`);

    if (!response.ok) {
      throw new Error("Failed to load answers");
    }

    const answers: AnswerListItem[] = await response.json();
    return answers;
  }, [promptId]);

  const { data: prompt, loading: promptLoading, error: promptError, refetch: refetchPrompt } = usePageData<PromptDetail>(fetchPrompt);
  const { data: experiment, loading: experimentLoading } = usePageData<ExperimentDetail>(fetchExperiment);
  const { data: answers, loading: answersLoading, error: answersError, refetch: refetchAnswers } = usePageData<AnswerListItem[]>(fetchAnswers);

  const handleDelete = async () => {
    setDeleting(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/eval/prompts/${promptId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete prompt");
      }

      toast({
        title: "Prompt deleted",
        description: "The prompt and all associated answers have been deleted.",
      });

      router.push(`/eval/${experimentId}`);
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to delete prompt",
        variant: "destructive",
      });
      setDeleting(false);
      setDeleteDialogOpen(false);
    }
  };

  const handleAnswersAdded = () => {
    refetchAnswers();
  };

  if (promptLoading || experimentLoading) {
    return <PageLoadingState title="Loading prompt..." />;
  }

  if (promptError) {
    return <PageErrorState error={promptError} onRetry={refetchPrompt} />;
  }

  if (!prompt || !experiment) {
    return null;
  }

  return (
    <div className="container mx-auto p-6">
      <StickyDetailHeader
        title="Prompt Details"
        subtitle={experiment.name}
        backUrl={`/eval/${experimentId}`}
        backLabel="Back to Experiment"
        actions={
          <>
            <Button
              variant="default"
              onClick={() => setAddAnswersDialogOpen(true)}
            >
              <Plus className="mr-2 h-4 w-4" />
              Add Answers
            </Button>
            <Button
              variant="destructive"
              onClick={() => setDeleteDialogOpen(true)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </Button>
          </>
        }
      />

      <div className="space-y-6">
        {/* Prompt Content */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Prompt
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="rounded-lg border bg-muted/50 p-4">
                <p className="text-base whitespace-pre-wrap">{prompt.prompt_text}</p>
              </div>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>Created: {new Date(prompt.created_at).toLocaleString()}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Experiment Context */}
        <Card>
          <CardHeader>
            <CardTitle>Evaluation Setup</CardTitle>
            <CardDescription>Models being compared in this experiment</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-lg border p-4">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Answer Set X</h3>
                <p className="text-base font-medium">
                  {experiment.description_x || "Not specified"}
                </p>
                {experiment.model_x && (
                  <p className="text-sm text-muted-foreground mt-1">
                    Model: {experiment.model_x}
                  </p>
                )}
              </div>
              <div className="rounded-lg border p-4">
                <h3 className="text-sm font-medium text-muted-foreground mb-2">Answer Set Y</h3>
                <p className="text-base font-medium">
                  {experiment.description_y || "Not specified"}
                </p>
                {experiment.model_y && (
                  <p className="text-sm text-muted-foreground mt-1">
                    Model: {experiment.model_y}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Answers Section */}
        <Card>
          <CardHeader>
            <CardTitle>Answer Pairs</CardTitle>
            <CardDescription>
              Answer pairs submitted for this prompt (blind randomized for evaluation)
            </CardDescription>
          </CardHeader>
          <CardContent>
            {answersError ? (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Failed to load answers. {answersError.message}
                </AlertDescription>
              </Alert>
            ) : (
              <AnswersTable
                answers={answers || []}
                loading={answersLoading}
              />
            )}
          </CardContent>
        </Card>
      </div>

      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Prompt"
        description="Are you sure you want to delete this prompt? This will permanently delete all associated answer pairs and evaluations. This action cannot be undone."
        confirmLabel="Delete Prompt"
        variant="destructive"
        onConfirm={handleDelete}
        loading={deleting}
      />

      <AddAnswersDialog
        open={addAnswersDialogOpen}
        onOpenChange={setAddAnswersDialogOpen}
        promptId={parseInt(promptId)}
        promptText={prompt.prompt_text}
        descriptionX={experiment.description_x || "Answer X"}
        descriptionY={experiment.description_y || "Answer Y"}
        onSuccess={handleAnswersAdded}
      />
    </div>
  );
}
