import { render, screen, waitFor, fireEvent, act } from "@testing-library/react"
import CorpusWorkViewerPage from "../page"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import { useToast } from "@/hooks/use-toast"

// Mock MarkdownEditor to avoid ESM issues with react-markdown
jest.mock("@/components/markdown-editor", () => ({
  MarkdownEditor: ({ content, highlightLines, onHighlightClear }: any) => (
    <div data-testid="markdown-editor">
      <div data-testid="markdown-content">{content}</div>
      {highlightLines && (
        <div data-testid="highlight-range">
          {highlightLines.start}-{highlightLines.end}
        </div>
      )}
      <button data-testid="clear-highlight" onClick={onHighlightClear}>
        Clear
      </button>
    </div>
  ),
}))

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useParams: jest.fn(),
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}))

// Mock useToast
jest.mock("@/hooks/use-toast", () => ({
  useToast: jest.fn(),
}))

// Mock components
jest.mock("@/components", () => ({
  StickyDetailHeader: ({ title, subtitle, actions }: any) => (
    <div data-testid="sticky-header">
      <h1>{title}</h1>
      <p>{subtitle}</p>
      <div data-testid="header-actions">{actions}</div>
    </div>
  ),
  PageErrorState: ({ error }: any) => <div>Error: {error.message}</div>,
  PageLoadingState: ({ title }: any) => <div>Loading: {title}</div>,
  SummarizationProgressModal: ({ isOpen, progress }: any) => 
    isOpen ? (
      <div data-testid="progress-modal">
        Summarizing work...
        {progress && <div>Processing node {progress.completed_nodes} of {progress.total_nodes}</div>}
      </div>
    ) : null,
  ConfirmDialog: ({ isOpen, onConfirm, title }: any) => 
    isOpen ? (
      <div data-testid="confirm-dialog">
        {title}
        <button onClick={onConfirm}>Confirm Re-summarize</button>
      </div>
    ) : null,
}))

// Mock fetch
const mockFetch = jest.fn()
global.fetch = mockFetch

describe("CorpusDetailPage", () => {
  const mockWorkContent = {
    content: "# Test Content\n\nThis is a test document.",
    filename: "test-work.md",
    work_id: 1,
    work_title: "Test Work Title",
  }

  const mockToast = jest.fn()
  const mockPush = jest.fn()
  const mockReplace = jest.fn()
  const mockSearchParams = new URLSearchParams()

  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
    ;(useParams as jest.Mock).mockReturnValue({ id: "1" })
    ;(useRouter as jest.Mock).mockReturnValue({ push: mockPush, replace: mockReplace })
    ;(useToast as jest.Mock).mockReturnValue({ toast: mockToast })
    ;(useSearchParams as jest.Mock).mockReturnValue(mockSearchParams)
    
    // Default mock for content fetch
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/content")) {
        return Promise.resolve({
          ok: true,
          json: async () => mockWorkContent,
        })
      }
      if (url.includes("/status")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: "none" }),
        })
      }
      return Promise.reject(new Error(`Unexpected call: ${url}`))
    })
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it("displays the correct corpus title in StickyDetailHeader", async () => {
    render(<CorpusWorkViewerPage />)

    await waitFor(() => {
      expect(screen.getByText("Corpus Work")).toBeInTheDocument()
      expect(screen.getByText("Test Work Title")).toBeInTheDocument()
    })
  })

  it("renders the markdown content", async () => {
    render(<CorpusWorkViewerPage />)

    await waitFor(() => {
      expect(screen.getByTestId("markdown-editor")).toBeInTheDocument()
      expect(screen.getByText(/Test Content/)).toBeInTheDocument()
    })
  })

  it("displays the filename in the header actions", async () => {
    render(<CorpusWorkViewerPage />)

    await waitFor(() => {
      expect(screen.getByText("test-work.md")).toBeInTheDocument()
    })
  })

  it("shows error state when fetch fails", async () => {
    mockFetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: false,
        status: 404,
        statusText: "Not Found",
      })
    )

    render(<CorpusWorkViewerPage />)

    await waitFor(() => {
      expect(screen.getByText(/Work not found/i)).toBeInTheDocument()
    })
  })

  it("shows 'Summarize' button when no summary exists", async () => {
    render(<CorpusWorkViewerPage />)

    await waitFor(() => {
      expect(screen.getByText("Summarize")).toBeInTheDocument()
    })
  })

  it("shows 'View Summary' and 'Re-summarize' when summary exists", async () => {
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/status")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: "completed" }),
        })
      }
      return Promise.resolve({
        ok: true,
        json: async () => mockWorkContent,
      })
    })

    render(<CorpusWorkViewerPage />)

    await waitFor(() => {
      expect(screen.getByText("View Summary")).toBeInTheDocument()
      expect(screen.getByText("Re-summarize")).toBeInTheDocument()
    })
  })

  it("triggers summarization and shows progress modal", async () => {
    // Current status is none
    let status = "none";
    
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/corpus/work/1/content")) {
        return Promise.resolve({ ok: true, json: async () => mockWorkContent })
      }
      if (url.includes("/api/v1/summarize/1/status")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status, total_nodes: 10, completed_nodes: 2 }),
        })
      }
      if (url.includes("/api/v1/summarize/1") && !url.includes("/status")) {
        status = "processing";
        return Promise.resolve({ ok: true })
      }
      return Promise.reject(new Error(`Unexpected call: ${url}`))
    })

    render(<CorpusWorkViewerPage />)

    // Wait for initial load
    await screen.findByText("Test Work Title")

    const summarizeBtn = await screen.findByText("Summarize")
    await act(async () => {
      fireEvent.click(summarizeBtn)
    })

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/summarize/1"),
        expect.objectContaining({ method: "POST" })
      )
    })

    // Advance timers to trigger the polling effect
    await act(async () => {
      jest.advanceTimersByTime(2000)
    })
    // Flush promises multiple times to handle async fetch in interval
    for (let i = 0; i < 5; i++) {
      await act(async () => {
        await Promise.resolve()
      })
    }

    await waitFor(() => {
      expect(screen.getByTestId("progress-modal")).toBeInTheDocument()
      expect(screen.getByText(/Processing node 2 of 10/)).toBeInTheDocument()
    })
  })

  it("updates progress via polling and navigates on completion", async () => {
    let callCount = 0
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/content")) {
        return Promise.resolve({ ok: true, json: async () => mockWorkContent })
      }
      if (url.includes("/status")) {
        callCount++
        // 1st call: check on load
        // 2nd call: 1st poll
        // 3rd call: 2nd poll
        if (callCount === 1) return Promise.resolve({ ok: true, json: async () => ({ status: "none" }) })
        if (callCount === 2) return Promise.resolve({ ok: true, json: async () => ({ status: "processing", total_nodes: 10, completed_nodes: 5 }) })
        return Promise.resolve({ ok: true, json: async () => ({ status: "completed", total_nodes: 10, completed_nodes: 10 }) })
      }
      if (url.endsWith("/1")) {
        return Promise.resolve({ ok: true })
      }
      return Promise.reject(new Error(`Unexpected call: ${url}`))
    })

    render(<CorpusWorkViewerPage />)

    // Wait for initial load
    await screen.findByText("Test Work Title")

    const summarizeBtn = await screen.findByText("Summarize")
    await act(async () => {
      fireEvent.click(summarizeBtn)
    })

    // Advance timers to trigger 1st poll
    await act(async () => {
      jest.advanceTimersByTime(2000)
    })
    for (let i = 0; i < 5; i++) { await act(async () => { await Promise.resolve() }) }

    await waitFor(() => {
      expect(screen.getByText(/Processing node 5 of 10/)).toBeInTheDocument()
    })

    // Advance timers to trigger 2nd poll
    await act(async () => {
      jest.advanceTimersByTime(2000)
    })
    for (let i = 0; i < 5; i++) { await act(async () => { await Promise.resolve() }) }

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/summarize/1")
      expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({ title: "Summarization complete" }))
    })
  })

  it("shows confirmation dialog for re-summarize", async () => {
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/status")) {
        return Promise.resolve({ ok: true, json: async () => ({ status: "completed" }) })
      }
      if (url.includes("/content")) {
        return Promise.resolve({ ok: true, json: async () => mockWorkContent })
      }
      if (url.includes("/api/v1/summarize/1")) {
        return Promise.resolve({ ok: true })
      }
      return Promise.reject(new Error(`Unexpected call: ${url}`))
    })

    render(<CorpusWorkViewerPage />)

    const reSummarizeBtn = await screen.findByText("Re-summarize")
    fireEvent.click(reSummarizeBtn)

    expect(screen.getByTestId("confirm-dialog")).toBeInTheDocument()
    
    const confirmBtn = screen.getByText("Confirm Re-summarize")
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/summarize/1?force=true"),
        expect.objectContaining({ method: "POST" })
      )
    })
  })

  describe("highlight parameter", () => {
    it("parses ?highlight=10-20 correctly", async () => {
      const searchParams = new URLSearchParams("highlight=10-20")
      ;(useSearchParams as jest.Mock).mockReturnValue(searchParams)

      render(<CorpusWorkViewerPage />)

      await waitFor(() => {
        expect(screen.getByTestId("highlight-range")).toHaveTextContent("10-20")
      })
    })

    it("handles single line highlight ?highlight=15", async () => {
      const searchParams = new URLSearchParams("highlight=15")
      ;(useSearchParams as jest.Mock).mockReturnValue(searchParams)

      render(<CorpusWorkViewerPage />)

      await waitFor(() => {
        expect(screen.getByTestId("highlight-range")).toHaveTextContent("15-15")
      })
    })

    it("ignores invalid highlight ?highlight=abc", async () => {
      const searchParams = new URLSearchParams("highlight=abc")
      ;(useSearchParams as jest.Mock).mockReturnValue(searchParams)

      render(<CorpusWorkViewerPage />)

      await waitFor(() => {
        expect(screen.queryByTestId("highlight-range")).not.toBeInTheDocument()
      })
    })

    it("ignores invalid range ?highlight=20-10", async () => {
      const searchParams = new URLSearchParams("highlight=20-10")
      ;(useSearchParams as jest.Mock).mockReturnValue(searchParams)

      render(<CorpusWorkViewerPage />)

      await waitFor(() => {
        expect(screen.queryByTestId("highlight-range")).not.toBeInTheDocument()
      })
    })

    it("clears highlight and updates URL when onHighlightClear is called", async () => {
      const searchParams = new URLSearchParams("highlight=10-20&other=param")
      ;(useSearchParams as jest.Mock).mockReturnValue(searchParams)

      render(<CorpusWorkViewerPage />)

      await waitFor(() => {
        expect(screen.getByTestId("highlight-range")).toBeInTheDocument()
      })

      fireEvent.click(screen.getByTestId("clear-highlight"))

      expect(mockReplace).toHaveBeenCalledWith(expect.stringContaining("/corpus/1?other=param"))
      expect(mockReplace).not.toHaveBeenCalledWith(expect.stringContaining("highlight=10-20"))
    })
  })
})
