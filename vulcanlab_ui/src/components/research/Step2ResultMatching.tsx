"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { toast } from "@/hooks/use-toast";
import { ResearchPlan, MatchResult, MatchResultsResponse } from "@/types/research";
import { Loader2, Search, CheckCircle2, ChevronRight, ChevronLeft, Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Step2ResultMatchingProps {
  sessionId: number;
  researchPlan: ResearchPlan;
  onComplete: () => void;
}

export function Step2ResultMatching({
  sessionId,
  researchPlan,
  onComplete,
}: Step2ResultMatchingProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isSearching, setIsSearching] = useState(false);
  const [matchingResults, setMatchingResults] = useState<Record<string, MatchResultsResponse>>({});
  const [selectedStrategies, setSelectedStrategies] = useState<Record<string, string>>({});
  const [isConfirming, setIsConfirming] = useState(false);

  const subQuestions = researchPlan.sub_questions;
  const currentQuestion = subQuestions[currentQuestionIndex];

  const handleCheckMatches = async () => {
    if (!currentQuestion) return;

    try {
      setIsSearching(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}/match-results`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: currentQuestion.id,
          question_text: currentQuestion.question,
        }),
      });

      if (!response.ok) throw new Error("Failed to check for matching results");

      const data: MatchResultsResponse = await response.json();
      setMatchingResults((prev) => ({
        ...prev,
        [currentQuestion.id]: data,
      }));

      // Auto-select recommended strategy if not already selected
      if (!selectedStrategies[currentQuestion.id]) {
        setSelectedStrategies((prev) => ({
          ...prev,
          [currentQuestion.id]: data.recommended_strategy,
        }));
      }

      if (data.matched_results.length === 0) {
        toast({
          title: "No Matches Found",
          description: "No existing results closely match this sub-question.",
        });
      } else {
        toast({
          title: "Matches Found",
          description: `Found ${data.matched_results.length} matching result(s).`,
        });
      }
    } catch (error) {
      console.error("Error matching results:", error);
      toast({
        title: "Error",
        description: "Failed to check for matching results.",
        variant: "destructive",
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleStrategyChange = (value: string) => {
    setSelectedStrategies((prev) => ({
      ...prev,
      [currentQuestion.id]: value,
    }));
  };

  const handleConfirmSelection = async () => {
    const strategy = selectedStrategies[currentQuestion.id] || "Generate New";
    const matches = matchingResults[currentQuestion.id]?.matched_results || [];

    try {
      setIsConfirming(true);
      
      // Update session state with the choice for this question
      // In a real app, you'd likely want to save this to the DB
      // The spec says: save matching info to session via PUT /api/v1/research-sessions/{sessionId}
      
      // Fetch current session to get existing state_data
      const sessionRes = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}`);
      const sessionData = await sessionRes.json();
      
      const newStateData = {
        ...(sessionData.state_data || {}),
        reuse_info: {
          ...(sessionData.state_data?.reuse_info || {}),
          [currentQuestion.id]: {
            strategy,
            matched_results: matches,
          }
        }
      };

      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          state_data: newStateData,
        }),
      });

      if (!response.ok) throw new Error("Failed to save selection");

      if (currentQuestionIndex < subQuestions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      } else {
        onComplete();
      }
    } catch (error) {
      console.error("Error confirming selection:", error);
      toast({
        title: "Error",
        description: "Failed to save your selection.",
        variant: "destructive",
      });
    } finally {
      setIsConfirming(false);
    }
  };

  const currentResults = matchingResults[currentQuestion.id];
  const currentStrategy = selectedStrategies[currentQuestion.id];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Step 2: Result Matching</h3>
          <p className="text-sm text-muted-foreground">
            Question {currentQuestionIndex + 1} of {subQuestions.length}
          </p>
        </div>
        <Badge variant="outline" className="px-3 py-1">
          {Math.round(((currentQuestionIndex + 1) / subQuestions.length) * 100)}% Done
        </Badge>
      </div>

      <Card className="border-primary/20 bg-primary/5">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium">Sub-Question</CardTitle>
          <CardDescription className="text-foreground font-semibold">
            {currentQuestion.question}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-start gap-2 text-sm text-muted-foreground">
            <Info className="h-4 w-4 mt-0.5 shrink-0" />
            <p><span className="font-semibold text-foreground">Rationale:</span> {currentQuestion.rationale}</p>
          </div>
        </CardContent>
      </Card>

      {!currentResults ? (
        <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed rounded-xl space-y-4">
          <Search className="h-10 w-10 text-muted-foreground/40" />
          <div className="text-center">
            <p className="font-medium">Check for existing work</p>
            <p className="text-sm text-muted-foreground">
              We'll look for previously generated results that might answer this question.
            </p>
          </div>
          <Button onClick={handleCheckMatches} disabled={isSearching}>
            {isSearching ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Search className="h-4 w-4 mr-2" />}
            Check for Matching Results
          </Button>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Matching Results Found ({currentResults.matched_results.length})</h4>
            {currentResults.matched_results.length > 0 ? (
              <div className="space-y-3">
                {currentResults.matched_results.map((result) => (
                  <Card key={result.result_id} className="bg-muted/30">
                    <CardContent className="p-4 space-y-2">
                      <div className="flex justify-between items-start">
                        <div className="text-sm font-medium">Result #{result.result_id}</div>
                        <Badge variant={result.similarity_score > 0.8 ? "default" : "secondary"}>
                          {Math.round(result.similarity_score * 100)}% Match
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-3 italic">
                        "{result.content_preview || "No preview available."}"
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground italic">No close matches found in this collection's history.</p>
            )}
          </div>

          <div className="space-y-4 pt-4 border-t">
            <h4 className="text-sm font-medium">Select Strategy</h4>
            <RadioGroup 
              value={currentStrategy} 
              onValueChange={handleStrategyChange}
              className="grid grid-cols-1 md:grid-cols-2 gap-4"
            >
              {[
                { id: "Exact Reuse", label: "Exact Reuse", desc: "Use existing result as-is" },
                { id: "Partial Reuse", label: "Partial Reuse", desc: "Update existing result with new data" },
                { id: "Ensemble", label: "Ensemble", desc: "Combine multiple results" },
                { id: "Generate New", label: "Generate New", desc: "Start from scratch" },
              ].map((s) => (
                <div key={s.id} className="flex items-start space-x-3 p-3 rounded-lg border hover:bg-accent transition-colors">
                  <RadioGroupItem value={s.id} id={s.id} className="mt-1" />
                  <Label htmlFor={s.id} className="flex-1 cursor-pointer">
                    <div className="font-semibold">{s.label}</div>
                    <div className="text-xs text-muted-foreground">{s.desc}</div>
                    {currentResults.recommended_strategy === s.id && (
                      <Badge variant="secondary" className="mt-2 text-[10px] bg-primary/10 text-primary border-primary/20">Recommended</Badge>
                    )}
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>

          <div className="flex justify-between pt-6">
            <Button 
              variant="outline" 
              onClick={() => setCurrentQuestionIndex(Math.max(0, currentQuestionIndex - 1))}
              disabled={currentQuestionIndex === 0 || isConfirming}
            >
              <ChevronLeft className="h-4 w-4 mr-2" />
              Previous Question
            </Button>
            <Button onClick={handleConfirmSelection} disabled={isConfirming || !currentStrategy}>
              {isConfirming ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <CheckCircle2 className="h-4 w-4 mr-2" />}
              Confirm & {currentQuestionIndex < subQuestions.length - 1 ? "Next Question" : "Continue to Step 3"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
