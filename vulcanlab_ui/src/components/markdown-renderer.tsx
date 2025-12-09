import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Components } from "react-markdown";

interface MarkdownRendererProps {
  content: string;
  className?: string;
  components?: Components;
}

export function MarkdownRenderer({
  content,
  className = "",
  components = {},
}: MarkdownRendererProps) {
  return (
    <div
      className={`prose prose-sm dark:prose-invert max-w-none 
        prose-headings:font-semibold prose-headings:tracking-tight
        prose-h1:text-3xl prose-h1:border-b prose-h1:pb-2 prose-h1:mb-6 prose-h1:mt-8
        prose-h2:text-2xl prose-h2:border-b prose-h2:pb-1 prose-h2:mb-4 prose-h2:mt-6
        prose-h3:text-xl prose-h3:mb-3 prose-h3:mt-5
        prose-p:leading-7 prose-p:mb-4
        prose-ul:my-4 prose-li:my-1
        prose-pre:bg-muted/50 prose-pre:border prose-pre:border-border
        break-words break-all
        overflow-x-hidden
        ${className}`}
    >
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

