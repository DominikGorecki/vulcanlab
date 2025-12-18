/**
 * Automatic Workflow Page
 *
 * Handles automatic execution of the simple conversion pipeline.
 * Executes the pipeline, polls for status updates, and displays results.
 */

"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2Icon, CheckCircle2, AlertCircle, FileText, ArrowLeft, ExternalLink } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface StatusData {
  work_id: number;
  step: string;
  classification?: string;
  token_count?: number;
  chunk_count?: number;
  mode?: string;
  error_message?: string;
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
  output_files?: Record<string, string>;
}

type ExecutionStep = 'executing' | 'parsing' | 'parsed' | 'sanitizing' | 'sanitized' | 'chunking' | 'chunked' | 'complete' | 'error';

export default function AutomaticWorkflowPage() {
  const params = useParams();
  const router = useRouter();
  const workId = params?.work_id as string;

  const [status, setStatus] = useState<StatusData | null>(null);
  const [results, setResults] = useState<ResultsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [executing, setExecuting] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [initialLoad, setInitialLoad] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/simple-conversion/status/${workId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch status');
      }
      const statusData = await response.json();
      setStatus(statusData);

      if (statusData.step === 'complete') {
        setExecuting(false);
        setCompleted(true);
        // Will fetch results in useEffect when completed becomes true
      } else if (statusData.step === 'error') {
        setExecuting(false);
        setError(statusData.error_message || 'Pipeline execution failed');
      }
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  }, [workId]);

  const executeAutomatic = useCallback(async () => {
    try {
      setExecuting(true);
      setError(null);

      // First check current status to see if already executed
      const statusResponse = await fetch(`${API_BASE_URL}/api/simple-conversion/status/${workId}`);
      if (statusResponse.ok) {
        const statusData = await statusResponse.json();

        // If already complete or in error state, don't execute again
        if (statusData.step === 'complete') {
          setStatus(statusData);
          setExecuting(false);
          setCompleted(true);
          return;
        } else if (statusData.step === 'error') {
          setStatus(statusData);
          setExecuting(false);
          setError(statusData.error_message || 'Pipeline execution failed');
          return;
        }

        // If in progress (parsing, sanitizing, chunking), just poll status
        if (['parsing', 'parsed', 'sanitizing', 'sanitized', 'chunking', 'chunked'].includes(statusData.step)) {
          setStatus(statusData);
          // Let the polling effect handle status updates
          return;
        }
      }

      // Only execute if status is 'converting' or unknown
      const response = await fetch(`${API_BASE_URL}/api/simple-conversion/execute-auto/${workId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to execute pipeline');
      }

      await fetchStatus();
    } catch (err) {
      console.error('Failed to execute automatic pipeline:', err);
      const message = err instanceof Error ? err.message : 'Failed to execute pipeline';
      setError(message);
      setExecuting(false);
    }
  }, [workId, fetchStatus]);

  const fetchResults = useCallback(async () => {
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
  }, [workId]);

  // Start execution on mount
  useEffect(() => {
    if (workId && initialLoad) {
      setInitialLoad(false);
      executeAutomatic();
    }
  }, [workId, initialLoad, executeAutomatic]);

  // Poll for status
  useEffect(() => {
    if (!executing || completed || error) return;

    const interval = setInterval(() => {
      fetchStatus();
    }, 2000);

    return () => clearInterval(interval);
  }, [executing, completed, error, fetchStatus]);

  // Fetch results when complete
  useEffect(() => {
    if (completed && !results) {
      fetchResults();
    }
  }, [completed, results, fetchResults]);

  const getStepLabel = (step: string): string => {
    const labels: Record<string, string> = {
      executing: 'Starting pipeline...',
      parsing: 'Parsing and classifying document...',
      parsed: 'Document parsed and classified',
      sanitizing: 'Sanitizing markdown...',
      sanitized: 'Markdown sanitized',
      chunking: 'Creating chunks...',
      chunked: 'Chunks created',
      complete: 'Pipeline complete!',
      error: 'Error occurred'
    };
    return labels[step] || step;
  };

  const isStepComplete = (stepName: string): boolean => {
    if (!status) return false;
    const stepOrder = ['parsing', 'parsed', 'sanitizing', 'sanitized', 'chunking', 'chunked', 'complete'];
    const currentIndex = stepOrder.indexOf(status.step);
    const checkIndex = stepOrder.indexOf(stepName);
    return currentIndex >= checkIndex;
  };

  const isStepActive = (stepName: string): boolean => {
    return status?.step === stepName;
  };

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

  const steps = [
    { key: 'parsing', label: 'Parse & Classify', icon: '1' },
    { key: 'sanitizing', label: 'Sanitize', icon: '2' },
    { key: 'chunking', label: 'Chunk', icon: '3' },
    { key: 'complete', label: 'Complete', icon: <CheckCircle2 className="h-5 w-5" /> },
  ];

  const mapStepToCompletionKey = (stepKey: string) => {
    switch (stepKey) {
      case 'parsing': return 'parsed';
      case 'sanitizing': return 'sanitized';
      case 'chunking': return 'chunked';
      case 'complete': return 'complete';
      default: return stepKey;
    }
  };

  return (
    <div className="container mx-auto max-w-4xl py-8 space-y-8">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push('/simple-conversion')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-3xl font-bold tracking-tight">Automatic Conversion</h1>
      </div>

      {/* Initial loading state before we have status */}
      {executing && !status && !error && (
        <Card>
          <CardContent className="pt-6 flex flex-col items-center justify-center space-y-4 min-h-[300px]">
            <Loader2Icon className="h-12 w-12 animate-spin text-primary" />
            <p className="text-lg font-medium">Starting automatic conversion...</p>
            <p className="text-sm text-muted-foreground">
              Preparing to process your document
            </p>
          </CardContent>
        </Card>
      )}

      {status && !completed && !error && (
        <Card>
          <CardHeader>
            <CardTitle>Pipeline Status</CardTitle>
            <CardDescription>
              Processing your document...
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-8">
            <div className="flex items-center gap-3 text-lg font-medium text-primary">
              <Loader2Icon className="h-6 w-6 animate-spin" />
              {getStepLabel(status.step)}
            </div>

            <div className="grid grid-cols-4 gap-4">
              {steps.map((step) => {
                const completionKey = mapStepToCompletionKey(step.key);
                const isComplete = isStepComplete(completionKey);
                const isActive = isStepActive(step.key);
                
                return (
                  <div 
                    key={step.key}
                    className={`flex flex-col items-center gap-2 text-center transition-all duration-300 ${
                      isComplete ? 'text-green-600 opacity-100' : isActive ? 'text-primary opacity-100 font-semibold' : 'text-muted-foreground opacity-40'
                    }`}
                  >
                    <div className={`
                      flex items-center justify-center w-12 h-12 rounded-full border-2 text-lg font-bold transition-all
                      ${isComplete 
                        ? 'bg-green-100 border-green-600' 
                        : isActive 
                          ? 'bg-background border-primary text-primary shadow-[0_0_15px_rgba(var(--primary),0.3)]' 
                          : 'bg-muted border-transparent'
                      }
                    `}>
                      {isComplete ? <CheckCircle2 className="h-6 w-6" /> : step.icon}
                    </div>
                    <span className="text-sm">{step.label}</span>
                  </div>
                );
              })}
            </div>

            {status.classification && (
              <div className="flex flex-wrap gap-4 pt-4 border-t">
                  <div className="flex flex-col">
                    <span className="text-xs text-muted-foreground uppercase font-bold">Classification</span>
                    <span className="font-mono text-lg">{status.classification.toUpperCase()}</span>
                  </div>
                  {status.token_count !== undefined && (
                    <div className="flex flex-col border-l pl-4">
                      <span className="text-xs text-muted-foreground uppercase font-bold">Tokens</span>
                      <span className="font-mono text-lg">{status.token_count.toLocaleString()}</span>
                    </div>
                  )}
              </div>
            )}
          </CardContent>
        </Card>
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
                  <Badge
                    variant={results.classification === 'small' ? 'default' : 'secondary'}
                    className={results.classification === 'small' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-purple-600 hover:bg-purple-700 text-white'}
                  >
                    {results.classification === 'small' ? 'Small' : 'Large'}
                  </Badge>
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
                <Button
                  variant="outline"
                  onClick={() => router.push(`/corpus/${workId}`)}
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  View in Corpus
                </Button>
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
