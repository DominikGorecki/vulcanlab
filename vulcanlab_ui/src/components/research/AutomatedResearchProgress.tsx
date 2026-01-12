"use client";

import { useEffect } from "react";
import { usePollSessionStatus } from "@/lib/polling";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Loader2, AlertCircle, PlayCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface AutomatedResearchProgressProps {
  sessionId: number;
  onComplete?: () => void;
}

export function AutomatedResearchProgress({ sessionId, onComplete }: AutomatedResearchProgressProps) {
  const { toast } = useToast();
  const {
    status,
    currentPhase,
    sectionsCompleted,
    totalSections,
    error
  } = usePollSessionStatus(sessionId);

  useEffect(() => {
    if (status === 'completed') {
      toast({
        title: "Deep research completed!",
        description: "Your automated research report is ready to view.",
      });
      if (onComplete) onComplete();
    } else if (status === 'failed') {
      toast({
        title: "Research failed",
        description: error || "An unexpected error occurred during research.",
        variant: "destructive",
      });
    }
  }, [status, error, toast, onComplete]);

  if (!status) return null;

  const getPhaseIcon = () => {
    if (status === 'completed') return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    if (status === 'failed') return <AlertCircle className="h-4 w-4 text-destructive" />;
    
    return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
  };

  const progressPercent = totalSections > 0 
    ? Math.round((sectionsCompleted / totalSections) * 100) 
    : status === 'completed' ? 100 : 0;

  return (
    <Card className="w-full mb-4">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <PlayCircle className="h-4 w-4 text-primary" />
              Automated Research Session #{sessionId}
            </CardTitle>
            <CardDescription className="text-xs">
              LangGraph-powered automated research
            </CardDescription>
          </div>
          <Badge variant={status === 'completed' ? 'outline' : status === 'failed' ? 'destructive' : 'secondary'}>
            {status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex justify-between items-center text-sm">
            <span className="flex items-center gap-2">
              {getPhaseIcon()}
              <span className="font-medium capitalize">{currentPhase || status}</span>
            </span>
            {totalSections > 0 && (
              <span className="text-muted-foreground text-xs">
                {sectionsCompleted} / {totalSections} sections
              </span>
            )}
          </div>
          
          <Progress value={progressPercent} className="h-2" />
          
          {status === 'failed' && error && (
            <div className="mt-2 p-2 rounded bg-destructive/10 text-destructive text-xs flex items-start gap-2">
              <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
