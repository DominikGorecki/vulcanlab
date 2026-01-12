"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ResearchPlan } from "@/types/research";
import { Loader2, Save, FileEdit, Eye, Copy, Check } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MarkdownRenderer } from "@/components/markdown-renderer";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Step5SynthesisProps {
  sessionId: number;
  researchPlan: ResearchPlan;
  onReportSaved: (report: string) => void;
  onBack: () => void;
}

export function Step5Synthesis({
  sessionId,
  researchPlan,
  onReportSaved,
  onBack,
}: Step5SynthesisProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [reportContent, setReportContent] = useState("");
  const [isCopied, setIsCopied] = useState(false);

  const fetchSectionsAndCopyPrompt = async () => {
    try {
      setIsFetching(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}/prompts/synthesis`);
      if (!response.ok) throw new Error("Failed to fetch synthesis prompt");
      
      const { prompt } = await response.json();

      await navigator.clipboard.writeText(prompt);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);

      toast({
        title: "Prompt Copied",
        description: "Synthesis prompt with all sections copied to clipboard.",
      });
    } catch (error) {
      console.error("Error fetching sections or copy prompt:", error);
      toast({
        title: "Error",
        description: "Failed to fetch synthesis prompt.",
        variant: "destructive",
      });
    } finally {
      setIsFetching(false);
    }
  };

  const handleSaveReport = async () => {
    if (!reportContent.trim()) {
      toast({
        title: "Empty Report",
        description: "Please paste the synthesized report content.",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSaving(true);
      // Extract first few lines as executive summary if not clearly marked
      const lines = reportContent.split("\n").filter(l => l.trim() !== "");
      const executiveSummary = lines.slice(0, 10).join("\n");
      const wordCount = reportContent.trim() ? reportContent.trim().split(/\s+/).length : 0;

      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_content: reportContent,
          executive_summary: executiveSummary,
          metadata: {
            total_words: wordCount,
          },
        }),
      });

      if (!response.ok) throw new Error("Failed to save report");

      toast({
        title: "Report Saved",
        description: "Your final research report has been saved successfully.",
      });

      onReportSaved(reportContent);
    } catch (error) {
      console.error("Error saving report:", error);
      toast({
        title: "Error",
        description: "Failed to save final report.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Step 5: Synthesis</h3>
          <p className="text-sm text-muted-foreground">
            Combine all generated sections into a cohesive final report.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={fetchSectionsAndCopyPrompt}
          disabled={isFetching}
          className="gap-2"
        >
          {isFetching ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : isCopied ? (
            <Check className="h-4 w-4" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
          Fetch Sections & Copy Prompt
        </Button>
      </div>

      <Tabs defaultValue="edit" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="edit" className="flex items-center gap-2">
            <FileEdit className="h-4 w-4" />
            Paste Final Report
          </TabsTrigger>
          <TabsTrigger value="preview" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Markdown Preview
          </TabsTrigger>
        </TabsList>
        <TabsContent value="edit" className="mt-4">
          <div className="space-y-4">
            <Textarea
              placeholder="Paste the final synthesized markdown report here..."
              className="min-h-[500px] font-mono text-sm resize-none"
              value={reportContent}
              onChange={(e) => setReportContent(e.target.value)}
            />
            <p className="text-xs text-muted-foreground italic">
              Tip: The report should include an executive summary, introduction, integrated findings, insights, limitations, conclusions, and references.
            </p>
          </div>
        </TabsContent>
        <TabsContent value="preview" className="mt-4">
          <Card className="min-h-[500px] overflow-hidden">
            <CardContent className="p-6">
              {reportContent ? (
                <MarkdownRenderer content={reportContent} />
              ) : (
                <div className="flex flex-col items-center justify-center h-96 text-muted-foreground">
                  <p>No content to preview.</p>
                  <p className="text-sm">Go to the "Edit" tab to paste your report.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex justify-between items-center pt-6 border-t">
        <Button variant="ghost" onClick={onBack}>
          Back to Sections
        </Button>
        <Button
          onClick={handleSaveReport}
          disabled={isSaving || !reportContent.trim()}
          className="min-w-[150px]"
        >
          {isSaving ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Final Report
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
