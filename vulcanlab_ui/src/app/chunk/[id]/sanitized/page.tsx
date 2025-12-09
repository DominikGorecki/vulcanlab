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

export default function InspectSanitizedPage() {
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

  // Track content modifications
  useEffect(() => {
    setModified(content !== originalContent);
  }, [content, originalContent]);

  const fetchFileContent = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/chunk/work/${workId}/sanitized/content`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Sanitized file not found.");
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
        `${API_BASE_URL}/chunk/work/${workId}/sanitized/content`,
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

  const handleBack = () => {
    if (modified) {
      const confirmLeave = confirm(
        "You have unsaved changes. Are you sure you want to leave?"
      );
      if (!confirmLeave) return;
    }
    router.push(`/chunk/${workId}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={handleBack}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Error</h2>
          </div>
        </div>
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <div className="flex items-center gap-3 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <p>{error}</p>
          </div>
          <Button onClick={fetchFileContent} variant="outline" className="mt-4">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0 sticky top-0 z-10 bg-background/95 backdrop-blur py-2 border-b">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={handleBack}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div>
            <h2 className="text-3xl font-bold tracking-tight">
              Sanitized Markdown
            </h2>
            <p className="text-muted-foreground">
              View and edit the sanitized markdown file
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setHelpDialogOpen(true)}
          >
            <HelpCircle className="h-4 w-4 mr-2" />
            Help
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
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>

      {/* Save Error Alert */}
      {saveError && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4 shrink-0">
          <div className="flex items-center gap-3 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <div>
              <p className="font-medium">Failed to save</p>
              <p className="text-sm">{saveError}</p>
            </div>
          </div>
        </div>
      )}

      {/* Modified Indicator */}
      {modified && (
        <div className="rounded-lg border border-yellow-500 bg-yellow-50 p-3 shrink-0">
          <p className="text-sm text-yellow-800">
            You have unsaved changes. Click &quot;Save Changes&quot; to update the file.
          </p>
        </div>
      )}

      {/* Content Editor */}
      <div className="rounded-lg">
        <MarkdownEditor 
          content={content} 
          onChange={setContent}
          viewMode="both"
          scrollMode="page"
        />
      </div>

      {/* Help Dialog */}
      <Dialog open={helpDialogOpen} onOpenChange={setHelpDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Sanitized Markdown Help</DialogTitle>
            <DialogDescription>
              This is the sanitized version of your markdown document, ready for chunking.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 text-sm">
            <div>
              <h4 className="font-semibold mb-2">What is this file?</h4>
              <p className="text-muted-foreground">
                This is the cleaned and structured markdown version of your document
                after title changes have been applied. This file is used as input for
                the chunking operations.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Editing Guidelines</h4>
              <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
                <li>Make sure heading hierarchy is correct (# H1, ## H2, etc.)</li>
                <li>Avoid manual edits unless necessary</li>
                <li>Changes here will affect downstream chunking operations</li>
                <li>Save your changes before navigating away</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Hash Validation</h4>
              <p className="text-muted-foreground">
                When you save changes, the file hash will be updated in the database.
                This ensures file integrity throughout the processing pipeline.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setHelpDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
