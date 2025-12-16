/**
 * SimpleConversionHistoryCard Component
 *
 * Displays a summary card for a simple conversion work in the history list.
 * Shows title, author, classification, mode, status, and creation date.
 * Clicking the card navigates to the detail page.
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, Play, Hand } from "lucide-react";

export interface SimpleConversionHistoryCardProps {
  work_id: number;
  title: string;
  author: string;
  classification: 'small' | 'large';
  mode: 'automatic' | 'manual';
  status: 'success' | 'error';
  created_at: string;
  error_message?: string | null;
}

export function SimpleConversionHistoryCard({
  work_id,
  title,
  author,
  classification,
  mode,
  status,
  created_at,
}: SimpleConversionHistoryCardProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/simple-conversion/history/${work_id}`);
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <Card
      onClick={handleClick}
      className="cursor-pointer transition-all hover:shadow-md hover:border-primary/50"
      data-testid={`history-card-${work_id}`}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg leading-tight">{title}</CardTitle>
          {status === 'success' ? (
            <CheckCircle2
              className="h-5 w-5 text-green-600 flex-shrink-0"
              data-testid="status-success"
            />
          ) : (
            <XCircle
              className="h-5 w-5 text-red-600 flex-shrink-0"
              data-testid="status-error"
            />
          )}
        </div>
        <p className="text-sm text-muted-foreground">{author}</p>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap items-center gap-2">
          <Badge
            variant={classification === 'small' ? 'default' : 'secondary'}
            className={classification === 'small' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-purple-600 hover:bg-purple-700 text-white'}
            data-testid="classification-badge"
          >
            {classification === 'small' ? 'Small' : 'Large'}
          </Badge>

          <Badge
            variant="outline"
            className="flex items-center gap-1"
            data-testid="mode-badge"
          >
            {mode === 'automatic' ? (
              <>
                <Play className="h-3 w-3" />
                <span>Automatic</span>
              </>
            ) : (
              <>
                <Hand className="h-3 w-3" />
                <span>Manual</span>
              </>
            )}
          </Badge>

          <span className="text-xs text-muted-foreground ml-auto" data-testid="created-date">
            {formatDate(created_at)}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
