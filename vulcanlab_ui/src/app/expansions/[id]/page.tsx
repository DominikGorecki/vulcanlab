"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  Play, 
  RefreshCcw, 
  Combine, 
  ArrowLeft, 
  ExternalLink,
  AlertCircle,
  Clock,
  CheckCircle,
  Loader2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageLoadingState } from "@/components/page-loading-state";
import { PageErrorState } from "@/components/page-error-state";
import { StickyDetailHeader } from "@/components/sticky-detail-header";
import { usePageData } from "@/hooks/use-page-data";
import {
  ExpansionStatusBadge,
  CombinedReport,
  ExpansionDetail,
  ExpansionWizard,
  ManualBreakdownDialog
} from "@/components/expansion";
import { toast } from "@/hooks/use-toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const POLL_INTERVAL = 3000;

export default function ExpansionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const expansionId = params.id as string;
  
  const [isPolling, setIsPolling] = useState(false);
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [showManualBreakdownDialog, setShowManualBreakdownDialog] = useState(false);

  const fetchExpansionData = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/expansions/${expansionId}`);
    if (!response.ok) {
      throw new Error("Failed to load expansion details");
    }
    const data: ExpansionDetail = await response.json();
    return data;
  }, [expansionId]);

  const { data, loading, error, refetch } = usePageData<ExpansionDetail>(fetchExpansionData);

  // Polling logic - only poll for automatic mode
  useEffect(() => {
    const shouldPoll = data && data.mode === "automatic" && [
      "breakdown_pending",
      "sections_in_progress",
      "combining"
    ].includes(data.status);

    setIsPolling(!!shouldPoll);

    if (shouldPoll) {
      pollTimerRef.current = setInterval(() => {
        refetch();
      }, POLL_INTERVAL);
    } else if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }

    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, [data?.status, refetch]);

  const handleRunAll = async () => {
    setIsActionLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/expansions/${expansionId}/run`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to start automatic expansion");
      
      toast({
        title: "Automatic expansion started",
        description: "The system will now process all sections.",
      });
      refetch();
    } catch (err) {
      toast({
        title: "Error starting expansion",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleBreakdown = async (overwrite: boolean = false) => {
    setIsActionLoading(true);
    try {
      const url = new URL(`${API_BASE_URL}/api/v1/expansions/${expansionId}/breakdown`);
      if (overwrite) url.searchParams.append("overwrite", "true");
      
      const response = await fetch(url.toString(), {
        method: "POST",
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to start breakdown");
      }
      
      toast({
        title: overwrite ? "Breakdown regenerated" : "Breakdown started",
        description: "The answer is being broken down into sections.",
      });
      refetch();
    } catch (err) {
      toast({
        title: "Error starting breakdown",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleCombine = async () => {
    setIsActionLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/expansions/${expansionId}/combine`, {
        method: "POST",
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to combine sections");
      }
      
      toast({
        title: "Sections combined",
        description: "The final report has been generated.",
      });
      refetch();
    } catch (err) {
      toast({
        title: "Error combining sections",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleRetrySection = async (sectionId: number) => {
    // Note: In manual mode, retry should open the ManualRAGDialog
    // This handler is only used for automatic mode retries from the list view
    // The wizard view handles manual mode through the dialog
    if (data?.mode === "manual") {
      toast({
        title: "Manual mode",
        description: "Please use the wizard view to manually process sections.",
        variant: "default",
      });
      return;
    }

    try {
      // First expand, then generate (automatic mode only)
      let response = await fetch(`${API_BASE_URL}/api/v1/expansions/${expansionId}/sections/${sectionId}/expand`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to expand section");

      response = await fetch(`${API_BASE_URL}/api/v1/expansions/${expansionId}/sections/${sectionId}/generate`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to generate section response");

      toast({
        title: "Section retried",
        description: "Section processing completed successfully.",
      });
      refetch();
    } catch (err) {
      toast({
        title: "Retry failed",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      });
    }
  };

  const handleSaveManual = async (sectionId: number, responseText: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/expansions/${expansionId}/sections/${sectionId}/manual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ response_text: responseText }),
      });
      
      if (!response.ok) throw new Error("Failed to save manual response");

      toast({
        title: "Response saved",
        description: "Manual response has been saved for this section.",
      });
      refetch();
    } catch (err) {
      toast({
        title: "Save failed",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      });
    }
  };

  if (loading && !data) {
    return <PageLoadingState title="Loading expansion detail..." />;
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <PageErrorState error={error} onRetry={refetch} />
        <div className="flex justify-center mt-4">
          <Button variant="outline" onClick={() => router.push("/expansions")}>
            Back to Expansions
          </Button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const originalAnswerUrl = `/rag/${data.query_id}/results/${data.result_id}`;
  const allSectionsCompleted = data.sections.length > 0 && data.sections.every(s => s.status === "completed");
  const canRunAll = data.status === "breakdown_complete" || data.sections.some(s => s.status === "pending" || s.status === "failed");
  const canCombine = allSectionsCompleted && data.status !== "completed";

  return (
    <div className="flex flex-col min-h-screen pb-12">
      <StickyDetailHeader
        title={`Expansion #${data.id}`}
        subtitle={
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1 capitalize">
              <Clock className="h-3 w-3" />
              Mode: {data.mode}
            </span>
            <span>•</span>
            <div className="flex items-center gap-2">
              Status: <ExpansionStatusBadge status={data.status} />
              {isPolling && <Loader2 className="h-3 w-3 animate-spin" />}
            </div>
          </div>
        }
        backUrl="/expansions"
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(originalAnswerUrl, "_blank")}
              className="gap-2"
            >
              <ExternalLink className="h-4 w-4" />
              Original Answer
            </Button>

            {data.sections.length > 0 && (data.status === "breakdown_complete" || data.status === "failed") && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBreakdown(true)}
                disabled={isActionLoading || isPolling}
                className="gap-2"
              >
                <RefreshCcw className="h-4 w-4" />
                Regenerate Breakdown
              </Button>
            )}

            {canRunAll && data.mode === "automatic" && (
              <Button
                size="sm"
                onClick={handleRunAll}
                disabled={isActionLoading || isPolling}
                className="gap-2"
              >
                <Play className="h-4 w-4" />
                Run All
              </Button>
            )}

            {canCombine && (
              <Button
                size="sm"
                onClick={handleCombine}
                disabled={isActionLoading || isPolling}
                className="gap-2 bg-green-600 hover:bg-green-700 text-white"
              >
                <Combine className="h-4 w-4" />
                Combine Report
              </Button>
            )}

            <Button
              variant="ghost"
              size="sm"
              onClick={refetch}
              disabled={isActionLoading || isPolling}
            >
              <RefreshCcw className={`h-4 w-4 ${isActionLoading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        }
      />

      <div className="container mx-auto px-6 py-8 space-y-8">
        {data.status === "completed" && data.combined_report ? (
          <CombinedReport 
            report={data.combined_report} 
            originalResultLink={originalAnswerUrl}
          />
        ) : (
          <div className="space-y-8">
            {data.status === "created" && (
              <div className="p-12 text-center border-2 border-dashed rounded-lg bg-muted/20 space-y-4">
                <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto" />
                <div className="space-y-2">
                  <h3 className="text-xl font-bold">Initial Breakdown Required</h3>
                  <p className="text-muted-foreground max-w-md mx-auto">
                    This expansion has been created but not yet broken down into sections. 
                    {data.mode === "automatic" 
                      ? "Click 'Run All' to start the automatic pipeline." 
                      : "Click 'Start Breakdown' to generate sections for manual processing."}
                  </p>
                </div>
                {data.mode === "automatic" ? (
                  <Button onClick={handleRunAll} disabled={isActionLoading}>
                    Start Pipeline (Automatic)
                  </Button>
                ) : (
                  <Button onClick={() => setShowManualBreakdownDialog(true)} disabled={isActionLoading}>
                    Start Breakdown (Manual)
                  </Button>
                )}
              </div>
            )}

            {data.sections.length > 0 && (
              <div className="w-full">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-bold">Expansion Sections</h2>
                </div>
                <ExpansionWizard
                  expansion={data}
                  onRefresh={refetch}
                  onCombine={handleCombine}
                  onRetrySection={handleRetrySection}
                  onSaveManual={handleSaveManual}
                />
              </div>
            )}
            
            {allSectionsCompleted && data.status !== "completed" && (
              <div className="p-8 border rounded-lg bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900 flex flex-col items-center gap-4">
                <CheckCircle className="h-10 w-10 text-green-600" />
                <div className="text-center">
                  <h3 className="text-lg font-bold">All Sections Completed</h3>
                  <p className="text-sm text-muted-foreground">
                    All expansion sections have been processed. You can now combine them into a final report.
                  </p>
                </div>
                <Button 
                  onClick={handleCombine} 
                  disabled={isActionLoading}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  Combine Sections & Generate Report
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Manual Breakdown Dialog */}
      <ManualBreakdownDialog
        expansionId={data.id}
        open={showManualBreakdownDialog}
        onOpenChange={setShowManualBreakdownDialog}
        onSuccess={() => {
          toast({
            title: "Breakdown saved",
            description: "Sections have been created from your pasted response.",
          });
          refetch();
        }}
      />
    </div>
  );
}
