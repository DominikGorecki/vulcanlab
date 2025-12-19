/**
 * Simple Conversion Detail Page
 *
 * Displays full conversion results for a specific work_id including:
 * - Summary card with metadata and metrics
 * - Data table of all chunks
 * - Navigation back to simple conversion page
 */

"use client";

import React, { useMemo, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Plus } from "lucide-react";
import { SimpleConversionSummaryCard } from "@/components/simple-conversion/SimpleConversionSummaryCard";
import { PageHeader } from "@/components/page-header";
import { DataTable, DataTableColumn } from "@/components/data-table";
import { usePageData } from "@/hooks/use-page-data";
import { PageLoadingState } from "@/components/page-loading-state";
import { PageErrorState } from "@/components/page-error-state";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChunkData {
  id: number;
  heading_level: string;
  heading_text: string;
  start_line: number;
  end_line: number;
  content_preview: string;
}

interface ResultsData {
  work_id: number;
  title: string;
  author: string;
  classification: 'small' | 'large';
  token_count: number;
  chunk_count: number;
  chunks: ChunkData[];
  mode?: 'automatic' | 'manual';
  status?: 'success' | 'failed';
  error_message?: string | null;
}

export default function ConversionDetailPage() {
  const router = useRouter();
  const params = useParams();
  const work_id = params?.work_id as string;

  const fetchResultsFn = useCallback(async () => {
    if (!work_id) throw new Error('Invalid work ID');

    const response = await fetch(`${API_BASE_URL}/api/simple-conversion/results/${work_id}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Work not found');
      } else if (response.status === 400) {
        throw new Error('This work has not been processed or is not a simple conversion');
      } else {
        throw new Error(`Failed to fetch results: ${response.statusText}`);
      }
    }

    const data = await response.json();

    // Fetch additional metadata from history endpoint
    let mode: 'automatic' | 'manual' = 'automatic';
    let status: 'success' | 'failed' = 'success';
    let error_message: string | null = null;

    try {
      const historyResponse = await fetch(`${API_BASE_URL}/api/simple-conversion/history`);
      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        const workHistory = historyData.items?.find((item: any) => item.work_id === parseInt(work_id));
        if (workHistory) {
          mode = workHistory.mode || 'automatic';
          status = workHistory.status === 'complete' ? 'success' : 'failed';
          error_message = workHistory.error_message || null;
        }
      }
    } catch (err) {
      console.warn('Failed to fetch history metadata:', err);
    }

    return {
      ...data,
      mode,
      status,
      error_message
    };
  }, [work_id]);

  const { 
    data: results, 
    loading, 
    error, 
    refetch: fetchResults 
  } = usePageData<ResultsData>(fetchResultsFn, { autoFetch: !!work_id });

  // Get badge color based on level
  const getBadgeColor = (level: string) => {
    const isContentChunk = level.endsWith('-chunk') || level === 'chunk';
    if (isContentChunk) {
      return 'bg-slate-500 hover:bg-slate-600 text-white';
    }

    switch (level) {
      case 'H1':
        return 'bg-indigo-600 hover:bg-indigo-700 text-white';
      case 'H2':
        return 'bg-blue-600 hover:bg-blue-700 text-white';
      case 'H3':
        return 'bg-cyan-600 hover:bg-cyan-700 text-white';
      case 'H4':
        return 'bg-teal-600 hover:bg-teal-700 text-white';
      case 'H5':
        return 'bg-green-600 hover:bg-green-700 text-white';
      default:
        return 'bg-gray-600 hover:bg-gray-700 text-white';
    }
  };

  const columns: DataTableColumn<ChunkData>[] = [
    {
      key: 'heading_level',
      header: 'Level',
      className: "w-[80px]",
      cell: (chunk) => (
        <Badge className={getBadgeColor(chunk.heading_level)}>
          {chunk.heading_level}
        </Badge>
      )
    },
    {
      key: 'heading_text',
      header: 'Heading',
      sortable: true,
      className: "min-w-[200px] max-w-[400px] whitespace-normal break-words font-medium",
    },
    {
      key: 'start_line',
      header: 'Range',
      sortable: true,
      cell: (chunk) => `Lines ${chunk.start_line}-${chunk.end_line}`,
      className: "w-[120px] text-xs text-muted-foreground whitespace-nowrap",
    },
    {
      key: 'content_preview',
      header: 'Content Preview',
      className: "min-w-[400px] whitespace-normal break-words font-mono text-xs",
      cell: (chunk) => (
        <div className="max-h-[80px] overflow-hidden text-ellipsis whitespace-pre-wrap">
          {chunk.content_preview}
        </div>
      )
    }
  ];

  const chunkCounts = useMemo(() => {
    if (!results?.chunks) return { heading_count: 0, content_count: 0 };
    
    let heading_count = 0;
    let content_count = 0;

    results.chunks.forEach(chunk => {
      const level = chunk.heading_level;
      if (['H1', 'H2', 'H3', 'H4', 'H5'].includes(level)) {
        heading_count++;
      } else if (level.endsWith('-chunk') || level === 'chunk') {
        content_count++;
      }
    });

    return { heading_count, content_count };
  }, [results?.chunks]);

  if (loading) {
    return <PageLoadingState />;
  }

  if (error || !results) {
    return (
      <PageErrorState 
        error={error || 'Failed to load results'} 
        title="Unable to load conversion results"
        onRetry={fetchResults}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Conversion Details"
        description={`Full results for "${results.title}"`}
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push('/simple-conversion')}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Simple Conversion
          </Button>
        }
      />

      <SimpleConversionSummaryCard
        title={results.title}
        author={results.author}
        classification={results.classification}
        mode={results.mode || 'automatic'}
        status={results.status || 'success'}
        token_count={results.token_count}
        chunk_count={results.chunk_count}
        heading_chunk_count={chunkCounts.heading_count}
        content_chunk_count={chunkCounts.content_count}
        error_message={results.error_message}
      />

      <div className="space-y-4">
        <div>
          <h3 className="text-2xl font-bold tracking-tight">
            Chunks ({results.chunks.length})
          </h3>
          <p className="text-sm text-muted-foreground">
            All chunks generated from this conversion
          </p>
        </div>

        <DataTable
          columns={columns}
          data={results.chunks}
          emptyState={{
            title: "No chunks found",
            description: "No chunks were generated for this conversion.",
          }}
        />
      </div>

      <div className="flex justify-end gap-2 pt-4 border-t">
        <Button
          onClick={() => router.push('/simple-conversion')}
          className="gap-2"
        >
          <Plus className="h-4 w-4" />
          Start New Conversion
        </Button>
      </div>
    </div>
  );
}
