# Ticket: ui-component-standardization.T06 - Form and Dialog Components

## Source

* Spec: documentation/work/ui-component-standardization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create FormField component integrated with react-hook-form for standardized form validation
* Create ConfirmDialog component for standardized confirmation workflows
* Enable consistent form and modal patterns across the application

## Scope

### In scope

* Implement FormField component wrapper for form inputs with validation
* Integrate FormField with react-hook-form for error display
* Implement ConfirmDialog component with configurable variants (danger, warning, info)
* Support async onConfirm handlers in ConfirmDialog
* Integration with useModal hook for dialog state
* TypeScript prop interfaces with JSDoc comments
* Unit tests for both components
* Markdown documentation for both components

### Out of scope

* Field arrays (dynamic lists of inputs)
* Complex multi-step forms
* Custom validation schema integration (Zod, Yup)
* Form submission hook (rely on react-hook-form's handleSubmit)
* File upload fields
* Custom input components (use existing shadcn/ui inputs)

## Dependencies

* Depends on: T01 (useModal hook, react-hook-form installed)
* Unblocks: Form implementations in future pages

## Implementation plan

* Create FormField component:
  * Create vulcanlab_ui/src/components/form-field.tsx
  * Add "use client" directive
  * Define FormFieldProps interface (label, error, required, description, children, className)
  * Render label with required indicator if required is true
  * Render children (input element passed from parent)
  * Render optional description text
  * Render error message in red when error prop is provided
  * Use existing Label component from vulcanlab_ui/src/components/ui/label.tsx
  * Apply className to container
  * Add JSDoc comments with react-hook-form usage example
* Create ConfirmDialog component:
  * Create vulcanlab_ui/src/components/confirm-dialog.tsx
  * Add "use client" directive
  * Define ConfirmDialogProps interface (open, onOpenChange, title, message, confirmLabel, cancelLabel, variant, onConfirm)
  * Use existing Dialog primitives from vulcanlab_ui/src/components/ui/dialog.tsx
  * Render dialog with title and message
  * Render cancel and confirm buttons
  * Apply variant styling (danger = red, warning = yellow, info = blue)
  * Handle async onConfirm by showing loading state on confirm button
  * Close dialog after successful confirmation
  * Add JSDoc comments with useModal usage example
* Write component documentation:
  * Create form-field.md with react-hook-form integration example
  * Create confirm-dialog.md with useModal integration example and variant examples
* Write unit tests:
  * Test FormField renders label correctly
  * Test FormField shows required indicator when required is true
  * Test FormField renders children input element
  * Test FormField displays error message when error prop provided
  * Test FormField displays description when provided
  * Test FormField applies className
  * Test ConfirmDialog renders title and message
  * Test ConfirmDialog renders custom confirm/cancel button labels
  * Test ConfirmDialog calls onConfirm when confirm button clicked
  * Test ConfirmDialog calls onOpenChange(false) when cancel button clicked
  * Test ConfirmDialog shows loading state during async onConfirm
  * Test ConfirmDialog applies variant styling (danger, warning, info)
  * Test ConfirmDialog does not render when open is false
* Patterns to apply:
  * Frontend Stack - Next.js, TypeScript, TailwindCSS, Radix UI (Dialog, Label)
  * Component Organization - Components in vulcanlab_ui/src/components/
  * Forms - react-hook-form integration following shadcn/ui patterns
  * File Naming - kebab-case for component files
  * Composition - Build on existing Dialog and Label primitives
* Deviations (if any):
  * react-hook-form dependency - New dependency - Aligns with shadcn/ui form patterns, lightweight validation

## Unit tests (required)

* Add tests for:
  * FormField: renders label, shows required asterisk when required is true, renders children, displays error message in red when error provided, does not display error when error is undefined, displays description when provided, applies className
  * ConfirmDialog: renders title and message when open is true, does not render when open is false, renders default confirm/cancel labels, renders custom confirm/cancel labels when provided, calls onConfirm when confirm clicked, calls onOpenChange(false) when cancel clicked, shows loading spinner on confirm button during async operation, applies danger variant styling (red button), applies warning variant styling (yellow button), applies info variant styling (blue button)
* Suggested locations:
  * vulcanlab_ui/src/components/form-field.test.tsx
  * vulcanlab_ui/src/components/confirm-dialog.test.tsx
* Mocking/fakes needed:
  * Mock Dialog primitives for ConfirmDialog tests
  * Mock async onConfirm function (resolved and rejected promises)
  * Mock children input elements for FormField tests

## Acceptance criteria (checklist)

* [ ] FormField component implemented with TypeScript types and JSDoc
* [ ] FormField integrates with react-hook-form error display pattern
* [ ] FormField shows required indicator and error messages
* [ ] FormField uses existing Label component from ui/
* [ ] ConfirmDialog component implemented with TypeScript types and JSDoc
* [ ] ConfirmDialog supports variants (danger, warning, info)
* [ ] ConfirmDialog handles async onConfirm with loading state
* [ ] ConfirmDialog uses existing Dialog primitives from ui/
* [ ] Both components support className prop
* [ ] Both components have "use client" directive
* [ ] Markdown documentation created for both components
* [ ] Unit tests written with at least 80% coverage
* [ ] All tests pass
* [ ] TypeScript compilation passes with strict mode
* [ ] Components tested manually with react-hook-form and useModal hook

## Manual verification

* Steps:
  * Create test page with form using react-hook-form and FormField components
  * Add validation rules (required, pattern) to test error display
  * Submit form with invalid data to verify error messages appear
  * Create test page with ConfirmDialog using useModal hook
  * Test all three variants (danger, warning, info) for visual differences
  * Test with async onConfirm handler that takes 2 seconds to verify loading state
  * Test cancel button closes dialog without calling onConfirm
  * Toggle between light and dark themes
* Expected results:
  * FormField shows validation errors below input when validation fails
  * Required indicator (asterisk) appears next to label when required is true
  * Description text appears below label when provided
  * ConfirmDialog opens and closes correctly with useModal hook
  * Danger variant shows red confirm button
  * Warning variant shows yellow/amber confirm button
  * Info variant shows blue confirm button
  * Loading spinner appears on confirm button during async operation
  * Dialog closes after successful confirmation
  * Components render correctly in both themes

## Notes

* Requirements covered: R11, R12, R15, R16, R17, R18, R19, R20
* FormField is a wrapper component - actual input elements (Input, Select, etc.) are passed as children
* This pattern allows FormField to work with any input type from shadcn/ui
* ConfirmDialog can replace existing ConfirmDeleteModal after testing
* react-hook-form reference: https://ui.shadcn.com/docs/components/form
* Consider creating specialized delete confirmation dialog wrapper in future
* Test with keyboard navigation (Tab, Enter, Escape) for accessibility
* Error messages should not expose sensitive information (as per security requirements)
