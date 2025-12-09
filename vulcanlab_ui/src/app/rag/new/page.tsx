"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  AlertCircle,
  ChevronLeft,
  Copy,
  Loader2Icon,
  PlayCircle,
  Check,
} from "lucide-react";
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

function NewQueryPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryText = searchParams.get("q") || "";

  // Content states
  const [prompt, setPrompt] = useState("");

  // Loading states
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [saving, setSaving] = useState(false);

  // Error states
  const [error, setError] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [operationSuccess, setOperationSuccess] = useState<string | null>(null);

  // Dialog states
  const [copyDialogOpen, setCopyDialogOpen] = useState(false);
  const [runDialogOpen, setRunDialogOpen] = useState(false);
  const [pastedResponse, setPastedResponse] = useState("");
  const [copySuccess, setCopySuccess] = useState(false);

  useEffect(() => {
    if (queryText) {
      fetchPrompt();
    } else {
      setError("No query provided. Please go back and enter a query.");
      setLoading(false);
    }
  }, [queryText]);

  const fetchPrompt = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/rag/expansion/prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: queryText,
          n: 3
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to generate prompt: ${response.statusText}`);
      }

      const data = await response.json();
      setPrompt(data.prompt);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate prompt");
    } finally {
      setLoading(false);
    }
  };

  const handleCopyPrompt = async () => {
    try {
      await navigator.clipboard.writeText(prompt);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
      setCopyDialogOpen(true);
      setPastedResponse("");
    } catch (err) {
      console.error("Failed to copy:", err);
      setOperationError("Failed to copy prompt to clipboard");
    }
  };

  const handleSaveManualResponse = async () => {
    if (!pastedResponse.trim()) {
      setOperationError("Please paste the LLM response");
      return;
    }

    setSaving(true);
    setOperationError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/rag/expansion/manual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: queryText,
          response_text: pastedResponse,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save expansion");
      }

      const data = await response.json();
      setOperationSuccess(data.message || "Query expansion saved successfully");
      setCopyDialogOpen(false);

      // Redirect back to main RAG page
      setTimeout(() => {
        router.push("/rag");
      }, 1500);
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to save expansion");
    } finally {
      setSaving(false);
    }
  };

  const handleRunPrompt = async () => {
    setRunning(true);
    setOperationError(null);
    setRunDialogOpen(false);

    try {
      const response = await fetch(`${API_BASE_URL}/rag/expansion/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: queryText,
          n: 3
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to run expansion");
      }

      const data = await response.json();
      setOperationSuccess(data.message || "Query expanded successfully");

      // Redirect back to main RAG page
      setTimeout(() => {
        router.push("/rag");
      }, 1500);
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to run expansion");
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
          <p className="text-destructive">{error}</p>
          <div className="flex gap-3 justify-center">
            <Button onClick={fetchPrompt} disabled={!queryText}>Retry</Button>
            <Button variant="outline" onClick={() => router.push("/rag")}>
              Back
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header with controls */}
      <div className="border-b bg-card p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Back button */}
          <Button
            onClick={() => router.push("/rag")}
            variant="ghost"
            size="sm"
            className="gap-1"
            disabled={running}
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>

          <div className="border-l h-8" />

          <div>
            <h1 className="text-2xl font-bold">Query Expansion</h1>
            <p className="text-sm text-muted-foreground max-w-lg truncate">
              {queryText}
            </p>
          </div>
        </div>
      </div>

      {/* Success/Error Messages */}
      {operationSuccess && (
        <div className="mx-4 mt-4">
          <Alert>
            <Check className="h-4 w-4" />
            <AlertDescription>{operationSuccess}</AlertDescription>
          </Alert>
        </div>
      )}

      {operationError && (
        <div className="mx-4 mt-4">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{operationError}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Main content area - read-only textarea */}
      <div className="flex-1 flex overflow-hidden" style={{ maxHeight: "calc(100vh - 220px)" }}>
        <div className="w-full flex flex-col p-4">
          <Textarea
            value={prompt}
            readOnly
            className="flex-1 font-mono text-sm resize-none select-text"
            placeholder="Loading prompt..."
          />
        </div>
      </div>

      {/* Bottom action bar */}
      <div className="border-t bg-card p-4">
        <div className="flex items-center justify-between max-w-full">
          <p className="text-sm text-muted-foreground flex-1 mr-4">
            You can either manually run this prompt in your favorite LLM (like ChatGPT, Claude, etc.)
            or run it automatically using our API with the FULL model.
          </p>
          <div className="flex gap-3 flex-shrink-0">
            <Button
              onClick={handleCopyPrompt}
              variant="outline"
              disabled={running}
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

            <Button
              onClick={() => setRunDialogOpen(true)}
              disabled={running}
              className="gap-2"
            >
              {running ? (
                <>
                  <Loader2Icon className="h-4 w-4 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <PlayCircle className="h-4 w-4" />
                  Run
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Manual Paste Dialog */}
      <Dialog open={copyDialogOpen} onOpenChange={setCopyDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>Paste LLM Response</DialogTitle>
            <DialogDescription>
              Paste the LLM&apos;s JSON response here. It should contain queries, hyde_answer, intent, and entities.
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-hidden py-4">
            <Textarea
              value={pastedResponse}
              onChange={(e) => setPastedResponse(e.target.value)}
              placeholder={'Paste the LLM response here...\nExample:\n{\n  "queries": [...],\n  "hyde_answer": "...",\n  "intent": "DEFINITION",\n  "entities": [...]\n}'}
              className="h-full min-h-[300px] max-h-[50vh] font-mono text-sm resize-none"
            />
          </div>

          <DialogFooter className="flex-shrink-0">
            <Button
              variant="outline"
              onClick={() => {
                setCopyDialogOpen(false);
                setPastedResponse("");
              }}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button onClick={handleSaveManualResponse} disabled={saving || !pastedResponse.trim()}>
              {saving ? (
                <>
                  <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                  Saving...
                </>
              ) : (
                "Save"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Run Confirmation Dialog */}
      <Dialog open={runDialogOpen} onOpenChange={setRunDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Run Query Expansion?</DialogTitle>
            <DialogDescription>
              This will expand the query using the FULL model.
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <p className="font-medium mb-2">This will use the FULL model which is:</p>
                <ul className="text-sm space-y-1 ml-4 list-disc">
                  <li>More expensive (higher API costs)</li>
                  <li>Slower (may take 10-30 seconds)</li>
                  <li>More accurate for complex queries</li>
                </ul>
              </AlertDescription>
            </Alert>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRunDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleRunPrompt}>
              Confirm & Run
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function NewQueryPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-screen">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    }>
      <NewQueryPageContent />
    </Suspense>
  );
}

