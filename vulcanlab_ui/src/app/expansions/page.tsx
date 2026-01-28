"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { Calendar, ListChecks, Link as LinkIcon, Expand } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { DataTable, type DataTableColumn } from "@/components/data-table";
import { EmptyState } from "@/components/empty-state";
import { PageLoadingState } from "@/components/page-loading-state";
import { PageErrorState } from "@/components/page-error-state";
import { ExpansionStatusBadge } from "@/components/expansion";
import { usePageData } from "@/hooks/use-page-data";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ExpansionListItem {
  id: number;
  result_id: number;
  query_id: number;
  mode: string;
  status: string;
  section_count: number;
  completed_count: number;
  failed_count: number;
  created_at: string;
}

export default function ExpansionsPage() {
  const router = useRouter();

  const fetchData = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/expansions/`);

    if (!response.ok) {
      throw new Error("Failed to load expansions");
    }

    const responseData = await response.json();
    return responseData.expansions;
  }, []);

  const { data, loading, error, refetch } = usePageData<ExpansionListItem[]>(fetchData);

  const handleRowClick = (expansion: ExpansionListItem) => {
    router.push(`/expansions/${expansion.id}`);
  };

  if (loading) {
    return <PageLoadingState title="Loading expansions..." />;
  }

  if (error) {
    return <PageErrorState error={error} onRetry={refetch} />;
  }

  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="container mx-auto p-6">
        <PageHeader
          title="Expansions"
          description="View and manage answer expansions"
        />
        <EmptyState
          title="No expansions yet"
          description="Expand an answer from a RAG result to create your first expansion"
          icon={Expand}
        />
      </div>
    );
  }

  const columns: DataTableColumn<ExpansionListItem>[] = [
    {
      key: "id",
      header: "ID",
      sortable: true,
      className: "w-[60px]",
    },
    {
      key: "original_query",
      header: "Original Query",
      sortable: true,
      cell: (row) => (
        <div className="max-w-[400px] truncate" title={row.original_query}>
          {row.original_query}
        </div>
      ),
    },
    {
      key: "mode",
      header: "Mode",
      cell: (row) => (
        <span className="capitalize text-sm">{row.mode}</span>
      ),
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => <ExpansionStatusBadge status={row.status} />,
    },
    {
      key: "section_count",
      header: "Sections",
      cell: (row) => (
        <div className="flex items-center gap-1">
          <ListChecks className="h-4 w-4 text-muted-foreground" />
          <span>{row.section_count}</span>
        </div>
      ),
      sortable: true,
    },
    {
      key: "result_id",
      header: "Result",
      cell: (row) => (
        <div className="flex items-center gap-1">
          <LinkIcon className="h-4 w-4 text-muted-foreground" />
          <span>#{row.result_id}</span>
        </div>
      ),
    },
    {
      key: "created_at",
      header: "Created",
      cell: (row) => (
        <div className="flex items-center gap-1">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <span>{new Date(row.created_at).toLocaleDateString()}</span>
        </div>
      ),
      sortable: true,
    },
  ];

  return (
    <div className="container mx-auto p-6">
      <PageHeader
        title="Expansions"
        description="View and manage answer expansions"
      />

      <DataTable
        data={data}
        columns={columns}
        onRowClick={handleRowClick}
        emptyState={{
          title: "No expansions found",
          description: "Create an expansion from a RAG result to get started",
          icon: Expand,
        }}
      />
    </div>
  );
}
