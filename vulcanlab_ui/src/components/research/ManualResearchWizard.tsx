"use client";

import { useState, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Step1Planning } from "./Step1Planning";
import { Step2ResultMatching } from "./Step2ResultMatching";
import { Step3ContextAssembly } from "./Step3ContextAssembly";
import { Step4SectionGeneration } from "./Step4SectionGeneration";
import { Step5Synthesis } from "./Step5Synthesis";
import { Step6QualityEvaluation } from "./Step6QualityEvaluation";
import { CompletionStep } from "./CompletionStep";
import { ResearchPlan, ResearchSession } from "@/types/research";
import { toast } from "@/hooks/use-toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ManualResearchWizardProps {
  collectionId: number;
  sessionId: number;
  onComplete: () => void;
}

const STEPS = [
  "Planning",
  "Result Matching",
  "Context Assembly",
  "Section Generation",
  "Synthesis",
  "Quality Evaluation",
];

export function ManualResearchWizard({
  collectionId,
  sessionId,
  onComplete,
}: ManualResearchWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [researchPlan, setResearchPlan] = useState<ResearchPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [contextData, setContextData] = useState<Record<string, any>>({});
  const [sections, setSections] = useState<Record<string, string>>({});
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [finalReport, setFinalReport] = useState<string>("");
  const [qualityEvaluation, setQualityEvaluation] = useState<any>(null);
  const [isCompleted, setIsCompleted] = useState(false);

  const fetchSession = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}`);
      if (!response.ok) throw new Error("Failed to fetch session");
      const data: ResearchSession = await response.json();
      
      if (data.research_plan) {
        setResearchPlan(data.research_plan);
      }

      // Restore step based on current_phase
      if (data.current_phase) {
        switch (data.current_phase) {
          case 'planning':
            setCurrentStep(1);
            break;
          case 'research':
            setCurrentStep(2);
            break;
          case 'context_assembly':
            setCurrentStep(3);
            break;
          case 'synthesis':
            setCurrentStep(5);
            break;
          case 'evaluation':
            setCurrentStep(6);
            break;
          case 'completed':
            setIsCompleted(true);
            break;
        }
      }

      // Fetch saved sections if we're past the planning stage
      if (data.current_phase && !['planning', 'research'].includes(data.current_phase)) {
        const sectionsResponse = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}/sections`);
        if (sectionsResponse.ok) {
          const sectionsData = await sectionsResponse.json();
          // Assuming sectionsData is an array of sections, we need to map them to the sections record
          // but first let's see what the sections data looks like.
          // Based on usage in Step4: Record<string, string>
          const sectionsRecord: Record<string, string> = {};
          const contextRecord: Record<string, any> = {};
          if (sectionsData && Array.isArray(sectionsData.sections)) {
            sectionsData.sections.forEach((s: any) => {
              sectionsRecord[s.question_id] = s.section_content;
              if (s.context_data) {
                contextRecord[s.question_id] = s.context_data;
              }
            });
          }
          setSections(sectionsRecord);
          setContextData(contextRecord);
          
          // Determine currentSectionIndex based on how many sections we have
          if (data.research_plan && data.current_phase === 'context_assembly') {
            const completedCount = Object.keys(sectionsRecord).length;
            if (completedCount < data.research_plan.sub_questions.length) {
              setCurrentSectionIndex(completedCount);
            } else {
              // If all sections are done but phase is still context_assembly, move to synthesis
              setCurrentStep(5);
            }
          }
        }
      }

    } catch (error) {
      console.error("Error fetching session:", error);
      toast({
        title: "Error",
        description: "Failed to load research session data.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  const updateSessionPhase = useCallback(async (phase: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_phase: phase }),
      });
      if (!response.ok) throw new Error("Failed to update session phase");
    } catch (error) {
      console.error("Error updating session phase:", error);
    }
  }, [sessionId]);

  const handlePlanSaved = (plan: ResearchPlan) => {
    setResearchPlan(plan);
    setCurrentStep(2);
    // Phase is already updated to 'research' by Step1Planning
  };

  const handleMatchingComplete = () => {
    setCurrentStep(3);
    updateSessionPhase('context_assembly');
  };

  const handleContextComplete = () => {
    setCurrentStep(4);
    // Stay in context_assembly phase while generating sections
  };

  const handleSectionSaved = () => {
    if (researchPlan && currentSectionIndex < researchPlan.sub_questions.length - 1) {
      setCurrentSectionIndex((prev) => prev + 1);
      setCurrentStep(3); // Loop back to context assembly for next question
    } else {
      setCurrentStep(5); // All sections done, move to synthesis
      updateSessionPhase('synthesis');
    }
  };

  const handleReportSaved = (report: string) => {
    setFinalReport(report);
    setCurrentStep(6);
    updateSessionPhase('evaluation');
  };

  const handleEvaluationComplete = (evaluation: any) => {
    setQualityEvaluation(evaluation);
    setIsCompleted(true);
    updateSessionPhase('completed');
  };

  const handleSkipEvaluation = () => {
    setIsCompleted(true);
    updateSessionPhase('completed');
  };

  const handleRestart = () => {
    setCurrentStep(1);
    setCurrentSectionIndex(0);
    setFinalReport("");
    setQualityEvaluation(null);
    setIsCompleted(false);
    fetchSession();
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <p className="text-muted-foreground animate-pulse">Loading wizard...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header / Stepper */}
      <div className="p-6 border-b bg-muted/30">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Manual Research Wizard</h2>
          <span className="text-sm font-medium text-muted-foreground">
            {isCompleted 
              ? "Research Completed" 
              : `Step ${currentStep} of ${STEPS.length}: ${STEPS[currentStep - 1]}`}
          </span>
        </div>
        <Progress value={isCompleted ? 100 : (currentStep / STEPS.length) * 100} className="h-2" />
        <div className="flex justify-between mt-2">
          {STEPS.map((step, idx) => (
            <div
              key={step}
              className={`text-[10px] uppercase tracking-wider font-semibold ${
                isCompleted || idx + 1 < currentStep
                  ? "text-muted-foreground"
                  : idx + 1 === currentStep
                  ? "text-primary"
                  : "text-muted-foreground/40"
              }`}
            >
              {step}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {isCompleted ? (
          <CompletionStep
            collectionId={collectionId}
            sessionId={sessionId}
            reportContent={finalReport}
            onClose={onComplete}
            onRestart={handleRestart}
          />
        ) : (
          <>
            {currentStep === 1 && (
              <Step1Planning
                collectionId={collectionId}
                sessionId={sessionId}
                onPlanSaved={handlePlanSaved}
              />
            )}
            {currentStep === 2 && researchPlan && (
              <Step2ResultMatching
                sessionId={sessionId}
                researchPlan={researchPlan}
                onComplete={handleMatchingComplete}
              />
            )}
            {currentStep === 3 && researchPlan && (
              <Step3ContextAssembly
                sessionId={sessionId}
                researchPlan={researchPlan}
                currentSectionIndex={currentSectionIndex}
                contextData={contextData}
                setContextData={setContextData}
                onNext={handleContextComplete}
                onBack={() => {
                  if (currentSectionIndex > 0) {
                    setCurrentSectionIndex(currentSectionIndex - 1);
                    setCurrentStep(4);
                  } else {
                    setCurrentStep(2);
                  }
                }}
              />
            )}
            {currentStep === 4 && researchPlan && (
              <Step4SectionGeneration
                sessionId={sessionId}
                researchPlan={researchPlan}
                currentSectionIndex={currentSectionIndex}
                contextData={contextData}
                sections={sections}
                setSections={setSections}
                onSaveAndNext={handleSectionSaved}
                onBack={() => setCurrentStep(3)}
              />
            )}
            {currentStep === 5 && researchPlan && (
              <Step5Synthesis
                sessionId={sessionId}
                researchPlan={researchPlan}
                onReportSaved={handleReportSaved}
                onBack={() => {
                  setCurrentSectionIndex(researchPlan.sub_questions.length - 1);
                  setCurrentStep(4);
                }}
              />
            )}
            {currentStep === 6 && (
              <Step6QualityEvaluation
                sessionId={sessionId}
                reportContent={finalReport}
                onComplete={handleEvaluationComplete}
                onSkip={handleSkipEvaluation}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
