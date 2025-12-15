/**
 * Summary Card Component for Simple Conversion Results
 *
 * Displays metadata and metrics for a completed conversion including:
 * - Work metadata (title, author, classification)
 * - Processing info (mode, status)
 * - Metrics (token count, chunk counts)
 * - Error message if conversion failed
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, CheckCircle2 } from "lucide-react";

export interface SimpleConversionSummaryCardProps {
  title: string;
  author: string;
  classification: 'small' | 'large';
  mode: 'automatic' | 'manual';
  status: 'success' | 'failed';
  token_count: number;
  chunk_count: number;
  heading_chunk_count: number;
  content_chunk_count: number;
  error_message?: string | null;
}

export function SimpleConversionSummaryCard({
  title,
  author,
  classification,
  mode,
  status,
  token_count,
  chunk_count,
  heading_chunk_count,
  content_chunk_count,
  error_message
}: SimpleConversionSummaryCardProps) {
  return (
    <div className="space-y-4">
      {/* Error Banner */}
      {status === 'failed' && error_message && (
        <Alert variant="destructive" data-testid="error-banner">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Conversion Failed</AlertTitle>
          <AlertDescription>{error_message}</AlertDescription>
        </Alert>
      )}

      {/* Summary Card */}
      <Card data-testid="summary-card">
        <CardHeader>
          <CardTitle>Conversion Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-2">
            {/* Left Column */}
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Title</h4>
                <p className="font-medium" data-testid="title">{title}</p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Author</h4>
                <p className="font-medium" data-testid="author">{author}</p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Classification</h4>
                <Badge
                  variant={classification === 'small' ? 'default' : 'secondary'}
                  className={classification === 'small' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-purple-600 hover:bg-purple-700 text-white'}
                  data-testid="classification-badge"
                >
                  {classification === 'small' ? 'Small' : 'Large'}
                </Badge>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Mode</h4>
                <Badge variant="outline" data-testid="mode-badge">
                  {mode === 'automatic' ? 'Automatic' : 'Manual'}
                </Badge>
              </div>
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Status</h4>
                {status === 'success' ? (
                  <div className="flex items-center gap-2 text-green-600" data-testid="status-indicator">
                    <CheckCircle2 className="h-4 w-4" />
                    <span className="font-medium">Success</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-red-600" data-testid="status-indicator">
                    <AlertCircle className="h-4 w-4" />
                    <span className="font-medium">Failed</span>
                  </div>
                )}
              </div>
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Token Count</h4>
                <p className="font-mono font-medium" data-testid="token-count">{token_count.toLocaleString()}</p>
              </div>
            </div>
          </div>

          {/* Chunk Counts Section */}
          <div className="mt-6 pt-6 border-t">
            <h4 className="text-sm font-medium text-muted-foreground mb-3">Chunk Statistics</h4>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="bg-muted/50 rounded-lg p-3">
                <p className="text-xs text-muted-foreground mb-1">Total Chunks</p>
                <p className="text-2xl font-bold" data-testid="chunk-count">{chunk_count}</p>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <p className="text-xs text-muted-foreground mb-1">Heading Chunks</p>
                <p className="text-2xl font-bold" data-testid="heading-chunk-count">{heading_chunk_count}</p>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <p className="text-xs text-muted-foreground mb-1">Content Chunks</p>
                <p className="text-2xl font-bold" data-testid="content-chunk-count">{content_chunk_count}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
