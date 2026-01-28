"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Save,
  FileText,
  Database,
  Zap,
  Search,
  Brain,
  Hash,
  Activity,
  Link as LinkIcon,
  Loader2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SectionStatusBadge } from "./section-status-badge";
import { SectionDetail as SectionDetailType } from "./types";
import { MarkdownEditor } from "@/components/markdown-editor";
import { TextStats } from "@/components/text-stats";
import { ManualRAGDialog } from "./manual-rag-dialog";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SectionDetailProps {
  section: SectionDetailType;
  mode: "automatic" | "manual";
  expansionId: number;
  onRetry: (sectionId: number) => Promise<void>;
  onSaveManual: (sectionId: number, responseText: string) => Promise<void>;
  onRefresh: () => Promise<void>;
  isLoading?: boolean;
}

export function SectionDetail({
  section,
  mode,
  expansionId,
  onRetry,
  onSaveManual,
  onRefresh,
  isLoading = false,
}: SectionDetailProps) {
  // Draft persistence key
  const DRAFT_KEY = `expansion-section-draft-${section.id}`;

  // Initialize manual response from localStorage or section data
  const [manualResponse, setManualResponse] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(DRAFT_KEY);
      if (saved) return saved;
    }
    return section.response_text || "";
  });

  const [isCopyingPrompt, setIsCopyingPrompt] = useState(false);
  const [isCopyingAugmented, setIsCopyingAugmented] = useState(false);
  const [showRAGData, setShowRAGData] = useState(false);
  const [isManualView, setIsManualView] = useState(mode === "manual" || section.status === "failed");
  const [showManualRAGDialog, setShowManualRAGDialog] = useState(false);

  // Source count selector state
  const availableSourceCount = section.clean_retrieval_context?.chunks?.length || 0;
  const [selectedSourceCount, setSelectedSourceCount] = useState(availableSourceCount || 5);
  const [augmentedPrompt, setAugmentedPrompt] = useState(section.augmented_prompt || "");
  const [regenerating, setRegenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [loadingPrompt, setLoadingPrompt] = useState(false);

  // Persist draft to localStorage
  useEffect(() => {
    if (manualResponse && manualResponse !== section.response_text) {
      localStorage.setItem(DRAFT_KEY, manualResponse);
    }
  }, [manualResponse, section.response_text, DRAFT_KEY]);

  // Reset state when section changes
  useEffect(() => {
    // Reset augmented prompt
    setAugmentedPrompt(section.augmented_prompt || "");

    // Reset manual response - check localStorage for draft, otherwise use section data
    const draftKey = `expansion-section-draft-${section.id}`;
    const savedDraft = typeof window !== 'undefined' ? localStorage.getItem(draftKey) : null;
    setManualResponse(savedDraft || section.response_text || "");

    // Reset source count to match available sources
    const availableSources = section.clean_retrieval_context?.chunks?.length || 0;
    setSelectedSourceCount(availableSources || 5);

    // Reset loading states
    setLoadingPrompt(false);
    setRegenerating(false);
  }, [section.id, section.response_text, section.augmented_prompt, section.clean_retrieval_context?.chunks?.length]);

  // Fetch augmented prompt when section is ready but prompt not loaded
  // This happens after manual RAG completes - the section has retrieval context but augmented_prompt is generated on-demand
  useEffect(() => {
    const shouldFetchPrompt =
      section.status === "ready" &&
      availableSourceCount > 0 &&
      !augmentedPrompt &&
      !loadingPrompt;

    if (shouldFetchPrompt) {
      setLoadingPrompt(true);
      fetch(`${API_BASE_URL}/api/v1/expansions/${expansionId}/sections/${section.id}/generate/prompt`)
        .then(res => res.json())
        .then(data => {
          setAugmentedPrompt(data.prompt);
          setSelectedSourceCount(data.source_count || availableSourceCount);
        })
        .catch(err => console.error("Failed to fetch augmented prompt:", err))
        .finally(() => setLoadingPrompt(false));
    }
  }, [section.status, section.id, availableSourceCount, augmentedPrompt, loadingPrompt, expansionId]);

  // Update selected source count when available sources change
  useEffect(() => {
    if (availableSourceCount > 0 && selectedSourceCount > availableSourceCount) {
      setSelectedSourceCount(availableSourceCount);
    }
  }, [availableSourceCount, selectedSourceCount]);

  const handleSourceCountChange = useCallback(async (value: string) => {
    const newCount = parseInt(value, 10);
    setSelectedSourceCount(newCount);
    setRegenerating(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/expansions/${expansionId}/sections/${section.id}/generate/prompt?top_n=${newCount}`
      );
      if (!response.ok) {
        throw new Error("Failed to regenerate prompt");
      }
      const data = await response.json();
      setAugmentedPrompt(data.prompt);
    } catch (err) {
      console.error("Failed to regenerate prompt:", err);
    } finally {
      setRegenerating(false);
    }
  }, [expansionId, section.id]);

  const handleExpand = async () => {
    if (mode === "manual") {
      // In manual mode, open dialog instead of calling API
      setShowManualRAGDialog(true);
    } else {
      // In automatic mode, call API directly
      await onRetry(section.id);
    }
  };

  const handleManualRAGSuccess = async () => {
    // Refresh section data after manual RAG completes
    await onRefresh();
  };

  const handleCopy = async (text: string, setCopyState: (v: boolean) => void) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopyState(true);
      setTimeout(() => setCopyState(false), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  const handleSaveManual = async () => {
    if (!manualResponse.trim()) return;

    setIsSaving(true);
    try {
      await onSaveManual(section.id, manualResponse);
      // Clear draft after successful save
      localStorage.removeItem(DRAFT_KEY);
    } finally {
      setIsSaving(false);
    }
  };

  const showManualInput = isManualView || mode === "manual";
  const isRAGComplete = section.status === "ready" && section.augmented_prompt;
  const needsManualInput = isRAGComplete && !section.response_text;

  return (
    <>
      <ManualRAGDialog
        expansionId={expansionId}
        sectionId={section.id}
        open={showManualRAGDialog}
        onOpenChange={setShowManualRAGDialog}
        onSuccess={handleManualRAGSuccess}
      />

      <div className="space-y-6">
        <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h3 className="text-lg font-semibold">{section.heading}</h3>
          <p className="text-sm text-muted-foreground">{section.summary}</p>
        </div>
        <div className="flex items-center gap-2">
          <SectionStatusBadge status={section.status} />
          {section.status === "pending" && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleExpand}
              disabled={isLoading}
              className="gap-2"
            >
              <Database className="h-4 w-4" />
              Run RAG
            </Button>
          )}
          {section.status === "failed" && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleExpand}
              disabled={isLoading}
              className="gap-2"
            >
              <RotateCcw className="h-4 w-4" />
              Retry
            </Button>
          )}
        </div>
      </div>

      {section.error_message && (
        <div className="p-4 bg-destructive/10 border border-destructive text-destructive text-sm rounded-md">
          <p className="font-semibold">Error:</p>
          <p>{section.error_message}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Column: Input/Prompts */}
        <div className="space-y-4">
          {loadingPrompt ? (
            <Card className="border-amber-200 bg-amber-50/30 dark:border-amber-900/50 dark:bg-amber-950/10">
              <CardContent className="py-12 flex flex-col items-center justify-center gap-4">
                <Loader2 className="h-8 w-8 animate-spin text-amber-600" />
                <p className="text-muted-foreground">Loading augmented prompt with sources...</p>
              </CardContent>
            </Card>
          ) : augmentedPrompt ? (
            <Card className="border-amber-200 bg-amber-50/30 dark:border-amber-900/50 dark:bg-amber-950/10">
              <CardHeader className="py-3 px-4 flex flex-row items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-amber-600" />
                  <CardTitle className="text-sm font-medium">Augmented Prompt (RAG Complete)</CardTitle>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopy(augmentedPrompt, setIsCopyingAugmented)}
                  className="gap-2"
                >
                  {isCopyingAugmented ? (
                    <>
                      <Check className="h-4 w-4 text-green-500" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Copy Prompt
                    </>
                  )}
                </Button>
              </CardHeader>
              <CardContent className="p-4 pt-0">
                {/* Source count selector */}
                <div className="flex items-center gap-3 mb-3 pb-3 border-b border-amber-100 dark:border-amber-900/30">
                  <Label htmlFor="source-count" className="text-sm font-medium whitespace-nowrap">
                    Sources to include:
                  </Label>
                  <Select
                    value={selectedSourceCount.toString()}
                    onValueChange={handleSourceCountChange}
                    disabled={regenerating || availableSourceCount === 0}
                  >
                    <SelectTrigger id="source-count" className="w-[140px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from({ length: availableSourceCount }, (_, i) => i + 1).map(n => (
                        <SelectItem key={n} value={n.toString()}>
                          {n} {n === 1 ? 'source' : 'sources'}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <span className="text-sm text-muted-foreground">
                    ({availableSourceCount} available)
                  </span>
                  {regenerating && (
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  )}
                  <TextStats text={augmentedPrompt} className="text-xs ml-auto" />
                </div>
                <div className="bg-muted/50 p-3 rounded-md text-sm font-mono whitespace-pre-wrap max-h-[500px] overflow-y-auto border border-amber-100 dark:border-amber-900/30">
                  {augmentedPrompt}
                </div>
                <CardDescription className="mt-2 text-[10px]">
                  Copy this prompt and paste into your preferred LLM. Adjust sources above if needed.
                </CardDescription>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader className="py-3 px-4 flex flex-row items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-amber-500" />
                  <CardTitle className="text-sm font-medium">Expansion Prompt</CardTitle>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleCopy(section.expansion_prompt, setIsCopyingPrompt)}
                >
                  {isCopyingPrompt ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                </Button>
              </CardHeader>
              <CardContent className="p-4 pt-0">
                <div className="bg-muted p-3 rounded-md text-sm font-mono whitespace-pre-wrap max-h-[200px] overflow-y-auto border">
                  {section.expansion_prompt}
                </div>
                <CardDescription className="mt-2 text-[10px]">
                  The base prompt. Run "Run RAG" to generate an augmented prompt with context.
                </CardDescription>
              </CardContent>
            </Card>
          )}

          {/* RAG Data Toggle */}
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-between"
            onClick={() => setShowRAGData(!showRAGData)}
          >
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              RAG Pipeline Data
            </div>
            {showRAGData ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>

          {showRAGData && (
            <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
              {section.augmented_prompt && (
                <Card>
                  <CardHeader className="py-3 px-4 flex flex-row items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Zap className="h-3 w-3 text-amber-500" />
                      <CardTitle className="text-xs font-medium">Original Expansion Prompt</CardTitle>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                      onClick={() => handleCopy(section.expansion_prompt, setIsCopyingPrompt)}
                    >
                      {isCopyingPrompt ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                    </Button>
                  </CardHeader>
                  <CardContent className="px-4 pb-3">
                    <div className="bg-muted p-2 rounded text-[10px] font-mono whitespace-pre-wrap max-h-[100px] overflow-y-auto border">
                      {section.expansion_prompt}
                    </div>
                  </CardContent>
                </Card>
              )}
              {section.expanded_queries && section.expanded_queries.queries && (
                <Card>
                  <CardHeader className="py-2 px-4">
                    <div className="flex items-center gap-2">
                      <Search className="h-3 w-3" />
                      <CardTitle className="text-xs font-medium">Expanded Queries</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent className="px-4 pb-3">
                    <ul className="list-disc list-inside text-xs space-y-1">
                      {section.expanded_queries.queries.map((q, i) => (
                        <li key={i}>{q}</li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {section.hyde_answer && (
                <Card>
                  <CardHeader className="py-2 px-4">
                    <div className="flex items-center gap-2">
                      <Brain className="h-3 w-3" />
                      <CardTitle className="text-xs font-medium">HyDE Answer</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent className="px-4 pb-3">
                    <p className="text-xs italic text-muted-foreground line-clamp-3">
                      {section.hyde_answer}
                    </p>
                  </CardContent>
                </Card>
              )}

              {section.clean_retrieval_context && section.clean_retrieval_context.chunks && section.clean_retrieval_context.chunks.length > 0 && (
                <Card>
                  <CardHeader className="py-2 px-4">
                    <div className="flex items-center gap-2">
                      <LinkIcon className="h-3 w-3" />
                      <CardTitle className="text-xs font-medium">Sources ({section.clean_retrieval_context.chunks.length})</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent className="px-4 pb-3">
                    <div className="max-h-[150px] overflow-y-auto pr-2">
                      <ul className="list-disc list-inside text-[10px] space-y-1">
                        {section.clean_retrieval_context.chunks.map((chunk, i) => (
                          <li key={i} className="text-muted-foreground truncate" title={`${chunk.work_title} | Line ${chunk.start_line}-${chunk.end_line}`}>
                            <span className="text-foreground font-medium">{chunk.work_title}</span>
                            {" "}(L{chunk.start_line}-{chunk.end_line})
                          </li>
                        ))}
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              )}

              <div className="flex gap-2">
                {section.intent && (
                  <Badge variant="outline" className="text-[10px] gap-1">
                    <Activity className="h-2 w-2" />
                    Intent: {section.intent}
                  </Badge>
                )}
                {section.entities && section.entities.entities && section.entities.entities.length > 0 && (
                  <Badge variant="outline" className="text-[10px] gap-1">
                    <Hash className="h-2 w-2" />
                    Entities: {section.entities.entities.length}
                  </Badge>
                )}
              </div>

            </div>
          )}
        </div>

        {/* Right Column: Output/Response */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium">Response</h4>
            {mode === "automatic" && (
              <div className="flex border rounded-md p-1 bg-muted/50">
                <Button
                  variant={!showManualInput ? "secondary" : "ghost"}
                  size="sm"
                  className="h-7 text-[10px] px-2"
                  onClick={() => setIsManualView(false)}
                >
                  Automatic
                </Button>
                <Button
                  variant={showManualInput ? "secondary" : "ghost"}
                  size="sm"
                  className="h-7 text-[10px] px-2"
                  onClick={() => setIsManualView(true)}
                >
                  Manual
                </Button>
              </div>
            )}
          </div>

          {showManualInput ? (
            <Card className="h-full flex flex-col">
              <CardHeader className="py-3 px-4">
                <CardTitle className="text-sm font-medium">Manual Entry</CardTitle>
                <CardDescription className="text-[10px]">
                  {augmentedPrompt
                    ? "Copy the Augmented prompt above, run it in your preferred LLM, and paste the result below."
                    : "Run RAG first to get the augmented prompt with sources."}
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 pt-0 flex-grow flex flex-col gap-4">
                <Textarea
                  value={manualResponse}
                  onChange={(e) => setManualResponse(e.target.value)}
                  placeholder="Paste response from external LLM here..."
                  className="flex-grow font-sans text-sm min-h-[300px]"
                />
                <Button
                  onClick={handleSaveManual}
                  disabled={isLoading || isSaving || !manualResponse.trim()}
                  className="w-full gap-2"
                >
                  {isSaving ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4" />
                      Save Manual Response
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Card className="h-full flex flex-col">
              <CardHeader className="py-3 px-4">
                <CardTitle className="text-sm font-medium">System Response</CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-0 flex-grow">
                {section.response_text ? (
                  <div className="prose prose-sm dark:prose-invert max-w-none border rounded-md p-4 bg-card h-[400px] overflow-y-auto">
                    <MarkdownEditor
                      content={section.response_text}
                      readOnly={true}
                      viewMode="both"
                    />
                  </div>
                ) : (
                  <div className="h-[400px] flex flex-col items-center justify-center border border-dashed rounded-md text-muted-foreground gap-2">
                    {section.status === "generating" || section.status === "expanding" ? (
                      <>
                        <Loader2 className="h-8 w-8 animate-spin" />
                        <p className="text-sm">Processing section...</p>
                      </>
                    ) : (
                      <>
                        <FileText className="h-8 w-8 opacity-20" />
                        <p className="text-sm">No response yet</p>
                        {mode === "automatic" && section.status === "ready" && (
                          <Button
                            size="sm"
                            onClick={() => onRetry(section.id)}
                            disabled={isLoading}
                            className="mt-2"
                          >
                            Generate Now
                          </Button>
                        )}
                      </>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      </div>
    </>
  );
}
