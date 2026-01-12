"use client";

import React, { useCallback } from "react";
import { FileSearch } from "lucide-react";
import { useRouter } from "next/navigation";
import { usePageData } from "@/hooks/use-page-data";
import { ResearchSession } from "@/types/research";
import { ResearchReportCard } from "./ResearchReportCard";
import { EmptyState } from "@/components/empty-state";
import { PageLoadingState } from "@/components/page-loading-state";
import { PageErrorState } from "@/components/page-error-state";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ResearchReportListProps {
  collectionId: number;
}

/**
 * ResearchReportList displays a list of completed research reports for a collection.
 */
export function ResearchReportList({ collectionId }: ResearchReportListProps) {
  const router = useRouter();

  const fetchCompletedSessions = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/collections/${collectionId}/research-sessions`);
    if (!response.ok) {
      throw new Error(`Failed to load research sessions: ${response.statusText}`);
    }
    const data = await response.json();
    // Filter for completed sessions only and sort by created_at DESC
    return (data.sessions || [])
      .filter((s: ResearchSession) => s.status === "completed")
      .sort((a: ResearchSession, b: ResearchSession) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
  }, [collectionId]);

  const { data: sessions, loading, error, refetch } = usePageData<ResearchSession[]>(fetchCompletedSessions);

  if (loading) return <PageLoadingState />;
  if (error) return <PageErrorState error={error} onRetry={refetch} />;

  if (!sessions || sessions.length === 0) {
    return (
      <div className="py-8">
        <h3 className="text-lg font-semibold tracking-tight mb-4">Research Reports</h3>
        <EmptyState
          title="No research reports yet"
          description="Start deep research to create comprehensive reports on your collection items."
          icon={FileSearch}
        />
      </div>
    );
  }

  return (
    <div className="py-8 space-y-4">
      <h3 className="text-lg font-semibold tracking-tight">Research Reports</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sessions.map((session) => (
          <ResearchReportCard 
            key={session.id} 
            session={session} 
            onClick={() => router.push(`/collections/${collectionId}/report/${session.id}`)}
          />
        ))}
      </div>
    </div>
  );
}
