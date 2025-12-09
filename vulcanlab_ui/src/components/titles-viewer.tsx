"use client";

import { useState, useEffect, useRef } from "react";

interface TitlesViewerProps {
  content: string;
  onContentChange?: (content: string) => void;
  readOnly?: boolean;
  title?: string;
  onScroll?: (scrollTop: number, scrollHeight: number, clientHeight: number) => void;
  syncScroll?: boolean;
  externalScrollTop?: number;
}

export function TitlesViewer({
  content,
  onContentChange,
  readOnly = false,
  title,
  onScroll,
  syncScroll = false,
  externalScrollTop,
}: TitlesViewerProps) {
  const [localContent, setLocalContent] = useState(content);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isScrollingFromExternal = useRef(false);

  // Update local content when prop changes
  useEffect(() => {
    setLocalContent(content);
  }, [content]);

  // Handle external scroll updates
  useEffect(() => {
    if (syncScroll && externalScrollTop !== undefined && textareaRef.current) {
      // Only update if the scroll position is actually different
      if (Math.abs(textareaRef.current.scrollTop - externalScrollTop) > 1) {
        isScrollingFromExternal.current = true;
        textareaRef.current.scrollTop = externalScrollTop;
        // Reset flag after a short delay
        setTimeout(() => {
          isScrollingFromExternal.current = false;
        }, 100);
      }
    }
  }, [externalScrollTop, syncScroll]);

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    setLocalContent(newContent);
    if (onContentChange) {
      onContentChange(newContent);
    }
  };

  const handleScroll = (e: React.UIEvent<HTMLTextAreaElement>) => {
    // Don't propagate scroll events that came from external source
    if (isScrollingFromExternal.current) {
      return;
    }

    const target = e.currentTarget;
    if (onScroll) {
      onScroll(target.scrollTop, target.scrollHeight, target.clientHeight);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with title */}
      {title && (
        <div className="p-3 border-b bg-card">
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
      )}

      {/* Content area - single scrollable textarea */}
      <textarea
        ref={textareaRef}
        value={localContent}
        onChange={handleContentChange}
        onScroll={handleScroll}
        readOnly={readOnly}
        className="flex-1 w-full p-4 font-mono text-sm resize-none bg-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        spellCheck={false}
        placeholder="No titles found..."
      />
    </div>
  );
}

