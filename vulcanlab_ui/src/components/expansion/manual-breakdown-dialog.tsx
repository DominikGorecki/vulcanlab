"use client";

import { useState, useEffect, useCallback } from "react";
import { Copy, Check, Loader2, ClipboardPaste } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { TextStats } from "@/components/text-stats";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ManualBreakdownDialogProps {
  expansionId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function ManualBreakdownDialog({
  expansionId,
  open,
  onOpenChange,
  onSuccess,
}: ManualBreakdownDialogProps) {
  const [step, setStep] = useState<"copy" | "paste">("copy");
  const [prompt, setPrompt] = useState<string>("");
  const [tokenEstimate, setTokenEstimate] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  const [pastedResponse, setPastedResponse] = useState("");

  const fetchPrompt = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/expansions/${expansionId}/breakdown/prompt`
      );
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to load breakdown prompt");
      }
      const data = await response.json();
      setPrompt(data.prompt);
      setTokenEstimate(data.answer_token_estimate);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load prompt");
    } finally {
      setLoading(false);
    }
  }, [expansionId]);

  useEffect(() => {
    if (open) {
      fetchPrompt();
      setStep("copy");
      setPastedResponse("");
      setCopySuccess(false);
    }
  }, [open, fetchPrompt]);

  const handleCopyPrompt = async () => {
    try {
      await navigator.clipboard.writeText(prompt);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      setError("Failed to copy to clipboard");
    }
  };

  const handleSaveBreakdown = async () => {
    if (!pastedResponse.trim()) {
      setError("Please paste the LLM response");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/expansions/${expansionId}/breakdown/manual`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ breakdown_json: pastedResponse }),
        }
      );

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to save breakdown");
      }

      onSuccess();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save breakdown");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>
            {step === "copy" ? "Step 1: Copy Breakdown Prompt" : "Step 2: Paste LLM Response"}
          </DialogTitle>
          <DialogDescription>
            {step === "copy"
              ? "Copy this prompt and paste it into your preferred LLM (ChatGPT, Claude, etc.) to generate the section breakdown."
              : "Paste the JSON response from the LLM below. The response should contain sections with heading, summary, and expansion_prompt."}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {step === "copy" ? (
          <div className="flex-1 flex flex-col gap-4 overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between pb-2 border-b">
                  <span className="text-sm text-muted-foreground">
                    Answer token estimate: ~{tokenEstimate.toLocaleString()}
                  </span>
                  <TextStats text={prompt} />
                </div>
                <Textarea
                  value={prompt}
                  readOnly
                  className="flex-1 font-mono text-sm resize-none min-h-[300px]"
                />
              </>
            )}
          </div>
        ) : (
          <div className="flex-1 flex flex-col gap-4 overflow-hidden">
            <Textarea
              value={pastedResponse}
              onChange={(e) => setPastedResponse(e.target.value)}
              placeholder='Paste the JSON response here. Expected format:
{
  "sections": [
    {
      "heading": "Section Title",
      "summary": "Brief description of this section",
      "expansion_prompt": "The prompt to use for expanding this section..."
    },
    ...
  ]
}'
              className="flex-1 font-mono text-sm resize-none min-h-[300px]"
            />
            {pastedResponse && <TextStats text={pastedResponse} />}
          </div>
        )}

        <DialogFooter className="flex-shrink-0 gap-2">
          {step === "copy" ? (
            <>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleCopyPrompt}
                variant="outline"
                disabled={loading}
                className="gap-2"
              >
                {copySuccess ? (
                  <>
                    <Check className="h-4 w-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    Copy Prompt
                  </>
                )}
              </Button>
              <Button onClick={() => setStep("paste")} disabled={loading} className="gap-2">
                <ClipboardPaste className="h-4 w-4" />
                Next: Paste Response
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={() => setStep("copy")}>
                Back
              </Button>
              <Button
                onClick={handleSaveBreakdown}
                disabled={saving || !pastedResponse.trim()}
                className="gap-2"
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  "Save Breakdown"
                )}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
