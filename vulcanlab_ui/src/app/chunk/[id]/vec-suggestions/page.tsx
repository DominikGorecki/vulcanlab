"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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

interface VecSuggestionRow {
  line_num: number;
  heading: string;
  decision: string; // "VECTORIZE" or "SKIP"
}

interface VecSuggestionsTableData {
  work_id: number;
  rows: VecSuggestionRow[];
  filename: string;
  hash: string;
}

export default function VecSuggestionsTablePage() {
  const params = useParams();
  const router = useRouter();
  const workId = params.id as string;

  // Data states
  const [tableData, setTableData] = useState<VecSuggestionsTableData | null>(null);
  const [originalRows, setOriginalRows] = useState<VecSuggestionRow[]>([]);
  const [currentRows, setCurrentRows] = useState<VecSuggestionRow[]>([]);
  const [modified, setModified] = useState(false);

  // Loading states
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Error states
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Dialog states
  const [helpDialogOpen, setHelpDialogOpen] = useState(false);

  // Fetch table data on mount
  useEffect(() => {
    fetchTableData();
  }, [workId]);

  // Track modifications
  useEffect(() => {
    if (originalRows.length > 0 && currentRows.length > 0) {
      const isModified = JSON.stringify(originalRows) !== JSON.stringify(currentRows);
      setModified(isModified);
    }
  }, [originalRows, currentRows]);

  const fetchTableData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/chunk/work/${workId}/vec-suggestions/table`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Vec suggestions not found. Please generate them first.");
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to load table: ${response.statusText}`);
      }

      const data: VecSuggestionsTableData = await response.json();
      setTableData(data);
      setOriginalRows(data.rows);
      setCurrentRows(data.rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load table data");
    } finally {
      setLoading(false);
    }
  };

  const handleDecisionChange = (lineNum: number, newDecision: string) => {
    setCurrentRows((prev) =>
      prev.map((row) =>
        row.line_num === lineNum
          ? { ...row, decision: newDecision }
          : row
      )
    );
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/chunk/work/${workId}/vec-suggestions/table`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rows: currentRows }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save changes");
      }

      const updatedData: VecSuggestionsTableData = await response.json();
      setTableData(updatedData);
      setOriginalRows(updatedData.rows);
      setCurrentRows(updatedData.rows);
      setModified(false);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save changes");
    } finally {
      setSaving(false);
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
            <Button onClick={fetchTableData}>Retry</Button>
            <Button
              variant="outline"
              onClick={() => router.push(`/chunk/${workId}`)}
            >
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
            onClick={() => router.push(`/chunk/${workId}`)}
            variant="ghost"
            size="sm"
            className="gap-1"
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>

          <div className="border-l h-8" />

          <div>
            <h1 className="text-2xl font-bold">Vec Suggestions</h1>
            <p className="text-sm text-muted-foreground">
              Work ID:{" "}
              <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{workId}</code>
            </p>
          </div>
        </div>

        {/* Action buttons in header */}
        <div className="flex items-center gap-2">
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

      {/* Main content area - interactive table */}
      <div
        className="flex-1 flex overflow-hidden"
        style={{ maxHeight: "calc(100vh - 180px)" }}
      >
        <div className="w-full flex flex-col p-4 overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-20">Line</TableHead>
                <TableHead className="w-2/3">Title</TableHead>
                <TableHead className="w-1/3">Embed Vec Sugg</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {currentRows.map((row) => (
                <TableRow key={row.line_num}>
                  <TableCell className="font-mono text-sm">{row.line_num}</TableCell>
                  <TableCell className="text-sm">{row.heading}</TableCell>
                  <TableCell>
                    <Select
                      value={row.decision}
                      onValueChange={(val) => handleDecisionChange(row.line_num, val)}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="VECTORIZE">Vectorize</SelectItem>
                        <SelectItem value="SKIP">Skip</SelectItem>
                      </SelectContent>
                    </Select>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {currentRows.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <p>No headings found in the document.</p>
            </div>
          )}
        </div>
      </div>

      {/* Bottom action bar */}
      <div className="border-t bg-card p-4 flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {modified && <span>Unsaved changes</span>}
          {!modified && currentRows.length > 0 && (
            <span className="text-green-600">All changes saved</span>
          )}
        </div>

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
            <DialogDescription>Interactive Vec Suggestions Editor</DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-3">
            <p className="text-sm text-muted-foreground">
              This table shows all headings from your sanitized document. You can
              interactively modify vectorization decisions before applying chunks.
            </p>
            <div className="text-sm text-muted-foreground space-y-2">
              <p>
                <strong>Columns:</strong>
              </p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>
                  <strong>Line</strong> - Line number in the sanitized document
                </li>
                <li>
                  <strong>Title</strong> - Heading text with markdown symbols
                </li>
                <li>
                  <strong>Embed Vec Sugg</strong> - Vectorize or Skip this heading
                </li>
              </ul>
            </div>
            <div className="text-sm text-muted-foreground space-y-2">
              <p>
                <strong>Decisions:</strong>
              </p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>
                  <strong>Vectorize</strong> - This heading and its content will be
                  chunked and vectorized for search
                </li>
                <li>
                  <strong>Skip</strong> - This heading will not be included in vector
                  search (use for TOC, appendices, references)
                </li>
              </ul>
            </div>
            <p className="text-sm text-muted-foreground">
              Click <strong>Save</strong> to persist your changes. These decisions
              affect which headings become searchable chunks when you run "Apply
              Heading Chunks".
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
