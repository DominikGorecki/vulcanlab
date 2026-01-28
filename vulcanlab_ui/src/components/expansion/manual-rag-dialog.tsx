"use client";

import { useState, useEffect, useCallback } from "react";
import { Copy, Check, Loader2, ClipboardPaste, ArrowRight } from "lucide-react";
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

interface ManualRAGDialogProps {
  expansionId: number;
  sectionId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

/**
 * Manual RAG Dialog - 2-step workflow for manual query expansion
 *
 * Step 1: Copy query expansion prompt
 * Step 2: Paste query expansion JSON response (MQE, HyDE, intent, entities)
 *
 * After step 2, embeddings + retrieval run automatically, dialog closes,
 * and the wizard shows the augmented prompt inline for copying and response pasting.
 */
export function ManualRAGDialog({
  expansionId,
  sectionId,
  open,
  onOpenChange,
  onSuccess,
}: ManualRAGDialogProps) {
  const [step, setStep] = useState<"expand-copy" | "expand-paste">("expand-copy");
  const [expandPrompt, setExpandPrompt] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  const [pastedExpansion, setPastedExpansion] = useState("");

  const fetchExpandPrompt = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/expansions/${expansionId}/sections/${sectionId}/expand/prompt`
      );
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to load query expansion prompt");
      }
      const data = await response.json();
      setExpandPrompt(data.prompt);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load prompt");
    } finally {
      setLoading(false);
    }
  }, [expansionId, sectionId]);

  useEffect(() => {
    if (open) {
      fetchExpandPrompt();
      setStep("expand-copy");
      setPastedExpansion("");
      setCopySuccess(false);
    }
  }, [open, fetchExpandPrompt]);

  const handleCopyPrompt = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      setError("Failed to copy to clipboard");
    }
  };

  const handleSaveExpansion = async () => {
    if (!pastedExpansion.trim()) {
      setError("Please paste the query expansion JSON response");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/expansions/${expansionId}/sections/${sectionId}/expand/manual`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ expansion_json: pastedExpansion }),
        }
      );

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to save query expansion");
      }

      // Expansion saved, embeddings and retrieval ran automatically
      // Close dialog and let wizard show the augmented prompt inline
      onSuccess();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save query expansion");
    } finally {
      setSaving(false);
    }
  };

  const getStepTitle = () => {
    switch (step) {
      case "expand-copy":
        return "Step 1: Copy Query Expansion Prompt";
      case "expand-paste":
        return "Step 2: Paste Query Expansion Response";
      default:
        return "";
    }
  };

  const getStepDescription = () => {
    switch (step) {
      case "expand-copy":
        return "Copy this prompt to generate query expansions (MQE, HyDE, intent, entities) in your preferred LLM.";
      case "expand-paste":
        return "Paste the JSON response containing queries, hyde_answer, intent, and entities. After saving, embeddings and retrieval will run automatically, then you can copy the full RAG prompt from the wizard.";
      default:
        return "";
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{getStepTitle()}</DialogTitle>
          <DialogDescription>{getStepDescription()}</DialogDescription>
        </DialogHeader>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {step === "expand-copy" && (
          <div className="flex-1 flex flex-col gap-4 overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between pb-2 border-b">
                  <TextStats text={expandPrompt} />
                </div>
                <Textarea
                  value={expandPrompt}
                  readOnly
                  className="flex-1 font-mono text-sm resize-none min-h-[300px]"
                />
              </>
            )}
          </div>
        )}

        {step === "expand-paste" && (
          <div className="flex-1 flex flex-col gap-4 overflow-hidden">
            <Textarea
              value={pastedExpansion}
              onChange={(e) => setPastedExpansion(e.target.value)}
              placeholder='Paste the JSON response here. Expected format:
{
  "queries": ["alternative query 1", "alternative query 2", ...],
  "hyde_answer": "Hypothetical answer text...",
  "intent": "RESEARCH" or "GENERAL",
  "entities": ["entity1", "entity2", ...]
}'
              className="flex-1 font-mono text-sm resize-none min-h-[300px]"
            />
            {pastedExpansion && <TextStats text={pastedExpansion} />}
          </div>
        )}

        <DialogFooter className="flex-shrink-0 gap-2">
          {step === "expand-copy" && (
            <>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => handleCopyPrompt(expandPrompt)}
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
              <Button onClick={() => setStep("expand-paste")} disabled={loading} className="gap-2">
                <ClipboardPaste className="h-4 w-4" />
                Next: Paste Response
              </Button>
            </>
          )}

          {step === "expand-paste" && (
            <>
              <Button variant="outline" onClick={() => setStep("expand-copy")}>
                Back
              </Button>
              <Button
                onClick={handleSaveExpansion}
                disabled={saving || !pastedExpansion.trim()}
                className="gap-2"
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Saving & Running RAG...
                  </>
                ) : (
                  <>
                    <ArrowRight className="h-4 w-4" />
                    Save & Run RAG
                  </>
                )}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
