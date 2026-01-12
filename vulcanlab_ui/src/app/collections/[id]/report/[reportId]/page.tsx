"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useMemo, useState } from "react";
import { StickyDetailHeader, PageErrorState, PageLoadingState } from "@/components";
import { MarkdownEditor } from "@/components/markdown-editor";
import { usePageData } from "@/hooks/use-page-data";
import { Button } from "@/components/ui/button";
import { Download, FileText, Calendar, Hash, Quote, FileSearch } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ResearchReportResponse {
  id: number;
  session_id: number;
  collection_id: number;
  report_content: string;
  synthesis_report?: string | null;
  executive_summary: string | null;
  quality_evaluation: any | null;
  report_metadata: {
    total_words?: number;
    word_count?: number;
    citation_count?: number;
  } | null;
  collection?: {
    id: number;
    name: string;
  } | null;
}

export default function ResearchReportPage() {
  const params = useParams();
  const router = useRouter();
  const collectionId = params.id as string;
  const sessionId = params.reportId as string;

  const fetchData = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}/report`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Research report not found.");
      }
      throw new Error(`Failed to load report: ${response.statusText}`);
    }

    return response.json();
  }, [sessionId]);

  const { data, loading, error, refetch } = usePageData<ResearchReportResponse>(fetchData);

  const reportTitle = useMemo(() => {
    if (!data?.report_content) return "Research Report";
    
    // Try to extract the first # Header from the markdown
    const titleMatch = data.report_content.match(/^#\s+(.+)$/m);
    if (titleMatch && titleMatch[1]) {
      return titleMatch[1].trim();
    }
    
    return "Research Report";
  }, [data?.report_content]);

  const handleExportMD = () => {
    const content = activeTab === "final" ? data?.report_content : data?.synthesis_report;
    if (!content) return;
    
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    
    // Sanitize function for filenames
    const sanitize = (text: string) => text.toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');

    const safeCollectionTitle = sanitize(data?.collection?.name || "collection");
    const safeReportTitle = sanitize(reportTitle || "report");
    const suffix = activeTab === "final" ? "main_report" : "synthesis_report";
    
    const filename = `${safeCollectionTitle}_${safeReportTitle}__${suffix}.md`;
    
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const [activeTab, setActiveTab] = useState("final");

  if (error) {
    return <PageErrorState error={error} onRetry={refetch} />;
  }

  if (loading && !data) {
    return <PageLoadingState title="Loading research report..." />;
  }

  const wordCount = data?.report_metadata?.word_count || data?.report_metadata?.total_words || 0;
  const citationCount = data?.report_metadata?.citation_count || 0;

  return (
    <div className="min-h-screen flex flex-col pt-0">
      <StickyDetailHeader
        title="Research Report"
        subtitle={reportTitle}
        backUrl={`/collections/${collectionId}`}
        backLabel="Back to Collection"
        actions={
          <div className="flex items-center gap-2">
            <div className="hidden md:flex items-center gap-3 mr-4">
              <div className="flex items-center gap-1 text-xs text-muted-foreground" title="Word count">
                <Hash className="h-3 w-3" />
                {wordCount} {wordCount === 1 ? 'word' : 'words'}
              </div>
              <div className="flex items-center gap-1 text-xs text-muted-foreground" title="Citation count">
                <Quote className="h-3 w-3" />
                {citationCount} {citationCount === 1 ? 'citation' : 'citations'}
              </div>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              className="gap-2"
              onClick={handleExportMD}
            >
              <Download className="h-4 w-4" />
              Export MD
            </Button>
          </div>
        }
      />

      <div className="p-6 max-w-5xl mx-auto w-full">
        <Tabs defaultValue="final" value={activeTab} onValueChange={setActiveTab} className="w-full">
          <div className="flex items-center justify-between mb-4">
            <TabsList className="bg-muted/50 p-1">
              <TabsTrigger value="final" className="gap-2 px-4 py-2">
                <FileText className="h-4 w-4" />
                Final Report
              </TabsTrigger>
              <TabsTrigger value="synthesis" className="gap-2 px-4 py-2">
                <FileSearch className="h-4 w-4" />
                Synthesis Report
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="bg-card border rounded-xl shadow-sm overflow-hidden">
            <TabsContent value="final" className="m-0 border-none">
              <div className="p-0">
                <MarkdownEditor
                  content={data?.report_content || ""}
                  onChange={() => {}} // Read-only
                  viewMode="preview"
                  readOnly={true}
                  scrollMode="page"
                />
              </div>
            </TabsContent>

            <TabsContent value="synthesis" className="m-0 border-none">
              <div className="p-0">
                <MarkdownEditor
                  content={data?.synthesis_report || ""}
                  onChange={() => {}} // Read-only
                  viewMode="preview"
                  readOnly={true}
                  scrollMode="page"
                />
              </div>
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}
