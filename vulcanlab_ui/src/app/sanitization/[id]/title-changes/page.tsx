"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

interface HeadingRow {
  line_num: number;
  original_heading: string;
  original_title: string;
  suggested_action: string;
  suggested_title: string;
}

interface HeadingTableData {
  work_id: number;
  source_file: string;
  rows: HeadingRow[];
  filename: string;
  hash: string;
}

export default function TitleChangesTablePage() {
  const params = useParams();
  const router = useRouter();
  const workId = params.id as string;

  // Data states
  const [tableData, setTableData] = useState<HeadingTableData | null>(null);
  const [originalRows, setOriginalRows] = useState<HeadingRow[]>([]);
  const [currentRows, setCurrentRows] = useState<HeadingRow[]>([]);
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
        `${API_BASE_URL}/sanitization/work/${workId}/title-changes/table`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Work not found or title changes not generated yet.");
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to load table: ${response.statusText}`);
      }

      const data: HeadingTableData = await response.json();
      setTableData(data);
      setOriginalRows(data.rows);
      setCurrentRows(data.rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load table data");
    } finally {
      setLoading(false);
    }
  };

  const handleActionChange = (lineNum: number, newAction: string) => {
    setCurrentRows((prev) =>
      prev.map((row) =>
        row.line_num === lineNum
          ? {
              ...row,
              suggested_action: newAction,
              suggested_title: newAction === "REMOVE" ? "" : row.suggested_title,
            }
          : row
      )
    );
  };

  const handleTitleChange = (lineNum: number, newTitle: string) => {
    setCurrentRows((prev) =>
      prev.map((row) =>
        row.line_num === lineNum ? { ...row, suggested_title: newTitle } : row
      )
    );
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/sanitization/work/${workId}/title-changes/table`,
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

      const updatedData: HeadingTableData = await response.json();
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
              onClick={() => router.push(`/sanitization/${workId}`)}
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
            <h1 className="text-2xl font-bold">Title Changes</h1>
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
                <TableHead className="w-20">Line #</TableHead>
                <TableHead className="w-24">Heading</TableHead>
                <TableHead className="w-1/3">Title</TableHead>
                <TableHead className="w-32">Heading Δ</TableHead>
                <TableHead className="w-1/3">Title Δ</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {currentRows.map((row) => (
                <TableRow key={row.line_num}>
                  <TableCell className="font-mono text-sm">{row.line_num}</TableCell>
                  <TableCell className="font-semibold">{row.original_heading}</TableCell>
                  <TableCell className="text-sm truncate max-w-xs" title={row.original_title}>
                    {row.original_title}
                  </TableCell>
                  <TableCell>
                    <Select
                      value={row.suggested_action}
                      onValueChange={(val) => handleActionChange(row.line_num, val)}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="H1">H1</SelectItem>
                        <SelectItem value="H2">H2</SelectItem>
                        <SelectItem value="H3">H3</SelectItem>
                        <SelectItem value="H4">H4</SelectItem>
                        <SelectItem value="H5">H5</SelectItem>
                        <SelectItem value="H6">H6</SelectItem>
                        <SelectItem value="REMOVE">REMOVE</SelectItem>
                      </SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell>
                    <Input
                      value={row.suggested_title}
                      onChange={(e) => handleTitleChange(row.line_num, e.target.value)}
                      disabled={row.suggested_action === "REMOVE"}
                      className="text-sm"
                      placeholder={row.suggested_action === "REMOVE" ? "Removed" : ""}
                    />
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
            <DialogDescription>Interactive Title Changes Editor</DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-3">
            <p className="text-sm text-muted-foreground">
              This table shows all headings from your document. You can interactively
              modify heading levels and titles before applying changes.
            </p>
            <div className="text-sm text-muted-foreground space-y-2">
              <p>
                <strong>Columns:</strong>
              </p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>
                  <strong>Line #</strong> - Line number in the original document
                </li>
                <li>
                  <strong>Heading</strong> - Current heading level (H1-H6)
                </li>
                <li>
                  <strong>Title</strong> - Current title text
                </li>
                <li>
                  <strong>Heading Δ</strong> - Change heading level or REMOVE
                </li>
                <li>
                  <strong>Title Δ</strong> - Modify title text (disabled if REMOVE)
                </li>
              </ul>
            </div>
            <div className="text-sm text-muted-foreground space-y-2">
              <p>
                <strong>Actions:</strong>
              </p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>Select a different heading level (H1-H6) to change it</li>
                <li>Select REMOVE to delete the heading entirely</li>
                <li>Edit the title text in the input field</li>
                <li>
                  If you keep the original heading level, no change will be saved
                </li>
              </ul>
            </div>
            <p className="text-sm text-muted-foreground">
              Click <strong>Save</strong> to persist your changes. Only actual changes
              are saved to the file.
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
