"use client";

import { useState, useEffect } from "react";
import { CheckCircle, AlertCircle, Info } from "lucide-react";
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
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/hooks/use-toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PasteResultDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  answerId: number;
  hasExistingEvaluation: boolean;
  onSuccess: () => void;
}

interface ParsedEvaluation {
  overall_score: number;
  justification?: string;
  dimension_scores: Record<string, number>;
}

export function PasteResultDialog({
  open,
  onOpenChange,
  answerId,
  hasExistingEvaluation,
  onSuccess,
}: PasteResultDialogProps) {
  const { toast } = useToast();
  const [jsonInput, setJsonInput] = useState("");
  const [parseError, setParseError] = useState<string | null>(null);
  const [parsedData, setParsedData] = useState<ParsedEvaluation | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [overwriteConfirmed, setOverwriteConfirmed] = useState(false);

  // Reset overwrite confirmation when dialog closes
  useEffect(() => {
    if (!open) {
      setOverwriteConfirmed(false);
    }
  }, [open]);

  const validateAndParseJSON = (input: string) => {
    if (!input.trim()) {
      setParseError(null);
      setParsedData(null);
      return;
    }

    try {
      const parsed = JSON.parse(input);

      // Validate structure
      if (typeof parsed !== "object" || parsed === null) {
        throw new Error("JSON must be an object");
      }

      if (!("overall_score" in parsed)) {
        throw new Error("Missing required field: overall_score");
      }

      if (!("dimension_scores" in parsed)) {
        throw new Error("Missing required field: dimension_scores");
      }

      if (typeof parsed.overall_score !== "number") {
        throw new Error("overall_score must be a number");
      }

      if (parsed.overall_score < -10 || parsed.overall_score > 10) {
        throw new Error("overall_score must be between -10 and 10");
      }

      if (!Number.isInteger(parsed.overall_score)) {
        throw new Error("overall_score must be an integer");
      }

      if (typeof parsed.dimension_scores !== "object" || parsed.dimension_scores === null) {
        throw new Error("dimension_scores must be an object");
      }

      // Validate dimension scores
      for (const [dimName, score] of Object.entries(parsed.dimension_scores)) {
        if (typeof score !== "number") {
          throw new Error(`Dimension score for '${dimName}' must be a number`);
        }
        if ((score as number) < -10 || (score as number) > 10) {
          throw new Error(`Dimension score for '${dimName}' must be between -10 and 10`);
        }
        if (!Number.isInteger(score as number)) {
          throw new Error(`Dimension score for '${dimName}' must be an integer`);
        }
      }

      // Optional justification validation
      if ("justification" in parsed && parsed.justification !== null && typeof parsed.justification !== "string") {
        throw new Error("justification must be a string or null");
      }

      setParsedData(parsed as ParsedEvaluation);
      setParseError(null);
    } catch (err) {
      setParseError(err instanceof Error ? err.message : "Invalid JSON");
      setParsedData(null);
    }
  };

  const handleInputChange = (value: string) => {
    setJsonInput(value);
    validateAndParseJSON(value);
  };

  const handleSubmit = async () => {
    if (!parsedData) {
      toast({
        title: "Validation error",
        description: "Please paste valid evaluation JSON",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);

    try {
      const url = hasExistingEvaluation
        ? `${API_BASE_URL}/api/v1/eval/answers/${answerId}/evaluation?overwrite=true`
        : `${API_BASE_URL}/api/v1/eval/answers/${answerId}/evaluation`;

      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(parsedData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to submit evaluation");
      }

      toast({
        title: hasExistingEvaluation ? "Evaluation updated" : "Evaluation submitted",
        description: hasExistingEvaluation
          ? "The existing evaluation has been overwritten successfully"
          : "The evaluation has been recorded successfully",
      });

      // Reset and close
      setJsonInput("");
      setParsedData(null);
      setParseError(null);
      onOpenChange(false);
      onSuccess();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to submit evaluation",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    setJsonInput("");
    setParsedData(null);
    setParseError(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Paste Evaluation Result</DialogTitle>
          <DialogDescription>
            Paste the JSON output from your evaluation model
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Warning Alert for Overwrite */}
          {hasExistingEvaluation && (
            <Alert variant="warning">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <strong>Warning:</strong> This answer already has an evaluation.
                Submitting will permanently overwrite the existing evaluation data.
              </AlertDescription>
            </Alert>
          )}

          {/* Overwrite Confirmation Checkbox */}
          {hasExistingEvaluation && (
            <div className="flex items-center space-x-2 border rounded-md p-3 bg-muted/50">
              <Checkbox
                id="overwrite-confirm"
                checked={overwriteConfirmed}
                onCheckedChange={(checked) => setOverwriteConfirmed(checked === true)}
              />
              <label
                htmlFor="overwrite-confirm"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
              >
                I understand this will permanently overwrite the existing evaluation
              </label>
            </div>
          )}

          {/* JSON Input */}
          <div className="space-y-2">
            <Label htmlFor="json-input">Evaluation JSON</Label>
            <Textarea
              id="json-input"
              placeholder='{"overall_score": 5, "justification": "...", "dimension_scores": {"clarity": 6}}'
              value={jsonInput}
              onChange={(e) => handleInputChange(e.target.value)}
              className="min-h-[200px] font-mono text-sm"
              disabled={submitting}
            />
          </div>

          {/* Validation Feedback */}
          {parseError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{parseError}</AlertDescription>
            </Alert>
          )}

          {parsedData && !parseError && (
            <Alert>
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription>
                Valid JSON: Overall score {parsedData.overall_score},
                {Object.keys(parsedData.dimension_scores).length} dimension(s)
              </AlertDescription>
            </Alert>
          )}

          {/* Format Hint */}
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription className="text-xs">
              Expected format: <code className="text-xs bg-muted px-1 py-0.5 rounded">
                {`{"overall_score": <-10 to 10>, "justification": "...", "dimension_scores": {"dim_name": <-10 to 10>}}`}
              </code>
            </AlertDescription>
          </Alert>
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
            disabled={
              !parsedData ||
              !!parseError ||
              submitting ||
              (hasExistingEvaluation && !overwriteConfirmed)
            }
          >
            {submitting ? "Submitting..." :
             hasExistingEvaluation ? "Overwrite Evaluation" : "Submit Evaluation"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
