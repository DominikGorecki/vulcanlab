"use client";

import React, { useCallback, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  StickyDetailHeader,
  PageLoadingState,
  PageErrorState,
  ConfirmDialog,
  StatusBadge,
} from "@/components";
import { usePageData } from "@/hooks/use-page-data";
import { useToast } from "@/hooks/use-toast";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  BookOpen,
  ChevronRight,
  ExternalLink,
  FileText,
  List,
  RefreshCw,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// --- Interfaces ---

interface SummaryNode {
  id: number;
  chunk_id: number;
  work_id: number;
  gist: string;
  key_points: any[];
  definitions: any[];
  key_terms: any[];
  examples: any[];
  start_line: number;
  end_line: number;
  salience_score: number;
  heading_breadcrumbs: string | null;
  level: string | null;
  parent_id: number | null;
}

interface WorkSummary {
  id: number;
  work_id: number;
  type: string;
  content: any;
  line_references: any[];
}

interface PageData {
  nodes: SummaryNode[];
  summaries: WorkSummary[];
  workTitle: string;
}

// --- Components ---

interface NodeTreeProps {
  nodes: SummaryNode[];
  workId: string;
}

const SummaryNodeCard = ({ node, workId }: { node: SummaryNode; workId: string }) => {
  const breadcrumbs = node.heading_breadcrumbs ? node.heading_breadcrumbs.split(" > ") : [];
  const heading = breadcrumbs.length > 0 ? breadcrumbs[breadcrumbs.length - 1] : "Section";

  return (
    <Card className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {breadcrumbs.map((bc, i) => (
                <React.Fragment key={i}>
                  {i > 0 && <ChevronRight size={12} />}
                  <span>{bc}</span>
                </React.Fragment>
              ))}
            </div>
            <CardTitle className="text-lg">{heading}</CardTitle>
          </div>
          <Link
            href={`/corpus/${workId}?highlight=${node.start_line}-${node.end_line}`}
            target="_blank"
            className="text-muted-foreground hover:text-primary transition-colors"
          >
            <ExternalLink size={16} />
          </Link>
        </div>
        <CardDescription className="text-foreground font-medium mt-2">
          {node.gist}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Accordion type="multiple" className="w-full">
          {node.key_points.length > 0 && (
            <AccordionItem value="key-points">
              <AccordionTrigger className="text-sm py-2">Key Points</AccordionTrigger>
              <AccordionContent>
                <ul className="list-disc pl-5 space-y-1">
                  {node.key_points.map((kp, i) => (
                    <li key={i} className="text-sm">
                      {kp.text}
                      <Link
                        href={`/corpus/${workId}?highlight=${kp.start_line}-${kp.end_line}`}
                        target="_blank"
                        className="ml-2 text-xs text-muted-foreground hover:underline inline-flex items-center gap-0.5"
                      >
                        L{kp.start_line} <ExternalLink size={10} />
                      </Link>
                    </li>
                  ))}
                </ul>
              </AccordionContent>
            </AccordionItem>
          )}

          {node.definitions.length > 0 && (
            <AccordionItem value="definitions">
              <AccordionTrigger className="text-sm py-2">Definitions</AccordionTrigger>
              <AccordionContent>
                <div className="space-y-3">
                  {node.definitions.map((d, i) => (
                    <div key={i} className="text-sm">
                      <div className="font-semibold flex items-center gap-2">
                        {d.term}
                        <Link
                          href={`/corpus/${workId}?highlight=${d.start_line}-${d.end_line}`}
                          target="_blank"
                          className="text-xs font-normal text-muted-foreground hover:underline inline-flex items-center gap-0.5"
                        >
                          L{d.start_line} <ExternalLink size={10} />
                        </Link>
                      </div>
                      <p className="text-muted-foreground">{d.definition}</p>
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          )}

          {node.key_terms.length > 0 && (
            <AccordionItem value="key-terms">
              <AccordionTrigger className="text-sm py-2">Key Terms</AccordionTrigger>
              <AccordionContent>
                <div className="flex flex-wrap gap-2">
                  {node.key_terms.map((kt, i) => (
                    <Link
                      key={i}
                      href={`/corpus/${workId}?highlight=${kt.start_line}-${kt.end_line}`}
                      target="_blank"
                      className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-muted text-xs hover:bg-muted/80 transition-colors"
                    >
                      {kt.term} <ExternalLink size={10} />
                    </Link>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          )}

          {node.examples.length > 0 && (
            <AccordionItem value="examples">
              <AccordionTrigger className="text-sm py-2">Examples</AccordionTrigger>
              <AccordionContent>
                <ul className="list-disc pl-5 space-y-2">
                  {node.examples.map((ex, i) => (
                    <li key={i} className="text-sm">
                      {ex.text}
                      <Link
                        href={`/corpus/${workId}?highlight=${ex.start_line}-${ex.end_line}`}
                        target="_blank"
                        className="ml-2 text-xs text-muted-foreground hover:underline inline-flex items-center gap-0.5"
                      >
                        L{ex.start_line} <ExternalLink size={10} />
                      </Link>
                    </li>
                  ))}
                </ul>
              </AccordionContent>
            </AccordionItem>
          )}
        </Accordion>
      </CardContent>
    </Card>
  );
};

// --- Main Page ---

export default function WorkSummaryDetailPage() {
  const params = useParams();
  const workId = params.id as string;
  const router = useRouter();
  const { toast } = useToast();
  const [isGenerating, setIsGenerating] = useState<string | null>(null);
  const [isResummarizing, setIsResummarizing] = useState(false);
  const [showResummarizeConfirm, setShowResummarizeConfirm] = useState(false);

  const fetchPageData = useCallback(async () => {
    const [nodesRes, summariesRes, contentRes] = await Promise.all([
      fetch(`${API_BASE_URL}/api/v1/summarize/${workId}/nodes`),
      fetch(`${API_BASE_URL}/api/v1/summarize/${workId}/summaries`),
      fetch(`${API_BASE_URL}/corpus/work/${workId}/content`),
    ]);

    if (!nodesRes.ok) throw new Error("Failed to fetch summary nodes");
    if (!summariesRes.ok) throw new Error("Failed to fetch summaries");
    if (!contentRes.ok) throw new Error("Failed to fetch work info");

    const nodesData = await nodesRes.json();
    const summariesData = await summariesRes.json();
    const contentData = await contentRes.json();

    return {
      nodes: nodesData.nodes,
      summaries: summariesData,
      workTitle: contentData.work_title,
    };
  }, [workId]);

  const { data, loading, error, refetch } = usePageData<PageData>(fetchPageData);

  const handleGenerate = async (type: string) => {
    setIsGenerating(type);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/summarize/${workId}/derive`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type }),
      });

      if (!response.ok) {
        throw new Error("Failed to generate output");
      }

      toast({
        title: "Success",
        description: `${type.replace('_', ' ')} generated successfully.`,
      });
      refetch();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to generate output",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(null);
    }
  };

  const handleResummarize = async () => {
    setIsResummarizing(true);
    setShowResummarizeConfirm(false);
    try {
      // 1. Delete existing summaries
      await fetch(`${API_BASE_URL}/api/v1/summarize/${workId}`, { method: "DELETE" });
      
      // 2. Trigger new summarization (force=true)
      const triggerRes = await fetch(`${API_BASE_URL}/api/v1/summarize/${workId}?force=true`, { method: "POST" });
      
      if (!triggerRes.ok) throw new Error("Failed to trigger re-summarization");

      toast({
        title: "Summarization started",
        description: "Regenerating summary nodes. This may take a while.",
      });
      
      // Polling could be added here, but for now we'll just redirect to the list
      router.push("/summarize");
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to re-summarize",
        variant: "destructive",
      });
      setIsResummarizing(false);
    }
  };

  const getSummary = (type: string) => data?.summaries.find(s => s.type === type);

  if (loading && !data) return <PageLoadingState title="Loading work summary..." />;
  if (error) return <PageErrorState error={error} onRetry={refetch} />;

  return (
    <div className="min-h-screen flex flex-col">
      <StickyDetailHeader
        title={data?.workTitle || "Work Summary"}
        backUrl="/summarize"
        backLabel="Back to Summaries"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowResummarizeConfirm(true)}
              disabled={isResummarizing}
            >
              <RefreshCw className={cn("size-4 mr-2", isResummarizing && "animate-spin")} />
              Re-summarize
            </Button>
          </div>
        }
      />

      <div className="p-6">
        <Tabs defaultValue="nodes" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="nodes">
              <List className="size-4 mr-2" /> Summary Nodes
            </TabsTrigger>
            <TabsTrigger value="abstract">
              <FileText className="size-4 mr-2" /> Abstract
            </TabsTrigger>
            <TabsTrigger value="outline">
              <Zap className="size-4 mr-2" /> Outline
            </TabsTrigger>
            <TabsTrigger value="key-concepts">
              <BookOpen className="size-4 mr-2" /> Key Concepts
            </TabsTrigger>
            <TabsTrigger value="chapters">
              <Layers className="size-4 mr-2" /> Chapters
            </TabsTrigger>
          </TabsList>

          <TabsContent value="nodes">
            <div className="max-w-4xl mx-auto">
              <div className="mb-4 flex justify-between items-center">
                <h2 className="text-xl font-bold">Hierarchical Summary Nodes</h2>
                <div className="text-sm text-muted-foreground">
                  {data?.nodes.length} nodes total
                </div>
              </div>
              <div className="space-y-4">
                {data?.nodes.map((node) => (
                  <div key={node.id} style={{ marginLeft: `${(node.heading_breadcrumbs?.split(" > ").length || 1) - 1}rem` }}>
                    <SummaryNodeCard node={node} workId={workId} />
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="abstract">
            <DerivedOutputSection
              type="abstract"
              title="Work Abstract"
              summary={getSummary("abstract")}
              onGenerate={() => handleGenerate("abstract")}
              isGenerating={isGenerating === "abstract"}
            />
          </TabsContent>

          <TabsContent value="outline">
            <DerivedOutputSection
              type="outline"
              title="Structured Outline"
              summary={getSummary("outline")}
              onGenerate={() => handleGenerate("outline")}
              isGenerating={isGenerating === "outline"}
            />
          </TabsContent>

          <TabsContent value="key-concepts">
            <DerivedOutputSection
              type="key_concepts"
              title="Key Concepts & Definitions"
              summary={getSummary("key_concepts")}
              onGenerate={() => handleGenerate("key_concepts")}
              isGenerating={isGenerating === "key_concepts"}
            />
          </TabsContent>

          <TabsContent value="chapters">
            <DerivedOutputSection
              type="chapter_summaries"
              title="Chapter/Section Summaries"
              summary={getSummary("chapter_summaries")}
              onGenerate={() => handleGenerate("chapter_summaries")}
              isGenerating={isGenerating === "chapter_summaries"}
            />
          </TabsContent>
        </Tabs>
      </div>

      <ConfirmDialog
        open={showResummarizeConfirm}
        onOpenChange={setShowResummarizeConfirm}
        title="Re-summarize Work?"
        message="This will delete all existing summary nodes and derived outputs for this work. This action cannot be undone."
        confirmLabel="Re-summarize"
        confirmVariant="destructive"
        onConfirm={handleResummarize}
      />
    </div>
  );
}

// --- Subcomponents ---

interface DerivedOutputSectionProps {
  type: string;
  title: string;
  summary: WorkSummary | undefined;
  onGenerate: () => void;
  isGenerating: boolean;
}

const DerivedOutputSection = ({ type, title, summary, onGenerate, isGenerating }: DerivedOutputSectionProps) => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">{title}</h2>
        <Button onClick={onGenerate} disabled={isGenerating}>
          <Zap className={cn("size-4 mr-2", isGenerating && "animate-spin")} />
          {summary ? "Regenerate" : "Generate"}
        </Button>
      </div>

      {!summary && !isGenerating && (
        <Card className="border-dashed flex flex-col items-center justify-center p-12 text-center">
          <CardDescription>
            This derived output has not been generated yet.
          </CardDescription>
          <Button variant="outline" className="mt-4" onClick={onGenerate}>
            Generate Now
          </Button>
        </Card>
      )}

      {isGenerating && (
        <div className="flex flex-col items-center justify-center p-12">
          <RefreshCw className="size-8 animate-spin text-muted-foreground mb-4" />
          <p className="text-muted-foreground">Generating {title.toLowerCase()}...</p>
        </div>
      )}

      {summary && !isGenerating && (
        <Card>
          <CardContent className="pt-6">
            {type === "abstract" && (
              <div className="prose dark:prose-invert max-w-none">
                <p className="whitespace-pre-wrap">{summary.content.abstract}</p>
              </div>
            )}

            {type === "outline" && (
              <div className="space-y-4">
                <OutlineTree items={summary.content.outline} workId={String(summary.work_id)} />
              </div>
            )}

            {type === "key_concepts" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {summary.content.key_concepts.map((concept: any, i: number) => (
                  <Card key={i}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-md">{concept.term}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground mb-2">{concept.definition}</p>
                      {concept.occurrences?.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {concept.occurrences.slice(0, 5).map((occ: any, j: number) => (
                            <Link
                              key={j}
                              href={`/corpus/${summary.work_id}?highlight=${occ.start_line}-${occ.end_line}`}
                              target="_blank"
                              className="text-[10px] px-1.5 py-0.5 rounded bg-muted hover:bg-muted/80 transition-colors inline-flex items-center gap-0.5"
                            >
                              L{occ.start_line} <ExternalLink size={8} />
                            </Link>
                          ))}
                          {concept.occurrences.length > 5 && (
                            <span className="text-[10px] text-muted-foreground">+{concept.occurrences.length - 5} more</span>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {type === "chapter_summaries" && (
              <div className="space-y-6">
                {summary.content.chapters.map((chapter: any, i: number) => (
                  <div key={i} className="border-l-2 border-primary pl-4 py-1">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className={cn("font-bold", chapter.level === "H1" ? "text-lg" : "text-md")}>
                        {chapter.heading}
                      </h3>
                      {chapter.line_references?.length > 0 && (
                        <Link
                          href={`/corpus/${summary.work_id}?highlight=${chapter.line_references[0].start_line}-${chapter.line_references[0].end_line}`}
                          target="_blank"
                          className="text-xs text-muted-foreground hover:text-primary transition-colors inline-flex items-center gap-1"
                        >
                          Source <ExternalLink size={12} />
                        </Link>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{chapter.summary}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

const OutlineTree = ({ items, workId, depth = 0 }: { items: any[]; workId: string; depth?: number }) => {
  return (
    <ul className={cn("space-y-2", depth > 0 && "ml-6 border-l pl-4")}>
      {items.map((item, i) => (
        <li key={i} className="text-sm">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2 group">
              <span className="font-semibold">{item.heading}</span>
              <Link
                href={`/corpus/${workId}?highlight=${item.start_line}-${item.end_line}`}
                target="_blank"
                className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground"
              >
                <ExternalLink size={12} />
              </Link>
            </div>
            <p className="text-muted-foreground leading-relaxed">{item.gist}</p>
          </div>
          {item.children?.length > 0 && (
            <div className="mt-2">
              <OutlineTree items={item.children} workId={workId} depth={depth + 1} />
            </div>
          )}
        </li>
      ))}
    </ul>
  );
};

function Layers(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z" />
      <path d="m2.6 12.08 8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9" />
      <path d="m2.6 17.08 8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9" />
    </svg>
  );
}
