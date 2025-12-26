"use client";

import { useState } from "react";
import { Send, Info } from "lucide-react";
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
import { useToast } from "@/hooks/use-toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AddAnswersDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  promptId: number;
  promptText: string;
  descriptionX: string;
  descriptionY: string;
  onSuccess: () => void;
}

export function AddAnswersDialog({
  open,
  onOpenChange,
  promptId,
  promptText,
  descriptionX,
  descriptionY,
  onSuccess,
}: AddAnswersDialogProps) {
  const { toast } = useToast();
  const [answerX, setAnswerX] = useState("");
  const [answerY, setAnswerY] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!answerX.trim() || !answerY.trim()) {
      toast({
        title: "Validation error",
        description: "Both answers are required",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/eval/prompts/${promptId}/answers`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            answer_x: answerX.trim(),
            answer_y: answerY.trim(),
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create answer pair");
      }

      toast({
        title: "Answers added",
        description: "The answer pair has been added with blind randomization.",
      });

      // Reset form and close dialog
      setAnswerX("");
      setAnswerY("");
      onOpenChange(false);
      onSuccess();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to create answer pair",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    setAnswerX("");
    setAnswerY("");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add Answer Pair</DialogTitle>
          <DialogDescription>
            Submit answers from both models for blind evaluation
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Prompt Context */}
          <div className="rounded-lg border bg-muted/50 p-4">
            <h3 className="text-sm font-medium mb-2">Prompt</h3>
            <p className="text-sm whitespace-pre-wrap">{promptText}</p>
          </div>

          {/* Blind Evaluation Notice */}
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Answers will be randomly assigned to A/B positions for blind evaluation.
              Evaluators will not know which answer comes from which model.
            </AlertDescription>
          </Alert>

          {/* Answer X Input */}
          <div className="space-y-2">
            <Label htmlFor="answer-x" className="text-base font-semibold">
              {descriptionX}
            </Label>
            <Textarea
              id="answer-x"
              placeholder="Enter the answer from model X..."
              value={answerX}
              onChange={(e) => setAnswerX(e.target.value)}
              className="min-h-[120px]"
              disabled={submitting}
            />
            <p className="text-xs text-muted-foreground">
              {answerX.length} characters
            </p>
          </div>

          {/* Answer Y Input */}
          <div className="space-y-2">
            <Label htmlFor="answer-y" className="text-base font-semibold">
              {descriptionY}
            </Label>
            <Textarea
              id="answer-y"
              placeholder="Enter the answer from model Y..."
              value={answerY}
              onChange={(e) => setAnswerY(e.target.value)}
              className="min-h-[120px]"
              disabled={submitting}
            />
            <p className="text-xs text-muted-foreground">
              {answerY.length} characters
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!answerX.trim() || !answerY.trim() || submitting}
          >
            <Send className="mr-2 h-4 w-4" />
            {submitting ? "Submitting..." : "Submit Answer Pair"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
