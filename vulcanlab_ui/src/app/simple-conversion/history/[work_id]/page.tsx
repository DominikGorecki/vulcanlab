/**
 * Simple Conversion Detail Page
 *
 * Displays full conversion results for a specific work_id including:
 * - Summary card with metadata and metrics
 * - Scrollable list of all chunks
 * - Navigation back to simple conversion page
 * - Error handling for invalid work_id or fetch failures
 */

"use client";

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2Icon, AlertCircle, ArrowLeft } from "lucide-react";
import { SimpleConversionSummaryCard } from "@/components/simple-conversion/SimpleConversionSummaryCard";
import { ChunkListItem } from "@/components/simple-conversion/ChunkListItem";

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

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ResultsData | null>(null);

  useEffect(() => {
    if (!work_id) {
      setError('Invalid work ID');
      setLoading(false);
      return;
    }

    fetchResults();
  }, [work_id]);

  const fetchResults = async () => {
    try {
      setLoading(true);
      setError(null);

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

      // Fetch additional metadata from history endpoint to get mode, status, error_message
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

      setResults({
        ...data,
        mode,
        status,
        error_message
      });
    } catch (err) {
      console.error('Failed to fetch results:', err);
      const message = err instanceof Error ? err.message : 'Failed to load conversion results';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  // Calculate heading and content chunk counts
  const calculateChunkCounts = (chunks: ChunkData[]) => {
    let heading_count = 0;
    let content_count = 0;

    chunks.forEach(chunk => {
      const level = chunk.heading_level;
      if (['H1', 'H2', 'H3', 'H4', 'H5'].includes(level)) {
        heading_count++;
      } else if (level.endsWith('-chunk') || level === 'chunk') {
        content_count++;
      }
    });

    return { heading_count, content_count };
  };

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6" data-testid="loading-state">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Conversion Details</h2>
          <p className="text-muted-foreground">Loading conversion results...</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  // Error state
  if (error || !results) {
    return (
      <div className="space-y-6" data-testid="error-state">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Conversion Details</h2>
          <p className="text-muted-foreground">Unable to load conversion results</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error || 'Failed to load results'}</AlertDescription>
        </Alert>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => router.push('/simple-conversion')}
            data-testid="back-to-simple-conversion"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Simple Conversion
          </Button>
          <Button onClick={fetchResults}>Retry</Button>
        </div>
      </div>
    );
  }

  const { heading_count, content_count } = calculateChunkCounts(results.chunks);

  return (
    <div className="space-y-6">
      {/* Header with Back Button */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/simple-conversion')}
          data-testid="back-button"
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Simple Conversion
        </Button>
      </div>

      <div>
        <h2 className="text-3xl font-bold tracking-tight">Conversion Details</h2>
        <p className="text-muted-foreground">
          Full results for &quot;{results.title}&quot;
        </p>
      </div>

      {/* Summary Card */}
      <SimpleConversionSummaryCard
        title={results.title}
        author={results.author}
        classification={results.classification}
        mode={results.mode || 'automatic'}
        status={results.status || 'success'}
        token_count={results.token_count}
        chunk_count={results.chunk_count}
        heading_chunk_count={heading_count}
        content_chunk_count={content_count}
        error_message={results.error_message}
      />

      {/* Chunks Section */}
      <div className="space-y-4">
        <div>
          <h3 className="text-2xl font-bold tracking-tight">
            Chunks ({results.chunks.length})
          </h3>
          <p className="text-sm text-muted-foreground">
            All chunks generated from this conversion
          </p>
        </div>

        <ScrollArea className="h-[600px] pr-4" data-testid="chunks-list">
          <div className="space-y-3">
            {results.chunks.map((chunk) => (
              <ChunkListItem
                key={chunk.id}
                level={chunk.heading_level}
                heading={chunk.heading_text}
                line_range={`Lines ${chunk.start_line}-${chunk.end_line}`}
                content={chunk.content_preview}
              />
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Footer Actions */}
      <div className="flex justify-end gap-2 pt-4 border-t">
        <Button
          onClick={() => router.push('/simple-conversion')}
          data-testid="start-new-conversion"
          className="bg-green-600 hover:bg-green-700"
        >
          Start New Conversion
        </Button>
      </div>
    </div>
  );
}
