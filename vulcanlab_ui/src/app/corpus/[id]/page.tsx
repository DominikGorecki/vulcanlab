"use client";

import { useParams } from "next/navigation";
import { useCallback } from "react";
import { StickyDetailHeader, PageErrorState, PageLoadingState } from "@/components";
import { MarkdownEditor } from "@/components/markdown-editor";
import { usePageData } from "@/hooks/use-page-data";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface WorkContentResponse {
  content: string;
  filename: string;
  work_id: number;
  work_title: string;
}

export default function CorpusWorkViewerPage() {
  const params = useParams();
  const workId = params.id as string;

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
          <div className="text-sm text-muted-foreground mr-4 px-2 py-1 rounded bg-muted/50">
            {data?.filename}
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
        />
      </div>
    </div>
  );
}
