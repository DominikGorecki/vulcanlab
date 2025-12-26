"use client";

import { useCallback, useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Loader2Icon,
  Save,
  Trash2,
  ArrowUp,
  ArrowDown,
  Plus,
  Check,
  ChevronRight,
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import { UpdateRetrieveConsolidateButton } from "@/components/rag/update-button";
import { Badge } from "@/components/ui/badge";
import {
  PageLoadingState,
  PageErrorState,
  StickyDetailHeader,
} from "@/components";
import { usePageData } from "@/hooks/use-page-data";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RetrievalContextItem {
  id: string | number;
  content: string;
  source?: string;
  score?: number;
  heading_chain?: string[];
  work_title?: string;
  work_authors?: string;
  work_year?: number;
  [key: string]: any;
}

interface QueryDetail {
  id: number;
  original_query: string;
  expanded_queries: string[] | null;
  hyde_answer: string | null;
  intent: string | null;
  entities: string[] | null;
  clean_retrieval_context: RetrievalContextItem[] | null;
  updated_at: string;
}

export default function InspectPage() {
  const params = useParams();
  const queryId = params.id as string;

  // Form states (local state for editing)
  const [expandedQueries, setExpandedQueries] = useState<string[]>([]);
  const [hydeAnswer, setHydeAnswer] = useState("");
  const [intent, setIntent] = useState("");
  const [entities, setEntities] = useState<string[]>([]);
  const [retrievalContext, setRetrievalContext] = useState<RetrievalContextItem[]>([]);

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Fetch query details
  const fetchQuery = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/rag/queries/${queryId}`);

    if (!response.ok) {
      throw new Error("Failed to load query details");
    }

    const data: QueryDetail = await response.json();
    return data;
  }, [queryId]);

  // Use usePageData
  const { data: query, loading, error, refetch } = usePageData<QueryDetail>(fetchQuery);

  // Initialize form fields when data loads
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (query && !initialized) {
      setExpandedQueries(query.expanded_queries || []);
      setHydeAnswer(query.hyde_answer || "");
      setIntent(query.intent || "");
      setEntities(query.entities || []);
      setRetrievalContext(query.clean_retrieval_context || []);
      setInitialized(true);
    }
  }, [query, initialized]);

  // Refetch wrapper that also resets initialization
  const handleRefresh = async () => {
    setInitialized(false);
    await refetch();
  };

  const handleSave = async () => {
    setSaving(true);
    setSuccessMessage(null);
    setSaveError(null);

    // Validate context length
    if (retrievalContext.length < 3) {
      setSaveError("At least 3 items are required in Clean Retrieval Data");
      setSaving(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/rag/queries/${queryId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          expanded_queries: expandedQueries,
          hyde_answer: hydeAnswer,
          intent: intent,
          entities: entities,
          clean_retrieval_context: retrievalContext,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to save changes");
      }

      const updatedData = await response.json();
      // Update local state with returned data to ensure sync
      setExpandedQueries(updatedData.expanded_queries || []);
      setHydeAnswer(updatedData.hyde_answer || "");
      setIntent(updatedData.intent || "");
      setEntities(updatedData.entities || []);
      setRetrievalContext(updatedData.clean_retrieval_context || []);
      
      setSuccessMessage("Changes saved successfully");
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save changes");
    } finally {
      setSaving(false);
    }
  };

  // Helper functions for list management
  const updateListItem = (setter: Function, list: any[], index: number, value: any) => {
    const newList = [...list];
    newList[index] = value;
    setter(newList);
  };

  const removeListItem = (setter: Function, list: any[], index: number) => {
    const newList = [...list];
    newList.splice(index, 1);
    setter(newList);
  };

  const addListItem = (setter: Function, list: any[], value: any = "") => {
    setter([...list, value]);
  };

  // Context management helpers
  const moveContextItem = (index: number, direction: 'up' | 'down') => {
    if (
      (direction === 'up' && index === 0) || 
      (direction === 'down' && index === retrievalContext.length - 1)
    ) return;

    const newContext = [...retrievalContext];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    [newContext[index], newContext[targetIndex]] = [newContext[targetIndex], newContext[index]];
    setRetrievalContext(newContext);
  };

  const removeContextItem = (index: number) => {
    if (retrievalContext.length <= 3) {
      alert("At least 3 items must remain in Clean Retrieval Data");
      return;
    }
    const newContext = [...retrievalContext];
    newContext.splice(index, 1);
    setRetrievalContext(newContext);
  };

  if (loading) {
    return <PageLoadingState />;
  }

  if (error) {
    return (
      <div className="space-y-4">
        <PageErrorState error={error} onRetry={refetch} />
      </div>
    );
  }

  if (!query) return null;

  return (
    <div className="flex flex-col min-h-screen">
      <StickyDetailHeader
        title={`Inspect Query #${query.id}`}
        subtitle={query.original_query}
        backUrl={`/rag/${queryId}`}
        actions={
          <div className="flex gap-2">
             <UpdateRetrieveConsolidateButton 
               queryId={query.id} 
               onSuccess={handleRefresh}
             />
             <Button onClick={handleSave} disabled={saving} className="gap-2">
              {saving ? <Loader2Icon className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Save Changes
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {saveError && (
          <Alert variant="destructive">
            <AlertDescription>{saveError}</AlertDescription>
          </Alert>
        )}
        {successMessage && (
          <Alert className="bg-green-50 text-green-800 border-green-200">
            <Check className="h-4 w-4 mr-2" />
            <AlertDescription>{successMessage}</AlertDescription>
          </Alert>
        )}

        {/* Read-Only Info */}
        <Card>
          <CardHeader>
            <CardTitle>Original Query</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-3 bg-muted rounded-md text-sm font-medium">
              {query.original_query}
            </div>
          </CardContent>
        </Card>

        {/* Editable Fields Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Intent */}
          <Card>
            <CardHeader>
              <CardTitle>Intent</CardTitle>
            </CardHeader>
            <CardContent>
              <Input 
                value={intent} 
                onChange={(e) => setIntent(e.target.value)} 
                placeholder="e.g. DEFINITION"
              />
            </CardContent>
          </Card>

           {/* HyDE Answer */}
           <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Hypothetical Document Embeddings (HyDE)</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea 
                value={hydeAnswer} 
                onChange={(e) => setHydeAnswer(e.target.value)} 
                className="min-h-[100px]"
              />
            </CardContent>
          </Card>

          {/* Expanded Queries */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Expanded Queries (MQE)</CardTitle>
              <Button size="sm" variant="ghost" onClick={() => addListItem(setExpandedQueries, expandedQueries)}>
                <Plus className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-2">
              {expandedQueries.map((q, idx) => (
                <div key={idx} className="flex gap-2">
                  <Input 
                    value={q} 
                    onChange={(e) => updateListItem(setExpandedQueries, expandedQueries, idx, e.target.value)}
                  />
                  <Button size="icon" variant="ghost" onClick={() => removeListItem(setExpandedQueries, expandedQueries, idx)}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Entities */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Entities</CardTitle>
              <Button size="sm" variant="ghost" onClick={() => addListItem(setEntities, entities)}>
                 <Plus className="h-4 w-4" />
              </Button>
            </CardHeader>
             <CardContent className="space-y-2">
              {entities.map((ent, idx) => (
                <div key={idx} className="flex gap-2">
                  <Input 
                    value={ent} 
                    onChange={(e) => updateListItem(setEntities, entities, idx, e.target.value)}
                  />
                  <Button size="icon" variant="ghost" onClick={() => removeListItem(setEntities, entities, idx)}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Clean Retrieval Data */}
        <Card>
          <CardHeader>
            <CardTitle className="flex justify-between items-center">
              <span>Clean Retrieval Data ({retrievalContext.length})</span>
              <Badge variant={retrievalContext.length < 3 ? "destructive" : "secondary"}>
                Min 3 items required
              </Badge>
            </CardTitle>
            <CardDescription>
              Re-order or remove retrieved chunks. This data is used for context in generation.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {retrievalContext.map((item, idx) => (
              <div key={idx} className="flex gap-4 p-4 border rounded-lg bg-card hover:bg-accent/50 transition-colors">
                <div className="flex flex-col gap-1 justify-center">
                  <Button 
                    size="icon" 
                    variant="ghost" 
                    disabled={idx === 0}
                    onClick={() => moveContextItem(idx, 'up')}
                    className="h-6 w-6"
                  >
                    <ArrowUp className="h-4 w-4" />
                  </Button>
                  <Button 
                    size="icon" 
                    variant="ghost" 
                    disabled={idx === retrievalContext.length - 1}
                    onClick={() => moveContextItem(idx, 'down')}
                    className="h-6 w-6"
                  >
                    <ArrowDown className="h-4 w-4" />
                  </Button>
                </div>
                
                <div className="flex-1 min-w-0 space-y-2">
                  <div className="flex justify-between items-start">
                    <div className="text-xs text-muted-foreground font-mono">
                      ID: {item.id} | Score: {item.score?.toFixed(4)}
                    </div>
                    <Button 
                      size="icon" 
                      variant="ghost" 
                      onClick={() => removeContextItem(idx)}
                      className="h-6 w-6 text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  {item.heading_chain && item.heading_chain.length > 0 && (
                    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[10px] text-muted-foreground uppercase tracking-wider mb-1.5">
                      {item.heading_chain.map((h, i) => (
                        <div key={i} className="flex items-center gap-1">
                          {i > 0 && <ChevronRight className="h-3 w-3 opacity-50" />}
                          <span>{h}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="max-h-[200px] overflow-y-auto border rounded p-2 bg-background text-sm">
                    <MarkdownRenderer content={item.content} />
                  </div>
                  <div className="mt-2 pt-2 border-t border-border/40">
                    {(item.work_title || item.work_authors || item.work_year) ? (
                      <div className="text-[11px] text-muted-foreground italic flex flex-wrap gap-x-3 gap-y-1">
                        {item.work_title && (
                          <span className="font-semibold text-foreground/70">{item.work_title}</span>
                        )}
                        {item.work_authors && (
                          <span>{item.work_authors}</span>
                        )}
                        {item.work_year && (
                          <span>({item.work_year})</span>
                        )}
                      </div>
                    ) : (
                      <div className="text-[10px] text-muted-foreground/50 italic">
                        No source metadata available. Re-run consolidation to update.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {retrievalContext.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                No retrieval context available. Run retrieval first.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
