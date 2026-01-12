"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ResearchPlan } from "@/types/research";
import { Loader2, Save, FileEdit, Eye, ArrowRight, CheckCircle2 } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MarkdownRenderer } from "@/components/markdown-renderer";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Step4SectionGenerationProps {
  sessionId: number;
  researchPlan: ResearchPlan;
  currentSectionIndex: number;
  contextData: Record<string, any>;
  sections: Record<string, string>;
  setSections: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  onSaveAndNext: () => void;
  onBack: () => void;
}

export function Step4SectionGeneration({
  sessionId,
  researchPlan,
  currentSectionIndex,
  contextData,
  sections,
  setSections,
  onSaveAndNext,
  onBack,
}: Step4SectionGenerationProps) {
  const [isSaving, setIsSaving] = useState(false);
  const subQuestion = researchPlan.sub_questions[currentSectionIndex];
  const [content, setContent] = useState(sections[subQuestion.id] || "");

  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;
  // Match any [brackets] which is the broad pattern used by the backend synthesizer
  const citationCount = (content.match(/\[([^\]]+)\]/g) || []).length;

  const handleSaveSection = async () => {
    if (!content.trim()) {
      toast({
        title: "Empty Content",
        description: "Please enter or paste the generated section content.",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSaving(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}/sections`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: subQuestion.id,
          question_text: subQuestion.question,
          section_content: content,
          context_data: contextData[subQuestion.id],
          metadata: {
            word_count: wordCount,
            citation_count: citationCount,
          },
        }),
      });

      if (!response.ok) throw new Error("Failed to save section");

      setSections((prev) => ({
        ...prev,
        [subQuestion.id]: content,
      }));

      toast({
        title: "Section Saved",
        description: `Successfully saved section for "${subQuestion.question.slice(0, 30)}..."`,
      });

      onSaveAndNext();
    } catch (error) {
      console.error("Error saving section:", error);
      toast({
        title: "Error",
        description: "Failed to save research section.",
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
          <h3 className="text-lg font-semibold">Step 4: Section Generation</h3>
          <p className="text-sm text-muted-foreground">
            Generate and review section for: {subQuestion.question}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            Section {currentSectionIndex + 1} of {researchPlan.sub_questions.length}
          </Badge>
          <Badge variant="secondary" className="bg-blue-500/10 text-blue-500 border-blue-500/20">
            {wordCount} words
          </Badge>
          <Badge variant="secondary" className="bg-purple-500/10 text-purple-500 border-purple-500/20">
            {citationCount} citations
          </Badge>
        </div>
      </div>

      <Card className="border-primary/10">
        <CardHeader className="pb-3 py-4 bg-muted/30">
          <CardTitle className="text-sm font-medium">Sub-Question</CardTitle>
          <p className="text-sm font-semibold">{subQuestion.question}</p>
        </CardHeader>
      </Card>

      <Tabs defaultValue="edit" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="edit" className="flex items-center gap-2">
            <FileEdit className="h-4 w-4" />
            Paste Content
          </TabsTrigger>
          <TabsTrigger value="preview" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Markdown Preview
          </TabsTrigger>
        </TabsList>
        <TabsContent value="edit" className="mt-4">
          <div className="space-y-4">
            <Textarea
              placeholder="Paste the LLM-generated markdown content here..."
              className="min-h-[400px] font-mono text-sm resize-none"
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
            <p className="text-xs text-muted-foreground italic">
              Tip: Use the context prompt from Step 3 in your favorite LLM, then paste the response here.
            </p>
          </div>
        </TabsContent>
        <TabsContent value="preview" className="mt-4">
          <Card className="min-h-[400px] overflow-hidden">
            <CardContent className="p-6">
              {content ? (
                <MarkdownRenderer content={content} />
              ) : (
                <div className="flex flex-col items-center justify-center h-80 text-muted-foreground">
                  <p>No content to preview.</p>
                  <p className="text-sm">Go to the "Edit" tab to paste your section.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex justify-between items-center pt-6 border-t">
        <Button variant="ghost" onClick={onBack}>
          Back to Context
        </Button>
        <Button 
          onClick={handleSaveSection} 
          disabled={isSaving || !content.trim()}
          className="min-w-[150px]"
        >
          {isSaving ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : currentSectionIndex < researchPlan.sub_questions.length - 1 ? (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save & Next Question
              <ArrowRight className="h-4 w-4 ml-2" />
            </>
          ) : (
            <>
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Save & Finish Sections
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
