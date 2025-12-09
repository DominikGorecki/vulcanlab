"use client";

import { useState, useEffect, useRef } from "react";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import { Button } from "@/components/ui/button";
import { Eye, FileText } from "lucide-react";

interface MarkdownStickyViewerProps {
  content: string;
  onContentChange?: (content: string) => void;
  readOnly?: boolean;
  title?: string;
}

export function MarkdownStickyViewer({
  content,
  onContentChange,
  readOnly = false,
  title,
}: MarkdownStickyViewerProps) {
  const [viewMode, setViewMode] = useState<"raw" | "rendered">("rendered");
  const [localContent, setLocalContent] = useState(content);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Update local content when prop changes
  useEffect(() => {
    setLocalContent(content);
  }, [content]);

  const handleContentChange = (newContent: string) => {
    setLocalContent(newContent);
    if (onContentChange) {
      onContentChange(newContent);
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    handleContentChange(e.target.value);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with title and toggle */}
      <div className="flex items-center justify-between p-4 border-b bg-card">
        {title && <h3 className="text-lg font-semibold">{title}</h3>}
        <div className="flex gap-2 ml-auto">
          <Button
            size="sm"
            variant={viewMode === "rendered" ? "default" : "outline"}
            onClick={() => setViewMode("rendered")}
            className="gap-2"
          >
            <Eye className="h-4 w-4" />
            Rendered
          </Button>
          <Button
            size="sm"
            variant={viewMode === "raw" ? "default" : "outline"}
            onClick={() => setViewMode("raw")}
            className="gap-2"
          >
            <FileText className="h-4 w-4" />
            Raw
          </Button>
        </div>
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-auto">
        {viewMode === "raw" ? (
          <textarea
            ref={textareaRef}
            value={localContent}
            onChange={handleTextareaChange}
            readOnly={readOnly}
            className="w-full h-full p-4 font-mono text-sm resize-none bg-background focus:outline-none"
            spellCheck={false}
          />
        ) : (
          <div className="sticky-markdown-container h-full overflow-auto p-6">
              <MarkdownRenderer
                content={localContent}
                components={{
                  h1: ({ node, ...props }) => (
                    <h1
                      className="sticky-h1 bg-background/95 backdrop-blur-sm shadow-sm px-2 py-1.5 -mx-2 border-b"
                      style={{
                        position: "sticky",
                        top: "0",
                        zIndex: 40,
                      }}
                      {...props}
                    />
                  ),
                  h2: ({ node, ...props }) => (
                    <h2
                      className="sticky-h2 bg-background/95 backdrop-blur-sm shadow-sm px-2 py-1 -mx-2 border-b"
                      style={{
                        position: "sticky",
                        top: "2.5rem",
                        zIndex: 30,
                      }}
                      {...props}
                    />
                  ),
                  h3: ({ node, ...props }) => (
                    <h3
                      className="sticky-h3 bg-background/90 backdrop-blur-sm shadow-sm px-2 py-0.5 -mx-2 border-b"
                      style={{
                        position: "sticky",
                        top: "5rem",
                        zIndex: 20,
                      }}
                      {...props}
                    />
                  ),
                  h4: ({ node, ...props }) => (
                    <h4
                      className="sticky-h4 bg-background/90 backdrop-blur-sm shadow-sm px-2 py-0.5 -mx-2 border-b"
                      style={{
                        position: "sticky",
                        top: "7.5rem",
                        zIndex: 10,
                      }}
                      {...props}
                    />
                  ),
                }}
              />
          </div>
        )}
      </div>
    </div>
  );
}

