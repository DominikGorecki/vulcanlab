"use client";

import { useState, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ResearchPlan, SubQuestion } from "@/types/research";
import { Loader2, Copy, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { copyToClipboard } from "@/lib/clipboard";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ContextData {
  context: string;
  token_count: number;
  sources: any[];
}

interface Step3ContextAssemblyProps {
  sessionId: number;
  researchPlan: ResearchPlan;
  currentSectionIndex: number;
  contextData: Record<string, ContextData>;
  setContextData: React.Dispatch<React.SetStateAction<Record<string, ContextData>>>;
  onNext: () => void;
  onBack: () => void;
}

export function Step3ContextAssembly({
  sessionId,
  researchPlan,
  currentSectionIndex,
  contextData,
  setContextData,
  onNext,
  onBack,
}: Step3ContextAssemblyProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [reuseInfo, setReuseInfo] = useState<any>(null);
  const [fetchingSession, setFetchingSession] = useState(true);

  const subQuestion = researchPlan.sub_questions[currentSectionIndex];

  const fetchSessionState = useCallback(async () => {
    try {
      setFetchingSession(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}`);
      if (!response.ok) throw new Error("Failed to fetch session state");
      const data = await response.json();
      setReuseInfo(data.state_data?.reuse_info?.[subQuestion.id]);
    } catch (error) {
      console.error("Error fetching session state:", error);
    } finally {
      setFetchingSession(false);
    }
  }, [sessionId, subQuestion.id]);

  useEffect(() => {
    fetchSessionState();
  }, [fetchSessionState]);

  const handleFetchContext = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}/context`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: subQuestion.id,
          relevant_item_ids: subQuestion.relevant_items,
        }),
      });

      if (!response.ok) throw new Error("Failed to fetch context");

      const data = await response.json();
      setContextData((prev) => ({
        ...prev,
        [subQuestion.id]: data,
      }));

      toast({
        title: "Context Fetched",
        description: `Successfully fetched context (${data.token_count.toLocaleString()} tokens).`,
      });
    } catch (error) {
      console.error("Error fetching context:", error);
      toast({
        title: "Error",
        description: "Failed to fetch context for this question.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyPrompt = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}/prompts/section_synthesis?question_id=${subQuestion.id}`);
      if (!response.ok) throw new Error("Failed to fetch formatted prompt");
      
      const { prompt } = await response.json();
      await copyToClipboard(prompt);
      
      toast({
        title: "Prompt Copied",
        description: "Section generation prompt copied to clipboard.",
      });
    } catch (error) {
      console.error("Error copying prompt:", error);
      toast({
        title: "Copy Failed",
        description: "Failed to fetch or copy prompt.",
        variant: "destructive",
      });
    }
  };

  const isReuse = reuseInfo?.strategy === "Exact Reuse" || reuseInfo?.strategy === "Ensemble";
  const currentContext = contextData[subQuestion.id];

  if (fetchingSession) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="mt-4 text-muted-foreground">Loading question context...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Step 3: Context Assembly</h3>
          <p className="text-sm text-muted-foreground">
            Gathering information for: {subQuestion.question}
          </p>
        </div>
        <Badge variant="outline">Question {currentSectionIndex + 1} of {researchPlan.sub_questions.length}</Badge>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Research Sub-Question</CardTitle>
          <CardDescription className="text-foreground font-medium">
            {subQuestion.question}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-muted-foreground bg-muted/50 p-3 rounded-md border italic">
            {subQuestion.rationale}
          </div>
        </CardContent>
      </Card>

      {isReuse ? (
        <Card className="border-green-500/20 bg-green-500/5">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              <CardTitle className="text-sm font-medium">Using Existing Result ({reuseInfo.strategy})</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              This question will be answered using previously generated results.
            </p>
            <div className="space-y-2">
              {reuseInfo.matched_results.map((result: any, idx: number) => (
                <div key={idx} className="p-3 bg-background border rounded-md text-xs">
                  <div className="font-semibold mb-1">Result #{result.result_id}</div>
                  <p className="line-clamp-3 text-muted-foreground italic">"{result.content_preview}"</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {!currentContext ? (
            <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed rounded-xl space-y-4">
              <FileText className="h-10 w-10 text-muted-foreground/40" />
              <div className="text-center">
                <p className="font-medium">Assemble Context</p>
                <p className="text-sm text-muted-foreground">
                  Fetch all relevant data points from the collection for this question.
                </p>
              </div>
              <Button onClick={handleFetchContext} disabled={isLoading}>
                {isLoading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FileText className="h-4 w-4 mr-2" />}
                Fetch Context
              </Button>
            </div>
          ) : (
            <Card>
              <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
                <div className="space-y-1">
                  <CardTitle className="text-sm font-medium">Context Preview</CardTitle>
                  <CardDescription className="text-xs">
                    Token count: <span className="font-bold text-primary">{currentContext.token_count.toLocaleString()}</span>
                  </CardDescription>
                </div>
                <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20">
                  Ready for Generation
                </Badge>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-40 w-full rounded-md border p-4 bg-muted/30">
                  <div className="text-xs font-mono whitespace-pre-wrap text-muted-foreground">
                    {currentContext.context.slice(0, 1000)}
                    {currentContext.context.length > 1000 && "\n\n... [truncated for preview]"}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      <div className="flex justify-between items-center pt-6 border-t">
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
        <div className="flex gap-3">
          <Button 
            variant="outline" 
            onClick={handleCopyPrompt}
            disabled={!isReuse && !currentContext}
          >
            <Copy className="h-4 w-4 mr-2" />
            Copy Prompt
          </Button>
          <Button 
            onClick={onNext}
            disabled={!isReuse && !currentContext}
          >
            Next: Generate Section
          </Button>
        </div>
      </div>
    </div>
  );
}
