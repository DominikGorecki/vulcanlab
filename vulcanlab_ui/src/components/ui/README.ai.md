# ui (AI README)

## Purpose
- Provides a library of reusable UI components built on Radix UI primitives and styled with Tailwind CSS
- Follows shadcn/ui patterns with consistent styling, accessibility, and composability
- Serves as the foundation for all UI elements in the VulcanLab frontend application

## Quick start
- Import components directly: `import { Button } from "@/components/ui/button"`
- Components are ready to use with TypeScript types and default styling
- No build step required - components are TypeScript/React files that compile with Next.js
- Run `npm run dev` in the parent project to see components in action
- Lint with `npm run lint` (uses ESLint with Next.js config)

## Architecture overview
- **Component pattern**: Each component wraps Radix UI primitives with Tailwind CSS styling
- **Styling system**: Uses `cn()` utility (clsx + tailwind-merge) for className merging and conditional classes
- **Variant system**: Components with variants use `class-variance-authority` (CVA) for type-safe variant props
- **Data attributes**: All components use `data-slot` attributes for CSS targeting and styling hooks
- **Composition**: Components export multiple sub-components (e.g., Card exports CardHeader, CardContent, CardFooter)
- **Accessibility**: Inherits accessibility features from Radix UI primitives (ARIA attributes, keyboard navigation, focus management)
- **Dark mode**: Components support dark mode via Tailwind's dark mode classes and CSS variables
- Key folders:
  - `ui/` - All component files are flat in this directory (no subfolders)

## Entry points and main flows
- Entry points:
  - `button.tsx` - Most commonly used component, demonstrates variant system with CVA
  - `card.tsx` - Shows composition pattern with multiple exported sub-components
  - `dialog.tsx` - Complex component with portal rendering and overlay
  - `toast.tsx` + `toaster.tsx` - Toast notification system (toast.tsx defines primitives, toaster.tsx provides React hook integration)
- Typical flows:
  - **Component usage**: Import → Use with props → Customize with className prop
  - **Variant customization**: Pass variant/size props → CVA applies appropriate classes → Can override with className
  - **Composition**: Import parent component → Use sub-components together → Style with Tailwind classes
  - **Form integration**: Use Input, Label, Select, Switch with form libraries → Components handle focus states and validation styling

## Key conventions
- **Naming**: Component files use kebab-case (e.g., `alert-dialog.tsx`), exports use PascalCase
- **Styling**: Always use `cn()` utility for className merging, never direct string concatenation
- **Data attributes**: Every component root element has a `data-slot` attribute matching component name (e.g., `data-slot="button"`)
- **TypeScript**: Components extend `React.ComponentProps<"element">` or Radix primitive props for type safety
- **Client components**: Some components include `"use client"` directive (required for Next.js client components with interactivity)
- **Exports**: Components export both the component and variant functions/types when applicable (e.g., `Button` and `buttonVariants`)
- **Props forwarding**: Use spread operator (`{...props}`) to forward all HTML attributes to underlying elements
- **Accessibility**: Preserve Radix UI's built-in accessibility features; don't override ARIA attributes unnecessarily

## Dependencies overview
- Runtime dependencies:
  - `@radix-ui/*` - Headless UI primitives (accordion, alert-dialog, dialog, label, scroll-area, select, slider, slot, switch, tabs, toast, tooltip)
  - `class-variance-authority` - Type-safe variant system for component styling
  - `clsx` - Conditional className utility
  - `tailwind-merge` - Intelligently merges Tailwind classes (via `cn` utility)
  - `lucide-react` - Icon library used in some components (ChevronDownIcon, XIcon, CheckIcon, etc.)
  - `react` + `react-dom` - React framework
- Dev dependencies and tooling:
  - `typescript` - Type checking
  - `tailwindcss` - CSS framework
  - `eslint` + `eslint-config-next` - Linting
- External services: None (pure UI components, no API calls)

## APIs and contracts
- **Component exports**: Each file exports one or more React components as named exports
- **Variant props**: Components with variants accept `VariantProps<typeof variantFunction>` for type-safe variant selection
- **Style customization**: All components accept `className?: string` prop for additional styling
- **Props forwarding**: Components forward all valid HTML/React props to underlying elements
- **Data models**: No data models - these are presentational components
- **Events**: Components emit standard React events (onClick, onChange, etc.) through prop forwarding
- Key component APIs:
  - `button.tsx`: Exports `Button` component and `buttonVariants` function; accepts `variant`, `size`, `asChild` props
  - `card.tsx`: Exports Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter, CardAction
  - `dialog.tsx`: Exports Dialog, DialogTrigger, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription, DialogClose, DialogOverlay, DialogPortal
  - `select.tsx`: Exports Select, SelectTrigger, SelectValue, SelectContent, SelectItem, SelectLabel, SelectGroup, SelectSeparator, SelectScrollUpButton, SelectScrollDownButton
  - `toast.tsx`: Exports Toast, ToastProvider, ToastViewport, ToastTitle, ToastDescription, ToastClose, ToastAction; also exports TypeScript types `ToastProps` and `ToastActionElement`

## Subfolders
No subfolders present in this directory.

## File tree (depth 3)
```
ui/
├── accordion.tsx
├── alert-dialog.tsx
├── alert.tsx
├── badge.tsx
├── button.tsx
├── card.tsx
├── dialog.tsx
├── input.tsx
├── label.tsx
├── scroll-area.tsx
├── select.tsx
├── slider.tsx
├── switch.tsx
├── table.tsx
├── tabs.tsx
├── textarea.tsx
├── toast.tsx
├── toaster.tsx
└── tooltip.tsx
```

## LLM handoff
- When asking an LLM to work in this folder, include:
  - `button.tsx` - Reference implementation for variant system and CVA usage
  - `card.tsx` - Example of component composition pattern
  - `dialog.tsx` - Complex component with portal and overlay patterns
  - `select.tsx` - Multi-part component with many sub-components
  - `toast.tsx` - Forward ref patterns and variant system
  - `@/lib/utils` - The `cn` utility function (critical for all styling)
  - `components.json` - shadcn/ui configuration showing project setup
  - `package.json` - Dependency versions and Radix UI packages used
- Good first questions to ask:
  - "How do I add a new variant to an existing component?"
  - "What's the pattern for creating a new composite component like Card?"
  - "How do I ensure a component works with dark mode?"
  - "What's the correct way to style a component without breaking its variants?"
  - "How do I add a new Radix UI primitive-based component?"
  - "What's the difference between components that need 'use client' and those that don't?"
- Guardrails:
  - **Never remove `data-slot` attributes** - They're used for CSS targeting throughout the app
  - **Always use `cn()` utility** - Never use template literals or string concatenation for className
  - **Preserve Radix UI props** - Don't break prop forwarding to underlying Radix primitives
  - **Maintain TypeScript types** - Keep `VariantProps` and `React.ComponentProps` types accurate
  - **Test accessibility** - Verify keyboard navigation and screen reader compatibility after changes
  - **Run linting** - Use `npm run lint` before committing changes
  - **Follow existing patterns** - Match the structure and naming conventions of existing components

## Gotchas
- Some components have `"use client"` directive and some don't - this depends on whether they use React hooks or browser APIs (check existing components to determine pattern)
- The `cn()` utility is critical - importing it incorrectly or using wrong path (`@/lib/utils`) will break all components
- `data-slot` attributes are not just for debugging - they're actively used in CSS selectors, so changing them breaks styling
- Components that wrap Radix primitives must preserve the primitive's prop types - don't narrow the prop types unnecessarily
- The `asChild` prop pattern (from Radix Slot) allows composition but requires careful prop forwarding - see Button component for reference
- Dark mode classes use Tailwind's `dark:` prefix and CSS variables - ensure new components follow this pattern for consistency

