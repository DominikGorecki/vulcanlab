"use client";

import { useState, useRef, useEffect } from "react";
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
}

export function MarkdownEditor({
  content,
  onChange,
  readOnly = false,
  viewMode = "both",
  scrollMode = "container",
  className = "",
}: MarkdownEditorProps) {
  const [userTab, setUserTab] = useState<string>("rendered");
  const [editorHeight, setEditorHeight] = useState("100%");
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  
  // Force light theme (white background) as requested
  const monacoTheme = "light";

  const activeTab = viewMode === "markdown-only" ? "markdown" : userTab;

  const handleEditorChange = (value: string | undefined) => {
    if (onChange && value !== undefined) {
      onChange(value);
    }
  };

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
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
  };

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
                <MarkdownRenderer content={content} />
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
