"use client";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Hash, FileText, Layers } from "lucide-react";
import { truncateToWordLimit } from "@/lib/utils";
import Link from "next/link";

export interface SearchResult {
  id: number;
  content_preview: string;
  breadcrumb: string;
  level: string;
  work_id: number;
  work_title: string;
  work_authors: string | null;
  work_year: number | null;
  start_line: number;
  end_line: number;
  rank_score?: number; // For lexical search
  similarity_score?: number; // For dense search
  rrf_score?: number; // For hybrid search
  dense_rank?: number | null;
  lexical_rank?: number | null;
}

interface SearchResultCardProps {
  result: SearchResult;
  searchMode: "lexical" | "dense" | "hybrid";
  maxPreviewWords: number;
}

export function SearchResultCard({ result, searchMode, maxPreviewWords }: SearchResultCardProps) {
  const getLevelBadgeVariant = (level: string): "default" | "secondary" | "outline" => {
    if (level.startsWith("H")) return "default";
    if (level === "sentence") return "secondary";
    return "outline";
  };

  const formatBibliographic = (res: SearchResult): string => {
    const parts: string[] = [];
    if (res.work_authors) parts.push(res.work_authors);
    if (res.work_year) parts.push(`(${res.work_year})`);
    
    const biblio = parts.length > 0 ? `${parts.join(" ")}. ` : "";
    return biblio;
  };

  const truncatedContent = truncateToWordLimit(result.content_preview, maxPreviewWords);

  return (
    <Link href={`/search/result/${result.work_id}/${result.start_line}/${result.end_line}`} className="block">
      <Card className="p-5 transition-all hover:shadow-md hover:border-primary/50 group cursor-pointer">
        {/* Bibliographic Info & Icon */}
        <div className="flex items-start gap-2 mb-0.5">
          <BookOpen className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
          <div>
            <span className="text-sm font-bold text-foreground group-hover:text-primary transition-colors">
              {result.work_title}
            </span>
            <span className="text-xs text-muted-foreground italic ml-2">
              {formatBibliographic(result)}
            </span>
          </div>
        </div>

        {/* Breadcrumb - Styled as a heading */}
        <div className="mb-2 pl-6">
          <h4 className="text-[13px] font-semibold text-muted-foreground/90 leading-snug">
            {result.breadcrumb}
          </h4>
        </div>

        {/* Content Preview */}
        <p className="text-[13px] text-foreground/80 mb-3 leading-relaxed pl-6">
          {truncatedContent}
        </p>

        {/* Metadata Row */}
        <div className="flex items-center gap-3 text-[10px] text-muted-foreground flex-wrap pl-6">
          <Badge variant={getLevelBadgeVariant(result.level)} className="px-1.5 py-0 h-4 text-[10px]">
            {result.level}
          </Badge>
          
          <div className="flex items-center gap-1">
            <Layers className="h-3 w-3" />
            <span>Work ID: {result.work_id}</span>
          </div>

          <div className="flex items-center gap-1">
            <FileText className="h-3 w-3" />
            <span>Lines {result.start_line}-{result.end_line}</span>
          </div>

          <div className="flex items-center gap-1">
            <Hash className="h-3 w-3" />
            <span>ID: {result.id}</span>
          </div>
          
          {/* Scores and Ranks */}
          <div className="ml-auto flex items-center gap-2">
            {searchMode === "hybrid" && (
              <>
                {result.dense_rank !== undefined && result.dense_rank !== null && (
                  <Badge variant="outline" className="text-[10px] h-4 px-1 border-blue-200 bg-blue-50/30 text-blue-700 dark:text-blue-400 dark:bg-blue-900/20">
                    Dense Rank: {result.dense_rank}
                  </Badge>
                )}
                {result.lexical_rank !== undefined && result.lexical_rank !== null && (
                  <Badge variant="outline" className="text-[10px] h-4 px-1 border-orange-200 bg-orange-50/30 text-orange-700 dark:text-orange-400 dark:bg-orange-900/20">
                    Lexical Rank: {result.lexical_rank}
                  </Badge>
                )}
                <span className="font-semibold text-foreground text-xs ml-1">
                  RRF: {result.rrf_score?.toFixed(4)}
                </span>
              </>
            )}

            {searchMode === "lexical" && result.rank_score !== undefined && (
              <span className="font-medium text-foreground text-xs">
                Score: {result.rank_score.toFixed(4)}
              </span>
            )}

            {searchMode === "dense" && result.similarity_score !== undefined && (
              <span className="font-medium text-foreground text-xs">
                Similarity: {result.similarity_score.toFixed(4)}
              </span>
            )}
          </div>
        </div>
      </Card>
    </Link>
  );
}

