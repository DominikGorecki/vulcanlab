import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Truncate a string to a maximum number of words.
 *
 * @param content The text to truncate
 * @param maxWords Maximum number of words to keep
 * @returns Truncated text with ellipsis if truncated
 */
export function truncateToWordLimit(content: string, maxWords: number): string {
  const words = content.trim().split(/\s+/);
  if (words.length <= maxWords) {
    return content;
  }
  return words.slice(0, maxWords).join(" ") + "...";
}

/**
 * Processes RAG response content to identify source references at the bottom,
 * formats them into separate lines, and links them to the search result page.
 *
 * Expected formats:
 *   [S1] Source: ... | (work_id=84, start-line=7599, end-line=7643)
 *   [S1] Title > Section | (work_id=84, start-line=7599, end-line=7643)
 *
 * @param content The markdown content to process
 * @returns Processed markdown content
 */
export function processRagSources(content: string): string {
  if (!content) return content;

  // Regex to match the reference pattern: [S#] ... | (work_id=..., start-line=..., end-line=...)
  // We use a broader match first to identify the references section
  // Made more flexible to support references with or without "Source:" prefix
  const referenceRegex = /\[S\d+\]\s+.*?\|\s+\(work_id=\d+,\s+start-line=\d+,\s+end-line=\d+\)/g;
  
  // Find all matches in the entire content
  const matches = Array.from(content.matchAll(referenceRegex));
  if (matches.length === 0) return content;

  // We assume references are at the bottom. We'll split the content at the first reference.
  const firstMatchIndex = matches[0].index!;
  const mainContent = content.substring(0, firstMatchIndex).trimEnd();
  const referencesSection = content.substring(firstMatchIndex);

  // Re-extract references from the section to ensure we get them all even if they were on one line
  const references = referencesSection.match(referenceRegex);
  if (!references) return content;

  // Transform each reference into a linked version and ensure they are on separate lines
  const formattedReferences = references.map(ref => {
    const trimmedRef = ref.trim();
    
    // Extract parameters for the link
    const workIdMatch = trimmedRef.match(/work_id=(\d+)/);
    const startLineMatch = trimmedRef.match(/start-line=(\d+)/);
    const endLineMatch = trimmedRef.match(/end-line=(\d+)/);

    if (workIdMatch && startLineMatch && endLineMatch) {
      const workId = workIdMatch[1];
      const startLine = startLineMatch[1];
      const endLine = endLineMatch[1];
      const link = `/search/result/${workId}/${startLine}/${endLine}`;
      
      // Return as a markdown link
      return `[${trimmedRef}](${link})`;
    }
    
    return trimmedRef;
  });

  // Join with double newlines for clear separation in markdown
  return `${mainContent}\n\n${formattedReferences.join('\n\n')}`;
}
