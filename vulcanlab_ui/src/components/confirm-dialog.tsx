"use client"

import * as React from "react"
import { Loader2 } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

/**
 * Variant types for the confirm dialog
 */
export type ConfirmDialogVariant = "danger" | "warning" | "info"

/**
 * Props for the ConfirmDialog component
 */
export interface ConfirmDialogProps {
  /**
   * Whether the dialog is open
   */
  open: boolean
  /**
   * Callback when the dialog open state changes
   */
  onOpenChange: (open: boolean) => void
  /**
   * The title of the dialog
   */
  title: string
  /**
   * The message/description in the dialog
   */
  message: string
  /**
   * Label for the confirm button
   * @default "Confirm"
   */
  confirmLabel?: string
  /**
   * Label for the cancel button
   * @default "Cancel"
   */
  cancelLabel?: string
  /**
   * Visual variant of the dialog
   * @default "danger"
   */
  variant?: ConfirmDialogVariant
  /**
   * Callback when the confirm button is clicked
   * Can be async - dialog will show loading state
   */
  onConfirm: () => void | Promise<void>
}

/**
 * ConfirmDialog component provides a standardized confirmation dialog.
 * Supports different variants (danger, warning, info) and async confirm handlers.
 *
 * @example
 * ```tsx
 * import { useModal } from "@/hooks/use-modal"
 *
 * function DeleteButton() {
 *   const confirmDialog = useModal()
 *
 *   const handleDelete = async () => {
 *     await deleteItem(itemId)
 *     confirmDialog.close()
 *   }
 *
 *   return (
 *     <>
 *       <Button onClick={confirmDialog.open}>Delete</Button>
 *       <ConfirmDialog
 *         open={confirmDialog.isOpen}
 *         onOpenChange={confirmDialog.close}
 *         title="Delete Item"
 *         message="Are you sure you want to delete this item? This action cannot be undone."
 *         variant="danger"
 *         confirmLabel="Delete"
 *         onConfirm={handleDelete}
 *       />
 *     </>
 *   )
 * }
 * ```
 */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
  onConfirm,
}: ConfirmDialogProps) {
  const [isLoading, setIsLoading] = React.useState(false)

  const handleConfirm = async () => {
    setIsLoading(true)
    try {
      await onConfirm()
      onOpenChange(false)
    } catch (error) {
      // Error handling - keep dialog open on error
      console.error("Confirm action failed:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const getVariantProps = () => {
    switch (variant) {
      case "danger":
        return { variant: "destructive" as const }
      case "warning":
        return { variant: "default" as const, className: "bg-amber-600 hover:bg-amber-700 text-white" }
      case "info":
        return { variant: "default" as const, className: "bg-blue-600 hover:bg-blue-700 text-white" }
      default:
        return { variant: "destructive" as const }
    }
  }

  const variantProps = getVariantProps()

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{message}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isLoading}
          >
            {cancelLabel}
          </Button>
          <Button
            {...variantProps}
            onClick={handleConfirm}
            disabled={isLoading}
          >
            {isLoading && <Loader2 className="mr-2 size-4 animate-spin" />}
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
