"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Save, Copy, Check, SkipForward, AlertCircle } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { Textarea } from "@/components/ui/textarea";
import { extractJson } from "@/lib/utils";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Step6QualityEvaluationProps {
  sessionId: number;
  reportContent: string;
  onComplete: (evaluation: any) => void;
  onSkip: () => void;
}

export function Step6QualityEvaluation({
  sessionId,
  reportContent,
  onComplete,
  onSkip,
}: Step6QualityEvaluationProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [evaluationJson, setEvaluationJson] = useState("");
  const [isCopied, setIsCopied] = useState(false);

  const copyEvaluationPrompt = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}/prompts/quality_evaluation`);
      if (!response.ok) throw new Error("Failed to fetch quality evaluation prompt");
      
      const { prompt } = await response.json();
      await navigator.clipboard.writeText(prompt);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);

      toast({
        title: "Prompt Copied",
        description: "Quality evaluation prompt copied to clipboard.",
      });
    } catch (error) {
      console.error("Error copying prompt:", error);
      toast({
        title: "Error",
        description: "Failed to fetch or copy prompt.",
        variant: "destructive",
      });
    }
  };

  const handleSaveEvaluation = async () => {
    if (!evaluationJson.trim()) {
      toast({
        title: "Empty Evaluation",
        description: "Please paste the evaluation JSON.",
        variant: "destructive",
      });
      return;
    }

    let evaluation;
    try {
      const cleanJson = extractJson(evaluationJson);
      evaluation = JSON.parse(cleanJson);
    } catch (e) {
      console.error("JSON Parse Error details:", e);
      toast({
        title: "Invalid JSON",
        description: `JSON parsing failed: ${e instanceof Error ? e.message : String(e)}. Please ensure you pasted the full JSON object.`,
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSaving(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          quality_evaluation: evaluation,
          status: "completed",
        }),
      });

      if (!response.ok) throw new Error("Failed to save evaluation");

      toast({
        title: "Evaluation Saved",
        description: "Quality evaluation saved and session completed.",
      });

      onComplete(evaluation);
    } catch (error) {
      console.error("Error saving evaluation:", error);
      toast({
        title: "Error",
        description: "Failed to save quality evaluation.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Step 6: Quality Evaluation (Optional)</h3>
          <p className="text-sm text-muted-foreground">
            Critically evaluate the generated report's quality.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={copyEvaluationPrompt}
          className="gap-2"
        >
          {isCopied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          Copy Evaluation Prompt
        </Button>
      </div>

      <Card className="border-blue-500/20 bg-blue-500/5">
        <CardContent className="p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-blue-500 mt-0.5" />
          <div className="text-sm text-blue-700 dark:text-blue-300">
            <p className="font-semibold mb-1">How it works:</p>
            <ol className="list-decimal ml-4 space-y-1">
              <li>Copy the prompt and paste it into an LLM.</li>
              <li>The LLM will analyze your report and provide a JSON evaluation.</li>
              <li>Paste that JSON back here to store it with your research.</li>
            </ol>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <Textarea
          placeholder='Paste the evaluation JSON here, e.g.: {"citation_accuracy": "High", ...}'
          className="min-h-[300px] font-mono text-sm resize-none"
          value={evaluationJson}
          onChange={(e) => setEvaluationJson(e.target.value)}
        />
      </div>

      <div className="flex justify-between items-center pt-6 border-t">
        <Button variant="ghost" onClick={onSkip} className="gap-2">
          <SkipForward className="h-4 w-4" />
          Skip Evaluation
        </Button>
        <Button
          onClick={handleSaveEvaluation}
          disabled={isSaving || !evaluationJson.trim()}
          className="min-w-[150px]"
        >
          {isSaving ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save & Complete
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
