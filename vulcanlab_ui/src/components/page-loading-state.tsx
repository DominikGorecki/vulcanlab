"use client"

import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * Props for the PageLoadingState component
 */
export interface PageLoadingStateProps {
  /**
   * Optional title to display above the spinner
   */
  title?: string
  /**
   * Optional description to display below the title
   */
  description?: string
  /**
   * Optional className for custom styling
   */
  className?: string
}

/**
 * PageLoadingState component displays a centered loading spinner with optional title and description.
 * Used to indicate that a page or section is currently loading data.
 *
 * @example
 * ```tsx
 * // Basic usage
 * <PageLoadingState />
 *
 * // With title and description
 * <PageLoadingState
 *   title="Loading data"
 *   description="Please wait while we fetch your information..."
 * />
 * ```
 */
export function PageLoadingState({
  title,
  description,
  className,
}: PageLoadingStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[400px] flex-col items-center justify-center gap-3 text-center",
        className
      )}
    >
      <Loader2 className="size-8 animate-spin text-muted-foreground" />
      {title && (
        <h3 className="text-lg font-medium text-foreground">{title}</h3>
      )}
      {description && (
        <p className="text-sm text-muted-foreground max-w-md">{description}</p>
      )}
    </div>
  )
}
