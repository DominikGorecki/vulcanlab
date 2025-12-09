"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  AlertCircle,
  ChevronLeft,
  Loader2Icon,
  MessageSquare,
  Eye,
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

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

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const queryId = params.id as string;

  const [query, setQuery] = useState<QueryDetail | null>(null);
  const [results, setResults] = useState<ResultItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, [queryId]);

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

      // Fetch results
      const resultsResponse = await fetch(`${API_BASE_URL}/rag/queries/${queryId}/results`);
      if (!resultsResponse.ok) {
        throw new Error("Failed to load results");
      }
      const resultsData: ResultListResponse = await resultsResponse.json();
      setResults(resultsData.results);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "2-digit",
      day: "2-digit",
      year: "2-digit",
    }); // MM/DD/YY
  };

  const truncateText = (text: string, maxLength: number = 340) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
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
            <Button variant="outline" onClick={() => router.push("/rag")}>
              Back
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="border-b bg-card p-4 flex items-center gap-3">
        <Button
          onClick={() => router.push("/rag")}
          variant="ghost"
          size="sm"
          className="gap-1"
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </Button>
        <div className="border-l h-8" />
        <div>
          <h1 className="text-xl font-bold">Query Results</h1>
          <p className="text-sm text-muted-foreground max-w-4xl truncate">
            {query?.original_query}
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 overflow-auto">
        <Card>
          <CardHeader>
            <CardTitle>Results History</CardTitle>
            <CardDescription>
              Past generated responses for this query.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {results.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No results found for this query.</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[60%]">Response Preview</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.map((result) => (
                    <TableRow key={result.id}>
                      <TableCell className="align-top">
                        <div className="max-w-3xl whitespace-pre-wrap font-mono text-xs text-muted-foreground">
                          {truncateText(result.response_text)}
                        </div>
                      </TableCell>
                      <TableCell className="whitespace-nowrap align-top">
                        {formatDate(result.created_at)}
                      </TableCell>
                      <TableCell className="text-right align-top">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => router.push(`/rag/${queryId}/results/${result.id}`)}
                          className="gap-1"
                        >
                          <Eye className="h-3 w-3" />
                          Show
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

