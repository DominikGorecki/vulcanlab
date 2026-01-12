import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Step5Synthesis } from "../Step5Synthesis";
import { Step6QualityEvaluation } from "../Step6QualityEvaluation";
import { CompletionStep } from "../CompletionStep";
import { ResearchPlan } from "@/types/research";
import { toast } from "@/hooks/use-toast";

jest.mock("@/hooks/use-toast", () => ({
  toast: jest.fn(),
}));

// Mock MarkdownRenderer to avoid rendering issues in tests
jest.mock("@/components/markdown-renderer", () => ({
  MarkdownRenderer: ({ content }: { content: string }) => <div data-testid="markdown-preview">{content}</div>,
}));

// Mock navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn().mockImplementation(() => Promise.resolve()),
  },
});

describe("ManualResearchWizard Steps 5 & 6", () => {
  const sessionId = 10;
  const researchPlan: ResearchPlan = {
    research_goal: "Test Research Goal",
    key_themes: ["Theme 1"],
    sub_questions: [
      {
        id: "Q1",
        question: "What is X?",
        rationale: "Rationale",
        estimated_tokens: 1000,
        relevant_items: [1],
      },
    ],
    synthesis_approach: "Standard",
  };

  describe("Step5Synthesis", () => {
    const onReportSaved = jest.fn();
    const onBack = jest.fn();

    beforeEach(() => {
      jest.clearAllMocks();
      global.fetch = jest.fn().mockImplementation((url) => {
        if (url === `/api/v1/research-sessions/${sessionId}/sections`) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve([
              { question_text: "What is X?", section_content: "Content X" }
            ]),
          });
        }
        if (url === `/api/v1/research-sessions/${sessionId}/report`) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: true }),
          });
        }
        return Promise.reject(new Error("Unknown URL"));
      }) as jest.Mock;
    });

    it("fetches sections and copies prompt to clipboard", async () => {
      render(
        <Step5Synthesis
          sessionId={sessionId}
          researchPlan={researchPlan}
          onReportSaved={onReportSaved}
          onBack={onBack}
        />
      );

      const fetchBtn = screen.getByText(/Fetch Sections & Copy Prompt/i);
      fireEvent.click(fetchBtn);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(`/api/v1/research-sessions/${sessionId}/sections`);
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expect.stringContaining("Test Research Goal"));
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expect.stringContaining("Content X"));
        expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: "Prompt Copied" }));
      });
    });

    it("saves report and calls onReportSaved", async () => {
      render(
        <Step5Synthesis
          sessionId={sessionId}
          researchPlan={researchPlan}
          onReportSaved={onReportSaved}
          onBack={onBack}
        />
      );

      const textarea = screen.getByPlaceholderText(/Paste the final synthesized markdown report here/i);
      fireEvent.change(textarea, { target: { value: "# Final Report Content" } });

      const saveBtn = screen.getByText(/Save Final Report/i);
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          `/api/v1/research-sessions/${sessionId}/report`,
          expect.objectContaining({
            method: "POST",
            body: expect.stringContaining("# Final Report Content"),
          })
        );
        expect(onReportSaved).toHaveBeenCalledWith("# Final Report Content");
        expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: "Report Saved" }));
      });
    });

    it("renders markdown preview", async () => {
      render(
        <Step5Synthesis
          sessionId={sessionId}
          researchPlan={researchPlan}
          onReportSaved={onReportSaved}
          onBack={onBack}
        />
      );

      const textarea = screen.getByPlaceholderText(/Paste the final synthesized markdown report here/i);
      fireEvent.change(textarea, { target: { value: "# Preview Content" } });

      const previewTab = screen.getByRole("tab", { name: /markdown preview/i });
      fireEvent.click(previewTab);
      fireEvent.keyDown(previewTab, { key: " ", code: "Space" });

      await waitFor(() => {
        expect(screen.getByTestId("markdown-preview")).toHaveTextContent("# Preview Content");
      });
    });
  });

  describe("Step6QualityEvaluation", () => {
    const onComplete = jest.fn();
    const onSkip = jest.fn();
    const reportContent = "# Final Report Content";

    beforeEach(() => {
      jest.clearAllMocks();
      global.fetch = jest.fn().mockImplementation((url) => {
        if (url === `/api/v1/research-sessions/${sessionId}`) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: true }),
          });
        }
        return Promise.reject(new Error("Unknown URL"));
      }) as jest.Mock;
    });

    it("copies quality evaluation prompt", async () => {
      render(
        <Step6QualityEvaluation
          sessionId={sessionId}
          reportContent={reportContent}
          onComplete={onComplete}
          onSkip={onSkip}
        />
      );

      const copyBtn = screen.getByText(/Copy Evaluation Prompt/i);
      fireEvent.click(copyBtn);

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expect.stringContaining(reportContent));
        expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: "Prompt Copied" }));
      });
    });

    it("saves evaluation and completes session", async () => {
      render(
        <Step6QualityEvaluation
          sessionId={sessionId}
          reportContent={reportContent}
          onComplete={onComplete}
          onSkip={onSkip}
        />
      );

      const evalJson = JSON.stringify({
        citation_accuracy: "High",
        feedback: "Good job"
      });

      const textarea = screen.getByPlaceholderText(/Paste the evaluation JSON here/i);
      fireEvent.change(textarea, { target: { value: evalJson } });

      const saveBtn = screen.getByText(/Save & Complete/i);
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          `/api/v1/research-sessions/${sessionId}`,
          expect.objectContaining({
            method: "PUT",
            body: expect.stringContaining("High"),
          })
        );
        expect(onComplete).toHaveBeenCalled();
        expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: "Evaluation Saved" }));
      });
    });

    it("calls onSkip when skip button clicked", () => {
      render(
        <Step6QualityEvaluation
          sessionId={sessionId}
          reportContent={reportContent}
          onComplete={onComplete}
          onSkip={onSkip}
        />
      );

      fireEvent.click(screen.getByText(/Skip Evaluation/i));
      expect(onSkip).toHaveBeenCalled();
    });
  });

  describe("CompletionStep", () => {
    const onClose = jest.fn();
    const onRestart = jest.fn();
    const reportContent = "# Final Report Content";

    it("renders success message and preview", () => {
      render(
        <CompletionStep
          collectionId={1}
          reportContent={reportContent}
          onClose={onClose}
          onRestart={onRestart}
        />
      );

      expect(screen.getByText(/Research Completed!/i)).toBeInTheDocument();
      expect(screen.getByTestId("markdown-preview")).toHaveTextContent("# Final Report Content");
    });

    it("calls onClose when close button clicked", () => {
      render(
        <CompletionStep
          collectionId={1}
          reportContent={reportContent}
          onClose={onClose}
          onRestart={onRestart}
        />
      );

      fireEvent.click(screen.getByText(/Close Wizard/i));
      expect(onClose).toHaveBeenCalled();
    });

    it("calls onRestart when restart button clicked", () => {
      render(
        <CompletionStep
          collectionId={1}
          reportContent={reportContent}
          onClose={onClose}
          onRestart={onRestart}
        />
      );

      fireEvent.click(screen.getByText(/Start New Research/i));
      expect(onRestart).toHaveBeenCalled();
    });
  });
});
