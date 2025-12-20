import { render, screen, waitFor } from "@testing-library/react"
import CorpusWorkViewerPage from "../page"
import { useParams, useRouter } from "next/navigation"

// Mock MarkdownEditor to avoid ESM issues with react-markdown
jest.mock("@/components/markdown-editor", () => ({
  MarkdownEditor: ({ content }: { content: string }) => <div data-testid="markdown-editor">{content}</div>,
}))

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useParams: jest.fn(),
  useRouter: jest.fn(),
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

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useParams as jest.Mock).mockReturnValue({ id: "1" })
    ;(useRouter as jest.Mock).mockReturnValue({ push: jest.fn() })
    
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockWorkContent,
    })
  })

  it("displays the correct corpus title in StickyDetailHeader", async () => {
    render(<CorpusWorkViewerPage />)

    await waitFor(() => {
      // StickyDetailHeader uses title="Corpus Work" and subtitle as the work title
      expect(screen.getByText("Corpus Work")).toBeInTheDocument()
      expect(screen.getByText("Test Work Title")).toBeInTheDocument()
    })
  })

  it("renders the markdown content", async () => {
    render(<CorpusWorkViewerPage />)

    await waitFor(() => {
      expect(screen.getByText("Test Content")).toBeInTheDocument()
      expect(screen.getByText("This is a test document.")).toBeInTheDocument()
    })
  })

  it("displays the filename in the header actions", async () => {
    render(<CorpusWorkViewerPage />)

    await waitFor(() => {
      expect(screen.getByText("test-work.md")).toBeInTheDocument()
    })
  })

  it("shows error state when fetch fails", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
    })

    render(<CorpusWorkViewerPage />)

    await waitFor(() => {
      expect(screen.getByText(/Work not found/i)).toBeInTheDocument()
    })
  })
})
