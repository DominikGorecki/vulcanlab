import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { ManualResearchWizard } from "../ManualResearchWizard";
import { toast } from "@/hooks/use-toast";

// Mocking toast
jest.mock("@/hooks/use-toast", () => ({
  toast: jest.fn(),
}));

jest.mock("@/components/markdown-renderer", () => ({
  MarkdownRenderer: ({ content }: { content: string }) => <div data-testid="markdown-renderer">{content}</div>,
}));

// Mock Step components
jest.mock("../Step1Planning", () => ({
  Step1Planning: () => <div data-testid="step-1">Step 1 Planning</div>,
}));
jest.mock("../Step2ResultMatching", () => ({
  Step2ResultMatching: () => <div data-testid="step-2">Step 2 Result Matching</div>,
}));
jest.mock("../Step3ContextAssembly", () => ({
  Step3ContextAssembly: () => <div data-testid="step-3">Step 3 Context Assembly</div>,
}));
jest.mock("../Step4SectionGeneration", () => ({
  Step4SectionGeneration: () => <div data-testid="step-4">Step 4 Section Generation</div>,
}));
jest.mock("../Step5Synthesis", () => ({
  Step5Synthesis: () => <div data-testid="step-5">Step 5 Synthesis</div>,
}));
jest.mock("../Step6QualityEvaluation", () => ({
  Step6QualityEvaluation: () => <div data-testid="step-6">Step 6 Quality Evaluation</div>,
}));

describe("ManualResearchWizard Resume", () => {
  const collectionId = 1;
  const sessionId = 10;
  const onComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockFetch = (sessionData: any, sectionsData: any = { sections: [] }) => {
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url.endsWith(`/api/v1/research-sessions/${sessionId}`)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(sessionData),
        });
      }
      if (url.endsWith(`/api/v1/research-sessions/${sessionId}/sections`)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(sectionsData),
        });
      }
      if (url.includes(`/api/v1/research-sessions/${sessionId}`)) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      }
      return Promise.reject(new Error(`Unknown URL: ${url}`));
    }) as jest.Mock;
  };

  it("resumes at Step 1 when phase is planning", async () => {
    mockFetch({
      id: sessionId,
      current_phase: "planning",
    });

    render(<ManualResearchWizard collectionId={collectionId} sessionId={sessionId} onComplete={onComplete} />);

    await waitFor(() => {
      expect(screen.getByTestId("step-1")).toBeInTheDocument();
      expect(screen.getByText(/Step 1 of 6: Planning/i)).toBeInTheDocument();
    });
  });

  it("resumes at Step 2 when phase is research", async () => {
    mockFetch({
      id: sessionId,
      current_phase: "research",
      research_plan: { research_goal: "Goal", sub_questions: [{ id: "Q1", question: "Q1" }] },
    });

    render(<ManualResearchWizard collectionId={collectionId} sessionId={sessionId} onComplete={onComplete} />);

    await waitFor(() => {
      expect(screen.getByTestId("step-2")).toBeInTheDocument();
      expect(screen.getByText(/Step 2 of 6: Result Matching/i)).toBeInTheDocument();
    });
  });

  it("resumes at Step 3 when phase is context_assembly", async () => {
    mockFetch({
      id: sessionId,
      current_phase: "context_assembly",
      research_plan: { 
        research_goal: "Goal", 
        sub_questions: [
          { id: "Q1", question: "Q1" },
          { id: "Q2", question: "Q2" }
        ] 
      },
    }, {
      sections: [
        { question_id: "Q1", section_content: "Content 1" }
      ]
    });

    render(<ManualResearchWizard collectionId={collectionId} sessionId={sessionId} onComplete={onComplete} />);

    await waitFor(() => {
      expect(screen.getByTestId("step-3")).toBeInTheDocument();
      expect(screen.getByText(/Step 3 of 6: Context Assembly/i)).toBeInTheDocument();
    });
  });

  it("resumes at Step 5 when phase is synthesis", async () => {
    mockFetch({
      id: sessionId,
      current_phase: "synthesis",
      research_plan: { research_goal: "Goal", sub_questions: [{ id: "Q1", question: "Q1" }] },
    });

    render(<ManualResearchWizard collectionId={collectionId} sessionId={sessionId} onComplete={onComplete} />);

    await waitFor(() => {
      expect(screen.getByTestId("step-5")).toBeInTheDocument();
      expect(screen.getByText(/Step 5 of 6: Synthesis/i)).toBeInTheDocument();
    });
  });

  it("resumes at Step 6 when phase is evaluation", async () => {
    mockFetch({
      id: sessionId,
      current_phase: "evaluation",
      research_plan: { research_goal: "Goal", sub_questions: [{ id: "Q1", question: "Q1" }] },
    });

    render(<ManualResearchWizard collectionId={collectionId} sessionId={sessionId} onComplete={onComplete} />);

    await waitFor(() => {
      expect(screen.getByTestId("step-6")).toBeInTheDocument();
      expect(screen.getByText(/Step 6 of 6: Quality Evaluation/i)).toBeInTheDocument();
    });
  });
});
