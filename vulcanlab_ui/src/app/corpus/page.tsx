"use client";

import { useRouter } from "next/navigation";
import { Database, Trash2, BookOpen, Layers, CheckCircle2, AlertCircle, Clock, ListTree } from "lucide-react";
import {
  PageHeader,
  DataTable,
  DataTableColumn,
  StatsCardGrid,
  ConfirmDialog,
  StatusBadge,
  PageErrorState,
} from "@/components";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { usePageData } from "@/hooks/use-page-data";
import { useState, useMemo, useCallback } from "react";
import { Zap, FileText } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChunkVectorStats {
  no_vec: number;
  to_vec: number;
  vec: number;
  vec_err: number;
}

interface CorpusStats {
  total_works: number;
  chunk_stats: ChunkVectorStats;
}

interface CorpusWork {
  id: number;
  title: string;
  authors: string | null;
  created_at: string;
  status: string;
  vectorized_chunks: number;
  has_summary: boolean;
}

interface PageData {
  stats: CorpusStats;
  works: CorpusWork[];
}

export default function CorpusPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [workToDelete, setWorkToDelete] = useState<CorpusWork | null>(null);

  const fetchData = useCallback(async () => {
    const [statsRes, worksRes] = await Promise.all([
      fetch(`${API_BASE_URL}/corpus/stats`),
      fetch(`${API_BASE_URL}/corpus/works`),
    ]);

    if (!statsRes.ok) throw new Error("Failed to load statistics");
    if (!worksRes.ok) throw new Error("Failed to load works");

    const stats = await statsRes.json();
    const worksData = await worksRes.json();

    return {
      stats,
      works: worksData.works,
    };
  }, []);

  const { data, loading, error, refetch } = usePageData<PageData>(fetchData);

  const handleDelete = async () => {
    if (!workToDelete) return;

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/corpus/works/${workToDelete.id}`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        throw new Error("Failed to delete work");
      }

      toast({
        title: "Work deleted",
        description: `"${workToDelete.title}" has been removed from the corpus.`,
      });
      
      setWorkToDelete(null);
      refetch();
    } catch (err) {
      toast({
        title: "Deletion failed",
        description: err instanceof Error ? err.message : "An error occurred",
        variant: "destructive",
      });
    }
  };

  const columns: DataTableColumn<CorpusWork>[] = useMemo(() => [
    {
      key: "id",
      header: "ID",
      sortable: true,
      className: "w-[60px] min-w-[60px]",
    },
    {
      key: "title",
      header: "Title",
      sortable: true,
      className: "min-w-[200px] max-w-[400px]",
      cell: (work) => (
        <div className="flex items-center gap-2 font-medium break-words whitespace-normal leading-tight py-1">
          {work.title}
          {work.has_summary && (
            <div className="flex-shrink-0" title="Summarized">
              <CheckCircle2 size={14} className="text-blue-500" />
            </div>
          )}
        </div>
      ),
    },
    {
      key: "authors",
      header: "Authors",
      sortable: true,
      className: "min-w-[150px] max-w-[250px] text-muted-foreground hidden md:table-cell",
      cell: (work) => (
        <div className="break-words whitespace-normal leading-tight">
          {work.authors || "-"}
        </div>
      ),
    },
    {
      key: "vectorized_chunks",
      header: "Vectorized",
      sortable: true,
      className: "w-[100px] min-w-[100px] text-center hidden lg:table-cell",
      cell: (work) => (
        <div className="flex items-center justify-center gap-1.5">
          <Database size={14} className="text-green-600 dark:text-green-500 flex-shrink-0" />
          <span className="font-medium text-green-600 dark:text-green-500">
            {work.vectorized_chunks.toLocaleString()}
          </span>
        </div>
      ),
    },
    {
      key: "created_at",
      header: "Date",
      sortable: true,
      className: "w-[110px] min-w-[110px] hidden sm:table-cell",
      cell: (work) => (
        <div className="flex items-center gap-1.5 text-muted-foreground whitespace-nowrap">
          <Clock size={14} className="flex-shrink-0" />
          <span className="text-xs">{new Date(work.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' })}</span>
        </div>
      ),
    },
    {
      key: "status",
      header: "Type",
      sortable: true,
      className: "w-[110px] min-w-[110px] hidden lg:table-cell",
      cell: (work) => (
        <StatusBadge
          status={work.status}
          statusConfig={{
            Automatic: {
              label: "Auto",
              variant: "default",
              icon: Zap,
            },
            Standard: {
              label: "Std",
              variant: "secondary",
              icon: FileText,
            },
          }}
        />
      ),
    },
    {
      key: "actions" as keyof CorpusWork,
      header: "",
      className: "w-[80px] text-right",
      cell: (work) => (
        <div className="flex items-center justify-end gap-1">
          <button
            onClick={(e) => {
              e.stopPropagation();
              router.push(`/summaries/workflow/${work.id}`);
            }}
            className="p-2 rounded hover:bg-muted transition-colors group"
            title="Generate summary for this work"
            aria-label="Summarize work"
          >
            <ListTree size={16} className="text-muted-foreground group-hover:text-primary" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setWorkToDelete(work);
            }}
            className="p-2 rounded hover:bg-muted transition-colors group"
            title="Delete work"
            aria-label="Delete work"
          >
            <Trash2 size={16} className="text-muted-foreground group-hover:text-destructive" />
          </button>
        </div>
      ),
    },
  ], []);

  if (error) {
    return <PageErrorState error={error} onRetry={refetch} />;
  }

  const stats = data?.stats;
  const works = data?.works || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Corpus"
        description="Works ready for vectorization and RAG."
      />

      {/* Consolidated Stats Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Embeddings Overview</CardTitle>
          <CardDescription>Chunk vectorization status across all corpus works</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
            {/* Total Works */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-muted-foreground">
                <BookOpen className="h-4 w-4" />
                <span className="text-sm font-medium">Total Works</span>
              </div>
              <div className="text-3xl font-bold text-foreground">
                {stats?.total_works || 0}
              </div>
            </div>

            {/* Not Queued */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Layers className="h-4 w-4" />
                <span className="text-sm font-medium">Not Queued</span>
              </div>
              <div className="text-3xl font-bold text-gray-600 dark:text-gray-400">
                {stats?.chunk_stats.no_vec || 0}
              </div>
            </div>

            {/* To Vectorize */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-amber-600 dark:text-amber-500">
                <Clock className="h-4 w-4" />
                <span className="text-sm font-medium">To Vectorize</span>
              </div>
              <div className="text-3xl font-bold text-amber-600 dark:text-amber-500">
                {stats?.chunk_stats.to_vec || 0}
              </div>
            </div>

            {/* Vectorized */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-green-600 dark:text-green-500">
                <CheckCircle2 className="h-4 w-4" />
                <span className="text-sm font-medium">Vectorized</span>
              </div>
              <div className="text-3xl font-bold text-green-600 dark:text-green-500">
                {stats?.chunk_stats.vec || 0}
              </div>
            </div>

            {/* Errors */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-red-600 dark:text-red-500">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm font-medium">Errors</span>
              </div>
              <div className="text-3xl font-bold text-red-600 dark:text-red-500">
                {stats?.chunk_stats.vec_err || 0}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <DataTable
        data={works}
        columns={columns}
        onRowClick={(work) => router.push(`/corpus/${work.id}`)}
        loading={loading}
        emptyState={{
          title: "No corpus works found",
          description: "Works must complete chunking before appearing here.",
          icon: Database,
        }}
      />

      <ConfirmDialog
        open={!!workToDelete}
        onOpenChange={(open) => !open && setWorkToDelete(null)}
        title="Delete Work"
        message={`Are you sure you want to delete "${workToDelete?.title}"? This action cannot be undone.`}
        confirmLabel="Delete"
        onConfirm={handleDelete}
      />
    </div>
  );
}
