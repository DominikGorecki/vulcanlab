import { truncateToWordLimit } from "../utils";

describe("truncateToWordLimit", () => {
  it("should not truncate if content is within limit", () => {
    const content = "This is a short sentence.";
    expect(truncateToWordLimit(content, 10)).toBe(content);
  });

  it("should truncate and add ellipsis if content exceeds limit", () => {
    const content = "This is a longer sentence that should be truncated.";
    const result = truncateToWordLimit(content, 5);
    expect(result).toBe("This is a longer sentence...");
  });

  it("should handle exact word limit", () => {
    const content = "One two three four five";
    expect(truncateToWordLimit(content, 5)).toBe(content);
  });

  it("should handle empty strings", () => {
    expect(truncateToWordLimit("", 5)).toBe("");
  });

  it("should handle multiple whitespaces", () => {
    const content = "One   two \n three";
    expect(truncateToWordLimit(content, 2)).toBe("One two...");
  });
});

