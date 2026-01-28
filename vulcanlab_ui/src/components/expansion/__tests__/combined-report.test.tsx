import { render, screen } from '@testing-library/react';
import { CombinedReport } from '../combined-report';

// Mock MarkdownEditor as it might be complex to render in tests
jest.mock('@/components/markdown-editor', () => ({
  MarkdownEditor: ({ content }: { content: string }) => <div data-testid="markdown-content">{content}</div>,
}));

describe('CombinedReport', () => {
  it('renders report content', () => {
    const report = '## Final Report\n\nThis is a test report.';
    render(<CombinedReport report={report} />);
    
    expect(screen.getByText('Final Combined Report')).toBeInTheDocument();
    expect(screen.getByTestId('markdown-content')).toHaveTextContent(/Final Report/);
    expect(screen.getByTestId('markdown-content')).toHaveTextContent(/This is a test report/);
  });

  it('renders original answer link when provided', () => {
    const report = 'Test report';
    const link = '/rag/1/results/2';
    render(<CombinedReport report={report} originalResultLink={link} />);
    
    const backButton = screen.getByRole('link', { name: /original answer/i });
    expect(backButton).toBeInTheDocument();
    expect(backButton).toHaveAttribute('href', link);
  });

  it('does not render original answer link when not provided', () => {
    render(<CombinedReport report="Test report" />);
    expect(screen.queryByRole('link', { name: /original answer/i })).not.toBeInTheDocument();
  });
});
