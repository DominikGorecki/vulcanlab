"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, Eye, Loader2Icon, PlayCircle, Trash2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface InspectionItem {
  name: string;
  available: boolean;
  files_checked: string[];
}

interface InspectionResponse {
  items: InspectionItem[];
}

interface ReadinessResponse {
  ready: boolean;
  reasons: string[];
  base_name: string;
}

// Map inspection names to human-readable labels
const INSPECTION_LABELS: Record<string, string> = {
  inspect_style_hier: "Style vs Hier Comparison",
  inspect_toc_titles: "Table of Contents Titles (REQUIRED)",
  inspect_original_md: "Original Markdown (REQUIRED)",
};

// Map inspection names to descriptions
const INSPECTION_DESCRIPTIONS: Record<string, string> = {
  inspect_style_hier: "Compare style.md and hier.md versions side by side",
  inspect_toc_titles: "Review and edit table of contents titles",
  inspect_original_md: "View the original converted markdown file",
};

export default function ConvertedFilePage() {
  const params = useParams();
  const router = useRouter();
  const fileId = params.id as string;

  const [inspectionItems, setInspectionItems] = useState<InspectionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState<string | null>(null); // Track which item is being generated
  const [generateError, setGenerateError] = useState<string | null>(null);

  // Readiness state
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [checkingReadiness, setCheckingReadiness] = useState(false);

  // Delete state
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    fetchInspectionOptions();
    fetchReadiness();
  }, [fileId]);

  const fetchInspectionOptions = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/conv/inspection/${fileId}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("File not found. It may have been deleted or moved.");
        }
        throw new Error(`Failed to load inspection options: ${response.statusText}`);
      }

      const data: InspectionResponse = await response.json();
      setInspectionItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load inspection options");
    } finally {
      setLoading(false);
    }
  };

  const fetchReadiness = async () => {
    try {
      setCheckingReadiness(true);

      const response = await fetch(`${API_BASE_URL}/conv/readiness/${fileId}`);
      
      if (!response.ok) {
        // Don't set error for readiness check - just leave it as not ready
        console.error("Failed to check readiness:", response.statusText);
        return;
      }

      const data: ReadinessResponse = await response.json();
      setReadiness(data);
    } catch (err) {
      console.error("Error checking readiness:", err);
    } finally {
      setCheckingReadiness(false);
    }
  };

  const handleInspect = (inspectionName: string) => {
    router.push(`/conv/${fileId}/${inspectionName}`);
  };

  const handleGenerate = async (inspectionName: string) => {
    // Only handle toc_titles generation for now
    if (inspectionName !== "inspect_toc_titles") {
      console.log(`Generate ${inspectionName} for file ${fileId} - not yet implemented`);
      return;
    }

    try {
      setGenerating(inspectionName);
      setGenerateError(null);

      const response = await fetch(`${API_BASE_URL}/conv/generate-toc-titles/${fileId}`, {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Generation failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Refresh inspection items and readiness to show the newly created file
      await fetchInspectionOptions();
      await fetchReadiness();
      
      // Show success message (could be enhanced with a toast notification)
      if (!data.success) {
        setGenerateError(data.message);
      }
    } catch (err) {
      setGenerateError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(null);
    }
  };

  const handleAddToDatabase = () => {
    router.push(`/conv/${fileId}/add`);
  };

  const handleDelete = async () => {
    try {
      setDeleting(true);
      setDeleteError(null);

      const response = await fetch(`${API_BASE_URL}/conv/delete/${fileId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Delete failed: ${response.statusText}`);
      }

      // Success - redirect to conversion list
      router.push("/conv");
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Delete failed");
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Review Conversion</h2>
          <p className="text-muted-foreground">
            Review and finalize the converted document before adding to database.
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Review Conversion</h2>
          <p className="text-muted-foreground">
            Review and finalize the converted document before adding to database.
          </p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
            <Button onClick={fetchInspectionOptions} className="mt-4">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Review Conversion</h2>
        <p className="text-muted-foreground">
          Review and finalize the converted document before adding to database.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Inspection Options</CardTitle>
          <CardDescription>
            File ID: <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{fileId}</code>
          </CardDescription>
        </CardHeader>
        <CardContent>
          {generateError && (
            <div className="mb-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
              <div className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <p className="text-sm">{generateError}</p>
              </div>
            </div>
          )}
          <div className="space-y-3">
            {inspectionItems.length === 0 ? (
              <div className="text-sm text-muted-foreground py-8 text-center">
                No inspection options available for this file.
              </div>
            ) : (
              inspectionItems
                .filter((item) =>
                  item.name !== "inspect_titles" &&
                  item.name !== "inspect_title_changes"
                )
                .map((item) => (
                <div
                  key={item.name}
                  className="flex items-start gap-4 p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="flex-shrink-0 mt-1">
                    {item.available ? (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-amber-500" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold mb-1">
                      {INSPECTION_LABELS[item.name] || item.name}
                    </h3>
                    <p className="text-xs text-muted-foreground mb-2">
                      {INSPECTION_DESCRIPTIONS[item.name] || "No description available"}
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {item.files_checked.map((file) => (
                        <code
                          key={file}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground"
                        >
                          {file}
                        </code>
                      ))}
                    </div>
                  </div>

                  <div className="flex-shrink-0">
                    {item.available ? (
                      <Button
                        size="sm"
                        onClick={() => handleInspect(item.name)}
                        className="gap-2"
                      >
                        <Eye className="h-4 w-4" />
                        Inspect
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={generating !== null || item.name !== "inspect_toc_titles"}
                        onClick={() => handleGenerate(item.name)}
                        className="gap-2"
                      >
                        {generating === item.name ? (
                          <Loader2Icon className="h-4 w-4 animate-spin" />
                        ) : (
                          <PlayCircle className="h-4 w-4" />
                        )}
                        {generating === item.name ? "Generating..." : "Generate"}
                      </Button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Next Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <p className="text-muted-foreground">
              Once you&apos;ve reviewed all necessary inspection items:
            </p>
            <ol className="list-decimal list-inside space-y-2 text-muted-foreground">
              <li>Verify the conversion quality using the inspection tools above</li>
              <li>Make any necessary manual corrections to the files</li>
              <li>Click &quot;Add to Database&quot; to finalize the conversion</li>
            </ol>
            
            {/* Show readiness status */}
            {readiness && !readiness.ready && (
              <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <div className="flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 flex-shrink-0 text-amber-500 mt-0.5" />
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-amber-700 dark:text-amber-400">
                      Not ready to add to database
                    </p>
                    <ul className="text-xs text-amber-600 dark:text-amber-500 space-y-1">
                      {readiness.reasons.map((reason, idx) => (
                        <li key={idx}>• {reason}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
            
            {readiness && readiness.ready && (
              <div className="mt-4 p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <p className="text-sm font-medium text-green-700 dark:text-green-400">
                    Ready to add to database
                  </p>
                </div>
              </div>
            )}
            
            <Button 
              className="mt-4" 
              variant="default" 
              disabled={!readiness?.ready || checkingReadiness}
              onClick={handleAddToDatabase}
            >
              {checkingReadiness ? (
                <>
                  <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                  Checking...
                </>
              ) : (
                "Add to Database"
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Danger Zone</CardTitle>
          <CardDescription>
            Permanently delete this conversion and all associated files
          </CardDescription>
        </CardHeader>
        <CardContent>
          {deleteError && (
            <div className="mb-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
              <div className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <p className="text-sm">{deleteError}</p>
              </div>
            </div>
          )}
          <div className="flex items-start gap-3">
            <div className="flex-1">
              <p className="text-sm text-muted-foreground mb-2">
                This will permanently delete all files associated with this conversion from the output directory and remove the database entry.
              </p>
              <p className="text-sm font-semibold text-destructive">
                This action cannot be undone.
              </p>
            </div>
            <Button
              variant="destructive"
              onClick={() => setShowDeleteDialog(true)}
              className="gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Conversion?</DialogTitle>
            <DialogDescription>
              This will permanently delete all files associated with this conversion and remove the database entry.
              This action is not recoverable.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-4">
              <p className="text-sm font-medium text-destructive mb-2">
                The following will be deleted:
              </p>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• All files in output directory with base name matching this conversion</li>
                <li>• Database entry for this conversion</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleting}
              className="gap-2"
            >
              {deleting ? (
                <>
                  <Loader2Icon className="h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4" />
                  Delete Permanently
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
