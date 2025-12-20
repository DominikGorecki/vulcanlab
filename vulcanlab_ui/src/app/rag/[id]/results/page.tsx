"use client";

import { useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Eye } from "lucide-react";
import {
  PageLoadingState,
  PageErrorState,
  StickyDetailHeader,
  DataTable,
  DataTableColumn,
  EmptyState,
} from "@/components";
import { usePageData } from "@/hooks/use-page-data";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ResultItem {
  id: number;
  query_id: number;
  response_text: string;
  created_at: string;
}

interface ResultListResponse {
  query_id: number;
  results: ResultItem[];
  total: number;
}

interface QueryDetail {
  id: number;
  original_query: string;
}

interface PageData {
  query: QueryDetail;
  results: ResultItem[];
}

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const queryId = params.id as string;

  const fetchPageData = useCallback(async () => {
    // Fetch query details
    const queryResponse = await fetch(`${API_BASE_URL}/rag/queries/${queryId}`);
    if (!queryResponse.ok) {
      throw new Error("Failed to load query details");
    }
    const queryData = await queryResponse.json();

    // Fetch results
    const resultsResponse = await fetch(`${API_BASE_URL}/rag/queries/${queryId}/results`);
    if (!resultsResponse.ok) {
      throw new Error("Failed to load results");
    }
    const resultsData: ResultListResponse = await resultsResponse.json();

    return {
      query: queryData,
      results: resultsData.results,
    };
  }, [queryId]);

  const { data, loading, error, refetch } = usePageData<PageData>(fetchPageData);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "2-digit",
      day: "2-digit",
      year: "2-digit",
    }); // MM/DD/YY
  };

  const columns: DataTableColumn<ResultItem>[] = [
    {
      header: "Response Preview",
      key: "response_text",
      cell: (item) => (
        <div className="max-w-3xl whitespace-pre-wrap font-mono text-xs text-muted-foreground line-clamp-3">
          {item.response_text}
        </div>
      ),
    },
    {
      header: "Date",
      key: "created_at",
      cell: (item) => formatDate(item.created_at),
      className: "w-[150px] whitespace-nowrap",
      sortable: true,
    },
    {
      header: "Action",
      key: "id",
      cell: (item) => (
        <div className="flex justify-end">
          <Button
            size="sm"
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              router.push(`/rag/${queryId}/results/${item.id}`);
            }}
            className="gap-1"
          >
            <Eye className="h-3 w-3" />
            Show
          </Button>
        </div>
      ),
      className: "text-right",
    },
  ];

  if (loading) {
    return <PageLoadingState />;
  }

  if (error) {
    return (
      <div className="space-y-4">
        <PageErrorState error={error} onRetry={refetch} />
        <div className="flex justify-center">
          <Button variant="outline" onClick={() => router.push("/rag")}>
            Back to Queries
          </Button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="flex flex-col h-screen">
      <StickyDetailHeader
        title="Query Results"
        subtitle={data.query.original_query}
        backUrl={`/rag/${queryId}`}
      />

      <div className="flex-1 p-6 overflow-auto">
        <div className="bg-card rounded-lg border shadow-sm">
          <DataTable
            data={data.results}
            columns={columns}
            onRowClick={(item) => router.push(`/rag/${queryId}/results/${item.id}`)}
            emptyState={{
              title: "No results found",
              description: "No results have been generated for this query yet.",
            }}
          />
        </div>
      </div>
    </div>
  );
}
