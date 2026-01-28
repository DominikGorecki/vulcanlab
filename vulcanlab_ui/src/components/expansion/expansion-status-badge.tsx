"use client";

import { StatusBadge, type StatusConfig } from "@/components/status-badge";
import {
  Clock,
  Loader2,
  CheckCircle,
  XCircle,
  ListChecks,
  Combine
} from "lucide-react";

/**
 * Status configuration for expansion statuses.
 * Maps status values to display labels, colors, and icons.
 */
export const expansionStatusConfig: Record<string, StatusConfig> = {
  created: {
    label: "Created",
    variant: "secondary",
    icon: Clock,
  },
  breakdown_pending: {
    label: "Breakdown Pending",
    variant: "secondary",
    icon: Clock,
  },
  breakdown_complete: {
    label: "Breakdown Complete",
    variant: "outline",
    icon: ListChecks,
  },
  sections_in_progress: {
    label: "Processing Sections",
    variant: "outline",
    icon: Loader2,
  },
  combining: {
    label: "Combining",
    variant: "outline",
    icon: Combine,
  },
  completed: {
    label: "Completed",
    variant: "default",
    icon: CheckCircle,
  },
  failed: {
    label: "Failed",
    variant: "destructive",
    icon: XCircle,
  },
};

export interface ExpansionStatusBadgeProps {
  /**
   * The expansion status value
   */
  status: string;
  /**
   * Optional className for custom styling
   */
  className?: string;
}

/**
 * ExpansionStatusBadge displays the status of an expansion with appropriate
 * colors and icons based on the expansion workflow states.
 *
 * @example
 * ```tsx
 * <ExpansionStatusBadge status="completed" />
 * <ExpansionStatusBadge status="sections_in_progress" />
 * ```
 */
export function ExpansionStatusBadge({
  status,
  className,
}: ExpansionStatusBadgeProps) {
  return (
    <StatusBadge
      status={status}
      statusConfig={expansionStatusConfig}
      className={className}
    />
  );
}
