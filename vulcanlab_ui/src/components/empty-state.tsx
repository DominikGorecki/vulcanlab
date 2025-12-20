"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

/**
 * Action configuration for the EmptyState component
 */
export interface EmptyStateAction {
  /**
   * The label text to display on the action button
   */
  label: string
  /**
   * Callback function when the action button is clicked
   */
  onClick: () => void
}

/**
 * Props for the EmptyState component
 */
export interface EmptyStateProps {
  /**
   * The title to display
   */
  title: string
  /**
   * Optional icon component to display above the title
   */
  icon?: React.ComponentType<{ className?: string }>
  /**
   * Optional description to provide additional context
   */
  description?: string
  /**
   * Optional action button configuration
   */
  action?: EmptyStateAction
  /**
   * Optional className for custom styling
   */
  className?: string
}

/**
 * EmptyState component displays a centered message when no data is available.
 * Optionally includes an icon, description, and action button.
 *
 * @example
 * ```tsx
 * import { FileQuestion } from "lucide-react"
 *
 * // Basic usage
 * <EmptyState title="No items found" />
 *
 * // With icon, description, and action
 * <EmptyState
 *   icon={FileQuestion}
 *   title="No documents"
 *   description="You haven't uploaded any documents yet"
 *   action={{
 *     label: "Upload Document",
 *     onClick: handleUpload
 *   }}
 * />
 * ```
 */
export function EmptyState({
  title,
  icon: Icon,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[400px] flex-col items-center justify-center gap-4 text-center",
        className
      )}
    >
      {Icon && <Icon className="size-16 text-muted-foreground/50" />}
      <div className="space-y-2 max-w-md">
        <h3 className="text-lg font-semibold text-foreground">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {action && (
        <Button onClick={action.onClick} className="mt-2">
          {action.label}
        </Button>
      )}
    </div>
  )
}
