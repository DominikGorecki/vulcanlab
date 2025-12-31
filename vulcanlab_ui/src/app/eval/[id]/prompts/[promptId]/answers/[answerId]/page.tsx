"use client";

import { use, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { MessageSquare, Trash2, Calendar, FileText, Award, Shuffle } from "lucide-react";
import {
  StickyDetailHeader,
  PageLoadingState,
  PageErrorState,
  ConfirmDialog,
} from "@/components";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { usePageData } from "@/hooks/use-page-data";
import { useToast } from "@/hooks/use-toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DimensionResult {
  dimension_name: string;
  score: number;
}

interface EvaluationDetail {
  id: number;
  overall_score: number;
  unblinded_score: number;
  justification?: string;
  dimension_results: DimensionResult[];
  created_at: string;
}

interface AnswerDetail {
  id: number;
  prompt_id: number;
  answer_x: string;
  answer_y: string;
  is_x_mapped_to_a: boolean;
  answer_a: string;
  answer_b: string;
  created_at: string;
  updated_at: string;
  evaluation?: EvaluationDetail;
}

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
  auto_mode_enabled: boolean;
  auto_answer_provider: string | null;
  auto_judge_provider: string | null;
}

interface PageProps {
  params: Promise<{
    id: string;
    promptId: string;
    answerId: string;
  }>;
}

export default function AnswerDetailPage({ params }: PageProps) {
  const { id: experimentId, promptId, answerId } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Fetch answer detail
  const fetchAnswer = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/eval/answers/${answerId}`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Answer not found");
      }
      throw new Error("Failed to load answer");
    }
    const answer: AnswerDetail = await response.json();
    return answer;
  }, [answerId]);

  // Fetch prompt for context
  const fetchPrompt = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/eval/prompts/${promptId}`);
    if (!response.ok) throw new Error("Failed to load prompt");
    const prompt: PromptDetail = await response.json();
    return prompt;
  }, [promptId]);

  // Fetch experiment for header
  const fetchExperiment = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/eval/experiments/${experimentId}`);
    if (!response.ok) throw new Error("Failed to load experiment");
    const experiment: ExperimentDetail = await response.json();
    return experiment;
  }, [experimentId]);

  const { data: answer, loading: answerLoading, error: answerError, refetch: refetchAnswer }
    = usePageData<AnswerDetail>(fetchAnswer);
  const { data: prompt, loading: promptLoading }
    = usePageData<PromptDetail>(fetchPrompt);
  const { data: experiment, loading: experimentLoading }
    = usePageData<ExperimentDetail>(fetchExperiment);

  // Delete handler
  const handleDelete = async () => {
    setDeleting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/eval/answers/${answerId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete answer pair");
      }

      toast({
        title: "Answer pair deleted",
        description: "The answer pair has been deleted successfully",
      });

      router.push(`/eval/${experimentId}/prompts/${promptId}`);
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to delete answer pair",
        variant: "destructive",
      });
      setDeleting(false);
      setDeleteDialogOpen(false);
    }
  };

  // Loading state
  if (answerLoading || promptLoading || experimentLoading) {
    return <PageLoadingState title="Loading answer details..." />;
  }

  // Error state
  if (answerError) {
    return <PageErrorState error={answerError} onRetry={refetchAnswer} />;
  }

  // Null check
  if (!answer || !prompt || !experiment) {
    return null;
  }

  return (
    <div className="container mx-auto p-6">
      <StickyDetailHeader
        title="Answer Pair Details"
        subtitle={experiment.name}
        backUrl={`/eval/${experimentId}/prompts/${promptId}`}
        backLabel="Back to Prompt"
        actions={
          <Button variant="destructive" onClick={() => setDeleteDialogOpen(true)}>
            <Trash2 className="mr-2 h-4 w-4" />
            Delete Answer
          </Button>
        }
      />

      <div className="space-y-6">
        {/* Prompt Context Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Prompt Context
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Accordion type="single" collapsible defaultValue="">
              <AccordionItem value="prompt-text">
                <AccordionTrigger>View Prompt</AccordionTrigger>
                <AccordionContent>
                  <div className="rounded-lg border bg-muted/50 p-4">
                    <p className="text-base whitespace-pre-wrap">{prompt.prompt_text}</p>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>

        {/* Answer Data Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Answer Pair
            </CardTitle>
            <CardDescription>Unblinded and blind-randomized answers</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Unblinded Answers */}
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-3">Unblinded Answers</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Answer X</Label>
                    <div className="rounded-lg border bg-muted/50 p-4 max-h-[300px] overflow-y-auto">
                      <p className="text-sm whitespace-pre-wrap">{answer.answer_x}</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Answer Y</Label>
                    <div className="rounded-lg border bg-muted/50 p-4 max-h-[300px] overflow-y-auto">
                      <p className="text-sm whitespace-pre-wrap">{answer.answer_y}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Blind Answers */}
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-3">
                  Blind Randomized (for Evaluation)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Answer A</Label>
                    <div className="rounded-lg border bg-muted/50 p-4 max-h-[300px] overflow-y-auto">
                      <p className="text-sm whitespace-pre-wrap">{answer.answer_a}</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Answer B</Label>
                    <div className="rounded-lg border bg-muted/50 p-4 max-h-[300px] overflow-y-auto">
                      <p className="text-sm whitespace-pre-wrap">{answer.answer_b}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Mapping Indicator */}
              <div className="flex items-center gap-4 pt-2 border-t">
                <div className="flex items-center gap-2 text-sm">
                  <Shuffle className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">Randomization Mapping:</span>
                  <span className="font-mono bg-muted px-2 py-1 rounded">
                    X → {answer.is_x_mapped_to_a ? 'A' : 'B'}
                  </span>
                  <span className="text-muted-foreground">|</span>
                  <span className="font-mono bg-muted px-2 py-1 rounded">
                    Y → {answer.is_x_mapped_to_a ? 'B' : 'A'}
                  </span>
                </div>
              </div>

              {/* Metadata */}
              <div className="flex items-center gap-4 text-sm text-muted-foreground border-t pt-4">
                <Calendar className="h-4 w-4" />
                <span>Created: {new Date(answer.created_at).toLocaleString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Evaluation Results Card (Conditional) */}
        {answer.evaluation && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="h-5 w-5" />
                Evaluation Results
              </CardTitle>
              <CardDescription>
                Evaluated on {new Date(answer.evaluation.created_at).toLocaleString()}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Scores */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="rounded-lg border bg-muted/50 p-4">
                    <div className="text-sm font-medium text-muted-foreground mb-1">
                      Overall Score (Blinded)
                    </div>
                    <div className="text-3xl font-bold">
                      {answer.evaluation.overall_score > 0 ? '+' : ''}{answer.evaluation.overall_score}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      -10 to +10 (positive = A wins)
                    </div>
                  </div>
                  <div className="rounded-lg border bg-muted/50 p-4">
                    <div className="text-sm font-medium text-muted-foreground mb-1">
                      Unblinded Score
                    </div>
                    <div className="text-3xl font-bold">
                      {answer.evaluation.unblinded_score > 0 ? '+' : ''}{answer.evaluation.unblinded_score}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Positive = X wins, Negative = Y wins
                    </div>
                  </div>
                </div>

                {/* Justification */}
                {answer.evaluation.justification && (
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">Justification</h3>
                    <div className="rounded-lg border bg-muted/50 p-4">
                      <p className="text-sm whitespace-pre-wrap">{answer.evaluation.justification}</p>
                    </div>
                  </div>
                )}

                {/* Dimension Scores */}
                {answer.evaluation.dimension_results.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-3">Dimension Scores</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {answer.evaluation.dimension_results
                        .sort((a, b) => a.dimension_name.localeCompare(b.dimension_name))
                        .map((dim) => (
                          <div key={dim.dimension_name} className="rounded-lg border bg-muted/50 p-3">
                            <div className="text-sm font-medium mb-1">{dim.dimension_name}</div>
                            <div className="text-2xl font-bold">
                              {dim.score > 0 ? '+' : ''}{dim.score}
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Answer Pair"
        description="Are you sure you want to delete this answer pair? This will permanently delete the answer and any associated evaluation. This action cannot be undone."
        confirmLabel="Delete Answer Pair"
        variant="destructive"
        onConfirm={handleDelete}
        loading={deleting}
      />
    </div>
  );
}
