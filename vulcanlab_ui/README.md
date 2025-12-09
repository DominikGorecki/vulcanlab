# VulcanLab UI

Frontend for the VulcanLab system, built with Next.js, Tailwind CSS, and shadcn/ui.

## Development Rules

**CRITICAL**: This project exclusively uses Client Components.
- ALL files in `src/components` and `src/app` (except layout/page wrappers if strictly necessary) MUST start with `"use client";`.
- We are avoiding Server Components for this initial implementation to simplify state management and interactivity.

## Setup

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

## Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **Icons**: Lucide React
- **Markdown**: react-markdown + remark-gfm

## Project Structure

```
vulcanlab_ui/
├── src/
│   ├── app/            # Next.js App Router pages
│   ├── components/     # React components ("use client" required)
│   │   ├── ui/         # shadcn/ui components
│   │   └── ...
│   ├── lib/            # Utilities
│   └── styles/         # Global styles
├── public/             # Static assets
└── ...
```
