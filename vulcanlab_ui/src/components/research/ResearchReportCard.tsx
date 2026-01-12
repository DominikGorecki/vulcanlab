"use client";

import React from "react";
import { FileText, Calendar, AlignLeft, Hash, Quote } from "lucide-react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ResearchSession } from "@/types/research";
import { cn } from "@/lib/utils";

interface ResearchReportCardProps {
  session: ResearchSession;
  onClick: () => void;
}

/**
 * ResearchReportCard component displays a summary of a completed research report.
 */
export function ResearchReportCard({ session, onClick }: ResearchReportCardProps) {
  const { 
    session_type, 
    created_at, 
    state_data 
  } = session;

  const formattedDate = new Date(created_at).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });

  // Extract metadata from state_data if available
  const executiveSummary = state_data?.executive_summary || "";
  const preview = executiveSummary 
    ? (executiveSummary.length > 150 ? executiveSummary.substring(0, 150) + "..." : executiveSummary)
    : "No executive summary available.";
  
  const wordCount = state_data?.report_metadata?.word_count || state_data?.report_metadata?.total_words || 0;
  const citationCount = state_data?.report_metadata?.citation_count || 0;
  const reportTitle = state_data?.report_title || "Research Report";

  return (
    <Card 
      className={cn(
        "group cursor-pointer transition-all hover:border-primary/50 hover:shadow-md",
        "flex flex-col h-full"
      )}
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start mb-2">
          <Badge 
            variant={session_type === "automated" ? "default" : "secondary"}
            className="capitalize"
          >
            {session_type}
          </Badge>
          <div className="flex items-center text-xs text-muted-foreground gap-1">
            <Calendar className="h-3 w-3" />
            {formattedDate}
          </div>
        </div>
        <CardTitle className="text-base flex items-center gap-2">
          <FileText className="h-4 w-4 text-primary" />
          {reportTitle}
        </CardTitle>
      </CardHeader>
      
      <CardContent className="pb-4 flex-grow">
        <div className="flex items-start gap-2 text-sm text-muted-foreground">
          <AlignLeft className="h-4 w-4 mt-0.5 shrink-0" />
          <p className="italic line-clamp-3">
            {preview}
          </p>
        </div>
      </CardContent>
      
      <CardFooter className="pt-0 flex justify-between items-center border-t mt-auto py-3">
        <div className="flex gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1" title="Word count">
            <Hash className="h-3 w-3" />
            {wordCount} {wordCount === 1 ? 'word' : 'words'}
          </div>
          <div className="flex items-center gap-1" title="Citation count">
            <Quote className="h-3 w-3" />
            {citationCount} {citationCount === 1 ? 'citation' : 'citations'}
          </div>
        </div>
        <Button size="sm" variant="ghost" className="h-8 group-hover:text-primary">
          View Report
        </Button>
      </CardFooter>
    </Card>
  );
}
