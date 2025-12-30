"use client";

import { useState } from "react";
import { Sparkles, Info, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface NewEvalDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  experimentId: number;
  promptText: string;
  onSuccess: () => void;
}

type ProgressStep = "idle" | "step1" | "step2" | "step3" | "success" | "error";

const PROGRESS_MESSAGES = {
  idle: "",
  step1: "Step 1/3: Generating answer X...",
  step2: "Step 2/3: Generating answer Y...",
  step3: "Step 3/3: Running judge evaluation...",
  success: "Evaluation completed!",
  error: "An error occurred",
};

const PROGRESS_VALUES = {
  idle: 0,
  step1: 33,
  step2: 66,
  step3: 100,
  success: 100,
  error: 0,
};

export function NewEvalDialog({
  open,
  onOpenChange,
  experimentId,
  promptText,
  onSuccess,
}: NewEvalDialogProps) {
  const { toast } = useToast();
  const [answerXPrompt, setAnswerXPrompt] = useState("");
  const [answerYPrompt, setAnswerYPrompt] = useState("");
  const [progressStep, setProgressStep] = useState<ProgressStep>("idle");

  const isSubmitting = progressStep !== "idle" && progressStep !== "error";

  const handleSubmit = async () => {
    if (!answerXPrompt.trim() || !answerYPrompt.trim()) {
      toast({
        title: "Validation error",
        description: "Both answer prompts are required",
        variant: "destructive",
      });
      return;
    }

    try {
      // Start progress simulation
      setProgressStep("step1");

      // Simulate progress transitions while backend processes
      const step2Timer = setTimeout(() => setProgressStep("step2"), 2000);
      const step3Timer = setTimeout(() => setProgressStep("step3"), 4000);

      const response = await fetch(
        `${API_BASE_URL}/api/v1/eval/experiments/${experimentId}/prompts/auto-eval`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            main_prompt_text: promptText,
            answer_x_prompt_text: answerXPrompt.trim(),
            answer_y_prompt_text: answerYPrompt.trim(),
          }),
        }
      );

      // Clear timers in case request finishes faster
      clearTimeout(step2Timer);
      clearTimeout(step3Timer);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to execute automatic evaluation");
      }

      setProgressStep("success");

      toast({
        title: "Automatic evaluation completed",
        description: "The answer pair has been generated and evaluated automatically.",
      });

      // Reset form and close dialog
      setAnswerXPrompt("");
      setAnswerYPrompt("");
      setProgressStep("idle");
      onOpenChange(false);
      onSuccess();
    } catch (err) {
      setProgressStep("error");

      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to execute automatic evaluation",
        variant: "destructive",
      });

      // Reset to idle after showing error
      setTimeout(() => setProgressStep("idle"), 2000);
    }
  };

  const handleCancel = () => {
    if (isSubmitting) {
      // Don't allow cancel during submission
      return;
    }
    setAnswerXPrompt("");
    setAnswerYPrompt("");
    setProgressStep("idle");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={(open) => !isSubmitting && onOpenChange(open)}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            New Automatic Evaluation
          </DialogTitle>
          <DialogDescription>
            Provide prompts to generate answers automatically and run judge evaluation
          </DialogDescription>
        </DialogHeader>

        {isSubmitting ? (
          // Progress indicator when submitting
          <div className="space-y-6 py-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">{PROGRESS_MESSAGES[progressStep]}</p>
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
              <Progress value={PROGRESS_VALUES[progressStep]} className="h-2" />
            </div>
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                This may take 30-90 seconds as the system generates both answers and runs the judge evaluation.
              </AlertDescription>
            </Alert>
          </div>
        ) : (
          // Form when not submitting
          <div className="space-y-6">
            {/* Main Prompt (Read-only) */}
            <div className="space-y-2">
              <Label className="text-base font-semibold">Main Prompt (Read-only)</Label>
              <div className="rounded-lg border bg-muted/50 p-4">
                <p className="text-sm whitespace-pre-wrap">{promptText}</p>
              </div>
            </div>

            {/* Automatic Evaluation Notice */}
            <Alert>
              <Sparkles className="h-4 w-4" />
              <AlertDescription>
                The system will use these prompts to automatically generate answer X and answer Y,
                then run a judge evaluation. The answers will be blindly randomized for evaluation.
              </AlertDescription>
            </Alert>

            {/* Answer X Prompt Input */}
            <div className="space-y-2">
              <Label htmlFor="answer-x-prompt" className="text-base font-semibold">
                Answer X Prompt
              </Label>
              <Textarea
                id="answer-x-prompt"
                placeholder="Enter the prompt for generating answer X (e.g., 'Provide a concise answer')..."
                value={answerXPrompt}
                onChange={(e) => setAnswerXPrompt(e.target.value)}
                className="min-h-[100px]"
                disabled={isSubmitting}
              />
              <p className="text-xs text-muted-foreground">
                This prompt will be used to generate the first answer automatically.
              </p>
            </div>

            {/* Answer Y Prompt Input */}
            <div className="space-y-2">
              <Label htmlFor="answer-y-prompt" className="text-base font-semibold">
                Answer Y Prompt
              </Label>
              <Textarea
                id="answer-y-prompt"
                placeholder="Enter the prompt for generating answer Y (e.g., 'Provide a detailed explanation')..."
                value={answerYPrompt}
                onChange={(e) => setAnswerYPrompt(e.target.value)}
                className="min-h-[100px]"
                disabled={isSubmitting}
              />
              <p className="text-xs text-muted-foreground">
                This prompt will be used to generate the second answer automatically.
              </p>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!answerXPrompt.trim() || !answerYPrompt.trim() || isSubmitting}
          >
            <Sparkles className="mr-2 h-4 w-4" />
            {isSubmitting ? "Evaluating..." : "Run Automatic Eval"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
