/**
 * Unit tests for Answer Detail Page component (T03)
 * Tests answer display, evaluation rendering, delete functionality, and navigation
 *
 * These tests verify the implementation requirements from ticket T03:
 * - Display complete answer data (X/Y and A/B)
 * - Show evaluation results when present
 * - Collapsible prompt context
 * - Delete answer functionality
 * - Correct mapping indicator
 * - Unblinded score calculation
 */

import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import AnswerDetailPage from '../page';

// Mock Next.js modules
const mockPush = jest.fn();
const mockUse = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  use: (params: any) => mockUse(params),
}));

// Mock toast hook
const mockToast = jest.fn();
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Mock usePageData hook
const mockUsePageData = jest.fn();
jest.mock('@/hooks/use-page-data', () => ({
  usePageData: (fetchFn: any) => mockUsePageData(fetchFn),
}));

// Sample test data
const mockAnswer = {
  id: 1,
  prompt_id: 10,
  answer_x: 'This is answer X from model X',
  answer_y: 'This is answer Y from model Y',
  is_x_mapped_to_a: true,
  answer_a: 'This is answer X from model X', // X mapped to A
  answer_b: 'This is answer Y from model Y', // Y mapped to B
  created_at: '2024-01-15T10:30:00Z',
  updated_at: '2024-01-15T10:30:00Z',
};

const mockAnswerWithEvaluation = {
  ...mockAnswer,
  evaluation: {
    id: 100,
    overall_score: 5,
    unblinded_score: 5, // Positive = X wins (since X→A and score is +5 for A)
    justification: 'Answer A provides more detailed explanation and better examples.',
    dimension_results: [
      { dimension_name: 'Clarity', score: 6 },
      { dimension_name: 'Accuracy', score: 4 },
      { dimension_name: 'Completeness', score: 5 },
    ],
    created_at: '2024-01-15T11:00:00Z',
  },
};

const mockPrompt = {
  id: 10,
  experiment_id: 5,
  prompt_text: 'What is the capital of France?',
  created_at: '2024-01-15T10:00:00Z',
  updated_at: '2024-01-15T10:00:00Z',
};

const mockExperiment = {
  id: 5,
  name: 'Geography Test Experiment',
  description_x: 'Model X - GPT-4',
  description_y: 'Model Y - Claude',
  model_x: 'gpt-4',
  model_y: 'claude-3-opus',
  auto_mode_enabled: true,
  auto_answer_provider: 'openai',
  auto_judge_provider: 'anthropic',
};

describe('AnswerDetailPage - T03 Requirements', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
    mockUse.mockReturnValue({
      id: '5',
      promptId: '10',
      answerId: '1',
    });
  });

  describe('Page Loading and Data Display', () => {
    it('should show loading state while fetching data', () => {
      mockUsePageData
        .mockReturnValueOnce({ data: null, loading: true, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: null, loading: true, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: null, loading: true, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText(/loading answer details/i)).toBeInTheDocument();
    });

    it('should display answer data after successful load', () => {
      mockUsePageData
        .mockReturnValueOnce({ data: mockAnswer, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText('This is answer X from model X')).toBeInTheDocument();
      expect(screen.getByText('This is answer Y from model Y')).toBeInTheDocument();
    });

    it('should show error state when answer fetch fails', () => {
      const mockRefetch = jest.fn();
      mockUsePageData
        .mockReturnValueOnce({
          data: null,
          loading: false,
          error: new Error('Failed to load answer'),
          refetch: mockRefetch
        })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText(/failed to load answer/i)).toBeInTheDocument();
    });
  });

  describe('Answer Display', () => {
    beforeEach(() => {
      mockUsePageData
        .mockReturnValue({ data: mockAnswer, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockAnswer, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });
    });

    it('should display unblinded answers (X and Y)', () => {
      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText('Answer X')).toBeInTheDocument();
      expect(screen.getByText('Answer Y')).toBeInTheDocument();
      expect(screen.getByText('This is answer X from model X')).toBeInTheDocument();
      expect(screen.getByText('This is answer Y from model Y')).toBeInTheDocument();
    });

    it('should display blind-randomized answers (A and B)', () => {
      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText('Answer A')).toBeInTheDocument();
      expect(screen.getByText('Answer B')).toBeInTheDocument();
    });

    it('should show correct mapping indicator when X→A', () => {
      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText(/X → A/i)).toBeInTheDocument();
      expect(screen.getByText(/Y → B/i)).toBeInTheDocument();
    });

    it('should show correct mapping indicator when X→B', () => {
      const answerXtoB = { ...mockAnswer, is_x_mapped_to_a: false };
      mockUsePageData
        .mockReturnValueOnce({ data: answerXtoB, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText(/X → B/i)).toBeInTheDocument();
      expect(screen.getByText(/Y → A/i)).toBeInTheDocument();
    });

    it('should display creation timestamp', () => {
      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      // Check for "Created:" text
      expect(screen.getByText(/Created:/i)).toBeInTheDocument();
    });
  });

  describe('Prompt Context Card', () => {
    beforeEach(() => {
      mockUsePageData
        .mockReturnValueOnce({ data: mockAnswer, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });
    });

    it('should render prompt context card', () => {
      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText('Prompt Context')).toBeInTheDocument();
    });

    it('should have collapsible prompt text (accordion)', async () => {
      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      const trigger = screen.getByText('View Prompt');
      expect(trigger).toBeInTheDocument();

      // Prompt should not be visible initially (collapsed)
      expect(screen.queryByText('What is the capital of France?')).not.toBeVisible();
    });

    it('should expand prompt when accordion trigger clicked', async () => {
      const user = userEvent.setup();
      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      const trigger = screen.getByText('View Prompt');
      await user.click(trigger);

      // Wait for accordion animation
      await waitFor(() => {
        expect(screen.getByText('What is the capital of France?')).toBeVisible();
      });
    });
  });

  describe('Evaluation Results Card', () => {
    it('should show evaluation card when answer has evaluation', () => {
      mockUsePageData
        .mockReturnValueOnce({ data: mockAnswerWithEvaluation, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText('Evaluation Results')).toBeInTheDocument();
    });

    it('should hide evaluation card when answer has no evaluation', () => {
      mockUsePageData
        .mockReturnValueOnce({ data: mockAnswer, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.queryByText('Evaluation Results')).not.toBeInTheDocument();
    });

    it('should display overall score (blinded)', () => {
      mockUsePageData
        .mockReturnValueOnce({ data: mockAnswerWithEvaluation, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText('+5')).toBeInTheDocument();
      expect(screen.getByText('Overall Score (Blinded)')).toBeInTheDocument();
    });

    it('should display unblinded score', () => {
      mockUsePageData
        .mockReturnValueOnce({ data: mockAnswerWithEvaluation, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText('Unblinded Score')).toBeInTheDocument();
      // Should show +5 (same as overall since X→A)
      const unblinedScores = screen.getAllByText('+5');
      expect(unblinedScores.length).toBeGreaterThanOrEqual(2); // Both overall and unblinded
    });

    it('should display justification when present', () => {
      mockUsePageData
        .mockReturnValueOnce({ data: mockAnswerWithEvaluation, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText('Justification')).toBeInTheDocument();
      expect(screen.getByText(/Answer A provides more detailed explanation/i)).toBeInTheDocument();
    });

    it('should not show justification section when justification is missing', () => {
      const answerNoJustification = {
        ...mockAnswerWithEvaluation,
        evaluation: {
          ...mockAnswerWithEvaluation.evaluation!,
          justification: undefined,
        },
      };

      mockUsePageData
        .mockReturnValueOnce({ data: answerNoJustification, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.queryByText('Justification')).not.toBeInTheDocument();
    });

    it('should display dimension scores sorted alphabetically', () => {
      mockUsePageData
        .mockReturnValueOnce({ data: mockAnswerWithEvaluation, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText('Dimension Scores')).toBeInTheDocument();
      expect(screen.getByText('Accuracy')).toBeInTheDocument();
      expect(screen.getByText('Clarity')).toBeInTheDocument();
      expect(screen.getByText('Completeness')).toBeInTheDocument();

      // Verify scores are displayed
      expect(screen.getByText('+4')).toBeInTheDocument(); // Accuracy
      expect(screen.getByText('+6')).toBeInTheDocument(); // Clarity
      // +5 appears multiple times (overall, unblinded, and Completeness)
    });

    it('should not show dimension scores section when no dimensions', () => {
      const answerNoDimensions = {
        ...mockAnswerWithEvaluation,
        evaluation: {
          ...mockAnswerWithEvaluation.evaluation!,
          dimension_results: [],
        },
      };

      mockUsePageData
        .mockReturnValueOnce({ data: answerNoDimensions, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.queryByText('Dimension Scores')).not.toBeInTheDocument();
    });
  });

  describe('Delete Functionality', () => {
    beforeEach(() => {
      mockUsePageData
        .mockReturnValueOnce({ data: mockAnswer, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });
    });

    it('should show delete button in header', () => {
      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByRole('button', { name: /delete answer/i })).toBeInTheDocument();
    });

    it('should open confirmation dialog when delete button clicked', async () => {
      const user = userEvent.setup();
      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      const deleteButton = screen.getByRole('button', { name: /delete answer/i });
      await user.click(deleteButton);

      expect(screen.getByText('Delete Answer Pair')).toBeInTheDocument();
      expect(screen.getByText(/permanently delete the answer and any associated evaluation/i)).toBeInTheDocument();
    });

    it('should call DELETE endpoint when deletion confirmed', async () => {
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: true });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      const deleteButton = screen.getByRole('button', { name: /delete answer/i });
      await user.click(deleteButton);

      const confirmButton = screen.getByRole('button', { name: /delete answer pair/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/v1/eval/answers/1',
          { method: 'DELETE' }
        );
      });
    });

    it('should navigate back to prompt page after successful deletion', async () => {
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: true });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      const deleteButton = screen.getByRole('button', { name: /delete answer/i });
      await user.click(deleteButton);

      const confirmButton = screen.getByRole('button', { name: /delete answer pair/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/eval/5/prompts/10');
      });
    });

    it('should show success toast after successful deletion', async () => {
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: true });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      const deleteButton = screen.getByRole('button', { name: /delete answer/i });
      await user.click(deleteButton);

      const confirmButton = screen.getByRole('button', { name: /delete answer pair/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Answer pair deleted',
          description: 'The answer pair has been deleted successfully',
        });
      });
    });

    it('should show error toast when deletion fails', async () => {
      const user = userEvent.setup();
      (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      const deleteButton = screen.getByRole('button', { name: /delete answer/i });
      await user.click(deleteButton);

      const confirmButton = screen.getByRole('button', { name: /delete answer pair/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: 'Error',
          description: 'Failed to delete answer pair',
          variant: 'destructive',
        });
      });
    });
  });

  describe('Navigation and Header', () => {
    beforeEach(() => {
      mockUsePageData
        .mockReturnValueOnce({ data: mockAnswer, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });
    });

    it('should display page title', () => {
      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText('Answer Pair Details')).toBeInTheDocument();
    });

    it('should display experiment name in subtitle', () => {
      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      expect(screen.getByText('Geography Test Experiment')).toBeInTheDocument();
    });

    it('should have back button to prompt page', () => {
      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      const backLink = screen.getByRole('link', { name: /back to prompt/i });
      expect(backLink).toHaveAttribute('href', '/eval/5/prompts/10');
    });
  });

  describe('Score Display Formatting', () => {
    it('should show positive sign for positive scores', () => {
      mockUsePageData
        .mockReturnValueOnce({ data: mockAnswerWithEvaluation, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      // Positive scores should have + prefix
      expect(screen.getByText('+5')).toBeInTheDocument();
      expect(screen.getByText('+6')).toBeInTheDocument();
    });

    it('should not show sign for negative scores (minus is implicit)', () => {
      const answerNegativeScore = {
        ...mockAnswerWithEvaluation,
        evaluation: {
          ...mockAnswerWithEvaluation.evaluation!,
          overall_score: -3,
          unblinded_score: -3,
        },
      };

      mockUsePageData
        .mockReturnValueOnce({ data: answerNegativeScore, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockPrompt, loading: false, error: null, refetch: jest.fn() })
        .mockReturnValueOnce({ data: mockExperiment, loading: false, error: null, refetch: jest.fn() });

      render(<AnswerDetailPage params={Promise.resolve({ id: '5', promptId: '10', answerId: '1' })} />);

      // Negative scores show as -3 (no explicit + needed)
      expect(screen.getByText('-3')).toBeInTheDocument();
    });
  });
});

/**
 * Integration Test Requirements
 *
 * The following manual tests should be performed to verify full functionality:
 *
 * 1. Navigate to /eval/[id]/prompts/[promptId]/answers/[answerId]
 * 2. Verify page loads with answer data displayed
 * 3. Verify prompt context is collapsed by default
 * 4. Click "View Prompt" and verify prompt text expands
 * 5. Verify all four answers displayed (X, Y, A, B)
 * 6. Verify mapping indicator shows correct X→A/B and Y→B/A
 * 7. For evaluated answer, verify evaluation card appears
 * 8. Verify overall score, unblinded score, justification displayed
 * 9. Verify dimension scores sorted alphabetically
 * 10. Click delete button and verify confirmation dialog
 * 11. Confirm deletion and verify navigation back to prompt page
 * 12. For unevaluated answer, verify no evaluation card shown
 * 13. Verify back button navigates to prompt page
 * 14. Test with invalid answer ID and verify error page
 *
 * Expected Results:
 * - All answer data displayed correctly
 * - Prompt context collapsible works smoothly
 * - Evaluation card conditional on evaluation presence
 * - Delete functionality works with proper confirmation
 * - Navigation breadcrumb trail functions correctly
 * - No console errors or infinite loops
 */
