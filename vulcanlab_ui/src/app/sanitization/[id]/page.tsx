"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, Eye, Loader2Icon, PlayCircle, Check, X } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FileStatusInfo {
  exists: boolean;
  path: string | null;
  hash: string | null;
  hash_match: boolean | null;
  error: string | null;
}

interface WorkDetailResponse {
  id: number;
  title: string;
  authors: string | null;
  year: number | null;
  work_type: string | null;
  original_markdown: FileStatusInfo;
  titles: FileStatusInfo;
  title_changes: FileStatusInfo;
  sanitized: FileStatusInfo;
}

export default function WorkSanitizationPage() {
  const params = useParams();
  const router = useRouter();
  const workId = parseInt(params.id as string);

  const [workDetail, setWorkDetail] = useState<WorkDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [operationLoading, setOperationLoading] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [operationSuccess, setOperationSuccess] = useState<string | null>(null);
  const [verifyErrors, setVerifyErrors] = useState<string[]>([]);

  useEffect(() => {
    fetchWorkDetail();
  }, [workId]);

  const fetchWorkDetail = async (): Promise<WorkDetailResponse | null> => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/sanitization/work/${workId}`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Work not found. It may have been deleted.");
        }
        throw new Error(`Failed to load work detail: ${response.statusText}`);
      }

      const data: WorkDetailResponse = await response.json();
      setWorkDetail(data);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load work detail");
      return null;
    } finally {
      setLoading(false);
    }
  };

  const handleExtractTitles = async () => {
    setOperationLoading("extract-titles");
    setOperationError(null);
    setOperationSuccess(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/sanitization/work/${workId}/extract-titles`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_key: "original_markdown",
            force: false,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed: ${response.statusText}`);
      }

      const data = await response.json();
      setOperationSuccess(data.message || "Titles extracted successfully");
      
      // Refresh work detail and check if titles are ready
      const updatedWorkDetail = await fetchWorkDetail();
      
      // Navigate to titles inspect page if extraction completed successfully
      if (updatedWorkDetail && updatedWorkDetail.titles.exists && updatedWorkDetail.titles.hash_match) {
        setTimeout(() => {
          router.push(`/sanitization/${workId}/titles`);
        }, 500);
      }
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to extract titles");
    } finally {
      setOperationLoading(null);
    }
  };

  const handleSuggestTitleChanges = async () => {
    router.push(`/sanitization/${workId}/gen-title-changes`);
  };

  const handleVerifyTitleChanges = async () => {
    setOperationLoading("verify-title-changes");
    setOperationError(null);
    setOperationSuccess(null);
    setVerifyErrors([]);

    try {
      const response = await fetch(
        `${API_BASE_URL}/sanitization/work/${workId}/verify-title-changes`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_key: "original_markdown",
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setOperationSuccess(data.message || "Title changes verified and hash updated successfully");
        // Refresh work detail
        await fetchWorkDetail();
      } else {
        setOperationError(data.message || "Verification failed");
        setVerifyErrors(data.errors || []);
      }
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to verify title changes");
    } finally {
      setOperationLoading(null);
    }
  };

  const handleApplyTitleChanges = async () => {
    setOperationLoading("apply-changes");
    setOperationError(null);
    setOperationSuccess(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/sanitization/work/${workId}/apply-title-changes`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_key: "original_markdown",
            force: false,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed: ${response.statusText}`);
      }

      const data = await response.json();
      setOperationSuccess(data.message || "Title changes applied successfully");
      
      // Refresh work detail
      await fetchWorkDetail();
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to apply title changes");
    } finally {
      setOperationLoading(null);
    }
  };

  const handleSkipApply = async () => {
    setOperationLoading("skip-apply");
    setOperationError(null);
    setOperationSuccess(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/sanitization/work/${workId}/skip-apply`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_key: "original_markdown",
            force: false,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed: ${response.statusText}`);
      }

      const data = await response.json();
      setOperationSuccess(data.message || "Original copied to sanitized successfully");
      
      // Refresh work detail
      await fetchWorkDetail();
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to skip-apply");
    } finally {
      setOperationLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Sanitization Workflow</h2>
          <p className="text-muted-foreground">
            Process markdown headings and structure.
          </p>
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
          <h2 className="text-3xl font-bold tracking-tight">Sanitization Workflow</h2>
          <p className="text-muted-foreground">
            Process markdown headings and structure.
          </p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error || "Failed to load work"}</p>
            </div>
            <div className="flex gap-3 mt-4">
              <Button onClick={fetchWorkDetail}>Retry</Button>
              <Button variant="outline" onClick={() => router.push("/sanitization")}>
                Back to List
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const titlesReady = workDetail.titles.exists && workDetail.titles.hash_match;
  const titleChangesReady = workDetail.title_changes.exists && workDetail.title_changes.hash_match;
  const sanitizedExists = workDetail.sanitized.exists;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Sanitization Workflow</h2>
        <p className="text-muted-foreground">
          Work ID: <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{workId}</code>
        </p>
      </div>

      {/* Work Info */}
      <Card>
        <CardHeader>
          <CardTitle>{workDetail.title}</CardTitle>
          <CardDescription>
            {workDetail.authors && <span>{workDetail.authors}</span>}
            {workDetail.year && <span> ({workDetail.year})</span>}
            {workDetail.work_type && <span className="ml-2">• {workDetail.work_type}</span>}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Operation Messages */}
      {operationSuccess && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>{operationSuccess}</AlertDescription>
        </Alert>
      )}

      {operationError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{operationError}</AlertDescription>
        </Alert>
      )}

      {/* Card 1: Titles */}
      <Card>
        <CardHeader>
          <CardTitle>1. Extract Titles</CardTitle>
          <CardDescription>
            Extract all headings from the markdown document
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Status */}
            <div className="flex items-start gap-4 p-4 rounded-lg border bg-card">
              <div className="flex-shrink-0 mt-1">
                {titlesReady ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                ) : workDetail.titles.exists ? (
                  <AlertCircle className="h-5 w-5 text-amber-500" />
                ) : (
                  <X className="h-5 w-5 text-muted-foreground" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold mb-1">
                  {workDetail.titles.exists ? "Titles File Exists" : "Titles Not Extracted"}
                </h3>
                {workDetail.titles.exists && workDetail.titles.path && (
                  <p className="text-xs text-muted-foreground mb-2">
                    {workDetail.titles.path}
                  </p>
                )}
                {workDetail.titles.error && (
                  <Alert variant="destructive" className="mt-2">
                    <AlertCircle className="h-3 w-3" />
                    <AlertDescription className="text-xs">
                      {workDetail.titles.error}
                    </AlertDescription>
                  </Alert>
                )}
              </div>

              <div className="flex-shrink-0">
                {titlesReady ? (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => router.push(`/sanitization/${workId}/titles`)}
                    className="gap-2"
                  >
                    <Eye className="h-4 w-4" />
                    Inspect
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    onClick={handleExtractTitles}
                    disabled={operationLoading !== null}
                    className="gap-2"
                  >
                    {operationLoading === "extract-titles" ? (
                      <Loader2Icon className="h-4 w-4 animate-spin" />
                    ) : (
                      <PlayCircle className="h-4 w-4" />
                    )}
                    Generate
                  </Button>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Card 2: Title Changes */}
      <Card>
        <CardHeader>
          <CardTitle>2. Suggest Title Changes</CardTitle>
          <CardDescription>
            Use AI to suggest heading hierarchy improvements
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Status */}
            <div className="flex items-start gap-4 p-4 rounded-lg border bg-card">
              <div className="flex-shrink-0 mt-1">
                {titleChangesReady ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                ) : workDetail.title_changes.exists ? (
                  <AlertCircle className="h-5 w-5 text-amber-500" />
                ) : (
                  <X className="h-5 w-5 text-muted-foreground" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold mb-1">
                  {workDetail.title_changes.exists
                    ? "Title Changes File Exists"
                    : "Title Changes Not Generated"}
                </h3>
                {workDetail.title_changes.exists && workDetail.title_changes.path && (
                  <p className="text-xs text-muted-foreground mb-2">
                    {workDetail.title_changes.path}
                  </p>
                )}
                {workDetail.title_changes.error && (
                  <Alert variant="destructive" className="mt-2">
                    <AlertCircle className="h-3 w-3" />
                    <AlertDescription className="text-xs">
                      {workDetail.title_changes.error}
                    </AlertDescription>
                  </Alert>
                )}
                {verifyErrors.length > 0 && (
                  <Alert variant="destructive" className="mt-2">
                    <AlertCircle className="h-3 w-3" />
                    <AlertDescription className="text-xs">
                      <p className="font-semibold mb-1">Verification errors:</p>
                      <ul className="list-disc list-inside space-y-1">
                        {verifyErrors.slice(0, 5).map((error, idx) => (
                          <li key={idx}>{error}</li>
                        ))}
                        {verifyErrors.length > 5 && (
                          <li>... and {verifyErrors.length - 5} more errors</li>
                        )}
                      </ul>
                    </AlertDescription>
                  </Alert>
                )}
                {!titlesReady && (
                  <p className="text-xs text-muted-foreground mt-2">
                    Requires titles to be extracted first
                  </p>
                )}
              </div>

              <div className="flex-shrink-0 flex gap-2">
                {titleChangesReady ? (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => router.push(`/sanitization/${workId}/title-changes`)}
                    className="gap-2"
                  >
                    <Eye className="h-4 w-4" />
                    Inspect
                  </Button>
                ) : workDetail.title_changes.exists && !workDetail.title_changes.hash_match ? (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleVerifyTitleChanges}
                      disabled={operationLoading !== null}
                      className="gap-2"
                    >
                      {operationLoading === "verify-title-changes" ? (
                        <Loader2Icon className="h-4 w-4 animate-spin" />
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                      Verify
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleSuggestTitleChanges}
                      disabled={!titlesReady || operationLoading !== null}
                      className="gap-2"
                    >
                      <PlayCircle className="h-4 w-4" />
                      Regenerate
                    </Button>
                  </>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleSuggestTitleChanges}
                    disabled={!titlesReady}
                    className="gap-2"
                  >
                    <PlayCircle className="h-4 w-4" />
                    Generate
                  </Button>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Card 3: Next Steps */}
      <Card>
        <CardHeader>
          <CardTitle>3. Next Steps</CardTitle>
          <CardDescription>
            Apply title changes or skip to finalize sanitization
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sanitizedExists && (
              <Alert>
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>
                  Sanitized file already exists. You can still apply changes to update it.
                </AlertDescription>
              </Alert>
            )}

            <div className="flex gap-3">
              <Button
                onClick={handleApplyTitleChanges}
                disabled={!titleChangesReady || operationLoading !== null}
                className="gap-2"
              >
                {operationLoading === "apply-changes" ? (
                  <Loader2Icon className="h-4 w-4 animate-spin" />
                ) : (
                  <Check className="h-4 w-4" />
                )}
                Apply Title Changes
              </Button>

              <Button
                variant="outline"
                onClick={handleSkipApply}
                disabled={operationLoading !== null}
                className="gap-2"
              >
                {operationLoading === "skip-apply" ? (
                  <Loader2Icon className="h-4 w-4 animate-spin" />
                ) : (
                  <X className="h-4 w-4" />
                )}
                Skip Apply (Copy Original)
              </Button>
            </div>

            <p className="text-xs text-muted-foreground">
              <strong>Apply Title Changes:</strong> Apply the suggested changes to create a sanitized version.
              <br />
              <strong>Skip Apply:</strong> Copy the original markdown without changes if no sanitization is needed.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={() => router.push("/sanitization")}>
          Back to List
        </Button>
        
        {sanitizedExists && (
          <Button onClick={() => router.push(`/chunk/${workId}`)}>
            Continue to Chunking →
          </Button>
        )}
      </div>
    </div>
  );
}

