"use client";

import { useCallback, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  AlertCircle,
  CheckCircle2,
  Loader2Icon,
  MessageSquare,
  Clock,
  Zap,
  Search,
  Layers,
  PlayCircle,
  Plus,
  FastForward,
  Files,
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { UpdateRetrieveConsolidateButton } from "@/components/rag/update-button";
import {
  PageHeader,
  PageLoadingState,
  PageErrorState,
  DataTable,
  StatusBadge,
  StatsCardGrid,
  type DataTableColumn,
  type StatusConfig,
} from "@/components";
import { usePageData } from "@/hooks/use-page-data";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface QueryListItem {
  id: number;
  original_query: string;
  created_at: string;
  updated_at?: string;
  status: string;
  intent: string | null;
  entities_count: number;
}

interface QueryListResponse {
  queries: QueryListItem[];
  total: number;
}

// Status configuration for RAG queries
const ragStatusConfig: Record<string, StatusConfig> = {
  needs_embeddings: {
    label: "Needs Embeddings",
    variant: "secondary",
    icon: Zap,
  },
  needs_retrieval: {
    label: "Needs Retrieval",
    variant: "outline",
    icon: Search,
  },
  needs_consolidation: {
    label: "Needs Consolidation",
    variant: "outline",
    icon: Layers,
  },
  ready: {
    label: "Ready",
    variant: "default",
    icon: CheckCircle2,
  },
};

/**
 * Component for creating a new query.
 * Managed locally to avoid re-rendering the entire page on every keystroke.
 */
function NewQueryCard({ 
  onAuto, 
  onManual 
}: { 
  onAuto: (q: string) => void; 
  onManual: (q: string) => void; 
}) {
  const [newQuery, setNewQuery] = useState("");

  const handleAuto = () => {
    if (!newQuery.trim()) return;
    onAuto(newQuery.trim());
  };

  const handleManual = () => {
    if (!newQuery.trim()) return;
    onManual(newQuery.trim());
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>New Query</CardTitle>
        <CardDescription>
          Enter a new query to expand and process through the RAG pipeline.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex gap-3">
          <Textarea
            value={newQuery}
            onChange={(e) => setNewQuery(e.target.value)}
            placeholder="Enter your query here... (e.g., What is working memory?)"
            className="flex-1 min-h-[80px] resize-none"
          />
          <div className="flex flex-col gap-2 self-end">
            <Button
              onClick={handleAuto}
              disabled={!newQuery.trim()}
              className="gap-2"
            >
              <Zap className="h-4 w-4" />
              Auto
            </Button>
            <Button
              onClick={handleManual}
              disabled={!newQuery.trim()}
              variant="outline"
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              Manual
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function RAGPage() {
  const router = useRouter();

  // Operation states
  const [operatingId, setOperatingId] = useState<number | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [operationSuccess, setOperationSuccess] = useState<string | null>(null);

  // Run All states
  const [runAllId, setRunAllId] = useState<number | null>(null);
  const [runAllStep, setRunAllStep] = useState<string | null>(null);

  // Fetch queries using usePageData
  const fetchFn = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/rag/queries`);

    if (!response.ok) {
      throw new Error(`Failed to load queries: ${response.statusText}`);
    }

    const data: QueryListResponse = await response.json();
    return data;
  }, []);

  const { data, loading, error, refetch } = usePageData<QueryListResponse>(fetchFn);

  const handleNewQuery = useCallback((query: string) => {
    router.push(`/rag/new?q=${encodeURIComponent(query)}`);
  }, [router]);

  const handleAutoQuery = useCallback((query: string) => {
    // Store query in sessionStorage for the auto page
    sessionStorage.setItem("vulcanlab_auto_query_text", query);
    router.push("/rag/auto");
  }, [router]);

  const handleEmbed = useCallback(async (queryId: number) => {
    setOperatingId(queryId);
    setOperationError(null);
    setOperationSuccess(null);

    try {
      const response = await fetch(`${API_BASE_URL}/rag/queries/${queryId}/embed`, {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to embed query");
      }

      setOperationSuccess("Embeddings generated successfully");
      await refetch();
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to embed query");
    } finally {
      setOperatingId(null);
    }
  }, [refetch]);

  const handleRetrieve = useCallback(async (queryId: number) => {
    setOperatingId(queryId);
    setOperationError(null);
    setOperationSuccess(null);

    try {
      const response = await fetch(`${API_BASE_URL}/rag/queries/${queryId}/retrieve`, {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to retrieve");
      }

      const responseData = await response.json();
      setOperationSuccess(`Retrieved ${responseData.final_count} chunks`);
      await refetch();
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to retrieve");
    } finally {
      setOperatingId(null);
    }
  }, [refetch]);

  const handleConsolidate = useCallback(async (queryId: number) => {
    setOperatingId(queryId);
    setOperationError(null);
    setOperationSuccess(null);

    try {
      const response = await fetch(`${API_BASE_URL}/rag/queries/${queryId}/consolidate`, {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to consolidate");
      }

      const responseData = await response.json();
      setOperationSuccess(responseData.message);
      await refetch();
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed to consolidate");
    } finally {
      setOperatingId(null);
    }
  }, [refetch]);

  const handleGenerate = useCallback((queryId: number) => {
    router.push(`/rag/${queryId}`);
  }, [router]);

  const handleRunAll = useCallback(async (queryId: number, currentStatus: string) => {
    setRunAllId(queryId);
    setOperationError(null);
    setOperationSuccess(null);

    try {
      // Determine which steps to run based on current status
      const steps: { name: string; label: string; endpoint: string }[] = [];

      if (currentStatus === "needs_embeddings") {
        steps.push({ name: "embed", label: "Embedding", endpoint: `/rag/queries/${queryId}/embed` });
      }
      if (currentStatus === "needs_embeddings" || currentStatus === "needs_retrieval") {
        steps.push({ name: "retrieve", label: "Retrieving", endpoint: `/rag/queries/${queryId}/retrieve` });
      }
      if (currentStatus === "needs_embeddings" || currentStatus === "needs_retrieval" || currentStatus === "needs_consolidation") {
        steps.push({ name: "consolidate", label: "Consolidating", endpoint: `/rag/queries/${queryId}/consolidate` });
      }

      // Run each step sequentially
      for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        setRunAllStep(`${i + 1}/${steps.length} ${step.label}`);

        const response = await fetch(`${API_BASE_URL}${step.endpoint}`, {
          method: "POST",
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Failed at step: ${step.label}`);
        }
      }

      setOperationSuccess("All steps completed successfully - query is ready for generation");
      await refetch();
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : "Failed during run all");
      await refetch(); // Refresh to show current status
    } finally {
      setRunAllId(null);
      setRunAllStep(null);
    }
  }, [refetch]);

  const getActionButton = useCallback((query: QueryListItem) => {
    const isOperating = operatingId === query.id;
    const isRunningAll = runAllId === query.id;
    const isDisabled = isOperating || isRunningAll;

    // Helper to get the single-step button
    const getSingleStepButton = () => {
      switch (query.status) {
        case "needs_embeddings":
          return (
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleEmbed(query.id)}
              disabled={isDisabled}
              className="gap-1"
            >
              {isOperating ? (
                <Loader2Icon className="h-3 w-3 animate-spin" />
              ) : (
                <Zap className="h-3 w-3" />
              )}
              Embed
            </Button>
          );
        case "needs_retrieval":
          return (
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleRetrieve(query.id)}
              disabled={isDisabled}
              className="gap-1"
            >
              {isOperating ? (
                <Loader2Icon className="h-3 w-3 animate-spin" />
              ) : (
                <Search className="h-3 w-3" />
              )}
              Retrieve
            </Button>
          );
        case "needs_consolidation":
          return (
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleConsolidate(query.id)}
              disabled={isDisabled}
              className="gap-1"
            >
              {isOperating ? (
                <Loader2Icon className="h-3 w-3 animate-spin" />
              ) : (
                <Layers className="h-3 w-3" />
              )}
              Consolidate
            </Button>
          );
        default:
          return null;
      }
    };

    // Helper to get the "Run All" button for non-ready statuses
    const getRunAllButton = () => {
      if (query.status === "ready") return null;

      return (
        <Button
          size="sm"
          variant="default"
          onClick={() => handleRunAll(query.id, query.status)}
          disabled={isDisabled}
          className="gap-1"
        >
          {isRunningAll ? (
            <>
              <Loader2Icon className="h-3 w-3 animate-spin" />
              {runAllStep}
            </>
          ) : (
            <>
              <FastForward className="h-3 w-3" />
              Run All
            </>
          )}
        </Button>
      );
    };

    if (query.status === "ready") {
      return (
        <div className="flex gap-2 justify-end">
          {/* View Results */}
          <Button
            size="sm"
            variant="outline"
            onClick={() => router.push(`/rag/${query.id}/results`)}
            disabled={isDisabled}
            title="View Results"
          >
            <Files className="h-3 w-3" />
          </Button>
          {/* Update R & C */}
          <UpdateRetrieveConsolidateButton
            queryId={query.id}
            onSuccess={refetch}
            disabled={isDisabled}
            className="gap-1"
          />
          <Button
            size="sm"
            onClick={() => handleGenerate(query.id)}
            disabled={isDisabled}
            className="gap-1"
          >
            <PlayCircle className="h-3 w-3" />
            Go
          </Button>
        </div>
      );
    }

    return (
      <div className="flex gap-2 justify-end">
        {getSingleStepButton()}
        {getRunAllButton()}
      </div>
    );
  }, [operatingId, runAllId, runAllStep, handleEmbed, handleRetrieve, handleConsolidate, handleGenerate, handleRunAll, refetch, router]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  // Calculate stats - memoized to prevent recalculation on every render
  const stats = useMemo(() => {
    if (!data) return { total: 0, ready: 0, pending: 0 };
    const readyCount = data.queries.filter(q => q.status === "ready").length;
    return {
      total: data.total,
      ready: readyCount,
      pending: data.total - readyCount
    };
  }, [data]);

  // Define columns for DataTable - memoized to prevent re-rendering the whole table
  const columns = useMemo((): DataTableColumn<QueryListItem>[] => [
    {
      key: "original_query",
      header: "Query",
      cell: (query) => (
        <div className="font-medium max-w-md" style={{ wordBreak: "break-word", whiteSpace: "normal" }}>
          {query.original_query}
        </div>
      ),
    },
    {
      key: "created_at",
      header: "Date Created",
      cell: (query) => (
        <span className="text-sm text-muted-foreground whitespace-nowrap">
          {formatDate(query.created_at)}
        </span>
      ),
      sortable: true,
    },
    {
      key: "updated_at",
      header: "Date Modified",
      cell: (query) => (
        <span className="text-sm text-muted-foreground whitespace-nowrap">
          {query.updated_at ? formatDate(query.updated_at) : "-"}
        </span>
      ),
      sortable: true,
    },
    {
      key: "status",
      header: "Status",
      cell: (query) => <StatusBadge status={query.status} statusConfig={ragStatusConfig} />,
      sortable: true,
    },
    {
      key: "id",
      header: "Actions",
      cell: (query) => getActionButton(query),
      className: "text-right",
    },
  ], [getActionButton]);

  if (loading) {
    return <PageLoadingState />;
  }

  if (error) {
    return <PageErrorState error={error} onRetry={refetch} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="RAG Queries"
        description="Manage queries through the RAG pipeline."
      />

      {/* Success/Error Messages */}
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

      {/* Consolidated Stats Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Pipeline Overview</CardTitle>
          <CardDescription>Status of queries across the RAG pipeline</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            {/* Total Queries */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-muted-foreground">
                <MessageSquare className="h-4 w-4" />
                <span className="text-sm font-medium">Total Queries</span>
              </div>
              <div className="text-3xl font-bold text-foreground">
                {stats.total}
              </div>
            </div>

            {/* Ready */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-green-600 dark:text-green-500">
                <CheckCircle2 className="h-4 w-4" />
                <span className="text-sm font-medium">Ready</span>
              </div>
              <div className="text-3xl font-bold text-green-600 dark:text-green-500">
                {stats.ready}
              </div>
            </div>

            {/* Pending */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-amber-600 dark:text-amber-500">
                <Clock className="h-4 w-4" />
                <span className="text-sm font-medium">Pending</span>
              </div>
              <div className="text-3xl font-bold text-amber-600 dark:text-amber-500">
                {stats.pending}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* New Query Input - Managed by its own component to prevent page-wide lag */}
      <NewQueryCard
        onAuto={handleAutoQuery}
        onManual={handleNewQuery}
      />

      {/* Queries Table */}
      <Card>
        <CardHeader>
          <CardTitle>Queries</CardTitle>
          <CardDescription>
            All queries and their current pipeline status.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            data={data?.queries || []}
            columns={columns}
            emptyState={{
              title: "No queries found",
              description: "Create a new query above to get started.",
              icon: MessageSquare,
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
}
