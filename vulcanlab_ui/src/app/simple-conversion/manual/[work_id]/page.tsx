/**
 * Manual Workflow Page
 *
 * Handles manual execution mode for simple conversion pipeline.
 * Displays LLM prompt for user to copy/paste, with options to:
 * 1. Paste manual LLM response and submit
 * 2. Run automatically via direct LLM call
 */

"use client";

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Loader2Icon, CheckCircle2, AlertCircle, Copy, ArrowLeft, Play, FileText, Settings, User } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/page-header";
import { DataTable, DataTableColumn } from "@/components/data-table";
import { FormField } from "@/components/form-field";
import { usePageData } from "@/hooks/use-page-data";
import { PageLoadingState } from "@/components/page-loading-state";
import { PageErrorState } from "@/components/page-error-state";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PromptData {
  work_id: number;
  classification: string;
  prompt: string;
  instructions: string;
}

interface ChunkResult {
  id: number;
  heading_level: string;
  heading_text: string;
  start_line: number;
  end_line: number;
  content_preview: string;
}

interface ResultsData {
  work_id: number;
  title: string;
  author: string;
  classification: string;
  token_count: number;
  chunk_count: number;
  chunks: ChunkResult[];
}

interface ManualForm {
  llm_response: string;
}

export default function ManualWorkflowPage() {
  const params = useParams();
  const router = useRouter();
  const workId = params?.work_id as string;

  const [submitting, setSubmitting] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [results, setResults] = useState<ResultsData | null>(null);

  const { register, handleSubmit, watch, formState: { errors } } = useForm<ManualForm>();
  const llmResponse = watch('llm_response');

  const fetchPromptFn = useCallback(async () => {
    if (!workId) throw new Error('No Work ID provided');
    const response = await fetch(`${API_BASE_URL}/api/simple-conversion/manual-prompt/${workId}`);
    if (!response.ok) throw new Error('Failed to fetch prompt');
    return await response.json();
  }, [workId]);

  // Fetch prompt
  const { 
    data: promptData, 
    loading, 
    error: fetchError, 
    refetch: fetchPrompt 
  } = usePageData<PromptData>(fetchPromptFn, { autoFetch: !!workId });

  const copyPromptToClipboard = async () => {
    if (!promptData) return;
    try {
      await navigator.clipboard.writeText(promptData.prompt);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const fetchResults = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/simple-conversion/results/${workId}`);
      if (!response.ok) throw new Error('Failed to fetch results');
      const data = await response.json();
      setResults(data);
    } catch (err) {
      console.error('Failed to fetch results:', err);
      setSubmitError(err instanceof Error ? err.message : 'Failed to load results');
    }
  };

  const onManualSubmit = async (data: ManualForm) => {
    try {
      setSubmitting(true);
      setSubmitError(null);

      const response = await fetch(`${API_BASE_URL}/api/simple-conversion/manual-submit/${workId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ llm_response: data.llm_response })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to process result');
      }

      setCompleted(true);
      await fetchResults();
    } catch (err) {
      console.error('Failed to submit manual result:', err);
      setSubmitError(err instanceof Error ? err.message : 'Failed to process result');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAutoExecute = async () => {
    try {
      setExecuting(true);
      setSubmitError(null);

      const response = await fetch(`${API_BASE_URL}/api/simple-conversion/execute-auto/${workId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to execute pipeline');
      }
    } catch (err) {
      console.error('Failed to execute automatically:', err);
      setSubmitError(err instanceof Error ? err.message : 'Failed to execute pipeline');
      setExecuting(false);
    }
  };

  // Poll for completion if executing
  useEffect(() => {
    if (!executing || completed || submitError) return;

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/simple-conversion/status/${workId}`);
        if (!response.ok) return;
        
        const statusData = await response.json();
        
        if (statusData.step === 'complete') {
          setExecuting(false);
          setCompleted(true);
          await fetchResults();
        } else if (statusData.step === 'error') {
          setExecuting(false);
          setSubmitError(statusData.error_message || 'Pipeline execution failed');
        }
      } catch (e) {
        console.error("Polling error", e);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [executing, completed, submitError, workId]);

  const columns: DataTableColumn<ChunkResult>[] = [
    {
      key: 'heading_level',
      header: 'Level',
      className: "w-[80px]",
      cell: (chunk) => (
        <Badge variant="outline" className="font-mono">
          {chunk.heading_level}
        </Badge>
      )
    },
    {
      key: 'heading_text',
      header: 'Heading',
      className: "min-w-[200px] max-w-[400px] whitespace-normal break-words font-medium",
    },
    {
      key: 'start_line',
      header: 'Range',
      cell: (chunk) => `Lines ${chunk.start_line}-${chunk.end_line}`,
      className: "w-[120px] text-xs text-muted-foreground whitespace-nowrap",
    },
    {
      key: 'content_preview',
      header: 'Content Preview',
      className: "min-w-[400px] whitespace-normal break-words font-mono text-xs",
      cell: (chunk) => (
        <div className="max-h-[80px] overflow-hidden text-ellipsis whitespace-pre-wrap">
          {chunk.content_preview}
        </div>
      )
    }
  ];

  if (loading) {
    return <PageLoadingState />;
  }

  if (fetchError || !workId) {
    return (
      <PageErrorState 
        error={fetchError || 'No Work ID provided'} 
        title="Error loading workflow"
        onRetry={fetchPrompt}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Manual Conversion"
        description="Paste manual LLM response or run automatically."
        actions={
          <Button variant="ghost" size="sm" onClick={() => router.push('/simple-conversion')} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Simple Conversion
          </Button>
        }
      />

      {!completed && promptData && (
        <>
          <Card className="bg-muted/50 border-l-4 border-l-primary">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                 <span className="font-semibold text-sm">Classification:</span>
                 <Badge variant={promptData.classification === 'small' ? 'secondary' : 'default'} className="uppercase text-[10px]">
                    {promptData.classification}
                 </Badge>
              </div>
              <div>
                <h3 className="font-semibold mb-1 text-primary text-sm flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Instructions
                </h3>
                <p className="text-sm text-muted-foreground">{promptData.instructions}</p>
              </div>
            </CardContent>
          </Card>

           <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg font-medium">LLM Prompt</CardTitle>
              <Button variant="outline" size="sm" onClick={copyPromptToClipboard} className="gap-2">
                {copySuccess ? <CheckCircle2 className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                {copySuccess ? "Copied!" : "Copy to Clipboard"}
              </Button>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[250px] w-full rounded-md border bg-muted p-4">
                <pre className="text-xs font-mono whitespace-pre-wrap break-words">{promptData.prompt}</pre>
              </ScrollArea>
            </CardContent>
          </Card>

          <Tabs defaultValue="manual" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="manual" className="gap-2">
                <User className="h-4 w-4" />
                Manual Execution
              </TabsTrigger>
              <TabsTrigger value="auto" className="gap-2">
                <Settings className="h-4 w-4" />
                Automatic Execution
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="manual">
              <Card>
                <CardHeader>
                  <CardTitle>Manual LLM Response</CardTitle>
                  <CardDescription>
                    {promptData.classification === 'small'
                      ? 'Paste the sanitized markdown response from your LLM below.'
                      : 'Paste the JSON response from your LLM below.'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit(onManualSubmit)} className="space-y-4">
                    <FormField 
                      label="LLM Response" 
                      required 
                      error={errors.llm_response?.message}
                    >
                      <Textarea
                        {...register('llm_response', { required: 'Please paste the LLM response' })}
                        placeholder={promptData.classification === 'small'
                          ? "Paste sanitized markdown here..."
                          : "Paste LLM response here (JSON format)..."}
                        className="min-h-[200px] font-mono text-sm"
                        disabled={submitting || executing}
                      />
                    </FormField>
                    <Button 
                      type="submit"
                      disabled={submitting || executing || !llmResponse?.trim()} 
                      className="w-full"
                    >
                      {submitting ? (
                        <>
                          <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                          Processing Response...
                        </>
                      ) : (
                        'Submit Response'
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="auto">
               <Card>
                <CardHeader>
                  <CardTitle>Automatic Execution</CardTitle>
                  <CardDescription>
                    Let the system run the prompt automatically using the configured LLM.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="bg-muted p-4 rounded-md text-sm text-muted-foreground">
                    This will submit the prompt directly to the configured backend LLM service. No manual intervention required.
                  </div>
                  <Button 
                    onClick={handleAutoExecute} 
                    disabled={submitting || executing} 
                    className="w-full bg-blue-600 hover:bg-blue-700"
                  >
                     {executing ? (
                        <>
                           <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                           Running Pipeline...
                        </>
                     ) : (
                        <>
                           <Play className="mr-2 h-4 w-4" />
                           Run Automatically
                        </>
                     )}
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </>
      )}

      {submitError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{submitError}</AlertDescription>
           <div className="mt-4">
             <Button variant="outline" size="sm" onClick={() => router.push('/simple-conversion')}>
               Return to Start
             </Button>
          </div>
        </Alert>
      )}

      {completed && results && (
        <div className="space-y-6 animate-in fade-in duration-500">
          <Alert className="border-green-500 bg-green-50 text-green-900">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertTitle>Success</AlertTitle>
            <AlertDescription>
              Conversion completed successfully!
            </AlertDescription>
          </Alert>

          <Card>
            <CardHeader>
              <CardTitle>Results Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mb-6">
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground">Title</h4>
                  <p className="font-medium">{results.title}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground">Author</h4>
                  <p className="font-medium">{results.author}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground">Classification</h4>
                  <Badge variant="secondary" className="uppercase">{results.classification}</Badge>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground">Token Count</h4>
                  <p className="font-mono">{results.token_count.toLocaleString()}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground">Chunks Created</h4>
                  <p className="font-mono">{results.chunk_count}</p>
                </div>
              </div>

              <div className="flex justify-end gap-2">
                 <Button onClick={() => router.push('/simple-conversion')}>
                  Start Another Conversion
                </Button>
              </div>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <div>
              <h3 className="text-2xl font-bold tracking-tight">Generated Chunks</h3>
              <p className="text-sm text-muted-foreground">Preview of the generated chunks</p>
            </div>
            <DataTable
              columns={columns}
              data={results.chunks}
              emptyState={{
                title: "No chunks found",
                description: "No chunks were generated for this conversion.",
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
