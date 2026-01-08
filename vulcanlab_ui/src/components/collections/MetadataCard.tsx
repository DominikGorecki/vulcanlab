"use client";

import { useEffect, useState } from "react";
import { Loader2, BookOpen, MessageSquare, Search, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ExcerptMetadata {
  type: "excerpt";
  work_id: number;
  title: string;
  authors?: string;
  year?: number;
  heading_breadcrumbs?: string;
  excerpt_preview: string;
}

interface ResearchResultMetadata {
  type: "research_result";
  query_id: number;
  result_id: number;
  query_text: string;
  content_preview: string;
}

interface ResearchQueryMetadata {
  type: "research_query";
  query_id: number;
  query_text: string;
}

type Metadata = ExcerptMetadata | ResearchResultMetadata | ResearchQueryMetadata;

interface MetadataCardProps {
  collectionId: number;
  itemId: number;
}

export function MetadataCard({ collectionId, itemId }: MetadataCardProps) {
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/collections/${collectionId}/items/${itemId}/metadata`);
        if (!response.ok) {
          throw new Error("Failed to load metadata");
        }
        const data = await response.json();
        setMetadata(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error loading metadata");
      } finally {
        setLoading(false);
      }
    };

    fetchMetadata();
  }, [collectionId, itemId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader2 className="h-4 w-4 animate-spin mr-2" />
        <span className="text-sm text-muted-foreground">Loading metadata...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 text-destructive">
        <AlertCircle className="h-4 w-4" />
        <span className="text-sm">{error}</span>
      </div>
    );
  }

  if (!metadata) return null;

  if (metadata.type === "excerpt") {
    return (
      <div className="space-y-2 p-1 max-w-full">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <BookOpen className="h-3.5 w-3.5 text-primary shrink-0" />
            <span className="font-semibold text-sm break-words line-clamp-2">{metadata.title}</span>
          </div>
          {(metadata.authors || metadata.year) && (
            <span className="text-xs text-muted-foreground ml-5 break-words">
              {metadata.authors}{metadata.year ? ` (${metadata.year})` : ""}
            </span>
          )}
        </div>
        
        {metadata.heading_breadcrumbs && (
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium ml-5 break-words">
            {metadata.heading_breadcrumbs}
          </div>
        )}
        
        <blockquote className="mt-2 border-l-2 border-primary/20 pl-3 italic text-sm text-foreground/80 ml-5 break-words whitespace-normal">
          "{metadata.excerpt_preview}"
        </blockquote>
      </div>
    );
  }

  if (metadata.type === "research_result") {
    return (
      <div className="space-y-2 p-1 max-w-full">
        <div className="flex items-center gap-2">
          <Search className="h-3.5 w-3.5 text-primary shrink-0" />
          <span className="font-semibold text-sm">RAG Result for:</span>
        </div>
        <p className="text-sm italic text-muted-foreground ml-5 break-words whitespace-normal">"{metadata.query_text}"</p>
        <div className="mt-2 text-sm text-foreground/80 ml-5 break-words whitespace-normal">
          {metadata.content_preview}
        </div>
      </div>
    );
  }

  if (metadata.type === "research_query") {
    return (
      <div className="flex items-center gap-2 p-1 max-w-full">
        <MessageSquare className="h-3.5 w-3.5 text-primary shrink-0" />
        <span className="text-sm font-medium shrink-0">Query:</span>
        <span className="text-sm italic text-muted-foreground break-words whitespace-normal">"{metadata.query_text}"</span>
      </div>
    );
  }

  return null;
}

