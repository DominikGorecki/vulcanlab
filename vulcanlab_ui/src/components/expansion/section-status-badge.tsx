"use client";

import { StatusBadge, type StatusConfig } from "@/components/status-badge";
import {
  Clock,
  Loader2,
  CheckCircle,
  XCircle,
  PlayCircle,
  Wand2,
} from "lucide-react";

/**
 * Status configuration for section statuses.
 * Maps status values to display labels, colors, and icons.
 */
export const sectionStatusConfig: Record<string, StatusConfig> = {
  pending: {
    label: "Pending",
    variant: "secondary",
    icon: Clock,
  },
  expanding: {
    label: "Expanding",
    variant: "outline",
    icon: Loader2,
  },
  ready: {
    label: "Ready",
    variant: "outline",
    icon: PlayCircle,
  },
  generating: {
    label: "Generating",
    variant: "outline",
    icon: Wand2,
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

export interface SectionStatusBadgeProps {
  /**
   * The section status value
   */
  status: string;
  /**
   * Optional className for custom styling
   */
  className?: string;
}

/**
 * SectionStatusBadge displays the status of an expansion section.
 */
export function SectionStatusBadge({
  status,
  className,
}: SectionStatusBadgeProps) {
  return (
    <StatusBadge
      status={status}
      statusConfig={sectionStatusConfig}
      className={className}
    />
  );
}
