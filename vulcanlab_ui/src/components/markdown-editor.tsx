"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import Editor, { OnMount } from "@monaco-editor/react";
import type { editor } from "monaco-editor";

interface MarkdownEditorProps {
  content: string;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  viewMode?: "both" | "markdown-only";
  scrollMode?: "container" | "page";
  className?: string;
  processSources?: boolean;
  highlightLines?: { start: number; end: number } | null;
  onHighlightClear?: () => void;
}

export function MarkdownEditor({
  content,
  onChange,
  readOnly = false,
  viewMode = "both",
  scrollMode = "container",
  className = "",
  processSources = false,
  highlightLines = null,
  onHighlightClear,
}: MarkdownEditorProps) {
  const [userTab, setUserTab] = useState<string>("rendered");
  const [editorHeight, setEditorHeight] = useState("100%");
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const decorationIdsRef = useRef<string[]>([]);
  
  // Force light theme (white background) as requested
  const monacoTheme = "light";

  const activeTab = viewMode === "markdown-only" ? "markdown" : userTab;

  // Automatically switch to markdown tab if highlightLines is provided
  useEffect(() => {
    if (highlightLines && viewMode === "both" && userTab !== "markdown") {
      setUserTab("markdown");
    }
  }, [highlightLines, viewMode, userTab]);

  const handleEditorChange = (value: string | undefined) => {
    if (onChange && value !== undefined) {
      onChange(value);
    }
  };

  const applyHighlight = (editor: editor.IStandaloneCodeEditor, range: { start: number; end: number }) => {
    const start = Math.max(1, range.start);
    const end = Math.max(start, range.end);
    
    decorationIdsRef.current = editor.deltaDecorations(decorationIdsRef.current, [
      {
        range: { startLineNumber: start, startColumn: 1, endLineNumber: end, endColumn: 1 },
        options: {
          isWholeLine: true,
          className: "line-highlight",
          marginClassName: "line-highlight-margin",
        },
      },
    ]);

    // Scroll to the highlighted range
    editor.revealRangeInCenter(
      { 
        startLineNumber: start, 
        startColumn: 1, 
        endLineNumber: end, 
        endColumn: 1 
      }, 
      1 // 1 is Smooth scroll
    );
  };

  const clearHighlight = useCallback(() => {
    if (editorRef.current && decorationIdsRef.current.length > 0) {
      decorationIdsRef.current = editorRef.current.deltaDecorations(decorationIdsRef.current, []);
      if (onHighlightClear) {
        onHighlightClear();
      }
    }
  }, [onHighlightClear]);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    
    if (highlightLines) {
      applyHighlight(editor, highlightLines);
    }

    // Add click listener to clear highlight
    const mouseDownListener = editor.onMouseDown((e) => {
      if (decorationIdsRef.current.length > 0) {
        // If the user clicks elsewhere, clear the highlight
        // We check if the click is within the highlighted lines
        if (highlightLines) {
          const clickedLine = e.target.position?.lineNumber;
          if (clickedLine && (clickedLine < highlightLines.start || clickedLine > highlightLines.end)) {
            clearHighlight();
          }
        } else {
          clearHighlight();
        }
      }
    });

    if (scrollMode === "page") {
      const updateHeight = () => {
        const contentHeight = editor.getContentHeight();
        setEditorHeight(`${Math.max(100, contentHeight)}px`);
        editor.layout();
      };
      editor.onDidContentSizeChange(updateHeight);
      // Initial update
      updateHeight();
    }

    return () => {
      mouseDownListener.dispose();
    };
  };

  // Handle highlightLines updates after mount
  useEffect(() => {
    if (editorRef.current) {
      if (highlightLines) {
        applyHighlight(editorRef.current, highlightLines);
      } else if (decorationIdsRef.current.length > 0) {
        decorationIdsRef.current = editorRef.current.deltaDecorations(decorationIdsRef.current, []);
      }
    }
  }, [highlightLines]);

  // Re-measure when tab changes or content updates in page mode
  useEffect(() => {
    if (scrollMode === "page" && activeTab === "markdown" && editorRef.current) {
      const contentHeight = editorRef.current.getContentHeight();
      setEditorHeight(`${Math.max(100, contentHeight)}px`);
    }
  }, [activeTab, content, scrollMode]);

  // CSS classes based on scrollMode
  const containerClass = scrollMode === "container" ? "h-full" : "";
  const tabListClass = scrollMode === "container" ? "flex-1 flex flex-col overflow-hidden" : "flex-1 flex flex-col";
  const contentContainerClass = scrollMode === "container" ? "flex-1 overflow-hidden mt-0" : "mt-0";
  const cardClass = scrollMode === "container" ? "h-full overflow-hidden" : "border-0";
  
  // For Rendered view: Use ScrollArea in container mode, plain div in page mode
  const RenderedWrapper = scrollMode === "container" ? ScrollArea : "div";
  const renderedWrapperProps = scrollMode === "container" ? { className: "h-full p-6" } : { className: "p-6" };

  return (
    <div className={`flex flex-col ${containerClass} ${className}`}>
      <Tabs 
        value={activeTab} 
        onValueChange={setUserTab} 
        className={tabListClass}
      >
        {viewMode === "both" && (
          <div className="flex items-center justify-between mb-4">
            <TabsList className="w-[200px]">
              <TabsTrigger value="rendered">Rendered</TabsTrigger>
              <TabsTrigger value="markdown">Markdown</TabsTrigger>
            </TabsList>
          </div>
        )}

        <TabsContent value="rendered" className={contentContainerClass}>
          <Card className={cardClass}>
            <CardContent className="h-full p-0">
              <RenderedWrapper {...renderedWrapperProps}>
                <MarkdownRenderer content={content} processSources={processSources} />
              </RenderedWrapper>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="markdown" className={contentContainerClass}>
          <Card className={scrollMode === "container" ? "h-full border-0 rounded-none" : "border-0 rounded-none"}>
            <CardContent className="h-full p-0">
              <Editor
                height={scrollMode === "container" ? "100%" : editorHeight}
                defaultLanguage="markdown"
                value={content}
                theme={monacoTheme}
                onChange={handleEditorChange}
                onMount={handleEditorDidMount}
                options={{
                  readOnly: readOnly,
                  lineNumbers: "on",
                  minimap: { enabled: false },
                  wordWrap: "on",
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  padding: scrollMode === "page" ? { top: 3, bottom: 16 } : { top: 16, bottom: 16 },
                  fontSize: 14,
                  fontFamily: scrollMode === "page" ? "Inter, Inter Fallback, monospace" : "monospace",
                  overviewRulerLanes: scrollMode === "page" ? 0 : undefined,
                  scrollbar: scrollMode === "page" ? {
                    vertical: "hidden",
                    handleMouseWheel: false,
                  } : undefined,
                }}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
