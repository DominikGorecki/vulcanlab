import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import ExperimentDetailPage from "../page";
import { useRouter } from "next/navigation";
import { useToast } from "@/hooks/use-toast";
import React, { Suspense } from "react";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

// Mock useToast
jest.mock("@/hooks/use-toast", () => ({
  useToast: jest.fn(),
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe("ExperimentDetailPage", () => {
  const mockExperiment = {
    id: 1,
    name: "Test Experiment",
    description_x: "X desc",
    description_y: "Y desc",
    model_x: "gpt-4",
    model_y: "claude",
    judge_model: "gpt-4o",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    dimensions: [],
    stats: {
      eval_count: 5,
      x_win_rate: 60,
      mean_score: 0.5,
      median_score: 0.5,
      tie_percentage: 20,
      harm_rate: 0,
      wilcoxon_p_value: 0.04
    }
  };

  const mockPrompts = [
    {
      id: 1,
      experiment_id: 1,
      prompt_text: "Test Prompt",
      created_at: new Date().toISOString(),
      eval_count: 1
    }
  ];

  const mockToast = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: jest.fn() });
    (useToast as jest.Mock).mockReturnValue({ toast: mockToast });
    
    mockFetch.mockImplementation((url) => {
      if (url.includes("/prompts")) {
        return Promise.resolve({
          ok: true,
          json: async () => mockPrompts,
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => mockExperiment,
      });
    });
  });

  it("renders the 'Export CSV' button", async () => {
    const mockParams = Promise.resolve({ id: "1" });
    
    await act(async () => {
      render(
        <Suspense fallback={<div>Loading...</div>}>
          <ExperimentDetailPage params={mockParams} />
        </Suspense>
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Test Experiment")).toBeInTheDocument();
      expect(screen.getByText("Export CSV")).toBeInTheDocument();
    });
  });

  it("triggers CSV export and shows toast when button is clicked", async () => {
    const mockParams = Promise.resolve({ id: "1" });
    
    // Track if a link was clicked
    let clickedLink: HTMLAnchorElement | null = null;
    const originalCreateElement = document.createElement;
    const createElementSpy = jest.spyOn(document, 'createElement').mockImplementation((tagName) => {
      const element = originalCreateElement.call(document, tagName);
      if (tagName === 'a') {
        const anchor = element as HTMLAnchorElement;
        const originalClick = anchor.click;
        jest.spyOn(anchor, 'click').mockImplementation(function(this: HTMLAnchorElement) {
          clickedLink = this;
          // Don't actually navigate
        });
      }
      return element;
    });

    await act(async () => {
      render(
        <Suspense fallback={<div>Loading...</div>}>
          <ExperimentDetailPage params={mockParams} />
        </Suspense>
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Export CSV")).toBeInTheDocument();
    });

    const exportButton = screen.getByText("Export CSV");
    fireEvent.click(exportButton);

    expect(createElementSpy).toHaveBeenCalledWith("a");
    expect(clickedLink).not.toBeNull();
    if (clickedLink) {
      expect((clickedLink as HTMLAnchorElement).href).toContain("/api/v1/eval/experiments/1/export-csv");
      expect((clickedLink as HTMLAnchorElement).getAttribute("download")).toContain("experiment_1_evaluations.csv");
    }
    
    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
      title: "Export started"
    }));

    // Cleanup
    createElementSpy.mockRestore();
  });
});
