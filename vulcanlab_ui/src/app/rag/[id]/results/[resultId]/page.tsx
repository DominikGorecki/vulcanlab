"use client";

import { useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { PlayCircle, FolderPlus } from "lucide-react";
import { MarkdownEditor } from "@/components/markdown-editor";
import { TextStats } from "@/components/text-stats";
import {
  PageLoadingState,
  PageErrorState,
  StickyDetailHeader,
  AddToCollectionModal,
} from "@/components";
import { usePageData } from "@/hooks/use-page-data";
import { useAddToCollection } from "@/hooks/use-add-to-collection";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ResultItem {
  id: number;
  query_id: number;
  response_text: string;
  model_name?: string;
  created_at: string;
}

interface QueryDetail {
  id: number;
  original_query: string;
}

interface PageData {
  query: QueryDetail;
  result: ResultItem;
}

export default function ResultDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryId = params.id as string;
  const resultId = params.resultId as string;

  const fetchPageData = useCallback(async () => {
    // Fetch query details
    const queryResponse = await fetch(`${API_BASE_URL}/rag/queries/${queryId}`);
    if (!queryResponse.ok) {
      throw new Error("Failed to load query details");
    }
    const queryData = await queryResponse.json();

    // Fetch result details
    const resultResponse = await fetch(`${API_BASE_URL}/rag/queries/${queryId}/results/${resultId}`);
    if (!resultResponse.ok) {
      throw new Error("Failed to load result details");
    }
    const resultData: ResultItem = await resultResponse.json();

    return {
      query: queryData,
      result: resultData,
    };
  }, [queryId, resultId]);

  const { data, loading, error, refetch } = usePageData<PageData>(fetchPageData);

  const {
    isOpen,
    openAddToCollection,
    closeAddToCollection,
    itemType,
    itemLink
  } = useAddToCollection();

  if (loading) {
    return <PageLoadingState />;
  }

  if (error) {
    return (
      <div className="space-y-4">
        <PageErrorState error={error} onRetry={refetch} />
        <div className="flex justify-center">
          <Button variant="outline" onClick={() => router.push(`/rag/${queryId}/results`)}>
            Back to Results
          </Button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="flex flex-col min-h-screen">
      <StickyDetailHeader
        title="Result Detail"
        subtitle={data.query.original_query}
        backUrl={`/rag/${queryId}/results`}
        actions={
          <div className="flex items-center gap-4">
            {/* Model Info */}
            <div className="flex items-center gap-2 text-sm">
              <span className="font-medium text-muted-foreground">Model:</span>
              <span className={data.result.model_name ? "text-foreground" : "italic text-muted-foreground"}>
                {data.result.model_name || "Unspecified"}
              </span>
            </div>

            {/* Stats */}
            <TextStats text={data.result.response_text} />

            {/* Add to Collection */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => openAddToCollection("research_result", `/rag/${queryId}/results/${resultId}`)}
              className="gap-2"
            >
              <FolderPlus className="h-4 w-4" />
              Add to Collection
            </Button>

            {/* Query Button */}
            <Button
              onClick={() => router.push(`/rag/${queryId}`)}
              className="gap-1"
            >
              <PlayCircle className="h-4 w-4" />
              Query
            </Button>
          </div>
        }
      />

      {/* Content */}
      <div className="p-6 flex flex-col">
        <MarkdownEditor 
          content={data.result.response_text} 
          readOnly={true}
          viewMode="both"
          scrollMode="page"
          processSources={true}
        />
      </div>

      <AddToCollectionModal
        isOpen={isOpen}
        onClose={closeAddToCollection}
        itemType={itemType}
        itemLink={itemLink}
      />
    </div>
  );
}
