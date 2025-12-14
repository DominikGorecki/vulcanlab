/**
 * Manual Workflow Page
 *
 * Handles manual execution mode for simple conversion pipeline.
 * Displays LLM prompt for user to copy/paste, with options to:
 * 1. Paste manual LLM response and submit
 * 2. Run automatically via direct LLM call
 */

"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Loader2Icon, CheckCircle2, AlertCircle, Copy, ArrowLeft, Play, FileText } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PromptData {
  work_id: number;
  classification: string;
  prompt: string;
  instructions: string;
}

interface ChunkResult {
  id: number;
  heading_level: number;
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

export default function ManualWorkflowPage() {
  const params = useParams();
  const router = useRouter();
  const workId = params?.work_id as string;

  const [promptData, setPromptData] = useState<PromptData | null>(null);
  const [manualResponse, setManualResponse] = useState('');
  const [results, setResults] = useState<ResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  const [completed, setCompleted] = useState(false);
  
  // Fetch prompt on mount
  useEffect(() => {
    if (workId) {
      fetchPrompt();
    }
  }, [workId]);

  const fetchPrompt = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/api/simple-conversion/manual-prompt/${workId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch prompt');
      }
      const data = await response.json();
      setPromptData(data);
    } catch (err) {
      console.error('Failed to fetch prompt:', err);
      const message = err instanceof Error ? err.message : 'Failed to load prompt';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

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
      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }
      const data = await response.json();
      setResults(data);
    } catch (err) {
      console.error('Failed to fetch results:', err);
      const message = err instanceof Error ? err.message : 'Failed to load results';
      setError(message);
    }
  };

  const handleManualSubmit = async () => {
    if (!manualResponse.trim()) {
      setError('Please paste the LLM response before submitting');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/api/simple-conversion/manual-submit/${workId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ llm_response: manualResponse })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to process result');
      }

      setCompleted(true);
      await fetchResults();

    } catch (err) {
      console.error('Failed to submit manual result:', err);
      const message = err instanceof Error ? err.message : 'Failed to process result';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAutoExecute = async () => {
    try {
      setExecuting(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/api/simple-conversion/execute-auto/${workId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to execute pipeline');
      }

      // Start polling handled by effect
    } catch (err) {
      console.error('Failed to execute automatically:', err);
      const message = err instanceof Error ? err.message : 'Failed to execute pipeline';
      setError(message);
      setExecuting(false);
    }
  };

  // Poll for completion if executing
  useEffect(() => {
    if (!executing || completed || error) return;

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
          setError(statusData.error_message || 'Pipeline execution failed');
        }
      } catch (e) {
        console.error("Polling error", e);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [executing, completed, error, workId]);


  if (!workId) {
    return (
       <div className="p-8">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>No Work ID provided</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl py-8 space-y-8">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push('/simple-conversion')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-3xl font-bold tracking-tight">Manual Conversion</h1>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center p-12 space-y-4">
          <Loader2Icon className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Preparing prompt...</p>
        </div>
      )}

      {!completed && promptData && !loading && (
        <>
          <Card className="bg-muted/50 border-l-4 border-l-primary">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                 <span className="font-semibold">Document Classification:</span>
                 <Badge variant={promptData.classification === 'small' ? 'secondary' : 'default'} className="uppercase">
                    {promptData.classification}
                 </Badge>
              </div>
              <div>
                <h3 className="font-semibold mb-1 text-primary">Instructions</h3>
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
              <ScrollArea className="h-[300px] w-full rounded-md border bg-muted p-4">
                <pre className="text-xs font-mono whitespace-pre-wrap break-words">{promptData.prompt}</pre>
              </ScrollArea>
            </CardContent>
          </Card>

          <Tabs defaultValue="manual" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="manual">Option 1: Manual Execution</TabsTrigger>
              <TabsTrigger value="auto">Option 2: Automatic Execution</TabsTrigger>
            </TabsList>
            
            <TabsContent value="manual">
              <Card>
                <CardHeader>
                  <CardTitle>Manual LLM Response</CardTitle>
                  <CardDescription>
                    Paste the JSON response from your LLM below.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Textarea
                    placeholder="Paste LLM response here (JSON format)..."
                    className="min-h-[200px] font-mono text-sm"
                    value={manualResponse}
                    onChange={(e) => setManualResponse(e.target.value)}
                    disabled={submitting || executing}
                  />
                  <Button 
                    onClick={handleManualSubmit} 
                    disabled={submitting || executing || !manualResponse.trim()} 
                    className="w-full"
                  >
                    {submitting && <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />}
                    Submit Response
                  </Button>
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
                  <div className="bg-muted p-4 rounded-md text-sm">
                    <p>This will submit the prompt directly to the configured backend LLM service. You don't need to copy/paste anything.</p>
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

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
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

          <Card>
            <CardHeader>
              <CardTitle>Generated Chunks</CardTitle>
              <CardDescription>Preview of the generated chunks</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-4">
                  {results.chunks.map((chunk) => (
                    <div key={chunk.id} className="border rounded-lg p-4 bg-card hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div className="flex items-center gap-2">
                          <Badge className="bg-primary text-primary-foreground">H{chunk.heading_level}</Badge>
                          <h4 className="font-semibold text-lg">{chunk.heading_text}</h4>
                        </div>
                        <span className="text-xs text-muted-foreground bg-muted cx-2 py-1 rounded">
                          Lines {chunk.start_line}-{chunk.end_line}
                        </span>
                      </div>
                      <div className="pl-4 border-l-2 border-muted mt-2">
                        <p className="text-sm text-muted-foreground whitespace-pre-wrap font-mono text-xs">
                          {chunk.content_preview}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
