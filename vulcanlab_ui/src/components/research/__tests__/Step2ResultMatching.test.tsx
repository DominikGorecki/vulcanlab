import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Step2ResultMatching } from "../Step2ResultMatching";
import { toast } from "@/hooks/use-toast";

jest.mock("@/hooks/use-toast", () => ({
  toast: jest.fn(),
}));

describe("Step2ResultMatching", () => {
  const sessionId = 10;
  const researchPlan = {
    research_goal: "Test Goal",
    sub_questions: [
      { id: "Q1", question: "Question 1?", rationale: "Rationale 1", estimated_tokens: 1000, relevant_items: [1] },
      { id: "Q2", question: "Question 2?", rationale: "Rationale 2", estimated_tokens: 2000, relevant_items: [2] },
    ],
    key_themes: ["Theme 1"],
    synthesis_approach: "Synthesis",
  };
  const onComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url.includes(`/api/v1/research-sessions/${sessionId}/match-results`)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            matched_results: [
              { result_id: 101, question_text: "Old Q1", similarity_score: 0.9, content_preview: "Preview 1" }
            ],
            recommended_strategy: "Exact Reuse",
          }),
        });
      }
      if (url.includes(`/api/v1/research-sessions/${sessionId}`)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: sessionId, state_data: {} }),
        });
      }
      return Promise.reject(new Error("Unknown URL"));
    }) as jest.Mock;
  });

  it("displays current sub-question", () => {
    render(<Step2ResultMatching sessionId={sessionId} researchPlan={researchPlan} onComplete={onComplete} />);
    expect(screen.getByText("Question 1?")).toBeInTheDocument();
    expect(screen.getByText(/Rationale 1/)).toBeInTheDocument();
  });

  it("calls match-results API on 'Check for Matching Results' click", async () => {
    render(<Step2ResultMatching sessionId={sessionId} researchPlan={researchPlan} onComplete={onComplete} />);
    
    fireEvent.click(screen.getByText("Check for Matching Results"));
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        `/api/v1/research-sessions/${sessionId}/match-results`,
        expect.objectContaining({ method: "POST" })
      );
      expect(screen.getByText("90% Match")).toBeInTheDocument();
      expect(screen.getByText(/Preview 1/)).toBeInTheDocument();
    });
  });

  it("allows strategy selection when matches found", async () => {
    render(<Step2ResultMatching sessionId={sessionId} researchPlan={researchPlan} onComplete={onComplete} />);
    
    fireEvent.click(screen.getByText("Check for Matching Results"));
    await waitFor(() => screen.getByText("90% Match"));
    
    expect(screen.getByLabelText(/Generate New/)).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText(/Generate New/));
    
    expect(screen.getByLabelText(/Generate New/)).toBeChecked();
  });

  it("loops through sub-questions and calls onComplete at the end", async () => {
    render(<Step2ResultMatching sessionId={sessionId} researchPlan={researchPlan} onComplete={onComplete} />);
    
    // Q1
    fireEvent.click(screen.getByText("Check for Matching Results"));
    await waitFor(() => screen.getByText("Confirm & Next Question"));
    fireEvent.click(screen.getByText("Confirm & Next Question"));
    
    // Q2
    await waitFor(() => {
      expect(screen.getByText("Question 2?")).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText("Check for Matching Results"));
    await waitFor(() => screen.getByText("Confirm & Continue to Step 3"));
    fireEvent.click(screen.getByText("Confirm & Continue to Step 3"));
    
    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledTimes(1);
    });
  });
});
