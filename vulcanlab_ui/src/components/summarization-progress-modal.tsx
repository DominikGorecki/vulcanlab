"use client";

import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";

export interface SummarizationProgress {
  total_nodes: number;
  completed_nodes: number;
  status: "pending" | "processing" | "completed" | "failed";
}

interface SummarizationProgressModalProps {
  isOpen: boolean;
  progress: SummarizationProgress | null;
}

export function SummarizationProgressModal({
  isOpen,
  progress,
}: SummarizationProgressModalProps) {
  const percentage = progress
    ? Math.round((progress.completed_nodes / progress.total_nodes) * 100)
    : 0;

  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-md" onPointerDownOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle>Summarizing work...</DialogTitle>
          <DialogDescription>
            This may take a few minutes depending on the size of the work.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-4 py-4">
          <Progress value={percentage} className="h-2 w-full" />
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>
              {progress
                ? `Processing node ${progress.completed_nodes} of ${progress.total_nodes}`
                : "Initializing..."}
            </span>
            <span>{percentage}%</span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
