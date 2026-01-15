import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import WorkSummaryDetailPage from '../page';
import { useParams, useRouter } from 'next/navigation';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useParams: jest.fn(),
  useRouter: jest.fn(),
}));

// Mock useToast
const mockToast = jest.fn();
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Mock UI components to simplify tests and avoid Radix JSDOM issues
jest.mock('@/components/ui/tabs', () => {
  const React = require('react');
  return {
    Tabs: ({ children, defaultValue }: any) => {
      const [value, setValue] = React.useState(defaultValue);
      return <div data-testid="mock-tabs">{React.Children.map(children, (child: any) => {
        if (!child) return null;
        return React.cloneElement(child, { activeValue: value, onValueChange: setValue });
      })}</div>;
    },
    TabsList: ({ children, activeValue, onValueChange }: any) => (
      <div role="tablist">{React.Children.map(children, (child: any) => {
        if (!child) return null;
        return React.cloneElement(child, { activeValue, onValueChange });
      })}</div>
    ),
    TabsTrigger: ({ children, value, activeValue, onValueChange }: any) => (
      <button 
        role="tab" 
        aria-selected={activeValue === value} 
        data-state={activeValue === value ? 'active' : 'inactive'}
        onClick={() => onValueChange(value)}
      >
        {children}
      </button>
    ),
    TabsContent: ({ children, value, activeValue }: any) => (
      activeValue === value ? <div>{children}</div> : null
    ),
  };
});

jest.mock('@/components/ui/accordion', () => ({
  Accordion: ({ children }: any) => <div>{children}</div>,
  AccordionItem: ({ children, value }: any) => <div data-testid={`accordion-item-${value}`}>{children}</div>,
  AccordionTrigger: ({ children }: any) => <button>{children}</button>,
  AccordionContent: ({ children }: any) => <div>{children}</div>,
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('WorkSummaryDetailPage', () => {
  const mockWorkId = '1';
  const mockNodes = {
    nodes: [
      {
        id: 101,
        chunk_id: 201,
        work_id: 1,
        gist: 'Gist of node 1',
        key_points: [{ text: 'Point 1', start_line: 10, end_line: 12 }],
        definitions: [{ term: 'Term 1', definition: 'Def 1', start_line: 15, end_line: 16 }],
        key_terms: [{ term: 'Key Term 1', start_line: 20, end_line: 21 }],
        examples: [{ text: 'Example 1', start_line: 25, end_line: 26 }],
        start_line: 1,
        end_line: 100,
        salience_score: 0.9,
        heading_breadcrumbs: 'Chapter 1',
        level: 'H1',
        parent_id: null,
      },
      {
        id: 102,
        chunk_id: 202,
        work_id: 1,
        gist: 'Gist of node 2',
        key_points: [],
        definitions: [],
        key_terms: [],
        examples: [],
        start_line: 101,
        end_line: 200,
        salience_score: 0.8,
        heading_breadcrumbs: 'Chapter 1 > Section 1.1',
        level: 'H2',
        parent_id: 201,
      }
    ]
  };

  const mockSummaries = [
    {
      id: 501,
      work_id: 1,
      type: 'abstract',
      content: { abstract: 'This is a test abstract.' },
      line_references: [{ start_line: 1, end_line: 200 }],
    }
  ];

  const mockWorkInfo = {
    work_id: 1,
    work_title: 'Test Document Title',
    filename: 'test.md'
  };

  const mockPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useParams as jest.Mock).mockReturnValue({ id: mockWorkId });
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
    
    mockFetch.mockImplementation((url) => {
      if (url.includes('/nodes')) return Promise.resolve({ ok: true, json: async () => mockNodes });
      if (url.includes('/summaries')) return Promise.resolve({ ok: true, json: async () => mockSummaries });
      if (url.includes('/content')) return Promise.resolve({ ok: true, json: async () => mockWorkInfo });
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
  });

  it('renders StickyDetailHeader with work title', async () => {
    render(<WorkSummaryDetailPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Document Title')).toBeInTheDocument();
      expect(screen.getByText('Back to Summaries')).toBeInTheDocument();
    });
  });

  it('displays summary nodes in the Nodes tab', async () => {
    render(<WorkSummaryDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Gist of node 1')).toBeInTheDocument();
      expect(screen.getByText('Gist of node 2')).toBeInTheDocument();
      const chapters = screen.getAllByText('Chapter 1');
      expect(chapters.length).toBeGreaterThan(0);
      const sections = screen.getAllByText('Section 1.1');
      expect(sections.length).toBeGreaterThan(0);
    });
  });

  it('displays abstract in the Abstract tab', async () => {
    render(<WorkSummaryDetailPage />);

    const tabTrigger = await screen.findByRole('tab', { name: /Abstract/i });
    fireEvent.click(tabTrigger);

    await waitFor(() => {
      expect(tabTrigger).toHaveAttribute('data-state', 'active');
    });

    // If Radix is still not rendering content in JSDOM, we might need to mock Tabs
    // but let's try to find it now.
    await waitFor(() => {
      expect(screen.getByText(/This is a test abstract/i)).toBeInTheDocument();
    });
    
    expect(screen.getByRole('button', { name: /Regenerate/i })).toBeInTheDocument();
  });

  it('shows empty state for non-generated summaries', async () => {
    render(<WorkSummaryDetailPage />);

    const tabTrigger = await screen.findByRole('tab', { name: /Outline/i });
    fireEvent.click(tabTrigger);

    await waitFor(() => {
      expect(screen.getByText(/This derived output has not been generated yet/i)).toBeInTheDocument();
    });
    
    // There are two buttons: "Generate" in header and "Generate Now" in card
    expect(screen.getByRole('button', { name: /^Generate$/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Generate Now/i })).toBeInTheDocument();
  });

  it('triggers generation on button click', async () => {
    mockFetch.mockImplementation((url, options) => {
        if (options?.method === 'POST' && url.includes('/derive')) {
            return Promise.resolve({ ok: true, json: async () => ({}) });
        }
        if (url.includes('/nodes')) return Promise.resolve({ ok: true, json: async () => mockNodes });
        if (url.includes('/summaries')) return Promise.resolve({ ok: true, json: async () => mockSummaries });
        if (url.includes('/content')) return Promise.resolve({ ok: true, json: async () => mockWorkInfo });
        return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    render(<WorkSummaryDetailPage />);

    const tabTrigger = await screen.findByRole('tab', { name: /Outline/i });
    fireEvent.click(tabTrigger);

    const generateBtn = await screen.findByRole('button', { name: /^Generate$/ });
    fireEvent.click(generateBtn);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/derive'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ type: 'outline' }),
        })
      );
    });
  });

  it('shows confirmation dialog for re-summarize', async () => {
    render(<WorkSummaryDetailPage />);

    await waitFor(() => {
      fireEvent.click(screen.getByText('Re-summarize'));
    });

    expect(screen.getByText('Re-summarize Work?')).toBeInTheDocument();
    expect(screen.getByText(/This will delete all existing summary nodes/)).toBeInTheDocument();
  });

  it('triggers re-summarization on confirmation', async () => {
    render(<WorkSummaryDetailPage />);

    await waitFor(() => {
      fireEvent.click(screen.getByText('Re-summarize'));
    });

    const confirmBtn = screen.getByRole('button', { name: 'Re-summarize' });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/summarize/1'),
        expect.objectContaining({ method: 'DELETE' })
      );
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/summarize/1?force=true'),
        expect.objectContaining({ method: 'POST' })
      );
      expect(mockPush).toHaveBeenCalledWith('/summarize');
    });
  });

  it('renders line reference links correctly', async () => {
    render(<WorkSummaryDetailPage />);

    await waitFor(() => {
      const externalLinks = screen.getAllByRole('link');
      const corpusLink = externalLinks.find(link => link.getAttribute('href')?.includes('/corpus/1?highlight=1-100'));
      expect(corpusLink).toBeInTheDocument();
    });
  });
});
