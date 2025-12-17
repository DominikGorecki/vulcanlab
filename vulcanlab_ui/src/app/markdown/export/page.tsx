"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, Loader2Icon, Database, Download } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ErrorModal } from "@/components/ErrorModal";
import { useToast } from "@/hooks/use-toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CorpusWork {
  id: number;
  title: string;
  authors: string | null;
}

interface CorpusWorksResponse {
  works: CorpusWork[];
  total: number;
}

interface ExportResponse {
  success: boolean;
  message: string;
  export_path?: string;
  work_id?: number;
}

export default function MarkdownExportPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [works, setWorks] = useState<CorpusWork[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportingWorkId, setExportingWorkId] = useState<number | null>(null);
  const [exportError, setExportError] = useState<{ title: string; message: string; detail?: string } | null>(null);

  useEffect(() => {
    fetchWorks();
  }, []);

  const fetchWorks = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/corpus/works`);

      if (!response.ok) {
        throw new Error(`Failed to load works: ${response.statusText}`);
      }

      const data: CorpusWorksResponse = await response.json();
      setWorks(data.works);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load works");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (workId: number, event: React.MouseEvent) => {
    event.stopPropagation();

    try {
      setExportingWorkId(workId);

      const response = await fetch(
        `${API_BASE_URL}/api/v1/markdown/export/${workId}`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        // Parse error response
        let errorDetail: string | undefined;
        let errorMessage: string;
        let errorTitle: string;

        try {
          const contentType = response.headers.get("content-type");
          if (contentType && contentType.includes("application/json")) {
            const errorData = await response.json();

            // Handle structured error response from API
            if (errorData.detail && typeof errorData.detail === 'object') {
              const structuredError = errorData.detail;

              // Map error types to user-friendly messages
              switch (structuredError.error) {
                case "file_not_found":
                  errorTitle = "Work Not Found";
                  errorMessage = structuredError.message || "This work may have been deleted or does not exist.";
                  break;
                case "disk_full":
                  errorTitle = "Disk Full";
                  errorMessage = structuredError.message || "Cannot write export file: disk is full.";
                  break;
                case "permission_denied":
                  errorTitle = "Permission Denied";
                  errorMessage = structuredError.message || "Cannot write to exports directory due to permission restrictions.";
                  break;
                case "read_only":
                  errorTitle = "Read-Only Filesystem";
                  errorMessage = structuredError.message || "Cannot write to read-only exports directory.";
                  break;
                default:
                  if (response.status === 404) {
                    errorTitle = "Work Not Found";
                    errorMessage = structuredError.message || "This work may have been deleted or does not exist.";
                  } else if (response.status === 400) {
                    errorTitle = "Export Failed";
                    errorMessage = structuredError.message || "This work cannot be exported. It may not have sanitized markdown content.";
                  } else if (response.status === 500) {
                    errorTitle = "Export Failed";
                    errorMessage = structuredError.message || "An internal server error occurred while exporting the work.";
                  } else {
                    errorTitle = "Export Failed";
                    errorMessage = structuredError.message || `Failed to export work: ${response.statusText}`;
                  }
              }

              errorDetail = structuredError.detail;
            } else if (errorData.detail) {
              // Handle old-style string detail
              errorDetail = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);

              // Fallback to status code based messages
              if (response.status === 404) {
                errorTitle = "Work Not Found";
                errorMessage = "This work may have been deleted or does not exist.";
              } else if (response.status === 400) {
                errorTitle = "Export Failed";
                errorMessage = "This work cannot be exported. It may not have sanitized markdown content.";
              } else if (response.status === 500) {
                errorTitle = "Export Failed";
                errorMessage = "An internal server error occurred while exporting the work.";
              } else {
                errorTitle = "Export Failed";
                errorMessage = `Failed to export work: ${response.statusText}`;
              }
            } else {
              throw new Error("No error detail in response");
            }
          } else {
            throw new Error("Non-JSON error response");
          }
        } catch {
          // Couldn't parse error - use default messages based on status code
          if (response.status === 404) {
            errorTitle = "Work Not Found";
            errorMessage = "This work may have been deleted or does not exist.";
          } else if (response.status === 400) {
            errorTitle = "Export Failed";
            errorMessage = "This work cannot be exported. It may not have sanitized markdown content.";
          } else if (response.status === 500) {
            errorTitle = "Export Failed";
            errorMessage = "An internal server error occurred while exporting the work.";
          } else {
            errorTitle = "Export Failed";
            errorMessage = `Failed to export work: ${response.statusText}`;
          }
        }

        setExportError({ title: errorTitle, message: errorMessage, detail: errorDetail });
        return;
      }

      // Success
      const data: ExportResponse = await response.json();

      // Truncate export path if too long
      const displayPath = data.export_path
        ? data.export_path.length > 50
          ? `.../${data.export_path.split('/').slice(-2).join('/')}`
          : data.export_path
        : "Unknown path";

      toast({
        title: "Export Successful",
        description: `Exported to: ${displayPath}`,
        duration: 5000,
      });
    } catch (err) {
      // Handle network errors
      console.error("Error exporting work:", err);
      setExportError({
        title: "Connection Error",
        message: "Failed to connect to server. Please check your network connection and try again.",
        detail: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setExportingWorkId(null);
    }
  };

  const handleWorkClick = (workId: number) => {
    router.push(`/corpus/${workId}`);
  };

  const handleErrorClose = () => {
    setExportError(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <p>{error}</p>
          </div>
          <Button onClick={fetchWorks} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">

      {/* Works Table */}
      <Card>
        <CardHeader>
          <CardTitle>Corpus Works</CardTitle>
          <CardDescription>
            Click export to save a work as a markdown file. Click on a work to view details.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {works.length === 0 ? (
            <div className="text-center py-12">
              <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No corpus works found.</p>
              <p className="text-sm text-muted-foreground mt-2">
                Works must complete chunking before appearing here.
              </p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[60px]">ID</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Authors</TableHead>
                    <TableHead className="w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {works.map((work) => (
                    <TableRow
                      key={work.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleWorkClick(work.id)}
                    >
                      <TableCell className="font-medium">{work.id}</TableCell>
                      <TableCell className="max-w-md truncate">
                        {work.title}
                      </TableCell>
                      <TableCell className="max-w-xs truncate text-muted-foreground">
                        {work.authors || "-"}
                      </TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => handleExport(work.id, e)}
                          disabled={exportingWorkId === work.id}
                          data-testid={`export-button-${work.id}`}
                        >
                          {exportingWorkId === work.id ? (
                            <>
                              <Loader2Icon className="h-4 w-4 animate-spin" />
                            </>
                          ) : (
                            <>
                              <Download className="h-4 w-4 mr-1" />
                              Export
                            </>
                          )}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <ErrorModal
        isOpen={!!exportError}
        onClose={handleErrorClose}
        title={exportError?.title || "Error"}
        message={exportError?.message || "An error occurred"}
        error={exportError?.detail}
      />
    </div>
  );
}
