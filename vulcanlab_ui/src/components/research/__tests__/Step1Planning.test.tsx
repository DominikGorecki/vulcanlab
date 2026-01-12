import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Step1Planning } from "../Step1Planning";
import { toast } from "@/hooks/use-toast";
import { copyToClipboard } from "@/lib/clipboard";

jest.mock("@/hooks/use-toast", () => ({
  toast: jest.fn(),
}));

jest.mock("@/lib/clipboard", () => ({
  copyToClipboard: jest.fn().mockResolvedValue(undefined),
}));

describe("Step1Planning", () => {
  const collectionId = 1;
  const sessionId = 10;
  const onPlanSaved = jest.fn();

  const mockAnalysis = {
    name: "Test Collection",
    description: "Test Description",
    item_count: 5,
    items_by_type: { excerpt: 2, research_result: 2, research_query: 1 },
    items: [
      { id: 1, type: "excerpt", link: "link1", note: "note1" },
      { id: 2, type: "research_result", link: "link2", preview: "preview2" },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url.includes(`/api/v1/collections/${collectionId}/analyze`)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAnalysis),
        });
      }
      if (url.includes(`/api/v1/research-sessions/${sessionId}`)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({}),
        });
      }
      return Promise.reject(new Error("Unknown URL"));
    }) as jest.Mock;
  });

  it("renders collection overview correctly", async () => {
    render(<Step1Planning collectionId={collectionId} sessionId={sessionId} onPlanSaved={onPlanSaved} />);
    
    await waitFor(() => {
      expect(screen.getByText("Test Collection")).toBeInTheDocument();
      expect(screen.getByText("Test Description")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument(); // Total items
      // Check for Excerpts count (2)
      expect(screen.getAllByText("2")).toHaveLength(2); // One for Excerpts, one for Results
    });
  });

  it("copies prompt to clipboard when 'Copy Planning Prompt' is clicked", async () => {
    render(<Step1Planning collectionId={collectionId} sessionId={sessionId} onPlanSaved={onPlanSaved} />);
    
    await waitFor(() => screen.getByText("Copy Planning Prompt"));
    fireEvent.click(screen.getByText("Copy Planning Prompt"));
    
    await waitFor(() => {
      expect(copyToClipboard).toHaveBeenCalled();
      expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: "Copied!" }));
    });
  });

  it("validates JSON and saves plan on 'Save Research Plan' click", async () => {
    render(<Step1Planning collectionId={collectionId} sessionId={sessionId} onPlanSaved={onPlanSaved} />);
    
    await waitFor(() => screen.getByPlaceholderText(/Paste the JSON response/i));
    
    const textarea = screen.getByPlaceholderText(/Paste the JSON response/i);
    const validPlan = {
      research_goal: "Analyze trends",
      sub_questions: [{ id: "Q1", question: "Trend 1?", rationale: "Why", estimated_tokens: 1000 }],
    };
    
    fireEvent.change(textarea, { target: { value: JSON.stringify(validPlan) } });
    fireEvent.click(screen.getByText(/Save Research Plan/i));
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        `/api/v1/research-sessions/${sessionId}`,
        expect.objectContaining({ method: "PUT" })
      );
      expect(onPlanSaved).toHaveBeenCalledWith(validPlan);
      expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: "Plan Saved" }));
    });
  });

  it("shows error toast for invalid JSON", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    render(<Step1Planning collectionId={collectionId} sessionId={sessionId} onPlanSaved={onPlanSaved} />);
    
    await waitFor(() => screen.getByPlaceholderText(/Paste the JSON response/i));
    
    const textarea = screen.getByPlaceholderText(/Paste the JSON response/i);
    fireEvent.change(textarea, { target: { value: "invalid json" } });
    fireEvent.click(screen.getByText(/Save Research Plan/i));
    
    await waitFor(() => {
      expect(toast).toHaveBeenCalledWith(expect.objectContaining({ variant: "destructive", title: "Invalid JSON" }));
    });
    consoleSpy.mockRestore();
  });
});
