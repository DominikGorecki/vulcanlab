import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ManualResearchWizard } from "../ManualResearchWizard";
import { toast } from "@/hooks/use-toast";
import { copyToClipboard } from "@/lib/clipboard";

// Mocking toast and clipboard
jest.mock("@/hooks/use-toast", () => ({
  toast: jest.fn(),
}));

jest.mock("@/lib/clipboard", () => ({
  copyToClipboard: jest.fn(),
}));

// Mock Step components to simplify main wizard tests
jest.mock("../Step1Planning", () => ({
  Step1Planning: ({ onPlanSaved }: any) => (
    <div>
      <div data-testid="step-1">Step 1 Planning</div>
      <button onClick={() => onPlanSaved({ research_goal: "Test Goal", sub_questions: [{ id: "Q1", question: "Q1 Text" }] })}>
        Save Plan
      </button>
    </div>
  ),
}));

jest.mock("../Step2ResultMatching", () => ({
  Step2ResultMatching: ({ onComplete }: any) => (
    <div>
      <div data-testid="step-2">Step 2 Result Matching</div>
      <button onClick={onComplete}>Complete Matching</button>
    </div>
  ),
}));

describe("ManualResearchWizard", () => {
  const collectionId = 1;
  const sessionId = 10;
  const onComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock global fetch
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url.includes(`/api/v1/research-sessions/${sessionId}`)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: sessionId, collection_id: collectionId }),
        });
      }
      return Promise.reject(new Error("Unknown URL"));
    }) as jest.Mock;
  });

  it("renders loading state initially", async () => {
    render(<ManualResearchWizard collectionId={collectionId} sessionId={sessionId} onComplete={onComplete} />);
    expect(screen.getByText(/Loading wizard/i)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.queryByText(/Loading wizard/i)).not.toBeInTheDocument();
    });
  });

  it("renders step 1 by default after loading", async () => {
    render(<ManualResearchWizard collectionId={collectionId} sessionId={sessionId} onComplete={onComplete} />);
    
    await waitFor(() => {
      expect(screen.getByTestId("step-1")).toBeInTheDocument();
      expect(screen.getByText(/Step 1 of 6: Planning/i)).toBeInTheDocument();
    });
  });

  it("advances to step 2 after plan is saved", async () => {
    render(<ManualResearchWizard collectionId={collectionId} sessionId={sessionId} onComplete={onComplete} />);
    
    await waitFor(() => screen.getByTestId("step-1"));
    
    fireEvent.click(screen.getByText("Save Plan"));
    
    expect(screen.getByTestId("step-2")).toBeInTheDocument();
    expect(screen.getByText(/Step 2 of 6: Result Matching/i)).toBeInTheDocument();
  });

  it("advances to step 3 and shows coming soon after matching complete", async () => {
    render(<ManualResearchWizard collectionId={collectionId} sessionId={sessionId} onComplete={onComplete} />);
    
    await waitFor(() => screen.getByTestId("step-1"));
    fireEvent.click(screen.getByText("Save Plan"));
    
    await waitFor(() => screen.getByTestId("step-2"));
    fireEvent.click(screen.getByText("Complete Matching"));
    
    expect(screen.getByText(/Coming Soon/i)).toBeInTheDocument();
    expect(screen.getByText(/Step 3 of 6: Context Assembly/i)).toBeInTheDocument();
  });

  it("calls onComplete when Close Wizard is clicked on final screen", async () => {
    render(<ManualResearchWizard collectionId={collectionId} sessionId={sessionId} onComplete={onComplete} />);
    
    await waitFor(() => screen.getByTestId("step-1"));
    fireEvent.click(screen.getByText("Save Plan"));
    
    await waitFor(() => screen.getByTestId("step-2"));
    fireEvent.click(screen.getByText("Complete Matching"));
    
    fireEvent.click(screen.getByText("Close Wizard"));
    expect(onComplete).toHaveBeenCalledTimes(1);
  });
});
