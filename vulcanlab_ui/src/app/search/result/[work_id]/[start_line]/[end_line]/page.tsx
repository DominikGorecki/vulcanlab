"use client";

import { useEffect, useRef, useMemo, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronLeft, Loader2, AlertCircle, BookOpen, FolderPlus } from "lucide-react";
import { usePageData } from "@/hooks/use-page-data";
import { useAddToCollection } from "@/hooks/use-add-to-collection";
import { AddToCollectionModal } from "@/components/collections/AddToCollectionModal";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface MarkdownResponse {
  work_id: number;
  work_title: string;
  content: string; // From SanitizedContentResponse
  filename: string;
}

export default function DocumentViewerPage() {
  const params = useParams();
  const router = useRouter();
  
  const workId = params.work_id as string;
  const startLine = parseInt(params.start_line as string);
  const endLine = parseInt(params.end_line as string);

  // Memoized fetch function for usePageData
  const fetchMarkdown = useCallback(async () => {
    if (!workId) {
      throw new Error("Missing work ID");
    }
    const response = await fetch(`${API_BASE_URL}/corpus/work/${workId}/content`);
    if (!response.ok) {
      throw new Error(`Failed to fetch markdown: ${response.statusText}`);
    }
    return response.json() as Promise<MarkdownResponse>;
  }, [workId]);

  const { data, loading, error } = usePageData<MarkdownResponse>(fetchMarkdown, { autoFetch: !!workId });
  
  const { 
    isOpen, 
    openAddToCollection, 
    closeAddToCollection, 
    itemType, 
    itemLink 
  } = useAddToCollection();

  const highlightRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (data && highlightRef.current) {
      // Small delay to ensure rendering is complete
      const timer = setTimeout(() => {
        highlightRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [data]);

  const renderedContent = useMemo(() => {
    if (!data) return null;

    const lines = data.content.split("\n");
    
    // Line numbers are 1-indexed in our system.
    // Ensure startLine is at least 1 to avoid slice(-1) behavior.
    const safeStartLine = Math.max(1, startLine);
    
    // slice(start, end) where end is exclusive.
    // For 1-indexed line N, the array index is N-1.
    const beforeLines = lines.slice(0, safeStartLine - 1);
    const targetLines = lines.slice(safeStartLine - 1, endLine);
    const afterLines = lines.slice(endLine);

    return (
      <div className="prose dark:prose-invert max-w-none prose-sm sm:prose-base">
        {beforeLines.length > 0 && (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {beforeLines.join("\n")}
          </ReactMarkdown>
        )}
        
        <div 
          ref={highlightRef}
          className="bg-yellow-100 dark:bg-yellow-900/30 border-l-4 border-yellow-500 py-6 my-6 px-6 shadow-sm rounded-r-md scroll-mt-24"
        >
          <div className="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-wider font-bold text-yellow-700 dark:text-yellow-400">
            <span className="bg-yellow-200 dark:bg-yellow-800 px-1.5 py-0.5 rounded">Highlighted Passage</span>
            <span>Lines {safeStartLine} - {endLine}</span>
          </div>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {targetLines.join("\n")}
          </ReactMarkdown>
        </div>

        {afterLines.length > 0 && (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {afterLines.join("\n")}
          </ReactMarkdown>
        )}
      </div>
    );
  }, [data, startLine, endLine]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="text-muted-foreground">Loading document...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-20 px-4">
        <Card className="border-destructive">
          <CardHeader>
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-6 w-6" />
              <CardTitle>Error Loading Document</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{error.message}</p>
            <Button variant="outline" className="mt-6" onClick={() => router.back()}>
              <ChevronLeft className="mr-2 h-4 w-4" />
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="max-w-5xl mx-auto py-4 px-4 space-y-6">
      {/* Header Sticky Bar */}
      <div className="sticky top-0 z-20 bg-background/95 backdrop-blur-sm border-b py-4 px-2 -mx-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <Button variant="ghost" size="icon" onClick={() => router.back()} title="Back to Search">
              <ChevronLeft className="h-5 w-5" />
            </Button>
            <div className="min-w-0">
              <h1 className="text-lg font-bold truncate">{data.work_title}</h1>
              <p className="text-[10px] text-muted-foreground flex items-center gap-1 uppercase tracking-tight">
                <BookOpen className="h-3.5 w-3.5" />
                Document Viewer • Lines {startLine}-{endLine}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              className="gap-2"
              onClick={() => openAddToCollection("excerpt", `/search/result/${workId}/${startLine}/${endLine}`)}
            >
              <FolderPlus className="h-4 w-4" />
              <span className="hidden xs:inline">Add to Collection</span>
            </Button>
            <Button variant="outline" size="sm" onClick={() => router.push("/search")} className="shrink-0 hidden sm:flex">
              New Search
            </Button>
          </div>
        </div>
      </div>

      <div className="bg-card rounded-lg border shadow-sm p-6 sm:p-12 mb-20">
        {renderedContent}
      </div>
      
      {/* Footer helper */}
      <div className="fixed bottom-6 right-6 z-30 flex flex-col gap-2">
        <Button 
          variant="secondary" 
          size="sm" 
          onClick={() => highlightRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })}
          className="shadow-lg border"
        >
          Back to Highlight
        </Button>
      </div>

      <AddToCollectionModal
        isOpen={isOpen}
        onClose={closeAddToCollection}
        itemType={itemType}
        itemLink={itemLink}
      />
    </div>
  );
}

