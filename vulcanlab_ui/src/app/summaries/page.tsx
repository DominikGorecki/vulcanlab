"use client";

import { useRouter } from "next/navigation";
import { FileText, Clock, Hash, Database } from "lucide-react";
import {
  PageHeader,
  DataTable,
  DataTableColumn,
  PageErrorState,
} from "@/components";
import { usePageData } from "@/hooks/use-page-data";
import { useMemo, useCallback } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SummarizedWork {
  work_id: number;
  title: string;
  summary_count: number;
  last_updated: string;
}

interface PageData {
  works: SummarizedWork[];
}

export default function SummariesPage() {
  const router = useRouter();

  const fetchData = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/summarize/works`);

    if (!response.ok) {
      throw new Error("Failed to load summaries");
    }

    return await response.json();
  }, []);

  const { data, loading, error, refetch } = usePageData<PageData>(fetchData);

  const columns: DataTableColumn<SummarizedWork>[] = useMemo(
    () => [
      {
        key: "work_id",
        header: "ID",
        sortable: true,
        className: "w-[80px]",
      },
      {
        key: "title",
        header: "Title",
        sortable: true,
        className: "min-w-[200px]",
        cell: (work) => (
          <div className="font-medium text-foreground py-1">{work.title}</div>
        ),
      },
      {
        key: "summary_count",
        header: "Summaries",
        sortable: true,
        className: "w-[120px] text-center",
        cell: (work) => (
          <div className="flex items-center justify-center gap-1.5">
            <Hash size={14} className="text-muted-foreground" />
            <span>{work.summary_count}</span>
          </div>
        ),
      },
      {
        key: "last_updated",
        header: "Last Updated",
        sortable: true,
        className: "w-[180px]",
        cell: (work) => (
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Clock size={14} />
            <span className="text-xs">
              {new Date(work.last_updated).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
        ),
      },
    ],
    []
  );

  if (error) {
    return <PageErrorState error={error} onRetry={refetch} />;
  }

  const works = data?.works || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Summaries"
        description="View generated summaries for your works."
      />

      <DataTable
        data={works}
        columns={columns}
        onRowClick={(work) => router.push(`/summaries/${work.work_id}`)}
        loading={loading}
        emptyState={{
          title: "No summaries yet",
          description: "Start summarizing your works from the Corpus page.",
          icon: FileText,
          action: {
            label: "Go to Corpus",
            onClick: () => router.push("/corpus"),
          },
        }}
      />
    </div>
  );
}
