# Ticket: ui-component-standardization.T05 - Stats Display Components

## Source

* Spec: documentation/work/ui-component-standardization.spec.md
* Patterns: documentation/patterns.md

## Goal

* Create StatsCard and StatsCardGrid components for displaying metrics
* Enable standardized metric displays across dashboard and summary pages
* Support optional icons and trend indicators

## Scope

### In scope

* Implement StatsCard component with label, value, optional icon, and optional trend
* Implement StatsCardGrid component with responsive grid layout
* Both components support className prop
* TypeScript prop interfaces with JSDoc comments
* Unit tests for both components
* Markdown documentation for both components

### Out of scope

* Real-time updating of stats
* Animated trend indicators
* Sparkline charts or mini graphs
* Custom trend calculation logic
* Click handlers or navigation from stats cards

## Dependencies

* Depends on: none (uses existing shadcn/ui Card primitive)
* Unblocks: Dashboard and summary page implementations

## Implementation plan

* Create StatsCard component:
  * Create vulcanlab_ui/src/components/stats-card.tsx
  * Add "use client" directive
  * Define StatsCardProps interface (label, value required, icon, trend, className optional)
  * Define trend object shape (value number, direction 'up' | 'down')
  * Use existing Card component from vulcanlab_ui/src/components/ui/card.tsx
  * Render card with label as subtitle, value as large prominent text
  * Render optional icon in top-right corner
  * Render optional trend with up/down arrow indicator and color (green for up, red for down)
  * Apply className to card container
  * Add JSDoc comments with usage example
* Create StatsCardGrid component:
  * Create vulcanlab_ui/src/components/stats-card-grid.tsx
  * Add "use client" directive
  * Define StatsCardGridProps interface (stats array required, className optional)
  * Stats array contains objects with StatsCardProps shape
  * Render responsive grid container (3 columns desktop, 2 columns tablet, 1 column mobile)
  * Map over stats array and render StatsCard for each item
  * Apply className to grid container
  * Add JSDoc comments with usage example
* Write component documentation:
  * Create stats-card.md with usage example showing card with icon and trend
  * Create stats-card-grid.md with usage example showing grid with multiple stats
* Write unit tests:
  * Test StatsCard renders label and value
  * Test StatsCard renders icon when provided
  * Test StatsCard renders trend indicator when provided
  * Test StatsCard trend shows correct color and arrow for up/down direction
  * Test StatsCard applies className
  * Test StatsCardGrid renders correct number of cards
  * Test StatsCardGrid applies responsive grid classes
  * Test StatsCardGrid applies className
  * Test StatsCardGrid handles empty array gracefully
* Patterns to apply:
  * Frontend Stack - Next.js, TypeScript, TailwindCSS, Radix UI (Card)
  * Component Organization - Components in vulcanlab_ui/src/components/
  * Styling - TailwindCSS responsive grid utilities
  * File Naming - kebab-case for component files
  * Composition - Build on existing Card primitive
* Deviations (if any):
  * None - fully compliant with patterns.md

## Unit tests (required)

* Add tests for:
  * StatsCard: renders label, renders value (string and number types), renders icon when provided, renders trend when provided, trend shows up arrow for 'up' direction, trend shows down arrow for 'down' direction, trend applies green color for up, trend applies red color for down, applies className
  * StatsCardGrid: renders correct number of StatsCard components, applies grid layout classes, applies className, handles empty stats array, passes props correctly to each StatsCard
* Suggested locations:
  * vulcanlab_ui/src/components/stats-card.test.tsx
  * vulcanlab_ui/src/components/stats-card-grid.test.tsx
* Mocking/fakes needed:
  * Mock icon components for StatsCard tests
  * Mock stats data array for StatsCardGrid tests

## Acceptance criteria (checklist)

* [ ] StatsCard component implemented with TypeScript types and JSDoc
* [ ] StatsCard supports label, value, optional icon, and optional trend
* [ ] StatsCard uses existing Card component from ui/
* [ ] StatsCard trend indicator shows correct color and arrow direction
* [ ] StatsCardGrid component implemented with TypeScript types and JSDoc
* [ ] StatsCardGrid renders cards in responsive grid (3/2/1 columns)
* [ ] Both components support className prop
* [ ] Both components have "use client" directive
* [ ] Markdown documentation created for both components
* [ ] Unit tests written with at least 80% coverage
* [ ] All tests pass
* [ ] TypeScript compilation passes with strict mode
* [ ] Components tested manually on mobile, tablet, desktop viewports

## Manual verification

* Steps:
  * Create test page with single StatsCard showing label and value only
  * Create test page with StatsCard showing icon and trend (both up and down)
  * Create test page with StatsCardGrid showing 3-6 stats cards
  * Resize browser to verify responsive grid (3 columns on desktop, 2 on tablet, 1 on mobile)
  * Toggle between light and dark themes
  * Verify trend colors (green for up, red for down)
* Expected results:
  * StatsCard displays large, prominent value with smaller label
  * Icon appears in top-right corner when provided
  * Trend shows correct arrow direction and color
  * StatsCardGrid arranges cards in responsive grid layout
  * Grid adapts correctly to different viewport sizes
  * Cards render correctly in both light and dark themes
  * Cards have proper spacing and visual hierarchy

## Notes

* Requirements covered: R7, R8, R16, R17, R18, R19, R20
* StatsCard and StatsCardGrid will be used on dashboard pages and summary sections
* Trend value could be percentage or absolute number - component should handle both
* Consider adding loading skeleton variant for StatsCard in future iteration
* Grid layout should use TailwindCSS grid utilities (grid-cols-1 md:grid-cols-2 lg:grid-cols-3)
* Test with various value formats (numbers, percentages, abbreviated numbers like "1.2K")
* Icon should not be too large - keep it subtle in corner
