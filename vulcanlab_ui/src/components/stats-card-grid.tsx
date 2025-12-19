"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { StatsCard, StatsCardProps } from "@/components/stats-card"

/**
 * Props for the StatsCardGrid component
 */
export interface StatsCardGridProps {
  /**
   * Array of stats to display in the grid
   */
  stats: StatsCardProps[]
  /**
   * Optional className for custom styling
   */
  className?: string
}

/**
 * StatsCardGrid component displays multiple stat cards in a responsive grid layout.
 * Grid adapts to viewport: 3 columns on desktop, 2 on tablet, 1 on mobile.
 *
 * @example
 * ```tsx
 * import { Users, DollarSign, ShoppingCart } from "lucide-react"
 *
 * const stats = [
 *   {
 *     label: "Total Users",
 *     value: "1,234",
 *     icon: Users,
 *     trend: { value: "+12%", direction: "up" as const },
 *   },
 *   {
 *     label: "Revenue",
 *     value: "$45,231",
 *     icon: DollarSign,
 *     trend: { value: "+8%", direction: "up" as const },
 *   },
 *   {
 *     label: "Orders",
 *     value: "543",
 *     icon: ShoppingCart,
 *     trend: { value: "-3%", direction: "down" as const },
 *   },
 * ]
 *
 * <StatsCardGrid stats={stats} />
 * ```
 */
export function StatsCardGrid({ stats, className }: StatsCardGridProps) {
  if (stats.length === 0) {
    return null
  }

  return (
    <div
      className={cn(
        "grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
        className
      )}
    >
      {stats.map((stat, index) => (
        <StatsCard key={index} {...stat} />
      ))}
    </div>
  )
}
