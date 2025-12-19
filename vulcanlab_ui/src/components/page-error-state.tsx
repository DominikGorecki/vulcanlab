"use client"

import { AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

/**
 * Props for the PageErrorState component
 */
export interface PageErrorStateProps {
  /**
   * The error message or Error object to display
   */
  error: string | Error
  /**
   * Optional title to display above the error message
   */
  title?: string
  /**
   * Optional description to provide additional context
   */
  description?: string
  /**
   * Optional callback function to retry the failed operation
   */
  onRetry?: () => void
  /**
   * Optional className for custom styling
   */
  className?: string
}

/**
 * PageErrorState component displays a centered error message with an icon and optional retry button.
 * Used to indicate that a page or section encountered an error while loading data.
 *
 * @example
 * ```tsx
 * // Basic error display
 * <PageErrorState error="Failed to load data" />
 *
 * // With retry functionality
 * <PageErrorState
 *   error={error}
 *   title="Something went wrong"
 *   description="We couldn't load your data"
 *   onRetry={handleRetry}
 * />
 * ```
 */
export function PageErrorState({
  error,
  title,
  description,
  onRetry,
  className,
}: PageErrorStateProps) {
  const errorMessage = typeof error === 'string' ? error : error.message

  return (
    <div
      className={cn(
        "flex min-h-[400px] flex-col items-center justify-center gap-4 text-center",
        className
      )}
    >
      <AlertCircle className="size-12 text-destructive" />
      {title && (
        <h3 className="text-lg font-semibold text-foreground">{title}</h3>
      )}
      <div className="space-y-2 max-w-md">
        <p className="text-sm font-medium text-destructive">{errorMessage}</p>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {onRetry && (
        <Button onClick={onRetry} variant="outline" className="mt-2">
          Try Again
        </Button>
      )}
    </div>
  )
}
