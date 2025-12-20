"use client"

import * as React from "react"
import { TrendingUp, TrendingDown } from "lucide-react"
import { cn } from "@/lib/utils"
import { Card, CardHeader, CardContent } from "@/components/ui/card"

/**
 * Trend information for a stat
 */
export interface StatTrend {
  /**
   * The trend value (e.g., percentage or absolute number)
   */
  value: number | string
  /**
   * The direction of the trend
   */
  direction: "up" | "down"
}

/**
 * Props for the StatsCard component
 */
export interface StatsCardProps {
  /**
   * The label/title of the stat
   */
  label: string
  /**
   * The main value to display
   */
  value: string | number
  /**
   * Optional icon component to display in the top-right corner
   */
  icon?: React.ComponentType<{ className?: string }>
  /**
   * Optional trend indicator
   */
  trend?: StatTrend
  /**
   * Optional className for custom styling
   */
  className?: string
}

/**
 * StatsCard component displays a single metric or statistic.
 * Includes a label, prominent value display, optional icon, and optional trend indicator.
 *
 * @example
 * ```tsx
 * import { Users } from "lucide-react"
 *
 * // Basic usage
 * <StatsCard label="Total Users" value={1234} />
 *
 * // With icon
 * <StatsCard
 *   label="Active Users"
 *   value="1,234"
 *   icon={Users}
 * />
 *
 * // With trend
 * <StatsCard
 *   label="Revenue"
 *   value="$12,345"
 *   icon={DollarSign}
 *   trend={{ value: "+12%", direction: "up" }}
 * />
 * ```
 */
export function StatsCard({
  label,
  value,
  icon: Icon,
  trend,
  className,
}: StatsCardProps) {
  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            <p className="text-3xl font-bold tracking-tight">{value}</p>
          </div>
          {Icon && (
            <div className="rounded-lg bg-primary/10 p-2">
              <Icon className="size-5 text-primary" />
            </div>
          )}
        </div>
      </CardHeader>
      {trend && (
        <CardContent className="pt-0">
          <div className="flex items-center gap-1 text-sm">
            {trend.direction === "up" ? (
              <>
                <TrendingUp className="size-4 text-green-600 dark:text-green-500" />
                <span className="font-medium text-green-600 dark:text-green-500">
                  {trend.value}
                </span>
              </>
            ) : (
              <>
                <TrendingDown className="size-4 text-red-600 dark:text-red-500" />
                <span className="font-medium text-red-600 dark:text-red-500">
                  {trend.value}
                </span>
              </>
            )}
            <span className="text-muted-foreground ml-1">vs last period</span>
          </div>
        </CardContent>
      )}
    </Card>
  )
}
