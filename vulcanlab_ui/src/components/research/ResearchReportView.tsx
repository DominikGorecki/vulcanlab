"use client";

import React, { useCallback, useState } from "react";
import { 
  X, 
  Download, 
  ExternalLink, 
  Loader2, 
  Info
} from "lucide-react";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogFooter,
  DialogDescription
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { usePageData } from "@/hooks/use-page-data";
import { ResearchReport } from "@/types/research";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import { MetadataCard } from "@/components/collections/MetadataCard";
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ResearchReportViewProps {
  sessionId: number;
  collectionId: number;
  onClose: () => void;
}

/**
 * ResearchReportView component displays the full research report in a modal.
 */
export function ResearchReportView({ sessionId, collectionId, onClose }: ResearchReportViewProps) {
  const fetchReport = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}/report`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Report not found for this session.");
      }
      throw new Error(`Failed to load report: ${response.statusText}`);
    }
    return await response.json();
  }, [sessionId]);

  const { data: report, loading, error } = usePageData<ResearchReport>(fetchReport);

  // Custom link renderer to handle citation links
  const components = {
    a: ({ href, children, ...props }: any) => {
      if (href?.startsWith("link://collection-item/")) {
        const itemIdStr = href.replace("link://collection-item/", "");
        const itemId = parseInt(itemIdStr);
        
        if (isNaN(itemId)) return <span>{children}</span>;

        return (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="text-primary hover:underline font-medium cursor-help border-b border-primary/30 border-dotted">
                  {children}
                </span>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs p-0 bg-popover text-popover-foreground border shadow-md">
                <div className="p-3">
                  <h4 className="font-semibold text-xs mb-2 flex items-center gap-1.5 text-primary">
                    <Info className="h-3.5 w-3.5" />
                    Citation Source
                  </h4>
                  <MetadataCard 
                    collectionId={collectionId} 
                    itemId={itemId} 
                  />
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        );
      }

      // External links
      return (
        <a 
          href={href} 
          target="_blank" 
          rel="noopener noreferrer" 
          className="text-primary hover:underline inline-flex items-center gap-1"
          {...props}
        >
          {children}
          <ExternalLink className="h-3 w-3" />
        </a>
      );
    }
  };

  return (
    <Dialog open={true} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl w-[90vw] h-[90vh] flex flex-col p-0">
        <DialogHeader className="px-6 py-4 border-b">
          <div className="flex justify-between items-center">
            <div>
              <DialogTitle className="text-xl">Research Report</DialogTitle>
              <DialogDescription>
                Session ID: {sessionId}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-grow overflow-hidden flex flex-col">
          {loading ? (
            <div className="flex-grow flex items-center justify-center">
              <div className="flex flex-col items-center gap-4">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground font-medium">Fetching report content...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex-grow flex items-center justify-center p-8 text-center">
              <div className="max-w-md space-y-4">
                <div className="rounded-full bg-destructive/10 p-3 w-12 h-12 mx-auto flex items-center justify-center">
                  <X className="h-6 w-6 text-destructive" />
                </div>
                <h3 className="text-lg font-semibold">Error Loading Report</h3>
                <p className="text-sm text-muted-foreground">{error}</p>
                <Button onClick={onClose} variant="outline">Close</Button>
              </div>
            </div>
          ) : report ? (
            <ScrollArea className="flex-grow p-6 md:p-10">
              <div className="max-w-3xl mx-auto space-y-8">
                {report.executive_summary && (
                  <section className="bg-primary/5 border border-primary/10 rounded-lg p-6 mb-8">
                    <h3 className="text-lg font-bold mb-3 flex items-center gap-2 text-primary">
                      Executive Summary
                    </h3>
                    <p className="text-sm leading-relaxed italic text-foreground/90">
                      {report.executive_summary}
                    </p>
                  </section>
                )}

                <div className="markdown-content">
                  <MarkdownRenderer 
                    content={report.report_content} 
                    components={components as any}
                  />
                </div>
              </div>
            </ScrollArea>
          ) : null}
        </div>

        <DialogFooter className="px-6 py-4 border-t bg-muted/10">
          <div className="flex justify-between items-center w-full">
            <div className="flex gap-4 text-xs text-muted-foreground">
              {report?.report_metadata?.word_count !== undefined && (
                <span>{report.report_metadata.word_count} {report.report_metadata.word_count === 1 ? 'word' : 'words'}</span>
              )}
              {report?.report_metadata?.citation_count !== undefined && (
                <span>{report.report_metadata.citation_count} {report.report_metadata.citation_count === 1 ? 'citation' : 'citations'}</span>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>Close</Button>
              <Button disabled title="PDF Export coming soon">
                <Download className="h-4 w-4 mr-2" />
                Export PDF
              </Button>
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
