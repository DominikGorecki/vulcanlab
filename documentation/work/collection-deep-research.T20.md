# Ticket: collection-deep-research.T20 - Manual Research Wizard (Steps 5-6: Synthesis and Quality Evaluation)

## Source

* Spec: documentation/work/collection-deep-research.spec.md
* Patterns: documentation/patterns.md

## Goal

* Implement final two steps of manual research wizard UI
* Enable user to generate final report (Step 5) and optionally evaluate quality (Step 6)
* Complete wizard workflow and mark session as completed

## Phase

* Frontend

## Scope

### In scope

* Step 5 (Synthesis): fetch sections button, copy synthesis prompt, paste report area, preview, save report action
* Step 6 (Quality Evaluation - Optional): copy quality eval prompt, paste evaluation, save or skip
* Completion UI: success message, link to view report on collection page
* Integration with API endpoints: GET /api/v1/research-sessions/{session_id}/sections, POST /api/v1/research-sessions/{session_id}/report

### Out of scope

* Steps 1-4 of wizard (covered in T18-T19)
* Report viewing on collection page (covered in T23)
* Automated research (covered in T22)

## Dependencies

* Depends on: T09 (report endpoint), T19 (wizard Steps 3-4)
* Unblocks: T23 (report viewing)

## Implementation plan

* Update ManualResearchWizard component:
  * Add state for final report: const [finalReport, setFinalReport] = useState<string>('')
  * Add state for quality evaluation: const [qualityEvaluation, setQualityEvaluation] = useState<any>(null)
* Create Step5Synthesis component:
  * "Fetch All Sections" button:
    * onClick: call GET /api/v1/research-sessions/{sessionId}/sections
    * Store sections in state
    * Copy synthesis prompt to clipboard:
      * Prompt includes: all section contents + original research goal from researchPlan
      * Format from T08 synthesis.txt template
      * Prompt specifies output: executive summary, introduction, integrate sections, cross-cutting insights, limitations, conclusions, references
    * Show toast: "Synthesis prompt copied to clipboard"
  * Text area for user to paste final report markdown
  * Markdown preview pane (same as Step 4, using react-markdown)
  * "Save Report" button:
    * onClick: call POST /api/v1/research-sessions/{sessionId}/report with:
      * {report_content: pasted markdown, executive_summary: extract first section, metadata: {total_words: count}}
    * Update finalReport state
    * Advance to Step 6 (or completion if user skips Step 6)
* Create Step6QualityEvaluation component:
  * Display message: "Quality Evaluation (Optional)"
  * "Evaluate Quality" button:
    * onClick: copy quality evaluation prompt to clipboard
    * Prompt includes: final report content
    * Format from T08 quality_evaluation.txt template
    * Show toast: "Quality evaluation prompt copied to clipboard"
  * Text area for user to paste evaluation JSON
  * "Save Evaluation" button:
    * onClick: parse JSON and update session via PUT /api/v1/research-sessions/{sessionId}
    * Store quality_evaluation in database
    * Advance to completion
  * "Skip" button:
    * onClick: advance to completion without evaluation (R14)
* Create CompletionStep component:
  * Success message: "Research report completed!"
  * Display report preview (first 200 chars)
  * Link to view report on collection page: "View full report"
  * "Start New Research" button → close wizard and reset
  * "Close" button → close wizard
* Patterns to apply:
  * **useCallback for API calls** - Wrap fetch calls in useCallback per patterns.md section 4.1
  * **Theme awareness** - Use semantic Tailwind classes per patterns.md section 4.2
  * **Component composition** - Build from smaller components per patterns.md section 4.2
* Deviations (if any):
  * None

## Unit tests (required)

* Add tests for:
  * Step5Synthesis "Fetch All Sections" calls sections endpoint
  * Step5Synthesis copies synthesis prompt to clipboard
  * Step5Synthesis text area accepts final report markdown
  * Step5Synthesis markdown preview renders report correctly
  * Step5Synthesis "Save Report" calls report endpoint with report_content
  * Step6QualityEvaluation "Evaluate Quality" copies prompt to clipboard
  * Step6QualityEvaluation "Save Evaluation" parses JSON and updates session
  * Step6QualityEvaluation "Skip" button advances to completion (R14)
  * CompletionStep displays success message and report preview
  * CompletionStep "View full report" link works
  * Wizard marks session as completed after Step 5 or 6
* Suggested locations:
  * tests/unit/components/research/test_ManualResearchWizard_Steps56.test.tsx
* Mocking/fakes needed:
  * Mock API calls (GET sections, POST report, PUT session)
  * Mock clipboard utility
  * Mock react-markdown

## Acceptance criteria (checklist)

* [ ] Step 5 "Fetch All Sections" calls sections endpoint (R4)
* [ ] Step 5 copies synthesis prompt to clipboard (R4)
* [ ] Step 5 text area accepts final report markdown (R4)
* [ ] Step 5 markdown preview renders full report (R11)
* [ ] Step 5 "Save Report" saves to research_reports table (R6, R13)
* [ ] Step 6 "Evaluate Quality" copies prompt to clipboard (R14)
* [ ] Step 6 is optional and skippable (R14)
* [ ] Step 6 "Skip" button advances to completion
* [ ] Completion UI displays success message and link to report
* [ ] Session status updated to 'completed' after report saved
* [ ] Unit tests pass for Steps 5-6 and completion

## Manual verification

* Steps:
  * Complete Steps 1-4 (all sections saved)
  * Advance to Step 5 (Synthesis)
  * Click "Fetch All Sections"
  * Verify API called, synthesis prompt copied to clipboard
  * Paste sample final report markdown (with executive summary, sections, synthesis, conclusions, references)
  * Verify markdown preview renders full report correctly
  * Click "Save Report"
  * Verify API called, report saved
  * Advance to Step 6 (Quality Evaluation)
  * Click "Evaluate Quality"
  * Verify quality eval prompt copied
  * Paste sample evaluation JSON
  * Click "Save Evaluation"
  * Verify advances to completion
  * Test "Skip" button flow:
    * Complete Steps 1-5
    * In Step 6, click "Skip"
    * Verify advances to completion without evaluation
  * Verify completion UI displays success message
  * Click "View full report" link
  * Verify navigates to collection page with report displayed (to be tested in T23)
* Expected results:
  * Synthesis works correctly
  * Quality evaluation optional and skippable
  * Report saved to database
  * Completion UI displays correctly

## Notes

* Requirements covered: R3 (manual wizard Steps 5-6), R4 (copy prompts, paste responses, save report), R13 (final report structure), R14 (quality evaluation optional)
* Step 5 creates final report per R13: executive summary, introduction, findings, synthesis, limitations, conclusions, references
* Step 6 optional per R14 - user can skip quality evaluation
* Report saved to research_reports table per T03 create_research_report (also marks session completed)
* Completion step provides closure and link to view report on collection page
