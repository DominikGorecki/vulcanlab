/**
 * TextStats - Displays word count and estimated token count for text
 */

interface TextStatsProps {
  text: string;
  className?: string;
}

// Utility functions for text statistics
function countWords(text: string): number {
  if (!text) return 0;
  // Split by whitespace and filter out empty strings
  return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

function estimateTokens(text: string): number {
  if (!text) return 0;
  // Common heuristic: ~1 token per 4 characters for English text
  // This is approximately 0.75 tokens per word
  // Using character-based estimation as it's more consistent
  return Math.ceil(text.length / 4);
}

export function TextStats({ text, className = "" }: TextStatsProps) {
  const wordCount = countWords(text);
  const tokenCount = estimateTokens(text);

  return (
    <div className={`text-sm text-muted-foreground ${className}`}>
      Words: {wordCount.toLocaleString()} | Tokens: ~{tokenCount.toLocaleString()}
    </div>
  );
}
