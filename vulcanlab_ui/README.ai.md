# vulcanlab_ui (AI README)

## Purpose

* Frontend web interface for the VulcanLab document processing and RAG (Retrieval-Augmented Generation) system
* Built with Next.js 16 App Router providing a modern, reactive UI for managing document corpus, conversions, sanitization, chunking, vectorization, and RAG queries
* Communicates with the VulcanLab backend API for all data operations and processing workflows
* Provides both simplified and advanced modes for different user expertise levels

## Quick start

* Install dependencies: `npm install`
* Run development server: `npm run dev` (starts on http://localhost:3000)
* Build for production: `npm run build`
* Run linter: `npm run lint`
* Backend API must be running (defaults to http://localhost:8000)

## Architecture overview

* Next.js 16 App Router with React 19 and TypeScript in strict mode
* Client-side heavy architecture - most components use "use client" directive for interactivity
* Tailwind CSS v4 for styling with shadcn/ui component library built on Radix UI primitives
* Monaco Editor integration for code/markdown editing
* Context-based state management for conversion settings and theme (next-themes)
* Route-based navigation with dynamic routes for resource IDs
* Toast notifications for user feedback (Radix UI Toast)
* Key folders:
  * src/app - Next.js App Router pages and routes
  * src/components - Reusable React components (UI primitives, feature components, shared utilities)
  * src/contexts - React context providers for global state
  * src/hooks - Custom React hooks
  * src/lib - Utility functions and helpers
  * src/types - TypeScript type definitions
  * public - Static assets (images, favicons)

## Entry points and main flows

* Entry points:
  * src/app/layout.tsx - Root layout with navigation, theme provider, and toast notifications
  * src/app/page.tsx - Home page (redirects to /corpus)
  * src/components/nav-bar.tsx - Main navigation sidebar with conditional advanced mode items
  * src/components/providers.tsx - Wraps app with theme and settings providers

* Typical flows:
  * RAG Query Flow: /rag -> select config -> enter query -> /rag/[id] -> view results -> /rag/[id]/results/[resultId] for details
  * Simple Conversion: /simple-conversion -> choose manual/automatic/history -> /simple-conversion/{mode}/[work_id] -> convert EPUB to markdown
  * Corpus Management: /corpus -> view works -> /corpus/[id] -> inspect work details and metadata
  * Markdown Import/Export: /markdown/export (export) or /markdown/import (import) -> upload/download markdown files
  * Advanced Pipeline (when enabled): /conv -> /sanitization -> /chunk -> /vec for full document processing workflow
  * Settings: /settings -> configure RAG parameters, templates, and advanced mode toggle

## Key conventions

* All components in src/components and most in src/app use "use client" directive (client-side rendering)
* File naming: kebab-case for files (markdown-editor.tsx), PascalCase for component names (MarkdownEditor)
* Path alias: @/* maps to src/* (configured in tsconfig.json)
* Dynamic routes use [param] folder notation: [id], [work_id], [function_tag], [resultId]
* API calls go to backend at http://localhost:8000 (configurable via environment)
* TypeScript strict mode enabled - all props and state must be typed
* Testing: Jest with React Testing Library, tests in __tests__ folders
* Styling: Tailwind utility classes with cn() helper for conditional classes
* Component library: shadcn/ui components in src/components/ui

## Dependencies overview

* Runtime dependencies:
  * next@16.0.4 - React framework with App Router
  * react@19.2.0, react-dom@19.2.0 - UI library
  * @radix-ui/* - Headless UI primitives (dialog, select, tabs, toast, etc.)
  * @monaco-editor/react@4.7.0 - Code editor component
  * react-markdown@10.1.0 + remark-gfm@4.0.1 - Markdown rendering with GitHub Flavored Markdown
  * lucide-react@0.554.0 - Icon library
  * next-themes@0.4.6 - Dark/light theme management
  * tailwind-merge@3.4.0 + clsx@2.1.1 - Utility class merging
  * class-variance-authority@0.7.1 - Component variant styling

* Dev dependencies and tooling:
  * typescript@5 - Type checking
  * eslint@9 + eslint-config-next@16.0.4 - Linting
  * tailwindcss@4 + @tailwindcss/typography@0.5.15 - CSS framework
  * @types/* - TypeScript type definitions

* External services:
  * VulcanLab Backend API (http://localhost:8000) - All data persistence and processing operations
  * Backend provides endpoints for corpus, conversions, sanitization, chunking, vectorization, and RAG queries

## APIs and contracts

* Frontend communicates with backend via REST API:
  * GET /api/corpus - List works
  * GET /api/corpus/{id} - Get work details
  * POST /api/rag - Create RAG query
  * GET /api/rag/{id} - Get RAG results
  * POST /api/simple-conversion - Start conversion
  * GET /api/settings/rag-configs - Get RAG configurations
  * PUT /api/settings/rag-configs/{id} - Update RAG config
  * POST /api/markdown/export - Export markdown
  * POST /api/markdown/import - Import markdown

* Internal component contracts:
  * Context providers: ConversionSettingsProvider exports useConversionSettings hook
  * Theme provider: Wraps app for dark/light mode switching
  * Toast notifications: useToast hook from src/hooks/use-toast.ts
  * Utility functions: cn() from src/lib/utils.ts for className merging

* Type definitions:
  * src/types/rag-config.ts - RAG configuration types matching backend Pydantic schemas
  * Type-safe API responses expected throughout

## Subfolders

* public: Static assets including favicons, logos, and images served directly by Next.js
* src: Main source code directory containing all application logic, components, and configuration

## File tree (depth 5)

.
./README.md
./components.json
./eslint.config.mjs
./next-env.d.ts
./next.config.ts
./package-lock.json
./package.json
./postcss.config.mjs
./public
./public/README.ai.md
./public/android-chrome-192x192.png
./public/android-chrome-512x512.png
./public/apple-touch-icon.png
./public/favicon-16x16.png
./public/favicon-32x32.png
./public/favicon.ico
./public/favicon.png
./public/file.svg
./public/globe.svg
./public/logo-sm.png
./public/logo.png
./public/next.svg
./public/vercel.svg
./public/window.svg
./src
./src/README.ai.md
./src/app
./src/app/README.ai.md
./src/app/chunk
./src/app/chunk/README.ai.md
./src/app/chunk/[id]
./src/app/chunk/[id]/README.ai.md
./src/app/chunk/[id]/gen-vec-sugg
./src/app/chunk/[id]/gen-vec-sugg/README.ai.md
./src/app/chunk/[id]/gen-vec-sugg/page.tsx
./src/app/chunk/[id]/page.tsx
./src/app/chunk/[id]/san-titles
./src/app/chunk/[id]/san-titles/README.ai.md
./src/app/chunk/[id]/san-titles/page.tsx
./src/app/chunk/[id]/sanitized
./src/app/chunk/[id]/sanitized/README.ai.md
./src/app/chunk/[id]/sanitized/page.tsx
./src/app/chunk/[id]/vec-suggestions
./src/app/chunk/[id]/vec-suggestions/README.ai.md
./src/app/chunk/[id]/vec-suggestions/page.tsx
./src/app/chunk/page.tsx
./src/app/cleanup
./src/app/cleanup/README.ai.md
./src/app/cleanup/page.tsx
./src/app/conv
./src/app/conv/README.ai.md
./src/app/conv/[id]
./src/app/conv/[id]/README.ai.md
./src/app/conv/[id]/add
./src/app/conv/[id]/add/README.ai.md
./src/app/conv/[id]/add/page.tsx
./src/app/conv/[id]/inspect_original_md
./src/app/conv/[id]/inspect_original_md/README.ai.md
./src/app/conv/[id]/inspect_original_md/page.tsx
./src/app/conv/[id]/inspect_style_hier
./src/app/conv/[id]/inspect_style_hier/README.ai.md
./src/app/conv/[id]/inspect_style_hier/page.tsx
./src/app/conv/[id]/inspect_toc_titles
./src/app/conv/[id]/inspect_toc_titles/README.ai.md
./src/app/conv/[id]/inspect_toc_titles/page.tsx
./src/app/conv/[id]/page.tsx
./src/app/conv/page.tsx
./src/app/corpus
./src/app/corpus/README.ai.md
./src/app/corpus/[id]
./src/app/corpus/[id]/README.ai.md
./src/app/corpus/[id]/page.tsx
./src/app/corpus/__tests__
./src/app/corpus/__tests__/README.ai.md
./src/app/corpus/__tests__/page.test.tsx
./src/app/corpus/page.tsx
./src/app/favicon.ico
./src/app/globals.css
./src/app/init
./src/app/init/README.ai.md
./src/app/init/page.tsx
./src/app/layout.tsx
./src/app/markdown
./src/app/markdown/README.ai.md
./src/app/markdown/export
./src/app/markdown/export/README.ai.md
./src/app/markdown/export/__tests__
./src/app/markdown/export/__tests__/README.ai.md
./src/app/markdown/export/__tests__/page.test.tsx
./src/app/markdown/export/page.tsx
./src/app/markdown/import
./src/app/markdown/import/README.ai.md
./src/app/markdown/import/__tests__
./src/app/markdown/import/__tests__/README.ai.md
./src/app/markdown/import/__tests__/page.test.tsx
./src/app/markdown/import/page.tsx
./src/app/markdown/layout.tsx
./src/app/page.tsx
./src/app/rag
./src/app/rag/README.ai.md
./src/app/rag/[id]
./src/app/rag/[id]/README.ai.md
./src/app/rag/[id]/inspect
./src/app/rag/[id]/inspect/README.ai.md
./src/app/rag/[id]/inspect/page.tsx
./src/app/rag/[id]/page.tsx
./src/app/rag/[id]/results
./src/app/rag/[id]/results/README.ai.md
./src/app/rag/[id]/results/[resultId]
./src/app/rag/[id]/results/[resultId]/page.tsx
./src/app/rag/[id]/results/page.tsx
./src/app/rag/auto
./src/app/rag/auto/README.ai.md
./src/app/rag/auto/page.tsx
./src/app/rag/new
./src/app/rag/new/README.ai.md
./src/app/rag/new/page.tsx
./src/app/rag/page.tsx
./src/app/sanitization
./src/app/sanitization/README.ai.md
./src/app/sanitization/[id]
./src/app/sanitization/[id]/README.ai.md
./src/app/sanitization/[id]/gen-title-changes
./src/app/sanitization/[id]/gen-title-changes/README.ai.md
./src/app/sanitization/[id]/gen-title-changes/page.tsx
./src/app/sanitization/[id]/page.tsx
./src/app/sanitization/[id]/title-changes
./src/app/sanitization/[id]/title-changes/README.ai.md
./src/app/sanitization/[id]/title-changes/page.tsx
./src/app/sanitization/[id]/titles
./src/app/sanitization/[id]/titles/README.ai.md
./src/app/sanitization/[id]/titles/page.tsx
./src/app/sanitization/add
./src/app/sanitization/add/README.ai.md
./src/app/sanitization/add/page.tsx
./src/app/sanitization/page.tsx
./src/app/settings
./src/app/settings/README.ai.md
./src/app/settings/page.tsx
./src/app/settings/templates
./src/app/settings/templates/README.ai.md
./src/app/settings/templates/[function_tag]
./src/app/settings/templates/[function_tag]/README.ai.md
./src/app/settings/templates/[function_tag]/page.tsx
./src/app/simple-conversion
./src/app/simple-conversion/README.ai.md
./src/app/simple-conversion/__tests__
./src/app/simple-conversion/__tests__/README.ai.md
./src/app/simple-conversion/__tests__/page.test.tsx
./src/app/simple-conversion/automatic
./src/app/simple-conversion/automatic/README.ai.md
./src/app/simple-conversion/automatic/[work_id]
./src/app/simple-conversion/automatic/[work_id]/README.ai.md
./src/app/simple-conversion/automatic/[work_id]/__tests__
./src/app/simple-conversion/automatic/[work_id]/__tests__/page.test.tsx
./src/app/simple-conversion/automatic/[work_id]/page.tsx
./src/app/simple-conversion/history
./src/app/simple-conversion/history/README.ai.md
./src/app/simple-conversion/history/[work_id]
./src/app/simple-conversion/history/[work_id]/README.ai.md
./src/app/simple-conversion/history/[work_id]/__tests__
./src/app/simple-conversion/history/[work_id]/__tests__/page.test.tsx
./src/app/simple-conversion/history/[work_id]/page.tsx
./src/app/simple-conversion/manual
./src/app/simple-conversion/manual/README.ai.md
./src/app/simple-conversion/manual/[work_id]
./src/app/simple-conversion/manual/[work_id]/README.ai.md
./src/app/simple-conversion/manual/[work_id]/__tests__
./src/app/simple-conversion/manual/[work_id]/__tests__/page.test.tsx
./src/app/simple-conversion/manual/[work_id]/page.tsx
./src/app/simple-conversion/page.tsx
./src/app/vec
./src/app/vec/README.ai.md
./src/app/vec/page.tsx
./src/components
./src/components/ConfirmDeleteModal.tsx
./src/components/ErrorModal.tsx
./src/components/README.ai.md
./src/components/__tests__
./src/components/__tests__/README.ai.md
./src/components/__tests__/nav-bar.test.tsx
./src/components/markdown
./src/components/markdown/README.ai.md
./src/components/markdown/__tests__
./src/components/markdown/__tests__/MarkdownComparisonView.test.tsx
./src/components/markdown/__tests__/README.ai.md
./src/components/markdown/markdown-comparison-view.tsx
./src/components/markdown-editor.tsx
./src/components/markdown-renderer.tsx
./src/components/markdown-sticky-viewer.tsx
./src/components/nav-bar.tsx
./src/components/providers.tsx
./src/components/rag
./src/components/rag/README.ai.md
./src/components/rag/rag-settings-form.tsx
./src/components/settings
./src/components/settings/ConversionSettings.tsx
./src/components/settings/README.ai.md
./src/components/settings/RagConfigForm.tsx
./src/components/settings/RagConfigList.tsx
./src/components/settings/__tests__
./src/components/settings/__tests__/ConversionSettings.test.tsx
./src/components/settings/__tests__/README.ai.md
./src/components/simple-conversion
./src/components/simple-conversion/ConversionStatus.tsx
./src/components/simple-conversion/README.ai.md
./src/components/simple-conversion/__tests__
./src/components/simple-conversion/__tests__/ConversionStatus.test.tsx
./src/components/simple-conversion/__tests__/README.ai.md
./src/components/text-stats.tsx
./src/components/titles-viewer.tsx
./src/components/ui
./src/components/ui/README.ai.md
./src/components/ui/accordion.tsx
./src/components/ui/alert-dialog.tsx
./src/components/ui/button.tsx
./src/components/ui/card.tsx
./src/components/ui/checkbox.tsx
./src/components/ui/dialog.tsx
./src/components/ui/input.tsx
./src/components/ui/label.tsx
./src/components/ui/scroll-area.tsx
./src/components/ui/select.tsx
./src/components/ui/slider.tsx
./src/components/ui/switch.tsx
./src/components/ui/tabs.tsx
./src/components/ui/toast.tsx
./src/components/ui/toaster.tsx
./src/components/ui/tooltip.tsx
./src/contexts
./src/contexts/README.ai.md
./src/contexts/__tests__
./src/contexts/__tests__/README.ai.md
./src/contexts/__tests__/conversion-settings.test.tsx
./src/contexts/conversion-settings.tsx
./src/hooks
./src/hooks/README.ai.md
./src/hooks/use-toast.ts
./src/lib
./src/lib/README.ai.md
./src/lib/utils.ts
./src/types
./src/types/README.ai.md
./src/types/rag-config.ts
./tsconfig.json

## LLM handoff

* When asking an LLM to work in this folder, include:
  * This README.ai.md for project overview
  * package.json for dependencies and scripts
  * tsconfig.json for TypeScript configuration
  * src/app/layout.tsx for app structure
  * src/components/nav-bar.tsx for navigation understanding
  * src/types/rag-config.ts for key type definitions
  * Relevant subfolder README.ai.md files for specific features
  * README.md for development rules (client component requirement)

* Good first questions to ask:
  * How does the RAG query flow work from UI to backend?
  * What is the purpose of the advanced mode setting and how does it affect navigation?
  * How are markdown files converted in the simple conversion flow?
  * What are the main React contexts and what state do they manage?
  * How is the component library (shadcn/ui) integrated and where are components defined?
  * What testing strategy is used and where are test files located?
  * How does the app communicate with the backend API?
  * What is the routing structure and which routes are dynamic?
  * How is theming implemented (dark/light mode)?
  * What are the key TypeScript types and interfaces?

* Guardrails:
  * ALL components must use "use client" directive (project policy)
  * Maintain TypeScript strict mode - no any types without justification
  * Use cn() utility for className merging, never string concatenation
  * Follow Next.js App Router conventions (page.tsx, layout.tsx, route.ts naming)
  * Use Radix UI + shadcn/ui components, avoid custom implementations
  * Keep components in appropriate folders (ui/ for primitives, feature folders for domain components)
  * Run `npm run lint` before committing
  * Run `npm run build` to verify no type errors
  * Test new features with Jest + React Testing Library
  * Never commit node_modules or .next directories

## Gotchas

* This project uses client components exclusively - all files need "use client" at the top
* Next.js 16 App Router has different conventions than Pages Router - use page.tsx not index.tsx
* Dynamic routes use folder names like [id] not :id
* Monaco Editor is heavy - it lazy loads and may cause initial render delays
* Backend API must be running on http://localhost:8000 or frontend will show connection errors
* Tailwind CSS v4 is different from v3 - some plugin syntax has changed
