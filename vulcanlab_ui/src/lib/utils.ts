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

/**
 * Extract JSON string from text, handling markdown blocks, double braces, 
 * and conversational filler.
 */
export function extractJson(text: string): string {
  if (!text) return "";

  const content = text.trim();

  // 1. Try to find the best JSON block using code blocks first
  const codeBlocks = content.match(/```(?:json)?\s*([\s\S]*?)\s*```/g);
  if (codeBlocks && codeBlocks.length > 0) {
    // Try each code block from last to first (LLMs often show an example first)
    for (let i = codeBlocks.length - 1; i >= 0; i--) {
      const inner = codeBlocks[i].match(/```(?:json)?\s*([\s\S]*?)\s*```/)?.[1];
      if (inner) {
        const cleaned = _cleanJsonString(inner.trim());
        try {
          JSON.parse(cleaned);
          return cleaned;
        } catch (e) {
          // If it's the only one or the last one, we'll use it as fallback even if invalid
          if (i === 0) return cleaned;
        }
      }
    }
  }

  // 2. No code blocks or none were valid. Search for outermost { ... } or [ ... ]
  const starts = [];
  const ends = [];
  for (let i = 0; i < content.length; i++) {
    if (content[i] === '{' || content[i] === '[') starts.push(i);
    if (content[i] === '}' || content[i] === ']') ends.push(i);
  }
  
  if (starts.length > 0 && ends.length > 0) {
    // Check first few and last few to find a valid pair
    const maxToCheck = 10;
    let bestCandidate = "";

    for (let s = 0; s < Math.min(starts.length, maxToCheck); s++) {
      for (let e = ends.length - 1; e >= Math.max(0, ends.length - maxToCheck); e--) {
        const startIdx = starts[s];
        const endIdx = ends[e];
        if (endIdx > startIdx) {
          const candidate = content.substring(startIdx, endIdx + 1);
          const cleaned = _cleanJsonString(candidate);
          try {
            JSON.parse(cleaned);
            return cleaned;
          } catch (err) {
            if (!bestCandidate || candidate.length > bestCandidate.length) {
              bestCandidate = cleaned;
            }
          }
        }
      }
    }
    if (bestCandidate) return bestCandidate;
  }

  return _cleanJsonString(content);
}

/**
 * Internal helper to clean a potential JSON string of common LLM artifacts.
 */
function _cleanJsonString(jsonStr: string): string {
  let cleaned = jsonStr.trim();

  // 1. Handle double braces {{ ... }} -> { ... }
  if (cleaned.startsWith('{{') && cleaned.endsWith('}}')) {
    cleaned = cleaned.substring(1, cleaned.length - 1).trim();
  }

  // 2. Remove C-style comments (// or /* */)
  cleaned = cleaned.replace(/\/\*[\s\S]*?\*\/|([^\\:]|^)\/\/.*$/gm, '$1');

  // 3. Replace smart quotes with standard quotes
  cleaned = cleaned.replace(/[\u201C\u201D]/g, '"'); 
  cleaned = cleaned.replace(/[\u2018\u2019]/g, "'");

  // 4. Handle "garbage" lines that LLMs often hallucinate between valid keys
  // Specifically lines like ? or ?", or * that aren't valid JSON
  const lines = cleaned.split('\n');
  const filteredLines = lines.filter(line => {
    const trimmed = line.trim();
    // Keep lines that:
    // - Start/end with braces or brackets
    // - Contain a colon (likely a key-value pair)
    // - Are just a comma or closing brace
    // - Are empty
    if (!trimmed) return true;
    if (/^[\[\]{}]*,?$/.test(trimmed)) return true;
    if (trimmed.includes(':')) return true;
    if (trimmed === ',') return true;
    
    // If it's a very short line with punctuation like ?", it's likely garbage
    if (trimmed.length < 10 && /[?*!]/.test(trimmed)) return false;
    
    return true;
  });
  cleaned = filteredLines.join('\n');

  // 5. Handle trailing commas aggressively
  cleaned = cleaned.replace(/,(\s*[\]}])/g, '$1');
  cleaned = cleaned.replace(/,[\s\r\n\t]*,/g, ','); 

  // 6. Fix single-quoted keys and values
  cleaned = cleaned.replace(/([{,]\s*)'([^']+)'(\s*:)/g, '$1"$2"$3');
  cleaned = cleaned.replace(/:\s*'([^"'\n]+)'(?=\s*[,}\]])/g, ': "$1"');

  return cleaned;
}
