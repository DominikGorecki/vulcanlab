"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Label } from "@/components/ui/label"

/**
 * Props for the FormField component
 */
export interface FormFieldProps {
  /**
   * Optional ID for the field (associates label with input)
   */
  id?: string
  /**
   * The label text for the field
   */
  label: string
  /**
   * Error message to display (typically from react-hook-form)
   */
  error?: string
  /**
   * Whether this field is required
   * @default false
   */
  required?: boolean
  /**
   * Optional description text to display below the label
   */
  description?: string
  /**
   * The input element (Input, Select, Textarea, etc.)
   */
  children: React.ReactNode
  /**
   * Optional className for the container
   */
  className?: string
}

/**
 * FormField component provides a standardized wrapper for form inputs with label,
 * error display, and optional description text. Designed to integrate with react-hook-form.
 *
 * @example
 * ```tsx
 * import { useForm } from "react-hook-form"
 * import { Input } from "@/components/ui/input"
 *
 * function MyForm() {
 *   const { register, formState: { errors } } = useForm()
 *
 *   return (
 *     <form>
 *       <FormField
 *         label="Email"
 *         required
 *         error={errors.email?.message}
 *         description="We'll never share your email"
 *       >
 *         <Input
 *           type="email"
 *           {...register("email", {
 *             required: "Email is required",
 *             pattern: {
 *               value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
 *               message: "Invalid email address"
 *             }
 *           })}
 *         />
 *       </FormField>
 *     </form>
 *   )
 * }
 * ```
 */
export function FormField({
  id,
  label,
  error,
  required = false,
  description,
  children,
  className,
}: FormFieldProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={id}>
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      {description && (
        <p className="text-sm text-muted-foreground">{description}</p>
      )}
      {children}
      {error && (
        <p className="text-sm font-medium text-destructive">{error}</p>
      )}
    </div>
  )
}
