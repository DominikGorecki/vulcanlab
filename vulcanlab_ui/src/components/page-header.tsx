"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

/**
 * Props for the PageHeader component
 */
export interface PageHeaderProps {
  /**
   * The main title of the page
   */
  title: string
  /**
   * Optional description or subtitle for the page
   */
  description?: string
  /**
   * Optional actions (buttons, links, etc.) to display on the right side
   */
  actions?: React.ReactNode
  /**
   * Optional className for custom styling
   */
  className?: string
}

/**
 * PageHeader component displays a consistent header at the top of pages.
 * Includes a title, optional description, and optional action buttons.
 * Layout is responsive - actions stack on mobile and align right on desktop.
 *
 * @example
 * ```tsx
 * // Basic usage with title only
 * <PageHeader title="My Page" />
 *
 * // With description
 * <PageHeader
 *   title="User Management"
 *   description="Manage users and their permissions"
 * />
 *
 * // With actions
 * <PageHeader
 *   title="Documents"
 *   description="All your uploaded documents"
 *   actions={
 *     <Button>
 *       <Plus className="size-4" />
 *       Upload Document
 *     </Button>
 *   }
 * />
 * ```
 */
export function PageHeader({
  title,
  description,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-4 pb-6 sm:flex-row sm:items-start sm:justify-between",
        className
      )}
    >
      <div className="space-y-1 flex-1">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          {title}
        </h1>
        {description && (
          <p className="text-muted-foreground">{description}</p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2 sm:flex-shrink-0">
          {actions}
        </div>
      )}
    </div>
  )
}
