"use client";

import React, { useCallback } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/page-header";
import { DataTable, DataTableColumn } from "@/components/data-table";
import { PageLoadingState } from "@/components/page-loading-state";
import { PageErrorState } from "@/components/page-error-state";
import { usePageData } from "@/hooks/use-page-data";
import { StatusBadge, StatusConfig } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { BookOpen } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SummarizedWork {
  work_id: number;
  title: string;
  node_count: number;
  summaries: string[];
}

interface SummarizedWorksResponse {
  works: SummarizedWork[];
}

const summaryTypeConfig: Record<string, StatusConfig> = {
  abstract: { label: "Abstract", variant: "default" },
  outline: { label: "Outline", variant: "secondary" },
  key_concepts: { label: "Key Concepts", variant: "outline" },
  chapter_summaries: { label: "Chapter Summaries", variant: "outline" },
};

export default function SummarizePage() {
  const router = useRouter();

  const fetchSummarizedWorks = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/summarize/works`);
    if (!response.ok) {
      throw new Error("Failed to fetch summarized works");
    }
    return response.json();
  }, []);

  const { data, loading, error, refetch } = usePageData<SummarizedWorksResponse>(fetchSummarizedWorks);

  const works = data?.works || [];

  const columns: DataTableColumn<SummarizedWork>[] = [
    {
      key: "title",
      header: "Title",
      sortable: true,
      className: "font-medium",
    },
    {
      key: "node_count",
      header: "Nodes",
      sortable: true,
    },
    {
      key: "summaries",
      header: "Summaries",
      cell: (work) => (
        <div className="flex flex-wrap gap-1">
          {work.summaries.map((type) => (
            <StatusBadge
              key={type}
              status={type}
              statusConfig={summaryTypeConfig}
            />
          ))}
        </div>
      ),
    },
    {
      key: "work_id",
      header: "Actions",
      cell: (work) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            router.push(`/summarize/${work.work_id}`);
          }}
        >
          View
        </Button>
      ),
    },
  ];

  if (loading) {
    return (
      <div className="p-6">
        <PageHeader title="Summarize" description="View and manage work summaries" />
        <PageLoadingState />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <PageHeader title="Summarize" description="View and manage work summaries" />
        <PageErrorState
          error={error}
          onRetry={refetch}
          title="Error loading summaries"
        />
      </div>
    );
  }

  return (
    <div className="p-6">
      <PageHeader
        title="Summarize"
        description="View and manage work summaries"
      />
      <DataTable
        data={works}
        columns={columns}
        onRowClick={(work) => router.push(`/summarize/${work.work_id}`)}
        emptyState={{
          title: "No summarized works",
          description: "No works have been summarized yet. Go to Corpus to summarize a work.",
          icon: BookOpen,
        }}
      />
    </div>
  );
}
