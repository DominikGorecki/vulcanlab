import { copyToClipboard } from "../clipboard";

describe("copyToClipboard", () => {
  const originalClipboard = { ...global.navigator.clipboard };

  beforeEach(() => {
    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn().mockImplementation(() => Promise.resolve()),
      },
    });
  });

  afterEach(() => {
    Object.assign(navigator, { clipboard: originalClipboard });
  });

  it("calls navigator.clipboard.writeText with correct text", async () => {
    const text = "test text";
    await copyToClipboard(text);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(text);
  });

  it("throws error if clipboard API is not available", async () => {
    Object.assign(navigator, { clipboard: undefined });
    await expect(copyToClipboard("text")).rejects.toThrow("Clipboard API not available");
  });
});
