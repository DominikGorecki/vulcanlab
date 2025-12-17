"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertCircle, Loader2Icon, FileText, Upload, AlertTriangle } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ErrorModal } from "@/components/ErrorModal";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types
interface Metadata {
  title: string;
  author: string | null;
  year: number | null;
}

interface MarkdownFile {
  filename: string;
  file_path: string;
  has_metadata: boolean;
  metadata: Metadata | null;
}

interface FilesResponse {
  files: MarkdownFile[];
}

interface DuplicateInfo {
  work_id: number;
  work_title: string;
}

interface ImportMetadata {
  title: string;
  author: string;
  year: string;
}

interface ImportResponse {
  work_id: number;
  status: string;
  duplicate_warning: string | null;
}

// Metadata Entry Modal Component
interface MetadataEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (metadata: ImportMetadata) => void;
  initialMetadata?: Metadata | null;
  filename: string;
}

function MetadataEntryModal({
  isOpen,
  onClose,
  onSubmit,
  initialMetadata,
  filename,
}: MetadataEntryModalProps) {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [year, setYear] = useState("");
  const [errors, setErrors] = useState<{ title?: string; author?: string; year?: string }>({});

  // Pre-populate form if file has metadata
  useEffect(() => {
    if (isOpen && initialMetadata) {
      setTitle(initialMetadata.title || "");
      setAuthor(initialMetadata.author || "");
      setYear(initialMetadata.year?.toString() || "");
      setErrors({});
    } else if (isOpen) {
      setTitle("");
      setAuthor("");
      setYear("");
      setErrors({});
    }
  }, [isOpen, initialMetadata]);

  const validate = (): boolean => {
    const newErrors: { title?: string; author?: string; year?: string } = {};

    if (!title.trim()) {
      newErrors.title = "Title is required";
    }

    if (!author.trim()) {
      newErrors.author = "Author is required";
    }

    if (year && year.trim()) {
      const yearNum = parseInt(year);
      if (isNaN(yearNum) || yearNum < 1000 || yearNum > 2100) {
        newErrors.year = "Year must be between 1000 and 2100";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validate()) {
      onSubmit({ title: title.trim(), author: author.trim(), year: year.trim() });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Enter Metadata</DialogTitle>
          <DialogDescription>
            Provide metadata for <strong>{filename}</strong>
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="title">
              Title <span className="text-destructive">*</span>
            </Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={handleKeyDown}
              className={errors.title ? "border-destructive" : ""}
              placeholder="Enter work title"
              autoFocus
            />
            {errors.title && (
              <p className="text-sm text-destructive">{errors.title}</p>
            )}
          </div>

          <div className="grid gap-2">
            <Label htmlFor="author">
              Author <span className="text-destructive">*</span>
            </Label>
            <Input
              id="author"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              onKeyDown={handleKeyDown}
              className={errors.author ? "border-destructive" : ""}
              placeholder="Enter author name"
            />
            {errors.author && (
              <p className="text-sm text-destructive">{errors.author}</p>
            )}
          </div>

          <div className="grid gap-2">
            <Label htmlFor="year">Year (optional)</Label>
            <Input
              id="year"
              type="number"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              onKeyDown={handleKeyDown}
              className={errors.year ? "border-destructive" : ""}
              placeholder="Enter publication year"
              min="1000"
              max="2100"
            />
            {errors.year && (
              <p className="text-sm text-destructive">{errors.year}</p>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>Next</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Duplicate Warning Modal Component
interface DuplicateWarningModalProps {
  isOpen: boolean;
  onProceed: () => void;
  onCancel: () => void;
  duplicateInfo: DuplicateInfo;
}

function DuplicateWarningModal({
  isOpen,
  onProceed,
  onCancel,
  duplicateInfo,
}: DuplicateWarningModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onCancel()}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-yellow-600" />
            <DialogTitle>Duplicate Work Detected</DialogTitle>
          </div>
          <DialogDescription>
            A work with similar title and author already exists in the database.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <div className="rounded-md bg-yellow-50 dark:bg-yellow-900/20 p-4 border border-yellow-200 dark:border-yellow-900">
            <p className="text-sm font-medium text-foreground">
              Existing work:
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              <strong>ID:</strong> {duplicateInfo.work_id}
            </p>
            <p className="text-sm text-muted-foreground">
              <strong>Title:</strong> {duplicateInfo.work_title}
            </p>
          </div>

          <p className="text-sm text-muted-foreground mt-4">
            You can proceed with the import anyway, or cancel to avoid creating a duplicate.
          </p>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={onProceed}>Import Anyway</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Sanitization Decision Modal Component
interface SanitizationDecisionModalProps {
  isOpen: boolean;
  onDecision: (isSanitized: boolean) => void;
  onCancel: () => void;
  loading: boolean;
}

function SanitizationDecisionModal({
  isOpen,
  onDecision,
  onCancel,
  loading,
}: SanitizationDecisionModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && !loading && onCancel()}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Markdown Sanitization</DialogTitle>
          <DialogDescription>
            Is this markdown already sanitized?
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <p className="text-sm text-muted-foreground mb-4">
            Sanitization removes formatting artifacts and normalizes the markdown structure
            for better processing. Choose whether your file needs this step:
          </p>

          <div className="space-y-3">
            <div className="p-3 rounded-md border bg-card">
              <p className="text-sm font-medium">Sanitized Markdown</p>
              <p className="text-xs text-muted-foreground mt-1">
                Clean markdown without formatting artifacts, ready for chunking
              </p>
            </div>

            <div className="p-3 rounded-md border bg-card">
              <p className="text-sm font-medium">Unsanitized Markdown</p>
              <p className="text-xs text-muted-foreground mt-1">
                Raw markdown that needs sanitization processing before chunking
              </p>
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            onClick={onCancel}
            disabled={loading}
            className="w-full sm:w-auto"
          >
            Cancel
          </Button>
          <Button
            onClick={() => onDecision(false)}
            disabled={loading}
            variant="secondary"
            className="w-full sm:w-auto"
          >
            {loading ? (
              <>
                <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                Importing...
              </>
            ) : (
              "No, needs sanitization"
            )}
          </Button>
          <Button
            onClick={() => onDecision(true)}
            disabled={loading}
            className="w-full sm:w-auto"
          >
            {loading ? (
              <>
                <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                Importing...
              </>
            ) : (
              "Yes, it's sanitized"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Main Import Page Component
export default function MarkdownImportPage() {
  const router = useRouter();
  const [files, setFiles] = useState<MarkdownFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [selectedFile, setSelectedFile] = useState<MarkdownFile | null>(null);
  const [showMetadataModal, setShowMetadataModal] = useState(false);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [showSanitizationModal, setShowSanitizationModal] = useState(false);
  const [importing, setImporting] = useState(false);

  // Data states
  const [metadata, setMetadata] = useState<ImportMetadata>({ title: "", author: "", year: "" });
  const [duplicateInfo, setDuplicateInfo] = useState<DuplicateInfo | null>(null);
  const [importError, setImportError] = useState<{ title: string; message: string; detail?: string } | null>(null);

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/api/v1/markdown/files`);

      if (!response.ok) {
        throw new Error(`Failed to load files: ${response.statusText}`);
      }

      const data: FilesResponse = await response.json();
      setFiles(data.files);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load files");
    } finally {
      setLoading(false);
    }
  };

  const handleImportClick = (file: MarkdownFile) => {
    setSelectedFile(file);
    setShowMetadataModal(true);
  };

  const handleMetadataSubmit = async (submittedMetadata: ImportMetadata) => {
    setMetadata(submittedMetadata);
    setShowMetadataModal(false);

    // Check for duplicates
    try {
      const params = new URLSearchParams({
        title: submittedMetadata.title,
        author: submittedMetadata.author,
      });

      const response = await fetch(
        `${API_BASE_URL}/api/v1/markdown/check-duplicate?${params}`
      );

      if (response.ok) {
        const data = await response.json();

        if (data.exists) {
          // Show duplicate modal
          setDuplicateInfo({
            work_id: data.work_id,
            work_title: data.work_title,
          });
          setShowDuplicateModal(true);
        } else {
          // No duplicate, go to sanitization
          setShowSanitizationModal(true);
        }
      } else {
        // Error checking duplicates, proceed anyway
        setShowSanitizationModal(true);
      }
    } catch (err) {
      // Error checking duplicates, proceed anyway
      setShowSanitizationModal(true);
    }
  };

  const handleDuplicateDecision = (proceed: boolean) => {
    setShowDuplicateModal(false);
    if (proceed) {
      setShowSanitizationModal(true);
    } else {
      // Reset state
      setSelectedFile(null);
      setMetadata({ title: "", author: "", year: "" });
      setDuplicateInfo(null);
    }
  };

  const handleSanitizationDecision = async (isSanitized: boolean) => {
    if (!selectedFile) return;

    try {
      setImporting(true);

      const requestBody = {
        filename: selectedFile.filename,
        title: metadata.title,
        author: metadata.author,
        year: metadata.year ? parseInt(metadata.year) : null,
        is_sanitized: isSanitized,
      };

      const response = await fetch(`${API_BASE_URL}/api/v1/markdown/import`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        let errorTitle = "Import Failed";
        let errorMessage = "Failed to import the markdown file.";
        let errorDetail: string | undefined;

        if (response.status === 404) {
          errorTitle = "File Not Found";
          errorMessage = "The selected file could not be found.";
        } else if (response.status === 400) {
          errorTitle = "Validation Error";
          errorMessage = "The file content or metadata is invalid.";
        }

        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorData.message;
        } catch {
          // Couldn't parse error
        }

        setImportError({
          title: errorTitle,
          message: errorMessage,
          detail: errorDetail,
        });
        setShowSanitizationModal(false);
        return;
      }

      const data: ImportResponse = await response.json();

      // Success - redirect to simple conversion status page
      router.push(`/simple-conversion/automatic/${data.work_id}`);
    } catch (err) {
      setImportError({
        title: "Import Failed",
        message: "An unexpected error occurred during import.",
        detail: err instanceof Error ? err.message : undefined,
      });
      setShowSanitizationModal(false);
    } finally {
      setImporting(false);
    }
  };

  const handleCancelSanitization = () => {
    setShowSanitizationModal(false);
    setSelectedFile(null);
    setMetadata({ title: "", author: "", year: "" });
    setDuplicateInfo(null);
  };

  const handleCloseError = () => {
    setImportError(null);
    setSelectedFile(null);
    setMetadata({ title: "", author: "", year: "" });
    setDuplicateInfo(null);
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Loading markdown files...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="flex items-center gap-3 py-8 text-destructive">
          <AlertCircle className="h-6 w-6" />
          <div>
            <p className="font-semibold">Error loading files</p>
            <p className="text-sm">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Upload className="h-6 w-6" />
            <div>
              <CardTitle>Import Markdown</CardTitle>
              <CardDescription>
                Select a markdown file to import into the system
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {files.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
              <p className="mt-4 text-muted-foreground">
                No markdown files found in the input directory
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Filename</TableHead>
                  <TableHead>Has Metadata</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {files.map((file) => (
                  <TableRow key={file.filename}>
                    <TableCell className="font-medium">{file.filename}</TableCell>
                    <TableCell>
                      {file.has_metadata ? (
                        <span className="text-green-600 dark:text-green-400">Yes</span>
                      ) : (
                        <span className="text-muted-foreground">No</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        onClick={() => handleImportClick(file)}
                      >
                        <Upload className="mr-2 h-4 w-4" />
                        Import
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Modals */}
      {selectedFile && (
        <MetadataEntryModal
          isOpen={showMetadataModal}
          onClose={() => {
            setShowMetadataModal(false);
            setSelectedFile(null);
          }}
          onSubmit={handleMetadataSubmit}
          initialMetadata={selectedFile.metadata}
          filename={selectedFile.filename}
        />
      )}

      {duplicateInfo && (
        <DuplicateWarningModal
          isOpen={showDuplicateModal}
          onProceed={() => handleDuplicateDecision(true)}
          onCancel={() => handleDuplicateDecision(false)}
          duplicateInfo={duplicateInfo}
        />
      )}

      <SanitizationDecisionModal
        isOpen={showSanitizationModal}
        onDecision={handleSanitizationDecision}
        onCancel={handleCancelSanitization}
        loading={importing}
      />

      {importError && (
        <ErrorModal
          isOpen={true}
          onClose={handleCloseError}
          title={importError.title}
          message={importError.message}
          error={importError.detail}
        />
      )}
    </>
  );
}
