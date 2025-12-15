/**
 * Chunk List Item Component
 *
 * Displays a single chunk with:
 * - Level badge (H1-H5 for headings, different styling for content chunks)
 * - Heading text
 * - Line range
 * - Content preview
 */

import React from 'react';
import { Badge } from "@/components/ui/badge";

export interface ChunkListItemProps {
  level: string;
  heading: string;
  line_range: string;
  content: string;
}

export function ChunkListItem({
  level,
  heading,
  line_range,
  content
}: ChunkListItemProps) {
  // Determine if this is a heading chunk or content chunk
  const isHeadingChunk = ['H1', 'H2', 'H3', 'H4', 'H5'].includes(level);
  const isContentChunk = level.endsWith('-chunk') || level === 'chunk';

  // Get badge color based on level
  const getBadgeColor = () => {
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

  return (
    <div
      className="border rounded-lg p-4 bg-card hover:shadow-md transition-shadow"
      data-testid="chunk-item"
    >
      <div className="flex items-start justify-between gap-4 mb-2">
        <div className="flex items-center gap-2">
          <Badge
            className={getBadgeColor()}
            data-testid="level-badge"
          >
            {level}
          </Badge>
          {heading && (
            <h4 className="font-semibold text-lg" data-testid="chunk-heading">
              {heading}
            </h4>
          )}
        </div>
        <span
          className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded whitespace-nowrap"
          data-testid="line-range"
        >
          {line_range}
        </span>
      </div>
      {content && (
        <div className="pl-4 border-l-2 border-muted mt-2">
          <p
            className="text-sm text-muted-foreground whitespace-pre-wrap font-mono text-xs"
            data-testid="content-preview"
          >
            {content}
          </p>
        </div>
      )}
    </div>
  );
}
