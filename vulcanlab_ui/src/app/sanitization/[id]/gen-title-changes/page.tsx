"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
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

export default function GenTitleChangesPage() {
  const params = useParams();
  const router = useRouter();
  const workId = params.id as string;

  // Content states
  const [prompt, setPrompt] = useState("");
  const [workTitle, setWorkTitle] = useState("");
  const [workAuthors, setWorkAuthors] = useState("");

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

  // Fetch prompt on mount
  useEffect(() => {
    fetchPrompt();
  }, [workId]);

  const fetchPrompt = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/sanitization/work/${workId}/prompt?source_key=original_markdown&force=false`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Work or titles file not found. Generate titles first.");
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to load prompt: ${response.statusText}`);
      }

      const data = await response.json();
      setPrompt(data.prompt);
      setWorkTitle(data.work_title);
      setWorkAuthors(data.work_authors);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load prompt");
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
      const response = await fetch(
        `${API_BASE_URL}/sanitization/work/${workId}/manual-title-changes`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            llm_response: pastedResponse,
            source_key: "original_markdown",
            force: false,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save title changes");
      }

      const data = await response.json();
      setOperationSuccess(data.message || "Title changes saved successfully");
      setCopyDialogOpen(false);
      
      // Redirect back to workflow page
      setTimeout(() => {
        router.push(`/sanitization/${workId}`);
      }, 1500);
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to save title changes");
    } finally {
      setSaving(false);
    }
  };

  const handleRunPrompt = async () => {
    setRunning(true);
    setOperationError(null);
    setRunDialogOpen(false);

    try {
      const response = await fetch(
        `${API_BASE_URL}/sanitization/work/${workId}/suggest-title-changes`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_key: "original_markdown",
            use_full_model: true,
            force: false,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to run prompt");
      }

      const data = await response.json();
      setOperationSuccess(data.message || "Title changes generated successfully");
      
      // Redirect back to workflow page
      setTimeout(() => {
        router.push(`/sanitization/${workId}`);
      }, 1500);
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to run prompt");
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
            <Button onClick={fetchPrompt}>Retry</Button>
            <Button variant="outline" onClick={() => router.push(`/sanitization/${workId}`)}>
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
            onClick={() => router.push(`/sanitization/${workId}`)}
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
            <h1 className="text-2xl font-bold">Generate Title Changes</h1>
            <p className="text-sm text-muted-foreground">
              {workTitle && <span>{workTitle}</span>}
              {workAuthors && <span> • {workAuthors}</span>}
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
                  Run Prompt
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
              Paste the response from your LLM here to save the title changes
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-hidden py-4">
            <Textarea
              value={pastedResponse}
              onChange={(e) => setPastedResponse(e.target.value)}
              placeholder="Paste the LLM response here..."
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
                "Save Changes"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Run Confirmation Dialog */}
      <Dialog open={runDialogOpen} onOpenChange={setRunDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Run LLM Prompt?</DialogTitle>
            <DialogDescription>
              This will automatically run the prompt using the FULL model
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <p className="font-medium mb-2">This will use the FULL model which is:</p>
                <ul className="text-sm space-y-1 ml-4 list-disc">
                  <li>More expensive (higher API costs)</li>
                  <li>Slower (may take 30-60 seconds)</li>
                  <li>More accurate for complex documents</li>
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

