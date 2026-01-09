/**
 * Shared Component Library
 *
 * This file exports all shared, reusable components from the vulcanlab_ui component library.
 * These components provide standardized UI patterns across the application.
 *
 * @see documentation/work/ui-component-library-guide.md for usage guidelines
 */

// Layout State Components (T02)
export { PageLoadingState } from './page-loading-state'
export type { PageLoadingStateProps } from './page-loading-state'

export { PageErrorState } from './page-error-state'
export type { PageErrorStateProps } from './page-error-state'

export { EmptyState } from './empty-state'
export type { EmptyStateProps, EmptyStateAction } from './empty-state'

// Page Header Components (T03)
export { PageHeader } from './page-header'
export type { PageHeaderProps } from './page-header'

export { StickyDetailHeader } from './sticky-detail-header'
export type { StickyDetailHeaderProps } from './sticky-detail-header'

// Data Display Components (T04)
export { DataTable } from './data-table'
export type { DataTableProps, DataTableColumn } from './data-table'

export { StatusBadge } from './status-badge'
export type { StatusBadgeProps, StatusConfig } from './status-badge'

// Stats Display Components (T05)
export { StatsCard } from './stats-card'
export type { StatsCardProps, StatTrend } from './stats-card'

export { StatsCardGrid } from './stats-card-grid'
export type { StatsCardGridProps } from './stats-card-grid'

// Form and Dialog Components (T06)
export { FormField } from './form-field'
export type { FormFieldProps } from './form-field'

export { ConfirmDialog } from './confirm-dialog'
export type { ConfirmDialogProps, ConfirmDialogVariant } from './confirm-dialog'

// Collections Components (T07)
export { NewCollectionModal } from './collections/NewCollectionModal'
export { AddToCollectionModal } from './collections/AddToCollectionModal'
export { MetadataCard } from './collections/MetadataCard'
