"use client";

import { useState, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/hooks/use-toast";
import { copyToClipboard } from "@/lib/clipboard";
import { extractJson } from "@/lib/utils";
import { ResearchPlan } from "@/types/research";
import { Loader2, Clipboard, Save, CheckCircle2 } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Step1PlanningProps {
  collectionId: number;
  sessionId: number;
  onPlanSaved: (plan: ResearchPlan) => void;
}

interface CollectionAnalysis {
  name: string;
  description: string;
  item_count: number;
  items_by_type: {
    excerpt: number;
    research_result: number;
    research_query: number;
  };
  items: any[];
}

export function Step1Planning({
  collectionId,
  sessionId,
  onPlanSaved,
}: Step1PlanningProps) {
  const [analysis, setAnalysis] = useState<CollectionAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [planJson, setPlanJson] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const fetchAnalysis = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/collections/${collectionId}/analyze`);
      if (!response.ok) throw new Error("Failed to fetch collection analysis");
      const data = await response.json();
      setAnalysis(data);
    } catch (error) {
      console.error("Error fetching analysis:", error);
      toast({
        title: "Error",
        description: "Failed to load collection analysis.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [collectionId]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  const handleCopyPrompt = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}/prompts/research_planning`);
      if (!response.ok) throw new Error("Failed to fetch formatted prompt");
      
      const { prompt } = await response.json();
      await copyToClipboard(prompt);
      
      toast({
        title: "Copied!",
        description: "Research planning prompt copied to clipboard.",
      });
    } catch (error) {
      console.error("Error copying prompt:", error);
      toast({
        title: "Error",
        description: "Failed to fetch or copy prompt.",
        variant: "destructive",
      });
    }
  };

  const handleSavePlan = async () => {
    if (!planJson.trim()) {
      toast({
        title: "Empty Plan",
        description: "Please paste the research plan JSON from the LLM.",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSaving(true);
      const cleanJson = extractJson(planJson);
      let parsedPlan: ResearchPlan;
      
      try {
        parsedPlan = JSON.parse(cleanJson);
      } catch (parseError) {
        console.error("JSON Parse Error details:", parseError);
        console.log("Attempted to parse:", cleanJson);
        throw new Error(`JSON parsing failed: ${parseError instanceof Error ? parseError.message : String(parseError)}. Please check the format.`);
      }

      // Basic validation
      const missingFields = [];
      if (!parsedPlan.research_goal) missingFields.push("research_goal");
      if (!Array.isArray(parsedPlan.sub_questions) || parsedPlan.sub_questions.length === 0) missingFields.push("sub_questions");
      
      if (missingFields.length > 0) {
        console.log("Validation failed for object:", parsedPlan);
        throw new Error(`Invalid research plan structure. Missing or empty: ${missingFields.join(", ")}.`);
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          research_plan: parsedPlan,
          current_phase: "research", // Move to research phase
        }),
      });

      if (!response.ok) throw new Error("Failed to save research plan");

      toast({
        title: "Plan Saved",
        description: "Research plan has been validated and saved.",
      });
      onPlanSaved(parsedPlan);
    } catch (error) {
      console.error("Error saving plan:", error);
      toast({
        title: "Invalid JSON",
        description: error instanceof Error ? error.message : "Please ensure you pasted a valid JSON research plan.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!analysis) return <div>Failed to load collection data.</div>;

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">Step 1: Research Planning</h3>
        <p className="text-sm text-muted-foreground">
          Analyze your collection and define the research goals and sub-questions.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{analysis.name}</CardTitle>
          <CardDescription>{analysis.description || "No description provided"}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 bg-muted rounded-lg text-center">
              <div className="text-2xl font-bold">{analysis.item_count}</div>
              <div className="text-[10px] uppercase text-muted-foreground">Total Items</div>
            </div>
            <div className="p-3 bg-muted rounded-lg text-center">
              <div className="text-2xl font-bold">{analysis.items_by_type.excerpt}</div>
              <div className="text-[10px] uppercase text-muted-foreground">Excerpts</div>
            </div>
            <div className="p-3 bg-muted rounded-lg text-center">
              <div className="text-2xl font-bold">{analysis.items_by_type.research_result}</div>
              <div className="text-[10px] uppercase text-muted-foreground">Results</div>
            </div>
            <div className="p-3 bg-muted rounded-lg text-center">
              <div className="text-2xl font-bold">{analysis.items_by_type.research_query}</div>
              <div className="text-[10px] uppercase text-muted-foreground">Queries</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">1. Generate & Copy Prompt</label>
          <Button variant="outline" size="sm" onClick={handleCopyPrompt}>
            <Clipboard className="h-4 w-4 mr-2" />
            Copy Planning Prompt
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Click the button above to copy a detailed prompt for your LLM. Paste the prompt into your preferred LLM (like Claude or GPT-4) to generate a research plan.
        </p>

        <div className="space-y-2">
          <label className="text-sm font-medium">2. Paste LLM Response (JSON)</label>
          <Textarea
            placeholder='Paste the JSON response here (e.g., { "research_goal": "...", "sub_questions": [...] })'
            className="font-mono text-xs h-48"
            value={planJson}
            onChange={(e) => setPlanJson(e.target.value)}
          />
        </div>

        <Button className="w-full" onClick={handleSavePlan} disabled={isSaving}>
          {isSaving ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Save className="h-4 w-4 mr-2" />
          )}
          Save Research Plan & Continue
        </Button>
      </div>
    </div>
  );
}
