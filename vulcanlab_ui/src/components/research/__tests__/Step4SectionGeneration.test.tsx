import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Step4SectionGeneration } from "../Step4SectionGeneration";
import { ResearchPlan } from "@/types/research";
import { toast } from "@/hooks/use-toast";

jest.mock("@/hooks/use-toast", () => ({
  toast: jest.fn(),
}));

// Mock MarkdownRenderer to avoid rendering issues in tests
jest.mock("@/components/markdown-renderer", () => ({
  MarkdownRenderer: ({ content }: { content: string }) => <div data-testid="markdown-preview">{content}</div>,
}));

describe("Step4SectionGeneration", () => {
  const sessionId = 10;
  const researchPlan: ResearchPlan = {
    research_goal: "Test Goal",
    key_themes: ["Theme 1"],
    sub_questions: [
      {
        id: "Q1",
        question: "What is X?",
        rationale: "Rationale for X",
        estimated_tokens: 1000,
        relevant_items: [1, 2],
      },
      {
        id: "Q2",
        question: "What is Y?",
        rationale: "Rationale for Y",
        estimated_tokens: 1000,
        relevant_items: [3, 4],
      },
    ],
    synthesis_approach: "Standard",
  };
  const contextData = {
    Q1: { context: "Context Q1", token_count: 100, sources: [] }
  };
  const sections = {};
  const setSections = jest.fn();
  const onSaveAndNext = jest.fn();
  const onBack = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url === `/api/v1/research-sessions/${sessionId}/sections`) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        });
      }
      return Promise.reject(new Error("Unknown URL"));
    }) as jest.Mock;
  });

  it("renders textarea and accepts input", () => {
    render(
      <Step4SectionGeneration
        sessionId={sessionId}
        researchPlan={researchPlan}
        currentSectionIndex={0}
        contextData={contextData}
        sections={sections}
        setSections={setSections}
        onSaveAndNext={onSaveAndNext}
        onBack={onBack}
      />
    );

    const textarea = screen.getByPlaceholderText(/Paste the LLM-generated markdown content here/i);
    fireEvent.change(textarea, { target: { value: "Test markdown content with [S1] citation." } });

    expect(textarea).toHaveValue("Test markdown content with [S1] citation.");
    expect(screen.getByText("6 words")).toBeInTheDocument();
    expect(screen.getByText("1 citations")).toBeInTheDocument();
  });

  it("renders markdown preview when tab clicked", async () => {
    render(
      <Step4SectionGeneration
        sessionId={sessionId}
        researchPlan={researchPlan}
        currentSectionIndex={0}
        contextData={contextData}
        sections={sections}
        setSections={setSections}
        onSaveAndNext={onSaveAndNext}
        onBack={onBack}
      />
    );

    const textarea = screen.getByPlaceholderText(/Paste the LLM-generated markdown content here/i);
    fireEvent.change(textarea, { target: { value: "# Heading\nSome content" } });

    const previewTab = screen.getByRole("tab", { name: /markdown preview/i });
    fireEvent.click(previewTab);
    fireEvent.keyDown(previewTab, { key: " ", code: "Space" });

    await waitFor(() => {
      expect(screen.getByTestId("markdown-preview")).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it("calls save section API and onSaveAndNext when button clicked", async () => {
    render(
      <Step4SectionGeneration
        sessionId={sessionId}
        researchPlan={researchPlan}
        currentSectionIndex={0}
        contextData={contextData}
        sections={sections}
        setSections={setSections}
        onSaveAndNext={onSaveAndNext}
        onBack={onBack}
      />
    );

    const textarea = screen.getByPlaceholderText(/Paste the LLM-generated markdown content here/i);
    fireEvent.change(textarea, { target: { value: "Generated content" } });

    fireEvent.click(screen.getByText(/Save & Next Question/i));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        `/api/v1/research-sessions/${sessionId}/sections`,
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("Generated content"),
        })
      );
      expect(setSections).toHaveBeenCalled();
      expect(onSaveAndNext).toHaveBeenCalled();
      expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: "Section Saved" }));
    });
  });

  it("advances to Step 5 (finish) on last question", async () => {
    render(
      <Step4SectionGeneration
        sessionId={sessionId}
        researchPlan={researchPlan}
        currentSectionIndex={1} // Last question
        contextData={contextData}
        sections={sections}
        setSections={setSections}
        onSaveAndNext={onSaveAndNext}
        onBack={onBack}
      />
    );

    const textarea = screen.getByPlaceholderText(/Paste the LLM-generated markdown content here/i);
    fireEvent.change(textarea, { target: { value: "Final content" } });

    expect(screen.getByText(/Save & Finish Sections/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/Save & Finish Sections/i));

    await waitFor(() => {
      expect(onSaveAndNext).toHaveBeenCalled();
    });
  });
});
