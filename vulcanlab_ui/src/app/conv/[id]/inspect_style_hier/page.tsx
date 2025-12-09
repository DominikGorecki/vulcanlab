"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { TitlesViewer } from "@/components/titles-viewer";
import {
  AlertCircle,
  CheckCircle2,
  Loader2Icon,
  Save,
  Sparkles,
  AlignVerticalJustifyCenter,
  Link2Off,
  Link2,
  ChevronLeft,
  HelpCircle,
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

interface FileMetrics {
  total_headings: number;
  h1_h2_count: number;
  max_depth: number;
  avg_depth: number;
  coverage_score: number;
  hierarchy_score: number;
  chunkability_score: number;
  target_size_sections: number;
  small_sections: number;
  large_sections: number;
  level_jump_count: number;
  penalty_total: number;
  final_score: number;
}

interface Suggestion {
  style_metrics: FileMetrics;
  hier_metrics: FileMetrics;
  winner: "style" | "hier";
  score_difference: number;
}

export default function InspectStyleHierPage() {
  const params = useParams();
  const router = useRouter();
  const fileId = params.id as string;

  // Content states
  const [styleContent, setStyleContent] = useState("");
  const [hierContent, setHierContent] = useState("");
  
  // Modified states
  const [styleModified, setStyleModified] = useState(false);
  const [hierModified, setHierModified] = useState(false);
  
  // Original content for comparison
  const [originalStyleContent, setOriginalStyleContent] = useState("");
  const [originalHierContent, setOriginalHierContent] = useState("");

  // Scroll sync states
  const [syncScroll, setSyncScroll] = useState(true);
  const [styleScrollTop, setStyleScrollTop] = useState(0);
  const [hierScrollTop, setHierScrollTop] = useState(0);

  // Alignment state (default to true)
  const [isAligned, setIsAligned] = useState(true);
  const [alignedStyleContent, setAlignedStyleContent] = useState("");
  const [alignedHierContent, setAlignedHierContent] = useState("");

  // Loading states
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<"style" | "hier" | null>(null);
  const [selecting, setSelecting] = useState<"style" | "hier" | null>(null);
  const [loadingSuggestion, setLoadingSuggestion] = useState(false);

  // Error states
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Suggestion state
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null);

  // Selection dialog state
  const [selectionDialog, setSelectionDialog] = useState<{
    open: boolean;
    fileType: "style" | "hier" | null;
  }>({ open: false, fileType: null });

  // Help dialog state
  const [helpDialogOpen, setHelpDialogOpen] = useState(false);

  // Warning dialog for existing .md file
  const [baseMdExists, setBaseMdExists] = useState(false);
  const [baseMdWarningOpen, setBaseMdWarningOpen] = useState(false);

  // Fetch file contents and suggestion on mount
  useEffect(() => {
    fetchFiles();
    fetchSuggestion();
    checkBaseMdExists();
  }, [fileId]);

  // Auto-align when content is first loaded
  useEffect(() => {
    if (styleContent && hierContent && isAligned && !alignedStyleContent && !alignedHierContent) {
      alignTitles();
    }
  }, [styleContent, hierContent]);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch both files in parallel
      const [styleRes, hierRes] = await Promise.all([
        fetch(`${API_BASE_URL}/conv/file-content/${fileId}/style`),
        fetch(`${API_BASE_URL}/conv/file-content/${fileId}/hier`),
      ]);

      if (!styleRes.ok || !hierRes.ok) {
        throw new Error("Failed to load files");
      }

      const styleData = await styleRes.json();
      const hierData = await hierRes.json();

      setStyleContent(styleData.content);
      setHierContent(hierData.content);
      setOriginalStyleContent(styleData.content);
      setOriginalHierContent(hierData.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load files");
    } finally {
      setLoading(false);
    }
  };

  const fetchSuggestion = async () => {
    try {
      setLoadingSuggestion(true);
      const response = await fetch(`${API_BASE_URL}/conv/suggestion/${fileId}`);
      
      if (!response.ok) {
        throw new Error("Failed to load suggestion");
      }

      const data = await response.json();
      setSuggestion(data);
    } catch (err) {
      console.error("Error loading suggestion:", err);
      // Don't show error to user, suggestion is optional
    } finally {
      setLoadingSuggestion(false);
    }
  };

  const checkBaseMdExists = async () => {
    try {
      // Try to fetch the base .md file (not style or hier)
      const response = await fetch(`${API_BASE_URL}/conv/file-content/${fileId}/base`);
      
      if (response.ok) {
        setBaseMdExists(true);
        setBaseMdWarningOpen(true);
      } else {
        setBaseMdExists(false);
      }
    } catch (err) {
      // If fetch fails, assume file doesn't exist
      setBaseMdExists(false);
    }
  };

  const handleSave = async (fileType: "style" | "hier") => {
    setSaving(fileType);
    setSaveError(null);

    try {
      // Get the current content (aligned or unaligned)
      let content: string;
      if (isAligned) {
        content = fileType === "style" ? alignedStyleContent : alignedHierContent;
      } else {
        content = fileType === "style" ? styleContent : hierContent;
      }

      // Send title edits to API (API handles applying edits to the actual markdown file)
      const response = await fetch(
        `${API_BASE_URL}/conv/file-content/${fileId}/${fileType}`,
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

      // API returns the updated titles after applying edits
      const responseData = await response.json();
      const updatedTitles = responseData.content;

      // Update the content with what was actually saved
      if (fileType === "style") {
        setStyleContent(updatedTitles);
        setOriginalStyleContent(updatedTitles);
        setStyleModified(false);
      } else {
        setHierContent(updatedTitles);
        setOriginalHierContent(updatedTitles);
        setHierModified(false);
      }

      // If we're in aligned mode, re-run alignment with the new content
      if (isAligned) {
        // Wait a bit for state to update
        setTimeout(() => {
          alignTitles();
        }, 100);
      }
    } catch (err) {
      setSaveError(
        err instanceof Error ? err.message : "Failed to save file"
      );
    } finally {
      setSaving(null);
    }
  };

  const handleSelectClick = (fileType: "style" | "hier") => {
    setSelectionDialog({ open: true, fileType });
  };

  const handleSelectConfirm = async () => {
    const fileType = selectionDialog.fileType;
    if (!fileType) return;

    setSelecting(fileType);
    setSaveError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/conv/select-file/${fileId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ file_type: fileType }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to select file");
      }

      // Success - close dialog
      setSelectionDialog({ open: false, fileType: null });
      
      // Redirect back to the conversion page
      router.push(`/conv/${fileId}`);
    } catch (err) {
      setSaveError(
        err instanceof Error ? err.message : "Failed to select file"
      );
    } finally {
      setSelecting(null);
    }
  };

  const handleStyleContentChange = (newContent: string) => {
    if (isAligned) {
      setAlignedStyleContent(newContent);
      // Mark as modified if different from original
      setStyleModified(true);
    } else {
      setStyleContent(newContent);
      setStyleModified(newContent !== originalStyleContent);
    }
  };

  const handleHierContentChange = (newContent: string) => {
    if (isAligned) {
      setAlignedHierContent(newContent);
      // Mark as modified if different from original
      setHierModified(true);
    } else {
      setHierContent(newContent);
      setHierModified(newContent !== originalHierContent);
    }
  };

  const handleStyleScroll = (scrollTop: number, scrollHeight: number, clientHeight: number) => {
    if (syncScroll) {
      setHierScrollTop(scrollTop);
    }
  };

  const handleHierScroll = (scrollTop: number, scrollHeight: number, clientHeight: number) => {
    if (syncScroll) {
      setStyleScrollTop(scrollTop);
    }
  };

  const parseLineNumber = (line: string): number | null => {
    const match = line.match(/^(\d+):/);
    return match ? parseInt(match[1], 10) : null;
  };

  const alignTitles = () => {
    const styleLines = styleContent.split('\n');
    const hierLines = hierContent.split('\n');

    // Parse line numbers and content
    const styleMap = new Map<number, string>();
    const hierMap = new Map<number, string>();
    const allLineNumbers = new Set<number>();

    styleLines.forEach(line => {
      const lineNum = parseLineNumber(line);
      if (lineNum !== null) {
        styleMap.set(lineNum, line);
        allLineNumbers.add(lineNum);
      }
    });

    hierLines.forEach(line => {
      const lineNum = parseLineNumber(line);
      if (lineNum !== null) {
        hierMap.set(lineNum, line);
        allLineNumbers.add(lineNum);
      }
    });

    // Sort line numbers
    const sortedLineNumbers = Array.from(allLineNumbers).sort((a, b) => a - b);

    // Build aligned content with ***MISSING*** placeholders
    const alignedStyle: string[] = [];
    const alignedHier: string[] = [];

    sortedLineNumbers.forEach(lineNum => {
      const styleLine = styleMap.get(lineNum);
      const hierLine = hierMap.get(lineNum);

      // Add line with ***MISSING*** placeholder if missing
      alignedStyle.push(styleLine || `${lineNum}: ***MISSING***`);
      alignedHier.push(hierLine || `${lineNum}: ***MISSING***`);
    });

    setAlignedStyleContent(alignedStyle.join('\n'));
    setAlignedHierContent(alignedHier.join('\n'));
    setIsAligned(true);
  };

  const unalignTitles = () => {
    // Check if there are unsaved changes in aligned mode
    const hasStyleChanges = isAligned && alignedStyleContent !== styleContent;
    const hasHierChanges = isAligned && alignedHierContent !== hierContent;
    
    if (hasStyleChanges || hasHierChanges) {
      const confirmed = window.confirm(
        "You have unsaved changes in aligned mode. Unaligning will discard these changes. Continue?"
      );
      if (!confirmed) {
        return;
      }
    }
    
    setIsAligned(false);
    // Clear modified flags since we're discarding aligned changes
    setStyleModified(false);
    setHierModified(false);
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
          <Button onClick={fetchFiles}>Retry</Button>
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
            <h1 className="text-2xl font-bold">Style vs Hier Comparison</h1>
            <p className="text-sm text-muted-foreground">
              File ID: <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{fileId}</code>
            </p>
          </div>
        </div>
        
        {/* Controls in header */}
        <div className="flex items-center gap-2">
          {/* Sync scroll toggle */}
          <Button
            onClick={() => setSyncScroll(!syncScroll)}
            variant={syncScroll ? "default" : "outline"}
            size="sm"
            className="gap-2"
          >
            {syncScroll ? (
              <Link2 className="h-4 w-4" />
            ) : (
              <Link2Off className="h-4 w-4" />
            )}
            {syncScroll ? "Synced" : "Sync Off"}
          </Button>

          {/* Align button */}
          {!isAligned ? (
            <Button
              onClick={alignTitles}
              variant="outline"
              size="sm"
              className="gap-2"
            >
              <AlignVerticalJustifyCenter className="h-4 w-4" />
              Align by Line
            </Button>
          ) : (
            <Button
              onClick={unalignTitles}
              variant="outline"
              size="sm"
              className="gap-2"
            >
              <AlignVerticalJustifyCenter className="h-4 w-4" />
              Unalign
            </Button>
          )}

          {/* Suggest button */}
          <Button
            onClick={fetchSuggestion}
            disabled={loadingSuggestion}
            variant="secondary"
            className="gap-2"
          >
            {loadingSuggestion ? (
              <Loader2Icon className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            {loadingSuggestion ? "Analyzing..." : "Suggest Best"}
          </Button>

          {/* Help button */}
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

      {/* Main content area - 50/50 split, reduced height to prevent cutoff */}
      <div className="flex-1 flex overflow-hidden" style={{ maxHeight: "calc(100vh - 180px)" }}>
        {/* Left: Style file */}
        <div className="w-1/2 flex flex-col border-r">
          <TitlesViewer
            content={isAligned ? alignedStyleContent : styleContent}
            onContentChange={handleStyleContentChange}
            title="style.md titles"
            onScroll={handleStyleScroll}
            syncScroll={syncScroll}
            externalScrollTop={styleScrollTop}
          />
        </div>

        {/* Right: Hier file */}
        <div className="w-1/2 flex flex-col">
          <TitlesViewer
            content={isAligned ? alignedHierContent : hierContent}
            onContentChange={handleHierContentChange}
            title="hier.md titles"
            onScroll={handleHierScroll}
            syncScroll={syncScroll}
            externalScrollTop={hierScrollTop}
          />
        </div>
      </div>

      {/* Bottom action bar */}
      <div className="border-t bg-card p-4 flex items-center gap-4">
        {/* Style file actions */}
        <div className="flex items-center gap-3">
          <Button
            onClick={() => handleSave("style")}
            disabled={!styleModified || saving !== null}
            size="sm"
            className="gap-2"
          >
            {saving === "style" ? (
              <Loader2Icon className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Save Style
            {styleModified && <span className="text-xs">(modified)</span>}
          </Button>
          
          <Button
            onClick={() => handleSelectClick("style")}
            disabled={selecting !== null}
            variant="outline"
            size="sm"
            className="gap-2"
          >
            <CheckCircle2 className="h-4 w-4" />
            Select Style
          </Button>

          {suggestion && suggestion.winner === "style" && (
            <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
              <Sparkles className="h-4 w-4" />
              <span className="font-medium">Recommended</span>
            </div>
          )}
        </div>

        {/* Separator */}
        <div className="flex-1 border-l mx-4" />

        {/* Hier file actions */}
        <div className="flex items-center gap-3">
          <Button
            onClick={() => handleSave("hier")}
            disabled={!hierModified || saving !== null}
            size="sm"
            className="gap-2"
          >
            {saving === "hier" ? (
              <Loader2Icon className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Save Hier
            {hierModified && <span className="text-xs">(modified)</span>}
          </Button>
          
          <Button
            onClick={() => handleSelectClick("hier")}
            disabled={selecting !== null}
            variant="outline"
            size="sm"
            className="gap-2"
          >
            <CheckCircle2 className="h-4 w-4" />
            Select Hier
          </Button>

          {suggestion && suggestion.winner === "hier" && (
            <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
              <Sparkles className="h-4 w-4" />
              <span className="font-medium">Recommended</span>
            </div>
          )}
        </div>
      </div>

      {/* Error display */}
      {saveError && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-destructive text-destructive-foreground px-4 py-2 rounded-md shadow-lg flex items-center gap-2 z-50">
          <AlertCircle className="h-4 w-4" />
          {saveError}
        </div>
      )}

      {/* Selection confirmation dialog */}
      <Dialog
        open={selectionDialog.open}
        onOpenChange={(open) => setSelectionDialog({ open, fileType: null })}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm File Selection</DialogTitle>
            <DialogDescription>
              Are you sure you want to select <strong>{selectionDialog.fileType}.md</strong> as the main file?
              <br />
              <br />
              This will copy it to <strong>&lt;base&gt;.md</strong> and will be used as the final version.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSelectionDialog({ open: false, fileType: null })}
              disabled={selecting !== null}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSelectConfirm}
              disabled={selecting !== null}
            >
              {selecting ? (
                <>
                  <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                  Selecting...
                </>
              ) : (
                "Confirm Selection"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Help Dialog */}
      <Dialog open={helpDialogOpen} onOpenChange={setHelpDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Help - Style vs Hier Comparison</DialogTitle>
          </DialogHeader>
          <div className="py-4 space-y-3">
            <p className="text-sm text-muted-foreground">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do
              eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim
              ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
              aliquip ex ea commodo consequat.
            </p>
            <p className="text-sm text-muted-foreground">
              Duis aute irure dolor in reprehenderit in voluptate velit esse cillum
              dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non
              proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
            </p>
          </div>
          <DialogFooter>
            <Button onClick={() => setHelpDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Base MD exists warning */}
      <Dialog open={baseMdWarningOpen} onOpenChange={setBaseMdWarningOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Warning: Base File Already Exists</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-muted-foreground space-y-2">
                <p>
                  The base markdown file (<code className="text-xs bg-muted px-1 py-0.5 rounded">&lt;file&gt;.md</code>) 
                  already exists.
                </p>
                <p>
                  If you select either the <strong>style</strong> or <strong>hier</strong> file, 
                  the system will not be able to overwrite the existing base file.
                </p>
                <p className="font-medium">
                  To select a new file, please delete or rename the existing base file first.
                </p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setBaseMdWarningOpen(false)}>Understood</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
