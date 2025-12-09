"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, Eye, Loader2Icon, PlayCircle, FileText } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FileStatusInfo {
  exists: boolean;
  path: string | null;
  hash: string | null;
  hash_match: boolean | null;
}

interface WorkDetailResponse {
  id: number;
  title: string;
  authors: string | null;
  year: number | null;
  work_type: string | null;
  files: {
    sanitized: FileStatusInfo;
    sanitized_titles: FileStatusInfo;
    vec_suggestions: FileStatusInfo;
  };
  processing_status: {
    heading_chunks?: string;
    content_chunks?: string;
  } | null;
}

export default function ChunkWorkDetailPage() {
  const params = useParams();
  const router = useRouter();
  const workId = parseInt(params.id as string);

  const [workDetail, setWorkDetail] = useState<WorkDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [operationLoading, setOperationLoading] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [operationSuccess, setOperationSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchWorkDetail();
  }, [workId]);

  const fetchWorkDetail = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/chunk/work/${workId}`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Work not found. It may have been deleted.");
        }
        throw new Error(`Failed to load work detail: ${response.statusText}`);
      }

      const data: WorkDetailResponse = await response.json();
      setWorkDetail(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load work detail");
    } finally {
      setLoading(false);
    }
  };

  const handleExtractSanitizedTitles = async () => {
    setOperationLoading("extract-san-titles");
    setOperationError(null);
    setOperationSuccess(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/chunk/work/${workId}/extract-sanitized-titles`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ force: false }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed: ${response.statusText}`);
      }

      const data = await response.json();
      setOperationSuccess(data.message || "Sanitized titles extracted successfully");
      
      // Refresh work detail
      await fetchWorkDetail();
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to extract sanitized titles");
    } finally {
      setOperationLoading(null);
    }
  };

  const handleApplyHeadingChunks = async () => {
    setOperationLoading("apply-heading-chunks");
    setOperationError(null);
    setOperationSuccess(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/chunk/work/${workId}/apply-heading-chunks`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed: ${response.statusText}`);
      }

      const data = await response.json();
      setOperationSuccess(data.message || "Heading chunks applied successfully");
      
      // Refresh work detail
      await fetchWorkDetail();
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to apply heading chunks");
    } finally {
      setOperationLoading(null);
    }
  };

  const handleApplyContentChunks = async () => {
    setOperationLoading("apply-content-chunks");
    setOperationError(null);
    setOperationSuccess(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/chunk/work/${workId}/apply-content-chunks`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed: ${response.statusText}`);
      }

      const data = await response.json();
      setOperationSuccess(data.message || "Content chunks applied successfully");
      
      // Refresh work detail
      await fetchWorkDetail();
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to apply content chunks");
    } finally {
      setOperationLoading(null);
    }
  };

  const handleInspect = (fileType: string) => {
    if (fileType === "sanitized") {
      router.push(`/chunk/${workId}/sanitized`);
    } else if (fileType === "sanitized_titles") {
      router.push(`/chunk/${workId}/san-titles`);
    } else if (fileType === "vec_suggestions") {
      router.push(`/chunk/${workId}/vec-suggestions`);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Loading...</h2>
        </div>
        <div className="flex items-center justify-center h-64">
          <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error || !workDetail) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Error</h2>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error || "Failed to load work details"}</p>
            </div>
            <Button onClick={fetchWorkDetail} variant="outline" className="mt-4">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const allFilesReady = 
    workDetail.files.sanitized.exists &&
    workDetail.files.sanitized.hash_match &&
    workDetail.files.sanitized_titles.exists &&
    workDetail.files.sanitized_titles.hash_match &&
    workDetail.files.vec_suggestions.exists &&
    workDetail.files.vec_suggestions.hash_match;

  const headingChunksCompleted = workDetail.processing_status?.heading_chunks === "completed";
  const contentChunksCompleted = workDetail.processing_status?.content_chunks === "completed";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">{workDetail.title}</h2>
        <p className="text-muted-foreground">
          {workDetail.authors && `${workDetail.authors} • `}
          {workDetail.year && `${workDetail.year} • `}
          {workDetail.work_type || "Unknown type"}
        </p>
      </div>

      {operationError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{operationError}</AlertDescription>
        </Alert>
      )}

      {operationSuccess && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>{operationSuccess}</AlertDescription>
        </Alert>
      )}

      {/* Card 1: Sanitized File */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Sanitized File (Required)
          </CardTitle>
          <CardDescription>
            View and edit the sanitized markdown file.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                {workDetail.files.sanitized.exists && workDetail.files.sanitized.hash_match ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-red-600" />
                )}
                <span className="text-sm font-medium">
                  {workDetail.files.sanitized.exists
                    ? workDetail.files.sanitized.hash_match
                      ? "File ready"
                      : "Hash mismatch"
                    : "File not found"}
                </span>
              </div>
              {workDetail.files.sanitized.path && (
                <p className="text-xs text-muted-foreground">{workDetail.files.sanitized.path}</p>
              )}
            </div>
            <Button
              size="sm"
              onClick={() => handleInspect("sanitized")}
              className="gap-2"
              disabled={!workDetail.files.sanitized.exists}
            >
              <Eye className="h-4 w-4" /> Inspect
            </Button>
          </div>

          {workDetail.files.sanitized.exists && !workDetail.files.sanitized.hash_match && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                File hash mismatch detected. The file may have been modified outside the system.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Card 2: Sanitized Headings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Sanitized Headings (Required)
          </CardTitle>
          <CardDescription>
            Extract all headings from the sanitized markdown file.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                {workDetail.files.sanitized_titles.exists && workDetail.files.sanitized_titles.hash_match ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-yellow-600" />
                )}
                <span className="text-sm font-medium">
                  {workDetail.files.sanitized_titles.exists
                    ? workDetail.files.sanitized_titles.hash_match
                      ? "File ready"
                      : "Hash mismatch"
                    : "Not generated"}
                </span>
              </div>
              {workDetail.files.sanitized_titles.path && (
                <p className="text-xs text-muted-foreground">{workDetail.files.sanitized_titles.path}</p>
              )}
            </div>
            {workDetail.files.sanitized_titles.exists && workDetail.files.sanitized_titles.hash_match ? (
              <Button
                size="sm"
                onClick={() => handleInspect("sanitized_titles")}
                className="gap-2"
              >
                <Eye className="h-4 w-4" /> Inspect
              </Button>
            ) : (
              <Button
                size="sm"
                variant="outline"
                onClick={handleExtractSanitizedTitles}
                disabled={
                  operationLoading === "extract-san-titles" ||
                  !workDetail.files.sanitized.exists ||
                  !workDetail.files.sanitized.hash_match
                }
                className="gap-2"
              >
                {operationLoading === "extract-san-titles" ? (
                  <Loader2Icon className="h-4 w-4 animate-spin" />
                ) : (
                  <PlayCircle className="h-4 w-4" />
                )}
                Generate
              </Button>
            )}
          </div>

          {workDetail.files.sanitized_titles.exists && !workDetail.files.sanitized_titles.hash_match && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                File hash mismatch detected. Regenerate to update.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Card 3: Vector Embedding Suggestions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Vector Embedding Suggestions (Required)
          </CardTitle>
          <CardDescription>
            Suggestions for which headings should be vectorized.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                {workDetail.files.vec_suggestions.exists && workDetail.files.vec_suggestions.hash_match ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-yellow-600" />
                )}
                <span className="text-sm font-medium">
                  {workDetail.files.vec_suggestions.exists
                    ? workDetail.files.vec_suggestions.hash_match
                      ? "File ready"
                      : "Hash mismatch"
                    : "Not generated"}
                </span>
              </div>
              {workDetail.files.vec_suggestions.path && (
                <p className="text-xs text-muted-foreground">{workDetail.files.vec_suggestions.path}</p>
              )}
            </div>
            {workDetail.files.vec_suggestions.exists ? (
              <Button
                size="sm"
                onClick={() => handleInspect("vec_suggestions")}
                className="gap-2"
                disabled={!workDetail.files.vec_suggestions.hash_match}
              >
                <Eye className="h-4 w-4" /> Inspect
              </Button>
            ) : (
              <Button
                size="sm"
                variant="outline"
                onClick={() => router.push(`/chunk/${workId}/gen-vec-sugg`)}
                disabled={
                  !workDetail.files.sanitized.exists ||
                  !workDetail.files.sanitized.hash_match ||
                  !workDetail.files.sanitized_titles.exists ||
                  !workDetail.files.sanitized_titles.hash_match
                }
                className="gap-2"
              >
                <PlayCircle className="h-4 w-4" />
                Generate
              </Button>
            )}
          </div>

          {workDetail.files.vec_suggestions.exists && !workDetail.files.vec_suggestions.hash_match && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                File hash mismatch detected. All file hashes must match to proceed.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Card 4: Next Steps */}
      <Card>
        <CardHeader>
          <CardTitle>Next Steps</CardTitle>
          <CardDescription>
            Apply chunking operations to create chunks in the database.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Apply Heading Chunks</p>
              <p className="text-sm text-muted-foreground">
                Create heading-based chunks from sanitized titles
              </p>
            </div>
            <Button
              onClick={handleApplyHeadingChunks}
              disabled={
                operationLoading === "apply-heading-chunks" ||
                !allFilesReady ||
                headingChunksCompleted
              }
              variant={headingChunksCompleted ? "outline" : "default"}
              className="gap-2"
            >
              {operationLoading === "apply-heading-chunks" ? (
                <Loader2Icon className="h-4 w-4 animate-spin" />
              ) : headingChunksCompleted ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <PlayCircle className="h-4 w-4" />
              )}
              {headingChunksCompleted ? "Completed" : "Apply"}
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Apply Content Chunks</p>
              <p className="text-sm text-muted-foreground">
                Create paragraph-based content chunks
              </p>
            </div>
            <Button
              onClick={handleApplyContentChunks}
              disabled={
                operationLoading === "apply-content-chunks" ||
                !allFilesReady ||
                contentChunksCompleted
              }
              variant={contentChunksCompleted ? "outline" : "default"}
              className="gap-2"
            >
              {operationLoading === "apply-content-chunks" ? (
                <Loader2Icon className="h-4 w-4 animate-spin" />
              ) : contentChunksCompleted ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <PlayCircle className="h-4 w-4" />
              )}
              {contentChunksCompleted ? "Completed" : "Apply"}
            </Button>
          </div>

          {!allFilesReady && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                All files must be present with matching hashes before applying chunking operations.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

