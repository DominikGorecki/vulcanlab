"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  AlertCircle,
  ChevronLeft,
  Copy,
  Loader2Icon,
  PlayCircle,
  Check,
  MessageSquare,
  Eye,
  List,
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { TextStats } from "@/components/text-stats";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AugmentPromptResponse {
  query_id: number;
  original_query: string;
  prompt: string;
  context_count: number;
}

export default function GeneratePage() {
  const params = useParams();
  const router = useRouter();
  const queryId = params.id as string;

  // Content states
  const [promptData, setPromptData] = useState<AugmentPromptResponse | null>(null);
  const [generatedResponse, setGeneratedResponse] = useState<string | null>(null);

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

  // View mode: 'prompt' or 'response'
  const [viewMode, setViewMode] = useState<"prompt" | "response">("prompt");

  // Source selection states
  const [selectedSourceCount, setSelectedSourceCount] = useState<number>(5);
  const [availableSourceCount, setAvailableSourceCount] = useState<number>(0);
  const [regenerating, setRegenerating] = useState(false);

  // Results state
  const [hasResults, setHasResults] = useState(false);

  useEffect(() => {
    fetchAvailableSourceCount();
    fetchPrompt();
    fetchResultsCount();
  }, [queryId]);

  const fetchAvailableSourceCount = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/rag/queries/${queryId}`);

      if (!response.ok) {
        throw new Error("Failed to load query details");
      }

      const data = await response.json();
      const contextLength = data.clean_retrieval_context?.length || 0;
      setAvailableSourceCount(contextLength);

      // Adjust selected count if it exceeds available
      if (selectedSourceCount > contextLength) {
        setSelectedSourceCount(Math.min(5, contextLength));
      }
    } catch (err) {
      console.error("Failed to fetch source count:", err);
      // Non-critical error - use fallback
      setAvailableSourceCount(5);
    }
  };

  const fetchResultsCount = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/rag/queries/${queryId}/results`);

      if (!response.ok) {
        setHasResults(false);
        return;
      }

      const data = await response.json();
      setHasResults(data.results && data.results.length > 0);
    } catch (err) {
      console.error("Failed to fetch results count:", err);
      setHasResults(false);
    }
  };

  const fetchPrompt = async (topN: number = selectedSourceCount) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/rag/queries/${queryId}/augment/prompt?top_n=${topN}`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Query not found or not ready for generation.");
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to load prompt: ${response.statusText}`);
      }

      const data: AugmentPromptResponse = await response.json();
      setPromptData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load prompt");
    } finally {
      setLoading(false);
    }
  };

  const handleSourceCountChange = async (value: string) => {
    const newCount = parseInt(value, 10);
    setSelectedSourceCount(newCount);
    setRegenerating(true);
    setOperationError(null);

    try {
      await fetchPrompt(newCount);
    } catch (err) {
      setOperationError("Failed to regenerate prompt with new source count");
    } finally {
      setRegenerating(false);
    }
  };

  const handleCopyPrompt = async () => {
    if (!promptData) return;

    try {
      await navigator.clipboard.writeText(promptData.prompt);
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
        `${API_BASE_URL}/rag/queries/${queryId}/augment/manual`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            response_text: pastedResponse,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save response");
      }

      const data = await response.json();
      setOperationSuccess(data.message || "Response saved successfully");
      setCopyDialogOpen(false);
      setGeneratedResponse(pastedResponse);
      setViewMode("response");
      // Refresh results count since we just created a new result
      await fetchResultsCount();
      // Redirect to the result detail page
      if (data.result_id) {
        router.push(`/rag/${queryId}/results/${data.result_id}`);
      }
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to save response");
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
        `${API_BASE_URL}/rag/queries/${queryId}/augment/run`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            force: false,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to run prompt");
      }

      const data = await response.json();
      setOperationSuccess(data.message || "Response generated and saved successfully");
      setGeneratedResponse(data.response_text);
      setViewMode("response");
      // Refresh results count since we just created a new result
      await fetchResultsCount();
      // Redirect to the result detail page
      if (data.result_id) {
        router.push(`/rag/${queryId}/results/${data.result_id}`);
      }
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
            <Button onClick={() => fetchPrompt()}>Retry</Button>
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
            <h1 className="text-2xl font-bold">Generate Response</h1>
            <p className="text-sm text-muted-foreground max-w-lg truncate">
              {promptData?.original_query}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          {/* Inspect Query */}
           <Button
            variant="outline"
            size="sm"
            onClick={() => router.push(`/rag/${queryId}/inspect`)}
            className="gap-1"
          >
            <Eye className="h-4 w-4" />
            Inspect
          </Button>

          {/* Results */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push(`/rag/${queryId}/results`)}
            className="gap-1"
            disabled={!hasResults}
          >
            <List className="h-4 w-4" />
            Results
          </Button>

          {/* View toggle */}
          {generatedResponse && (
          <div className="flex gap-2">
            <Button
              variant={viewMode === "prompt" ? "default" : "outline"}
              size="sm"
              onClick={() => setViewMode("prompt")}
            >
              Prompt
            </Button>
            <Button
              variant={viewMode === "response" ? "default" : "outline"}
              size="sm"
              onClick={() => setViewMode("response")}
            >
              Response
            </Button>
          </div>
        )}
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

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden" style={{ maxHeight: "calc(100vh - 220px)" }}>
        <div className="w-full flex flex-col p-4">
          {viewMode === "prompt" ? (
            <>
              {/* Source count selector and stats */}
              <div className="flex items-center gap-3 mb-3 pb-3 border-b">
                <Label htmlFor="source-count" className="text-sm font-medium">
                  Sources to include:
                </Label>
                <Select
                  value={selectedSourceCount.toString()}
                  onValueChange={handleSourceCountChange}
                  disabled={loading || regenerating}
                >
                  <SelectTrigger id="source-count" className="w-[140px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Array.from({ length: availableSourceCount }, (_, i) => i + 1).map(n => (
                      <SelectItem key={n} value={n.toString()}>
                        {n} {n === 1 ? 'source' : 'sources'}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <span className="text-sm text-muted-foreground">
                  ({availableSourceCount} available)
                </span>
                {regenerating && (
                  <Loader2Icon className="h-4 w-4 animate-spin text-muted-foreground" />
                )}
                <TextStats text={promptData?.prompt || ""} className="ml-auto" />
              </div>

              <Textarea
                value={promptData?.prompt || ""}
                readOnly
                className="flex-1 font-mono text-sm resize-none select-text"
                placeholder={regenerating ? "Regenerating prompt..." : "Loading prompt..."}
              />
            </>
          ) : (
            <Card className="flex-1 overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Generated Response
                </CardTitle>
                <CardDescription>
                  The LLM response to your query
                </CardDescription>
              </CardHeader>
              <CardContent className="h-full overflow-hidden pb-6">
                <ScrollArea className="h-full pr-4" style={{ maxHeight: "calc(100vh - 380px)" }}>
                  <MarkdownRenderer content={generatedResponse || ""} />
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Bottom action bar */}
      <div className="border-t bg-card p-4">
        <div className="flex items-center justify-between max-w-full">
          <div className="text-sm text-muted-foreground flex-1 mr-4">
            {viewMode === "prompt" ? (
              <p>
                Context: {promptData?.context_count || 0} of {availableSourceCount} sources included.
                Run the prompt to generate a response.
              </p>
            ) : (
              <p>
                Response saved to database. You can run again to generate a new response.
              </p>
            )}
          </div>
          <div className="flex gap-3 flex-shrink-0">
            {viewMode === "prompt" && (
              <>
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
              </>
            )}

            {viewMode === "response" && (
              <Button
                onClick={() => {
                  setViewMode("prompt");
                  setGeneratedResponse(null);
                }}
                variant="outline"
                className="gap-2"
              >
                <PlayCircle className="h-4 w-4" />
                Run Again
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Manual Paste Dialog */}
      <Dialog open={copyDialogOpen} onOpenChange={setCopyDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>Paste LLM Response</DialogTitle>
            <DialogDescription>
              Paste the LLM&apos;s response here. This will be saved as a result for this query.
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
            <DialogTitle>Run Augmented Prompt?</DialogTitle>
            <DialogDescription>
              This will generate a response using the FULL model with search enabled.
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
                  <li>More accurate and comprehensive</li>
                  <li>Has search enabled for additional context</li>
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

