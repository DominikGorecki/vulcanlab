"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useMemo } from "react";
import { 
  StickyDetailHeader, 
  PageErrorState, 
  PageLoadingState,
  MarkdownRenderer 
} from "@/components";
import { usePageData } from "@/hooks/use-page-data";
import { Button } from "@/components/ui/button";
import { ListTree, BookOpen, ExternalLink } from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SummarySection {
  chunk_id: number;
  heading: string;
  summary_content: string;
  start_line: number;
  end_line: number;
}

interface SummaryResponse {
  work_id: number;
  work_title: string;
  sections: SummarySection[];
}

export default function SummaryViewerPage() {
  const params = useParams();
  const router = useRouter();
  const workId = params.work_id as string;

  const fetchData = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/summarize/works/${workId}/summary`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Summary not found for this work.");
      }
      throw new Error(`Failed to load summary: ${response.statusText}`);
    }

    return response.json();
  }, [workId]);

  const { data, loading, error, refetch } = usePageData<SummaryResponse>(fetchData);

  const actions = useMemo(() => (
    <div className="flex items-center gap-2">
      <Button
        size="sm"
        variant="outline"
        className="gap-2"
        onClick={() => router.push(`/corpus/${workId}`)}
      >
        <BookOpen size={16} />
        View Original
      </Button>
      <Button
        size="sm"
        variant="outline"
        className="gap-2"
        onClick={() => router.push(`/summaries/workflow/${workId}`)}
      >
        <ListTree size={16} />
        Re-summarize
      </Button>
    </div>
  ), [router, workId]);

  if (error) {
    return <PageErrorState error={error} onRetry={refetch} />;
  }

  if (loading && !data) {
    return <PageLoadingState title="Loading summary..." />;
  }

  const sections = data?.sections || [];

  return (
    <div className="min-h-screen flex flex-col pt-0">
      <StickyDetailHeader
        title="Summary"
        subtitle={data?.work_title || "Loading..."}
        backUrl="/summaries"
        backLabel="Back to Summaries"
        actions={actions}
      />

      <div className="p-6 max-w-4xl mx-auto w-full space-y-8">
        {sections.length === 0 ? (
          <Card>
            <CardContent className="py-12 flex flex-col items-center justify-center text-center">
              <div className="bg-muted p-3 rounded-full mb-4">
                <ListTree size={24} className="text-muted-foreground" />
              </div>
              <CardTitle className="mb-2">No summary content available</CardTitle>
              <p className="text-muted-foreground max-w-sm">
                This work has no summarized sections. You may need to run the summarization workflow.
              </p>
              <Button 
                variant="outline" 
                className="mt-6"
                onClick={() => router.push(`/summaries/workflow/${workId}`)}
              >
                Go to Workflow
              </Button>
            </CardContent>
          </Card>
        ) : (
          sections.map((section, index) => (
            <section key={`${section.chunk_id}-${index}`} className="space-y-4">
              <div className="flex items-start justify-between gap-4">
                <MarkdownRenderer content={section.heading} />
                <Link
                  href={`/search/result/${workId}/${section.start_line}/${section.end_line}`}
                  className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors shrink-0 mt-1"
                >
                  <span className="font-mono">L{section.start_line}–{section.end_line}</span>
                  <ExternalLink size={12} />
                </Link>
              </div>
              <div className="pl-4 border-l-2 border-muted">
                <MarkdownRenderer content={section.summary_content} />
              </div>
            </section>
          ))
        )}
      </div>
    </div>
  );
}
