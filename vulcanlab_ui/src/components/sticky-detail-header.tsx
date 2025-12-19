"use client"

import * as React from "react"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * Props for the StickyDetailHeader component
 */
export interface StickyDetailHeaderProps {
  /**
   * The main title of the detail page
   */
  title: string
  /**
   * The URL to navigate back to
   */
  backUrl: string
  /**
   * Optional subtitle or additional information
   */
  subtitle?: string
  /**
   * Optional custom label for the back button (defaults to "Back")
   */
  backLabel?: string
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
 * StickyDetailHeader component displays a sticky header at the top of detail pages.
 * Includes back navigation, title, optional subtitle, and optional action buttons.
 * The header remains visible when scrolling down the page.
 *
 * @example
 * ```tsx
 * // Basic usage
 * <StickyDetailHeader
 *   title="Document Details"
 *   backUrl="/documents"
 * />
 *
 * // With subtitle and custom back label
 * <StickyDetailHeader
 *   title="User Profile"
 *   subtitle="john.doe@example.com"
 *   backUrl="/users"
 *   backLabel="Back to Users"
 * />
 *
 * // With actions
 * <StickyDetailHeader
 *   title="Edit Document"
 *   backUrl="/documents"
 *   actions={
 *     <>
 *       <Button variant="outline">Cancel</Button>
 *       <Button>Save Changes</Button>
 *     </>
 *   }
 * />
 * ```
 */
export function StickyDetailHeader({
  title,
  backUrl,
  subtitle,
  backLabel = "Back",
  actions,
  className,
}: StickyDetailHeaderProps) {
  return (
    <div
      className={cn(
        "sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60",
        className
      )}
    >
      <div className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-3">
          <Link
            href={backUrl}
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors w-fit"
          >
            <ArrowLeft className="size-4" />
            {backLabel}
          </Link>
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              {title}
            </h1>
            {subtitle && (
              <p className="text-sm text-muted-foreground">{subtitle}</p>
            )}
          </div>
        </div>
        {actions && (
          <div className="flex items-center gap-2 sm:flex-shrink-0">
            {actions}
          </div>
        )}
      </div>
    </div>
  )
}
