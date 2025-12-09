"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  AlertCircle,
  ChevronLeft,
  HelpCircle,
  Loader2Icon,
  Save,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { MarkdownEditor } from "@/components/markdown-editor";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function InspectTocTitlesPage() {
  const params = useParams();
  const router = useRouter();
  const fileId = params.id as string;

  // Content states
  const [content, setContent] = useState("");
  const [originalContent, setOriginalContent] = useState("");
  const [modified, setModified] = useState(false);

  // Loading states
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [loadingPrompt, setLoadingPrompt] = useState(false);

  // Error states
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Dialog states
  const [helpDialogOpen, setHelpDialogOpen] = useState(false);
  const [manualDialogOpen, setManualDialogOpen] = useState(false);
  const [manualPrompt, setManualPrompt] = useState("");
  const [copySuccess, setCopySuccess] = useState(false);

  // Fetch file content on mount
  useEffect(() => {
    fetchFileContent();
  }, [fileId]);

  const fetchFileContent = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/conv/file-content/${fileId}/toc_titles`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("File not found. It may have been deleted or moved.");
        }
        throw new Error(`Failed to load file: ${response.statusText}`);
      }

      const data = await response.json();
      setContent(data.content);
      setOriginalContent(data.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load file");
    } finally {
      setLoading(false);
    }
  };

  const fetchManualPrompt = async () => {
    try {
      setLoadingPrompt(true);
      const response = await fetch(`${API_BASE_URL}/conv/manual-prompt-toc-titles`);

      if (!response.ok) {
        throw new Error("Failed to load manual prompt");
      }

      const data = await response.json();
      setManualPrompt(data.content);
    } catch (err) {
      console.error("Error loading manual prompt:", err);
      setManualPrompt("Error loading manual prompt. Please try again.");
    } finally {
      setLoadingPrompt(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/conv/file-content/${fileId}/toc_titles`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save file");
      }

      // Update original content to match saved content
      setOriginalContent(content);
      setModified(false);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save file");
    } finally {
      setSaving(false);
    }
  };

  const handleContentChange = (newContent: string) => {
    setContent(newContent);
    setModified(newContent !== originalContent);
  };

  const handleManualClick = () => {
    if (!manualPrompt) {
      fetchManualPrompt();
    }
    setManualDialogOpen(true);
  };

  const handleCopyPrompt = async () => {
    try {
      await navigator.clipboard.writeText(manualPrompt);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
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
          <Button onClick={fetchFileContent}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header with controls */}
      <div className="border-b bg-card p-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          {/* Back button */}
          <Button
            onClick={() => router.push(`/conv/${fileId}`)}
            variant="ghost"
            size="sm"
            className="gap-1"
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>

          <div className="border-l h-8" />

          <div>
            <h1 className="text-2xl font-bold">Table of Contents Titles <span className="text-sm text-muted-foreground">REQUIRED</span></h1>
            <p className="text-sm text-muted-foreground">
              File ID: <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{fileId}</code>
            </p>
          </div>
        </div>

        {/* Action buttons in header */}
        <div className="flex items-center gap-2">
          {modified && <span className="text-sm text-yellow-600 mr-2">Unsaved changes</span>}
          <Button
            onClick={() => setHelpDialogOpen(true)}
            variant="outline"
            size="sm"
            className="w-9 h-9 p-0"
          >
            <HelpCircle className="h-4 w-4" />
          </Button>

          <Button
            onClick={handleManualClick}
            variant="outline"
            size="sm"
            className="gap-2"
          >
            Manual
          </Button>

          <Button
            onClick={handleSave}
            disabled={!modified || saving}
            size="sm"
            className="gap-2"
          >
            {saving ? (
              <Loader2Icon className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Save
          </Button>


        </div>
      </div>

      {/* Main content area - editable markdown editor */}
      <div className="flex-1 flex">
        <div className="w-full flex flex-col p-4">
          <MarkdownEditor 
            content={content} 
            onChange={handleContentChange}
            viewMode="markdown-only"
            scrollMode="page"
          />
        </div>
      </div>

      {/* Bottom action bar removed - moved to top */}


      {/* Error display */}
      {saveError && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-destructive text-destructive-foreground px-4 py-2 rounded-md shadow-lg flex items-center gap-2 z-50">
          <AlertCircle className="h-4 w-4" />
          {saveError}
        </div>
      )}

      {/* Help Dialog */}
      <Dialog open={helpDialogOpen} onOpenChange={setHelpDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Help</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-muted-foreground">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do
              eiusmod tempor incididunt ut labore et dolore magna aliqua.
            </p>
          </div>
          <DialogFooter>
            <Button onClick={() => setHelpDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Manual Dialog */}
      <Dialog open={manualDialogOpen} onOpenChange={setManualDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Manual TOC Extraction</DialogTitle>
            <DialogDescription>
              Copy this prompt and use it with your favorite LLM
            </DialogDescription>
          </DialogHeader>

          <div className="py-4 overflow-y-auto max-h-[50vh]">
            {loadingPrompt ? (
              <div className="flex items-center justify-center py-8">
                <Loader2Icon className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <pre className="text-xs font-mono whitespace-pre-wrap bg-muted p-4 rounded-md select-text">
                {manualPrompt}
              </pre>
            )}
          </div>

          <div className="border-t pt-4">
            <p className="text-sm text-muted-foreground mb-4">
              Manually pass this prompt along with the PDF to your favorite LLM. Then
              copy the results and paste them into the toc_titles.md underneath.
            </p>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setManualDialogOpen(false);
                setCopySuccess(false);
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleCopyPrompt} disabled={loadingPrompt}>
              {copySuccess ? "Copied!" : "Copy"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
