"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import type { VariantProps } from "class-variance-authority"
import type { badgeVariants } from "@/components/ui/badge"

/**
 * Configuration for a specific status
 */
export interface StatusConfig {
  /**
   * The display label for the status
   */
  label: string
  /**
   * The visual variant to use for the badge
   */
  variant?: VariantProps<typeof badgeVariants>["variant"]
  /**
   * Optional icon component to display alongside the label
   */
  icon?: React.ComponentType<{ className?: string }>
}

/**
 * Props for the StatusBadge component
 */
export interface StatusBadgeProps {
  /**
   * The status value (key to look up in statusConfig)
   */
  status: string
  /**
   * Mapping of status values to their display configuration
   */
  statusConfig: Record<string, StatusConfig>
  /**
   * Optional className for custom styling
   */
  className?: string
}

/**
 * StatusBadge component displays a status indicator with configurable styling and labels.
 * Provides a flexible way to display statuses across the application with consistent styling.
 *
 * @example
 * ```tsx
 * import { CheckCircle, Clock, XCircle } from "lucide-react"
 *
 * const workStatusConfig = {
 *   completed: {
 *     label: "Completed",
 *     variant: "default",
 *     icon: CheckCircle,
 *   },
 *   pending: {
 *     label: "Pending",
 *     variant: "secondary",
 *     icon: Clock,
 *   },
 *   failed: {
 *     label: "Failed",
 *     variant: "destructive",
 *     icon: XCircle,
 *   },
 * }
 *
 * <StatusBadge status="completed" statusConfig={workStatusConfig} />
 * ```
 */
export function StatusBadge({
  status,
  statusConfig,
  className,
}: StatusBadgeProps) {
  const config = statusConfig[status] || {
    label: status,
    variant: "outline" as const,
  }

  const Icon = config.icon

  return (
    <Badge variant={config.variant} className={cn("gap-1", className)}>
      {Icon && <Icon className="size-3" />}
      {config.label}
    </Badge>
  )
}
