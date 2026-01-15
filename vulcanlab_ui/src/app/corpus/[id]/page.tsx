"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState, useMemo } from "react";
import {
  StickyDetailHeader,
  PageErrorState,
  PageLoadingState,
  SummarizationProgressModal,
  SummarizationProgress,
  ConfirmDialog,
} from "@/components";
import { Button } from "@/components/ui/button";
import { MarkdownEditor } from "@/components/markdown-editor";
import { usePageData } from "@/hooks/use-page-data";
import { useToast } from "@/hooks/use-toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface WorkContentResponse {
  content: string;
  filename: string;
  work_id: number;
  work_title: string;
}

export default function CorpusWorkViewerPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const workId = params.id as string;

  const [hasSummary, setHasSummary] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [progress, setProgress] = useState<SummarizationProgress | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // Parse highlight range from URL
  const highlightRange = useMemo(() => {
    const highlight = searchParams.get("highlight");
    if (!highlight) return null;

    const [startStr, endStr] = highlight.split("-");
    const start = parseInt(startStr, 10);
    const end = parseInt(endStr || startStr, 10);

    if (isNaN(start) || isNaN(end) || start < 1 || end < 1 || start > end) {
      console.warn(`Invalid highlight range: ${highlight}`);
      return null;
    }

    return { start, end };
  }, [searchParams]);

  const fetchData = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/corpus/work/${workId}/content`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Work not found or sanitized content not available.");
      }
      throw new Error(`Failed to load content: ${response.statusText}`);
    }

    return response.json();
  }, [workId]);

  const { data, loading, error, refetch } = usePageData<WorkContentResponse>(fetchData);

  // Check if work has summary or is currently being summarized on load
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/summarize/${workId}/status`);
        if (response.ok) {
          const statusData = await response.json();
          if (statusData.status === "completed") {
            setHasSummary(true);
          } else if (statusData.status === "processing" || statusData.status === "pending") {
            setIsSummarizing(true);
            setProgress(statusData);
          }
        }
      } catch (err) {
        console.error("Failed to check summarization status:", err);
      }
    };

    checkStatus();
  }, [workId]);

  // Polling for summarization progress
  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    if (isSummarizing) {
      intervalId = setInterval(async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/api/v1/summarize/${workId}/status`);
          if (response.ok) {
            const statusData = await response.json();
            setProgress(statusData);

            if (statusData.status === "completed") {
              setIsSummarizing(false);
              setHasSummary(true);
              toast({
                title: "Summarization complete",
                description: "The work has been successfully summarized.",
              });
              router.push(`/summarize/${workId}`);
            } else if (statusData.status === "failed") {
              setIsSummarizing(false);
              toast({
                title: "Summarization failed",
                description: statusData.error || "An error occurred during summarization.",
                variant: "destructive",
              });
            }
          }
        } catch (err) {
          console.error("Error polling summarization status:", err);
          setIsSummarizing(false);
          toast({
            title: "Error",
            description: "Failed to get summarization progress.",
            variant: "destructive",
          });
        }
      }, 2000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isSummarizing, workId, router, toast]);

  const handleSummarize = async (force = false) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/summarize/${workId}${force ? "?force=true" : ""}`, {
        method: "POST",
      });

      if (response.ok) {
        setIsSummarizing(true);
        setProgress({
          status: "pending",
          completed_nodes: 0,
          total_nodes: 0,
        });
      } else {
        const errData = await response.json();
        toast({
          title: "Summarization failed",
          description: errData.detail || "Could not start summarization.",
          variant: "destructive",
        });
      }
    } catch (err) {
      toast({
        title: "Error",
        description: "An unexpected error occurred.",
        variant: "destructive",
      });
    }
  };

  if (error) {
    return <PageErrorState error={error} onRetry={refetch} />;
  }

  if (loading && !data) {
    return <PageLoadingState title="Loading work content..." />;
  }

  return (
    <div className="min-h-screen flex flex-col pt-0">
      <StickyDetailHeader
        title="Corpus Work"
        subtitle={data?.work_title || "..."}
        backUrl="/corpus"
        backLabel="Back to Corpus"
        actions={
          <div className="flex items-center gap-2">
            <div className="text-sm text-muted-foreground mr-4 px-2 py-1 rounded bg-muted/50">
              {data?.filename}
            </div>
            {hasSummary ? (
              <>
                <Button
                  variant="outline"
                  onClick={() => setShowConfirmDialog(true)}
                  disabled={isSummarizing}
                >
                  Re-summarize
                </Button>
                <Button onClick={() => router.push(`/summarize/${workId}`)}>
                  View Summary
                </Button>
              </>
            ) : (
              <Button onClick={() => handleSummarize()} disabled={isSummarizing}>
                {isSummarizing ? "Summarizing..." : "Summarize"}
              </Button>
            )}
          </div>
        }
      />

      <div className="p-6">
        <MarkdownEditor
          content={data?.content || ""}
          onChange={() => {}} // No-op: read-only
          viewMode="both"
          readOnly={true}
          scrollMode="page"
          highlightLines={highlightRange}
          onHighlightClear={() => {
            const newParams = new URLSearchParams(searchParams.toString());
            newParams.delete("highlight");
            const query = newParams.toString();
            router.replace(`/corpus/${workId}${query ? `?${query}` : ""}`);
          }}
        />
      </div>

      <SummarizationProgressModal isOpen={isSummarizing} progress={progress} />

      <ConfirmDialog
        isOpen={showConfirmDialog}
        onOpenChange={setShowConfirmDialog}
        title="Re-summarize Work?"
        description="This will delete the existing summary and generate a new one. This action cannot be undone."
        confirmLabel="Re-summarize"
        onConfirm={() => {
          setShowConfirmDialog(false);
          handleSummarize(true);
        }}
        variant="destructive"
      />
    </div>
  );
}
