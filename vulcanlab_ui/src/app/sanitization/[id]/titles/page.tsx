"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { MarkdownEditor } from "@/components/markdown-editor";
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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function InspectTitlesPage() {
  const params = useParams();
  const router = useRouter();
  const workId = params.id as string;

  // Content states
  const [content, setContent] = useState("");
  const [originalContent, setOriginalContent] = useState("");
  const [modified, setModified] = useState(false);

  // Loading states
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Error states
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Dialog states
  const [helpDialogOpen, setHelpDialogOpen] = useState(false);

  // Fetch file content on mount
  useEffect(() => {
    fetchFileContent();
  }, [workId]);

  const fetchFileContent = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/sanitization/work/${workId}/titles/content`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Titles file not found. Generate it first.");
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

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/sanitization/work/${workId}/titles/content`,
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
            <Button onClick={fetchFileContent}>Retry</Button>
            <Button variant="outline" onClick={() => router.push(`/sanitization/${workId}`)}>
              Back
            </Button>
          </div>
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
            onClick={() => router.push(`/sanitization/${workId}`)}
            variant="ghost"
            size="sm"
            className="gap-1"
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>

          <div className="border-l h-8" />

          <div>
            <h1 className="text-2xl font-bold">Extracted Titles</h1>
            <p className="text-sm text-muted-foreground">
              Work ID: <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{workId}</code>
            </p>
          </div>
        </div>

        {/* Action buttons in header */}
        <div className="flex items-center gap-2">
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

          <Button
            onClick={() => setHelpDialogOpen(true)}
            variant="outline"
            size="sm"
            className="w-9 h-9 p-0"
          >
            <HelpCircle className="h-4 w-4" />
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
            <DialogDescription>
              About Extracted Titles
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-muted-foreground mb-3">
              This file contains all the headings extracted from your markdown document,
              with their line numbers.
            </p>
            <p className="text-sm text-muted-foreground mb-3">
              <strong>Format:</strong> Each line shows <code>line_number: # Heading Text</code>
            </p>
            <p className="text-sm text-muted-foreground mb-3">
              You can edit this file to:
            </p>
            <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1 ml-2">
              <li>Fix heading text errors</li>
              <li>Adjust heading levels (# for H1, ## for H2, etc.)</li>
              <li>Remove unwanted headings</li>
            </ul>
            <p className="text-sm text-muted-foreground mt-3">
              Changes here will be used when generating title change suggestions.
            </p>
          </div>
          <DialogFooter>
            <Button onClick={() => setHelpDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

