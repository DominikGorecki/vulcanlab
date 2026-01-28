import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SectionDetail } from '../section-detail';
import { SectionDetail as SectionDetailType } from '../types';

// Mock MarkdownEditor
jest.mock('@/components/markdown-editor', () => ({
  MarkdownEditor: ({ content }: { content: string }) => <div data-testid="markdown-content">{content}</div>,
}));

// Mock ManualRAGDialog
jest.mock('../manual-rag-dialog', () => ({
  ManualRAGDialog: () => null,
}));

const mockSection: SectionDetailType = {
  id: 1,
  expansion_id: 10,
  order: 1,
  heading: 'Test Heading',
  summary: 'Test Summary',
  expansion_prompt: 'Test Expansion Prompt',
  expanded_queries: { queries: ['query 1', 'query 2'] },
  hyde_answer: 'Test HyDE Answer',
  intent: 'Test Intent',
  entities: { entities: ['entity 1'] },
  clean_retrieval_context: { chunks: [] },
  augmented_prompt: 'Test Augmented Prompt',
  response_text: 'Test Response Text',
  status: 'completed',
  error_message: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:05:00Z',
};

describe('SectionDetail', () => {
  const mockOnRetry = jest.fn();
  const mockOnSaveManual = jest.fn();
  const mockOnRefresh = jest.fn();
  const mockExpansionId = 10;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders section basic info', () => {
    render(
      <SectionDetail
        section={mockSection}
        mode="automatic"
        expansionId={mockExpansionId}
        onRetry={mockOnRetry}
        onSaveManual={mockOnSaveManual}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText('Test Heading')).toBeInTheDocument();
    expect(screen.getByText('Test Summary')).toBeInTheDocument();
  });

  it('renders augmented prompt when available', () => {
    render(
      <SectionDetail
        section={mockSection}
        mode="automatic"
        expansionId={mockExpansionId}
        onRetry={mockOnRetry}
        onSaveManual={mockOnSaveManual}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText('Test Augmented Prompt')).toBeInTheDocument();
  });

  it('shows retry button when status is failed', () => {
    const failedSection = { ...mockSection, status: 'failed' };
    render(
      <SectionDetail
        section={failedSection}
        mode="automatic"
        expansionId={mockExpansionId}
        onRetry={mockOnRetry}
        onSaveManual={mockOnSaveManual}
        onRefresh={mockOnRefresh}
      />
    );

    const retryBtn = screen.getByRole('button', { name: /retry/i });
    expect(retryBtn).toBeInTheDocument();
  });

  it('shows manual mode interface when mode is manual and status is ready', () => {
    const readySection = { ...mockSection, status: 'ready', response_text: null };
    render(
      <SectionDetail
        section={readySection}
        mode="manual"
        expansionId={mockExpansionId}
        onRetry={mockOnRetry}
        onSaveManual={mockOnSaveManual}
        onRefresh={mockOnRefresh}
      />
    );

    expect(screen.getByText('Manual Entry')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/paste response from external llm/i)).toBeInTheDocument();
  });

  it('calls onSaveManual when save button is clicked in manual mode', async () => {
    const readySection = { ...mockSection, status: 'ready', response_text: null };
    render(
      <SectionDetail
        section={readySection}
        mode="manual"
        expansionId={mockExpansionId}
        onRetry={mockOnRetry}
        onSaveManual={mockOnSaveManual}
        onRefresh={mockOnRefresh}
      />
    );

    const textarea = screen.getByPlaceholderText(/paste response from external llm/i);
    fireEvent.change(textarea, { target: { value: 'User provided response' } });

    const saveBtn = screen.getByRole('button', { name: /save manual response/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(mockOnSaveManual).toHaveBeenCalledWith(readySection.id, 'User provided response');
    });
  });

  it('shows RAG data when toggled', () => {
    render(
      <SectionDetail
        section={mockSection}
        mode="automatic"
        expansionId={mockExpansionId}
        onRetry={mockOnRetry}
        onSaveManual={mockOnSaveManual}
        onRefresh={mockOnRefresh}
      />
    );

    const toggleBtn = screen.getByRole('button', { name: /rag pipeline data/i });
    fireEvent.click(toggleBtn);

    expect(screen.getByText('Expanded Queries')).toBeInTheDocument();
    expect(screen.getByText('query 1')).toBeInTheDocument();
    expect(screen.getByText('query 2')).toBeInTheDocument();
    expect(screen.getByText('HyDE Answer')).toBeInTheDocument();
  });
});
