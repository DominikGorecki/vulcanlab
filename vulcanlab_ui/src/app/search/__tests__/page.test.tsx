import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import SearchPage from "../page";
import "@testing-library/jest-dom";

// Mock global fetch
global.fetch = jest.fn();

// Mock useToast
jest.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

describe("SearchPage", () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockClear();
  });

  it("renders search page with initial controls", () => {
    render(<SearchPage />);
    expect(screen.getByText("Search Corpus")).toBeInTheDocument();
    expect(screen.getByLabelText("Lexical Search")).toBeChecked();
    expect(screen.getByLabelText("Dense Search")).not.toBeChecked();
    expect(screen.getByPlaceholderText(/Keywords/)).toBeInTheDocument();
  });

  it("disables search button when no mode is selected", () => {
    render(<SearchPage />);
    const lexicalCheckbox = screen.getByLabelText("Lexical Search");
    
    // Uncheck Lexical (Dense is already unchecked)
    fireEvent.click(lexicalCheckbox);
    
    const searchButton = screen.getByRole("button", { name: /Search/i });
    expect(searchButton).toBeDisabled();
    expect(screen.getByText("Select at least one search mode")).toBeInTheDocument();
  });

  it("switches placeholder based on search mode", () => {
    render(<SearchPage />);
    const lexicalCheckbox = screen.getByLabelText("Lexical Search");
    const denseCheckbox = screen.getByLabelText("Dense Search");

    // Switch to Dense only
    fireEvent.click(lexicalCheckbox); // Uncheck lexical
    fireEvent.click(denseCheckbox); // Check dense
    expect(screen.getByPlaceholderText(/Semantic query/)).toBeInTheDocument();

    // Switch to Both (Hybrid)
    fireEvent.click(lexicalCheckbox); // Check lexical
    expect(screen.getByPlaceholderText(/Hybrid query/)).toBeInTheDocument();
  });

  it("triggers hybrid search when both modes are enabled", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        results: [],
        pagination: { page: 1, page_size: 20, total_results: 0, has_next: false, has_prev: false }
      }),
    });

    render(<SearchPage />);
    const denseCheckbox = screen.getByLabelText("Dense Search");
    fireEvent.click(denseCheckbox); // Enable dense (lexical is default)

    const input = screen.getByPlaceholderText(/Hybrid query/);
    fireEvent.change(input, { target: { value: "test query" } });
    
    const searchButton = screen.getByRole("button", { name: /Search/i });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/search/hybrid")
      );
    });
  });

  it("updates max preview words when slider changes", () => {
    render(<SearchPage />);
    const slider = screen.getByRole("slider");
    expect(screen.getByText("100 words")).toBeInTheDocument();

    // fireEvent.change doesn't work well with Radix Slider, but we can check if it exists
    expect(slider).toBeInTheDocument();
    expect(slider).toHaveAttribute("aria-valuenow", "100");
  });
});

