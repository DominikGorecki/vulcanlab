import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import SummarizationWorkflowPage from "../page"
import { useParams, useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useParams: jest.fn(),
  useRouter: jest.fn(),
}))

// Mock useToast
jest.mock("@/hooks/use-toast", () => ({
  useToast: jest.fn(),
}))

// Mock fetch
const mockFetch = jest.fn()
global.fetch = mockFetch

// Mock navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn().mockImplementation(() => Promise.resolve()),
  },
})

describe("SummarizationWorkflowPage", () => {
  const mockWorkId = "123"
  const mockToast = jest.fn()

  const mockPrepareData = {
    headings: [
      { chunk_id: 1, level: 1, title: "Heading 1", start_line: 1, content_word_count: 100 },
      { chunk_id: 2, level: 2, title: "Heading 2", start_line: 10, content_word_count: 50 },
    ],
    total_prompts: 2,
    estimated_tokens: 1500,
    has_existing_summaries: true,
  }

  const mockPromptsData = {
    prompts: [
      { prompt_index: 0, content: "Prompt 1 content", heading_ids: [1] },
      { prompt_index: 1, content: "Prompt 2 content", heading_ids: [2] },
    ],
  }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useParams as jest.Mock).mockReturnValue({ work_id: mockWorkId })
    ;(useRouter as jest.Mock).mockReturnValue({ push: jest.fn() })
    ;(useToast as jest.Mock).mockReturnValue({ toast: mockToast })
    
    mockFetch.mockImplementation((url) => {
      if (url.includes("/prepare")) {
        return Promise.resolve({
          ok: true,
          json: async () => mockPrepareData,
        })
      }
      if (url.includes("/generate-prompts")) {
        return Promise.resolve({
          ok: true,
          json: async () => mockPromptsData,
        })
      }
      if (url.includes("/submit-response")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ success: true, summaries_saved: 1, errors: [] }),
        })
      }
      return Promise.reject(new Error("Unknown URL"))
    })
  })

  it("renders loading state initially", () => {
    render(<SummarizationWorkflowPage />)
    expect(screen.getByText(/Preparing Summarization.../i)).toBeInTheDocument()
  })

  it("displays preparation info after loading", async () => {
    render(<SummarizationWorkflowPage />)

    await waitFor(() => {
      expect(screen.getByText("Heading 1")).toBeInTheDocument()
      expect(screen.getByText("100 words")).toBeInTheDocument()
      // Use getAllByText for "2" or check by container
      const twoElements = screen.getAllByText("2")
      expect(twoElements.length).toBeGreaterThanOrEqual(2)
      expect(screen.getByText("1,500")).toBeInTheDocument() // Estimated tokens
    })
  })

  it("shows regenerate checkbox when existing summaries exist", async () => {
    render(<SummarizationWorkflowPage />)

    await waitFor(() => {
      expect(screen.getByLabelText(/Regenerate all summaries/i)).toBeInTheDocument()
    })
  })

  it("transitions to prompt display after clicking generate", async () => {
    render(<SummarizationWorkflowPage />)

    await waitFor(() => screen.getByText("Generate Prompts"))
    fireEvent.click(screen.getByText("Generate Prompts"))

    await waitFor(() => {
      expect(screen.getByText("Step 1 of 2")).toBeInTheDocument()
      expect(screen.getByText("Prompt 1 content")).toBeInTheDocument()
    })
  })

  it("copies prompt to clipboard", async () => {
    render(<SummarizationWorkflowPage />)

    await waitFor(() => screen.getByText("Generate Prompts"))
    fireEvent.click(screen.getByText("Generate Prompts"))

    await waitFor(() => screen.getByText("Copy to Clipboard"))
    fireEvent.click(screen.getByText("Copy to Clipboard"))

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith("Prompt 1 content")
    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
      title: "Copied to clipboard",
    }))
  })

  it("submits response and advances to next prompt", async () => {
    render(<SummarizationWorkflowPage />)

    await waitFor(() => screen.getByText("Generate Prompts"))
    fireEvent.click(screen.getByText("Generate Prompts"))

    await waitFor(() => screen.getByText("Submit Response"))
    
    const textarea = screen.getByPlaceholderText(/Paste JSON response here/i)
    fireEvent.change(textarea, { target: { value: '{"test": "data"}' } })
    
    fireEvent.click(screen.getByText("Submit Response"))

    await waitFor(() => {
      expect(screen.getByText("Step 2 of 2")).toBeInTheDocument()
      expect(screen.getByText("Prompt 2 content")).toBeInTheDocument()
    })
  })

  it("shows completion state after last prompt", async () => {
    render(<SummarizationWorkflowPage />)

    await waitFor(() => screen.getByText("Generate Prompts"))
    fireEvent.click(screen.getByText("Generate Prompts"))

    // Step 1
    await waitFor(() => screen.getByText("Step 1 of 2"))
    fireEvent.change(screen.getByPlaceholderText(/Paste JSON response here/i), { target: { value: '{"test": "data"}' } })
    fireEvent.click(screen.getByText("Submit Response"))

    // Step 2
    await waitFor(() => screen.getByText("Step 2 of 2"))
    fireEvent.change(screen.getByPlaceholderText(/Paste JSON response here/i), { target: { value: '{"test": "data"}' } })
    fireEvent.click(screen.getByText("Submit Response"))

    await waitFor(() => {
      expect(screen.getByText("Summarization Complete!")).toBeInTheDocument()
      expect(screen.getByText("2")).toBeInTheDocument() // Total sections summarized (1 + 1)
    })
  })

  it("handles JSON parsing errors", async () => {
    render(<SummarizationWorkflowPage />)

    await waitFor(() => screen.getByText("Generate Prompts"))
    fireEvent.click(screen.getByText("Generate Prompts"))

    await waitFor(() => screen.getByText("Submit Response"))
    
    const textarea = screen.getByPlaceholderText(/Paste JSON response here/i)
    fireEvent.change(textarea, { target: { value: "invalid json" } })
    
    fireEvent.click(screen.getByText("Submit Response"))

    await waitFor(() => {
      expect(screen.getByText(/Failed to parse LLM response as JSON/i)).toBeInTheDocument()
    })
  })

  it("displays API errors during submission", async () => {
    mockFetch.mockImplementation((url) => {
      if (url.includes("/prepare")) {
        return Promise.resolve({ ok: true, json: async () => mockPrepareData })
      }
      if (url.includes("/generate-prompts")) {
        return Promise.resolve({ ok: true, json: async () => mockPromptsData })
      }
      if (url.includes("/submit-response")) {
        return Promise.resolve({
          ok: false,
          json: async () => ({ detail: "API Error Message" }),
        })
      }
      return Promise.reject(new Error("Unknown URL"))
    })

    render(<SummarizationWorkflowPage />)

    await waitFor(() => screen.getByText("Generate Prompts"))
    fireEvent.click(screen.getByText("Generate Prompts"))

    await waitFor(() => screen.getByText("Submit Response"))
    fireEvent.change(screen.getByPlaceholderText(/Paste JSON response here/i), { target: { value: "{}" } })
    fireEvent.click(screen.getByText("Submit Response"))

    await waitFor(() => {
      expect(screen.getByText("API Error Message")).toBeInTheDocument()
    })
  })
})
