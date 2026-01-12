import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Step3ContextAssembly } from "../Step3ContextAssembly";
import { ResearchPlan } from "@/types/research";
import { toast } from "@/hooks/use-toast";
import { copyToClipboard } from "@/lib/clipboard";

jest.mock("@/hooks/use-toast", () => ({
  toast: jest.fn(),
}));

jest.mock("@/lib/clipboard", () => ({
  copyToClipboard: jest.fn().mockResolvedValue(undefined),
}));

describe("Step3ContextAssembly", () => {
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
    ],
    synthesis_approach: "Standard",
  };
  const contextData = {};
  const setContextData = jest.fn();
  const onNext = jest.fn();
  const onBack = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url === `/api/v1/research-sessions/${sessionId}`) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            state_data: {
              reuse_info: {
                Q1: { strategy: "Generate New", matched_results: [] }
              }
            }
          }),
        });
      }
      if (url === `/api/v1/research-sessions/${sessionId}/context`) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            context: "Test context content",
            token_count: 100,
            sources: [],
          }),
        });
      }
      return Promise.reject(new Error("Unknown URL"));
    }) as jest.Mock;
  });

  it("renders sub-question and rationale", async () => {
    render(
      <Step3ContextAssembly
        sessionId={sessionId}
        researchPlan={researchPlan}
        currentSectionIndex={0}
        contextData={contextData}
        setContextData={setContextData}
        onNext={onNext}
        onBack={onBack}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("What is X?")).toBeInTheDocument();
      expect(screen.getByText("Rationale for X")).toBeInTheDocument();
    });
  });

  it("calls fetch context API when button clicked", async () => {
    render(
      <Step3ContextAssembly
        sessionId={sessionId}
        researchPlan={researchPlan}
        currentSectionIndex={0}
        contextData={contextData}
        setContextData={setContextData}
        onNext={onNext}
        onBack={onBack}
      />
    );

    await waitFor(() => screen.getByText("Fetch Context"));
    fireEvent.click(screen.getByText("Fetch Context"));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        `/api/v1/research-sessions/${sessionId}/context`,
        expect.objectContaining({ method: "POST" })
      );
      expect(setContextData).toHaveBeenCalled();
    });
  });

  it("displays context preview and token count when context exists", async () => {
    const mockContext = {
      Q1: { context: "Test context content", token_count: 100, sources: [] }
    };

    render(
      <Step3ContextAssembly
        sessionId={sessionId}
        researchPlan={researchPlan}
        currentSectionIndex={0}
        contextData={mockContext}
        setContextData={setContextData}
        onNext={onNext}
        onBack={onBack}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Token count:")).toBeInTheDocument();
      expect(screen.getByText("100")).toBeInTheDocument();
      expect(screen.getByText("Test context content")).toBeInTheDocument();
    });
  });

  it("handles reuse strategy correctly", async () => {
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url === `/api/v1/research-sessions/${sessionId}`) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            state_data: {
              reuse_info: {
                Q1: { 
                  strategy: "Exact Reuse", 
                  matched_results: [{ result_id: 1, content_preview: "Existing result" }] 
                }
              }
            }
          }),
        });
      }
      return Promise.reject(new Error("Unknown URL"));
    }) as jest.Mock;

    render(
      <Step3ContextAssembly
        sessionId={sessionId}
        researchPlan={researchPlan}
        currentSectionIndex={0}
        contextData={contextData}
        setContextData={setContextData}
        onNext={onNext}
        onBack={onBack}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Using Existing Result \(Exact Reuse\)/)).toBeInTheDocument();
      expect(screen.getByText(/Existing result/)).toBeInTheDocument();
      expect(screen.queryByText("Fetch Context")).not.toBeInTheDocument();
    });
  });

  it("copies prompt to clipboard", async () => {
    const mockContext = {
      Q1: { context: "Test context content", token_count: 100, sources: [] }
    };

    render(
      <Step3ContextAssembly
        sessionId={sessionId}
        researchPlan={researchPlan}
        currentSectionIndex={0}
        contextData={mockContext}
        setContextData={setContextData}
        onNext={onNext}
        onBack={onBack}
      />
    );

    await waitFor(() => screen.getByText("Copy Prompt"));
    fireEvent.click(screen.getByText("Copy Prompt"));

    await waitFor(() => {
      expect(copyToClipboard).toHaveBeenCalled();
      expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: "Prompt Copied" }));
    });
  });
});
