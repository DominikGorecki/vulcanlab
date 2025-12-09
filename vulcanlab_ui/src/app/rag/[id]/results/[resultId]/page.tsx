"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  AlertCircle,
  ChevronLeft,
  Loader2Icon,
  PlayCircle,
} from "lucide-react";
import { MarkdownEditor } from "@/components/markdown-editor";
import { TextStats } from "@/components/text-stats";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ResultItem {
  id: number;
  query_id: number;
  response_text: string;
  created_at: string;
}

interface QueryDetail {
  id: number;
  original_query: string;
}

export default function ResultDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryId = params.id as string;
  const resultId = params.resultId as string;

  const [query, setQuery] = useState<QueryDetail | null>(null);
  const [result, setResult] = useState<ResultItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, [queryId, resultId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch query details
      const queryResponse = await fetch(`${API_BASE_URL}/rag/queries/${queryId}`);
      if (!queryResponse.ok) {
        throw new Error("Failed to load query details");
      }
      const queryData = await queryResponse.json();
      setQuery(queryData);

      // Fetch result details
      const resultResponse = await fetch(`${API_BASE_URL}/rag/queries/${queryId}/results/${resultId}`);
      if (!resultResponse.ok) {
        throw new Error("Failed to load result details");
      }
      const resultData: ResultItem = await resultResponse.json();
      setResult(resultData);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
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
            <Button onClick={fetchData}>Retry</Button>
            <Button variant="outline" onClick={() => router.push(`/rag/${queryId}/results`)}>
              Back to Results
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <div className="border-b bg-card p-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <Button
            onClick={() => router.push(`/rag/${queryId}/results`)}
            variant="ghost"
            size="sm"
            className="gap-1"
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>
          <div className="border-l h-8" />
          <div>
            <h1 className="text-xl font-bold">Result Detail</h1>
            <p className="text-sm text-muted-foreground max-w-2xl truncate">
              {query?.original_query}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Stats */}
          <TextStats text={result?.response_text || ""} />

          {/* Query Button */}
          <Button
            onClick={() => router.push(`/rag/${queryId}`)}
            className="gap-1"
          >
            <PlayCircle className="h-4 w-4" />
            Query
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 flex flex-col">
        <MarkdownEditor 
          content={result?.response_text || ""} 
          readOnly={true}
          viewMode="both"
          scrollMode="page"
        />
      </div>
    </div>
  );
}
