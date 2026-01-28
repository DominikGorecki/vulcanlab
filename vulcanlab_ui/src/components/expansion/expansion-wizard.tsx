"use client";

import { useState, useEffect, useCallback } from "react";
import { 
  ChevronLeft, 
  ChevronRight, 
  CheckCircle, 
  Database, 
  Zap, 
  Play, 
  Save,
  Combine,
  RefreshCcw,
  Loader2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { SectionDetail as SectionDetailView } from "./section-detail";
import { ExpansionDetail, SectionDetail } from "./types";
import { toast } from "@/hooks/use-toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ExpansionWizardProps {
  expansion: ExpansionDetail;
  onRefresh: () => void;
  onCombine: () => Promise<void>;
  onRetrySection: (sectionId: number) => Promise<void>;
  onSaveManual: (sectionId: number, responseText: string) => Promise<void>;
}

export function ExpansionWizard({
  expansion,
  onRefresh,
  onCombine,
  onRetrySection,
  onSaveManual,
}: ExpansionWizardProps) {
  const STORAGE_KEY = `expansion-wizard-${expansion.id}`;

  // Initialize current section index from localStorage
  const [currentSectionIndex, setCurrentSectionIndex] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        try {
          const data = JSON.parse(saved);
          // Ensure saved index is still valid
          const savedIndex = data.currentSectionIndex || 0;
          return Math.min(savedIndex, expansion.sections.length - 1);
        } catch {
          return 0;
        }
      }
    }
    return 0;
  });

  const [sectionDetail, setSectionDetail] = useState<SectionDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Persist current section index to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      currentSectionIndex,
      timestamp: Date.now()
    }));
  }, [currentSectionIndex, STORAGE_KEY]);

  const fetchSectionDetail = useCallback(async (sectionId: number) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/expansions/${expansion.id}/sections/${sectionId}`);
      if (!response.ok) throw new Error("Failed to load section details");
      const data = await response.json();
      setSectionDetail(data);
    } catch (err) {
      toast({
        title: "Error loading section",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [expansion.id]);

  useEffect(() => {
    if (expansion.sections.length > 0) {
      fetchSectionDetail(expansion.sections[currentSectionIndex].id);
    }
  }, [currentSectionIndex, expansion.sections, fetchSectionDetail]);

  const handleNext = () => {
    if (currentSectionIndex < expansion.sections.length - 1) {
      setSectionDetail(null); // Clear current section to force fresh load
      setCurrentSectionIndex(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentSectionIndex > 0) {
      setSectionDetail(null); // Clear current section to force fresh load
      setCurrentSectionIndex(prev => prev - 1);
    }
  };

  const currentSectionSummary = expansion.sections[currentSectionIndex];
  const progress = ((currentSectionIndex + 1) / expansion.sections.length) * 100;
  const allCompleted = expansion.sections.every(s => s.status === "completed");

  return (
    <div className="space-y-6">
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="pt-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Expansion Wizard</h2>
            <div className="text-sm font-medium text-muted-foreground">
              Section {currentSectionIndex + 1} of {expansion.sections.length}
            </div>
          </div>
          <Progress value={progress} className="h-2" />
          <div className="flex justify-between mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={handleBack}
              disabled={currentSectionIndex === 0 || isLoading}
              className="gap-2"
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            
            <div className="flex gap-2">
              {allCompleted && (
                <Button
                  size="sm"
                  onClick={onCombine}
                  className="gap-2 bg-green-600 hover:bg-green-700 text-white"
                >
                  <Combine className="h-4 w-4" />
                  Combine All
                </Button>
              )}
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleNext}
                disabled={currentSectionIndex === expansion.sections.length - 1 || isLoading}
                className="gap-2"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {isLoading && !sectionDetail ? (
        <div className="py-20 flex flex-col items-center justify-center gap-4">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <p className="text-muted-foreground text-lg">Loading section details...</p>
        </div>
      ) : sectionDetail ? (
        <div key={sectionDetail.id} className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          <SectionDetailView
            section={sectionDetail}
            mode={expansion.mode}
            expansionId={expansion.id}
            onRetry={async (id) => {
              await onRetrySection(id);
              fetchSectionDetail(id);
            }}
            onSaveManual={async (id, text) => {
              await onSaveManual(id, text);
              fetchSectionDetail(id);
            }}
            onRefresh={async () => {
              await fetchSectionDetail(sectionDetail.id);
              onRefresh();
            }}
            isLoading={isLoading}
          />
        </div>
      ) : (
        <div className="py-20 text-center border-2 border-dashed rounded-lg">
          <p className="text-muted-foreground">No sections found. Run breakdown first.</p>
        </div>
      )}
    </div>
  );
}
