# UI Component Library Guide

This guide provides comprehensive documentation for the vulcanlab_ui shared component library. All components follow consistent patterns and integrate seamlessly with our tech stack (Next.js, TypeScript, TailwindCSS, Radix UI).

## Table of Contents

- [Importing Components](#importing-components)
- [Layout State Components](#layout-state-components)
- [Page Header Components](#page-header-components)
- [Data Display Components](#data-display-components)
- [Stats Display Components](#stats-display-components)
- [Form and Dialog Components](#form-and-dialog-components)
- [Hooks](#hooks)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Importing Components

All components and hooks are available through centralized exports:

```tsx
// Import components
import {
  DataTable,
  PageHeader,
  StatusBadge,
  ConfirmDialog
} from '@/components'

// Import hooks
import { usePageData, useModal, useTable } from '@/hooks'
```

## Layout State Components

### PageLoadingState

Displays a centered loading spinner with optional title and description.

**When to use:** Show loading state while fetching data, especially with `usePageData` hook.

```tsx
import { PageLoadingState } from '@/components'

<PageLoadingState
  title="Loading data"
  description="Please wait..."
/>
```

**Props:**
- `title?: string` - Optional title
- `description?: string` - Optional description
- `className?: string` - Custom styling

### PageErrorState

Displays a centered error message with optional retry button.

**When to use:** Show error state when data fetching fails, especially with `usePageData` hook.

```tsx
import { PageErrorState } from '@/components'

<PageErrorState
  error={error}
  title="Failed to load"
  onRetry={handleRetry}
/>
```

**Props:**
- `error: string | Error` - Error message or Error object
- `title?: string` - Optional title
- `description?: string` - Optional description
- `onRetry?: () => void` - Optional retry callback
- `className?: string` - Custom styling

### EmptyState

Displays a centered empty state with optional icon and action button.

**When to use:** Show when data array is empty (e.g., no search results, no items).

```tsx
import { EmptyState } from '@/components'
import { FileQuestion } from 'lucide-react'

<EmptyState
  icon={FileQuestion}
  title="No documents"
  description="Upload your first document"
  action={{
    label: "Upload",
    onClick: handleUpload
  }}
/>
```

**Props:**
- `title: string` - Required title
- `icon?: React.ComponentType` - Optional icon component
- `description?: string` - Optional description
- `action?: { label: string, onClick: () => void }` - Optional action button
- `className?: string` - Custom styling

## Page Header Components

### PageHeader

Main page header with title, description, and action buttons.

**When to use:** At the top of list/index pages.

```tsx
import { PageHeader } from '@/components'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'

<PageHeader
  title="Documents"
  description="Manage your documents"
  actions={
    <Button>
      <Plus className="size-4" />
      Add Document
    </Button>
  }
/>
```

**Props:**
- `title: string` - Required page title
- `description?: string` - Optional description
- `actions?: React.ReactNode` - Optional action buttons
- `className?: string` - Custom styling

### StickyDetailHeader

Sticky header for detail pages with back navigation.

**When to use:** At the top of detail/edit pages.

```tsx
import { StickyDetailHeader } from '@/components'

<StickyDetailHeader
  title="Document Details"
  subtitle="document-123.pdf"
  backUrl="/documents"
  backLabel="Back to Documents"
  actions={
    <>
      <Button variant="outline">Cancel</Button>
      <Button>Save</Button>
    </>
  }
/>
```

**Props:**
- `title: string` - Required title
- `backUrl: string` - Required back navigation URL
- `subtitle?: string` - Optional subtitle
- `backLabel?: string` - Back button label (default: "Back")
- `actions?: React.ReactNode` - Optional action buttons
- `className?: string` - Custom styling

## Data Display Components

### DataTable

Generic table component with sorting and row click support.

**When to use:** Display tabular data with optional sorting and row interactions.

```tsx
import { DataTable, type DataTableColumn } from '@/components'
import { StatusBadge } from '@/components'

interface User {
  id: number
  name: string
  email: string
  status: string
}

const columns: DataTableColumn<User>[] = [
  {
    key: 'name',
    header: 'Name',
    sortable: true,
  },
  {
    key: 'email',
    header: 'Email',
    sortable: true,
  },
  {
    key: 'status',
    header: 'Status',
    cell: (user) => (
      <StatusBadge status={user.status} statusConfig={statusConfig} />
    ),
  },
]

<DataTable
  data={users}
  columns={columns}
  onRowClick={(user) => router.push(`/users/${user.id}`)}
  loading={isLoading}
  emptyState={{
    title: "No users found",
    description: "Try adding some users",
  }}
/>
```

**Props:**
- `data: TData[]` - Array of data
- `columns: DataTableColumn<TData>[]` - Column definitions
- `onRowClick?: (row: TData) => void` - Optional row click handler
- `loading?: boolean` - Show loading state
- `emptyState?: { title, description?, icon? }` - Custom empty state
- `className?: string` - Custom styling

**Column Configuration:**
- `key: keyof TData` - Column key (must match data property)
- `header: string` - Column header text
- `cell?: (row: TData) => React.ReactNode` - Custom cell renderer
- `sortable?: boolean` - Enable sorting (default: false)
- `className?: string` - Column styling

### StatusBadge

Displays status with configurable colors and icons.

**When to use:** Show status indicators in tables or detail views.

```tsx
import { StatusBadge, type StatusConfig } from '@/components'
import { CheckCircle, Clock, XCircle } from 'lucide-react'

const workStatusConfig: Record<string, StatusConfig> = {
  completed: {
    label: "Completed",
    variant: "default",
    icon: CheckCircle,
  },
  pending: {
    label: "Pending",
    variant: "secondary",
    icon: Clock,
  },
  failed: {
    label: "Failed",
    variant: "destructive",
    icon: XCircle,
  },
}

<StatusBadge status="completed" statusConfig={workStatusConfig} />
```

**Props:**
- `status: string` - Status key to lookup in config
- `statusConfig: Record<string, StatusConfig>` - Status configuration map
- `className?: string` - Custom styling

**StatusConfig:**
- `label: string` - Display label
- `variant?: 'default' | 'secondary' | 'destructive' | 'outline'` - Badge variant
- `icon?: React.ComponentType` - Optional icon

## Stats Display Components

### StatsCard

Displays a single metric with optional icon and trend.

**When to use:** Show key metrics on dashboards or summary pages.

```tsx
import { StatsCard } from '@/components'
import { Users } from 'lucide-react'

<StatsCard
  label="Total Users"
  value="1,234"
  icon={Users}
  trend={{ value: "+12%", direction: "up" }}
/>
```

**Props:**
- `label: string` - Metric label
- `value: string | number` - Metric value
- `icon?: React.ComponentType` - Optional icon
- `trend?: { value: string | number, direction: 'up' | 'down' }` - Optional trend
- `className?: string` - Custom styling

### StatsCardGrid

Displays multiple stats in a responsive grid.

**When to use:** Show multiple related metrics together.

```tsx
import { StatsCardGrid } from '@/components'
import { Users, DollarSign, ShoppingCart } from 'lucide-react'

const stats = [
  {
    label: "Total Users",
    value: "1,234",
    icon: Users,
    trend: { value: "+12%", direction: "up" as const },
  },
  {
    label: "Revenue",
    value: "$45,231",
    icon: DollarSign,
    trend: { value: "+8%", direction: "up" as const },
  },
  {
    label: "Orders",
    value: "543",
    icon: ShoppingCart,
    trend: { value: "-3%", direction: "down" as const },
  },
]

<StatsCardGrid stats={stats} />
```

**Props:**
- `stats: StatsCardProps[]` - Array of stat configurations
- `className?: string` - Custom styling

**Grid Layout:** 3 columns (desktop), 2 columns (tablet), 1 column (mobile)

## Form and Dialog Components

### FormField

Form field wrapper with label, error display, and description.

**When to use:** Wrap form inputs for consistent styling and error handling with react-hook-form.

```tsx
import { FormField } from '@/components'
import { Input } from '@/components/ui/input'
import { useForm } from 'react-hook-form'

function MyForm() {
  const { register, formState: { errors } } = useForm()

  return (
    <FormField
      label="Email"
      required
      error={errors.email?.message}
      description="We'll never share your email"
    >
      <Input
        type="email"
        {...register("email", {
          required: "Email is required",
          pattern: {
            value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
            message: "Invalid email address"
          }
        })}
      />
    </FormField>
  )
}
```

**Props:**
- `label: string` - Field label
- `children: React.ReactNode` - Input element
- `error?: string` - Error message (from react-hook-form)
- `required?: boolean` - Show required asterisk
- `description?: string` - Optional help text
- `className?: string` - Custom styling

### ConfirmDialog

Confirmation dialog with three variants and async support.

**When to use:** Require user confirmation for important actions.

```tsx
import { ConfirmDialog } from '@/components'
import { useModal } from '@/hooks'

function DeleteButton() {
  const confirmDialog = useModal()

  const handleDelete = async () => {
    await deleteItem(itemId)
    // Dialog closes automatically on success
  }

  return (
    <>
      <Button onClick={confirmDialog.open}>Delete</Button>
      <ConfirmDialog
        open={confirmDialog.isOpen}
        onOpenChange={(open) => !open && confirmDialog.close()}
        title="Delete Item"
        message="Are you sure? This action cannot be undone."
        variant="danger"
        confirmLabel="Delete"
        onConfirm={handleDelete}
      />
    </>
  )
}
```

**Props:**
- `open: boolean` - Dialog open state
- `onOpenChange: (open: boolean) => void` - Open state change handler
- `title: string` - Dialog title
- `message: string` - Dialog message
- `onConfirm: () => void | Promise<void>` - Confirm handler (can be async)
- `variant?: 'danger' | 'warning' | 'info'` - Visual variant (default: 'danger')
- `confirmLabel?: string` - Confirm button label (default: 'Confirm')
- `cancelLabel?: string` - Cancel button label (default: 'Cancel')
- `className?: string` - Custom styling

**Variants:**
- `danger` - Red button (destructive actions)
- `warning` - Amber button (cautionary actions)
- `info` - Blue button (informational confirmations)

## Hooks

### useModal

Manages modal/dialog open/close state.

**When to use:** Control any modal or dialog component.

```tsx
import { useModal } from '@/hooks'

const modal = useModal()
// or with default open state
const modal = useModal({ defaultOpen: true })

// API: modal.isOpen, modal.open(), modal.close(), modal.toggle()
```

### usePageData

Fetches data with loading/error/success states.

**When to use:** Fetch data for a page or section.

```tsx
import { usePageData } from '@/hooks'
import { PageLoadingState, PageErrorState } from '@/components'

const { data, loading, error, refetch } = usePageData(
  async () => {
    const res = await fetch('/api/users')
    if (!res.ok) throw new Error('Failed to fetch')
    return res.json()
  },
  {
    autoFetch: true,
    onError: (err) => console.error(err),
  }
)

if (loading) return <PageLoadingState />
if (error) return <PageErrorState error={error} onRetry={refetch} />
if (!data) return null

return <div>{/* Render data */}</div>
```

### useTable

Manages table sorting state.

**When to use:** Add sorting functionality to tables (used internally by DataTable).

```tsx
import { useTable } from '@/hooks'

const { sortedData, sortKey, sortDirection, handleSort } = useTable(
  data,
  'name', // default sort key
  'asc'   // default sort direction
)
```

## Common Patterns

### Data Fetching with Loading/Error States

```tsx
import { usePageData } from '@/hooks'
import { PageLoadingState, PageErrorState, DataTable } from '@/components'

function UsersPage() {
  const { data, loading, error, refetch } = usePageData(fetchUsers)

  if (loading) return <PageLoadingState title="Loading users" />
  if (error) return <PageErrorState error={error} onRetry={refetch} />
  if (!data || data.length === 0) {
    return <EmptyState title="No users found" />
  }

  return <DataTable data={data} columns={columns} />
}
```

### Confirmation Dialogs with useModal

```tsx
import { useModal } from '@/hooks'
import { ConfirmDialog } from '@/components'

const deleteDialog = useModal()

<Button onClick={deleteDialog.open}>Delete</Button>
<ConfirmDialog
  open={deleteDialog.isOpen}
  onOpenChange={(open) => !open && deleteDialog.close()}
  title="Delete Item"
  message="Are you sure?"
  variant="danger"
  onConfirm={async () => {
    await deleteItem()
    // Dialog auto-closes on success
  }}
/>
```

### DataTable with StatusBadge

```tsx
const columns: DataTableColumn<Work>[] = [
  { key: 'name', header: 'Name', sortable: true },
  { key: 'created', header: 'Created', sortable: true },
  {
    key: 'status',
    header: 'Status',
    cell: (work) => (
      <StatusBadge status={work.status} statusConfig={workStatusConfig} />
    ),
  },
]
```

### Page Header with Actions

```tsx
<PageHeader
  title="Documents"
  description="Manage your documents"
  actions={
    <div className="flex gap-2">
      <Button variant="outline">Export</Button>
      <Button>
        <Plus className="size-4" />
        Add Document
      </Button>
    </div>
  }
/>
```

## Troubleshooting

### Components not importing

**Issue:** Can't import components from `@/components`

**Solution:** Ensure you're using the centralized export:
```tsx
// ✅ Correct
import { DataTable } from '@/components'

// ❌ Incorrect
import { DataTable } from '@/components/data-table'
```

### TypeScript errors with DataTable

**Issue:** Type errors when defining columns

**Solution:** Use the `DataTableColumn<T>` type:
```tsx
import { type DataTableColumn } from '@/components'

const columns: DataTableColumn<User>[] = [...]
```

### StatusBadge showing unknown status

**Issue:** Status not found in config

**Solution:** StatusBadge has graceful fallback. Ensure status config includes all possible statuses:
```tsx
const statusConfig = {
  // ...all statuses
  unknown: { label: 'Unknown', variant: 'outline' as const }
}
```

### ConfirmDialog not closing

**Issue:** Dialog stays open after confirmation

**Solution:** Dialog auto-closes on successful confirmation. If it stays open, the onConfirm handler likely threw an error. Check console for errors.

### FormField errors not showing

**Issue:** Validation errors not displaying

**Solution:** Ensure you're passing the error from react-hook-form:
```tsx
error={errors.fieldName?.message}
```

### Dark mode colors incorrect

**Issue:** Components don't look right in dark mode

**Solution:** All components use theme-aware colors. Ensure your theme provider is set up correctly. Components use TailwindCSS color classes like `text-foreground`, `bg-background`, etc.

---

## Additional Resources

- **Patterns:** See `documentation/patterns.md` for coding patterns and conventions
- **shadcn/ui Docs:** https://ui.shadcn.com/docs for underlying UI primitives
- **TailwindCSS:** https://tailwindcss.com/docs for styling utilities
- **react-hook-form:** https://react-hook-form.com for form validation

## Component Checklist

When creating new pages or features, consider using:

- [ ] `PageHeader` or `StickyDetailHeader` for page structure
- [ ] `usePageData` for data fetching
- [ ] `PageLoadingState` and `PageErrorState` for loading/error states
- [ ] `DataTable` for tabular data
- [ ] `StatusBadge` for status indicators
- [ ] `EmptyState` for empty data scenarios
- [ ] `ConfirmDialog` for destructive actions
- [ ] `FormField` for form inputs
- [ ] `StatsCardGrid` for metrics displays
