"use client"

import * as React from "react"
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTable } from "@/hooks/use-table"
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table"
import { PageLoadingState } from "@/components/page-loading-state"
import { EmptyState } from "@/components/empty-state"

/**
 * Column definition for DataTable
 */
export interface DataTableColumn<TData> {
  /**
   * Unique key for the column (must match a key in TData)
   */
  key: keyof TData
  /**
   * Header text to display for the column
   */
  header: string
  /**
   * Optional custom cell renderer. If not provided, displays the raw value.
   */
  cell?: (row: TData) => React.ReactNode
  /**
   * Whether this column should support sorting
   * @default false
   */
  sortable?: boolean
  /**
   * Optional className for the column header and cells
   */
  className?: string
}

/**
 * Props for the DataTable component
 */
export interface DataTableProps<TData> {
  /**
   * Array of data to display in the table
   */
  data: TData[]
  /**
   * Column definitions for the table
   */
  columns: DataTableColumn<TData>[]
  /**
   * Optional callback when a row is clicked
   */
  onRowClick?: (row: TData) => void
  /**
   * Whether the table is currently loading data
   * @default false
   */
  loading?: boolean
  /**
   * Optional custom empty state configuration
   */
  emptyState?: {
    title: string
    description?: string
    icon?: React.ComponentType<{ className?: string }>
    action?: {
      label: string
      onClick: () => void
    }
  }
  /**
   * Optional className for the table container
   */
  className?: string
}

/**
 * DataTable component displays tabular data with optional sorting and row click handling.
 * Integrates with the useTable hook for sorting state management.
 * Displays loading and empty states appropriately.
 *
 * @example
 * ```tsx
 * interface User {
 *   id: number
 *   name: string
 *   email: string
 *   status: string
 * }
 *
 * const columns: DataTableColumn<User>[] = [
 *   {
 *     key: 'name',
 *     header: 'Name',
 *     sortable: true,
 *   },
 *   {
 *     key: 'email',
 *     header: 'Email',
 *   },
 *   {
 *     key: 'status',
 *     header: 'Status',
 *     cell: (user) => <StatusBadge status={user.status} statusConfig={statusConfig} />,
 *   },
 * ]
 *
 * <DataTable
 *   data={users}
 *   columns={columns}
 *   onRowClick={(user) => router.push(`/users/${user.id}`)}
 *   loading={isLoading}
 * />
 * ```
 */
export function DataTable<TData>({
  data,
  columns,
  onRowClick,
  loading = false,
  emptyState,
  className,
}: DataTableProps<TData>) {
  const { sortedData, sortKey, sortDirection, handleSort } = useTable(
    data,
    null,
    'asc'
  )

  // Show loading state
  if (loading) {
    return <PageLoadingState />
  }

  // Show empty state
  if (data.length === 0) {
    return (
      <EmptyState
        title={emptyState?.title || 'No data'}
        description={emptyState?.description}
        icon={emptyState?.icon}
        action={emptyState?.action}
      />
    )
  }

  const getSortIcon = (columnKey: keyof TData) => {
    if (sortKey !== columnKey) {
      return <ArrowUpDown className="ml-2 size-4" />
    }
    return sortDirection === 'asc' ? (
      <ArrowUp className="ml-2 size-4" />
    ) : (
      <ArrowDown className="ml-2 size-4" />
    )
  }

  return (
    <div className={cn("rounded-md border", className)}>
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((column) => (
              <TableHead
                key={String(column.key)}
                className={cn(
                  column.className,
                  column.sortable && "cursor-pointer select-none"
                )}
                onClick={() => column.sortable && handleSort(column.key)}
              >
                <div className="flex items-center">
                  {column.header}
                  {column.sortable && getSortIcon(column.key)}
                </div>
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedData.map((row, rowIndex) => (
            <TableRow
              key={rowIndex}
              onClick={() => onRowClick?.(row)}
              className={cn(onRowClick && "cursor-pointer")}
            >
              {columns.map((column) => (
                <TableCell
                  key={String(column.key)}
                  className={column.className}
                >
                  {column.cell
                    ? column.cell(row)
                    : String(row[column.key] ?? '')}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
