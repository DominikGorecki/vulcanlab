/**
 * Simple Conversion Page
 *
 * Entry point for the simple conversion workflow. Fetches available files
 * from input folder, collects metadata, and execution mode, then initiates
 * the conversion process.
 */

"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2Icon, AlertCircle, CheckCircle2, RefreshCw } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FormData {
  selectedFile: string;
  title: string;
  author: string;
  year: string;
  mode: 'automatic' | 'manual';
}

interface FormErrors {
  selectedFile?: string;
  title?: string;
  author?: string;
  year?: string;
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

interface HistoryWorkAPI {
  work_id: number;
  title: string;
  author: string;
  classification: 'small' | 'large' | null;
  mode: 'automatic' | 'manual';
  status: 'complete' | 'failed';
  created_at: string;
  error_message?: string | null;
}

interface HistoryWork {
  work_id: number;
  title: string;
  author: string;
  classification: 'small' | 'large';
  mode: 'automatic' | 'manual';
  status: 'success' | 'error';
  created_at: string;
  error_message?: string | null;
}

export default function SimpleConversionPage() {
  const router = useRouter();

  // File list state
  const [inputFiles, setInputFiles] = useState<string[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(true);
  const [filesFetchError, setFilesFetchError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState<FormData>({
    selectedFile: '',
    title: '',
    author: '',
    year: '',
    mode: 'automatic'
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Automatic execution state
  const [autoExecuting, setAutoExecuting] = useState(false);
  const [autoStatus, setAutoStatus] = useState<string>('');
  const [autoResults, setAutoResults] = useState<ResultsData | null>(null);
  const [autoError, setAutoError] = useState<string | null>(null);

  // History state
  const [historyWorks, setHistoryWorks] = useState<HistoryWork[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);

  // Fetch input files on mount
  useEffect(() => {
    fetchInputFiles();
  }, []);

  // Fetch history on mount
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchInputFiles = async () => {
    try {
      setLoadingFiles(true);
      setFilesFetchError(null);

      const response = await fetch(`${API_BASE_URL}/conv/io-folder-data`);
      if (!response.ok) {
        throw new Error(`Failed to fetch files: ${response.statusText}`);
      }

      const data = await response.json();
      setInputFiles(data.input_files || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load input files';
      setFilesFetchError(message);
    } finally {
      setLoadingFiles(false);
    }
  };

  const fetchHistory = async () => {
    try {
      setLoadingHistory(true);
      setHistoryError(null);

      const response = await fetch(`${API_BASE_URL}/api/simple-conversion/history`);
      if (!response.ok) {
        throw new Error(`Failed to fetch history: ${response.statusText}`);
      }

      const data = await response.json();
      // Filter out works with null classification (not yet classified/completed)
      // and map API response format to frontend format
      const completedWorks = (data.items || [])
        .filter((work: HistoryWorkAPI) => work.classification !== null)
        .map((work: HistoryWorkAPI): HistoryWork => ({
          ...work,
          classification: work.classification as 'small' | 'large',
          status: work.status === 'complete' ? 'success' : 'error'
        }));
      setHistoryWorks(completedWorks);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load conversion history';
      setHistoryError(message);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // Clear error for this field when user types
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleModeChange = (mode: 'automatic' | 'manual') => {
    setFormData(prev => ({ ...prev, mode }));
  };

  const handleFileSelect = (value: string) => {
    setFormData(prev => ({ ...prev, selectedFile: value }));
    if (errors.selectedFile) {
      setErrors(prev => ({ ...prev, selectedFile: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.selectedFile) {
      newErrors.selectedFile = 'Please select a file';
    }

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!formData.author.trim()) {
      newErrors.author = 'Author is required';
    }

    if (formData.year) {
      const yearNum = parseInt(formData.year, 10);
      if (isNaN(yearNum) || yearNum < 1000 || yearNum > new Date().getFullYear() + 1) {
        newErrors.year = 'Please enter a valid year';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const executeAutomaticPipeline = async (workId: number) => {
    try {
      setAutoError(null);

      // Step 1: Execute full pipeline
      setAutoStatus('Processing document...');
      const response = await fetch(`${API_BASE_URL}/api/simple-conversion/execute-auto/${workId}`, {
        method: 'POST'
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Pipeline execution failed');
      }

      // Step 2: Fetch results
      setAutoStatus('Loading results...');
      const resultsResponse = await fetch(`${API_BASE_URL}/api/simple-conversion/results/${workId}`);

      if (!resultsResponse.ok) {
        throw new Error('Failed to fetch results');
      }

      const resultsData = await resultsResponse.json();
      setAutoResults(resultsData);
      setAutoStatus('Complete!');

    } catch (err) {
      console.error('Automatic pipeline failed:', err);
      const message = err instanceof Error ? err.message : 'Pipeline execution failed';
      setAutoError(message);
    } finally {
      setAutoExecuting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/simple-conversion/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: formData.selectedFile,
          title: formData.title,
          author: formData.author,
          year: formData.year ? parseInt(formData.year, 10) : null,
          mode: formData.mode
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to start conversion');
      }

      const data = await response.json();
      const { work_id, mode } = data;

      console.log('Backend returned mode:', mode);
      console.log('Form data mode was:', formData.mode);

      // Branch based on mode
      if (mode === 'manual') {
        console.log('Redirecting to manual workflow');
        // Redirect to manual workflow
        router.push(`/simple-conversion/manual/${work_id}`);
        return; // Exit early to prevent any further execution
      }

      console.log('Executing automatic pipeline');
      // Automatic mode: Stay on page and execute pipeline
      setAutoExecuting(true);
      await executeAutomaticPipeline(work_id);

    } catch (err) {
      console.error('Failed to start conversion:', err);
      const message = err instanceof Error ? err.message : 'Failed to start conversion';
      setErrorMessage(message);
    } finally {
      setSubmitting(false);
    }
  };

  // Loading state for file fetch
  if (loadingFiles) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Simple Conversion</h2>
          <p className="text-muted-foreground">Loading available files...</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  // Error state for file fetch
  if (filesFetchError) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Simple Conversion</h2>
          <p className="text-muted-foreground">Streamlined document conversion workflow.</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {filesFetchError}
          </AlertDescription>
        </Alert>
        <Button onClick={fetchInputFiles}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Simple Conversion</h2>
        <p className="text-muted-foreground">
          Convert your PDF or EPUB document in a streamlined single-page workflow.
          Select a file from the input folder and provide metadata.
        </p>
      </div>

      {/* Show loading during manual redirect */}
      {submitting && !autoExecuting && (
        <Card>
          <CardContent className="pt-6 flex flex-col items-center justify-center space-y-4">
            <Loader2Icon className="h-8 w-8 animate-spin text-primary" />
            <p className="text-lg font-medium">Redirecting to manual workflow...</p>
          </CardContent>
        </Card>
      )}

      {/* Show form unless automatic execution is in progress or completed */}
      {!autoExecuting && !autoResults && !submitting && (
        <Card>
        <CardHeader>
          <CardTitle>Start Conversion</CardTitle>
          <CardDescription>
            Select a file and provide metadata to begin the conversion process.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* File Selection */}
            <div className="space-y-2">
              <Label htmlFor="selectedFile">
                Select File <span className="text-destructive">*</span>
              </Label>
              <Select
                value={formData.selectedFile}
                onValueChange={handleFileSelect}
                disabled={submitting || inputFiles.length === 0}
              >
                <SelectTrigger id="selectedFile" className={errors.selectedFile ? 'border-destructive' : ''}>
                  <SelectValue placeholder="Choose a file from input folder" />
                </SelectTrigger>
                <SelectContent>
                  {inputFiles.length === 0 ? (
                    <div className="text-sm text-muted-foreground p-2">
                      No files in input folder
                    </div>
                  ) : (
                    inputFiles.map((file) => (
                      <SelectItem key={file} value={file}>
                        {file}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {errors.selectedFile && (
                <p className="text-sm text-destructive">{errors.selectedFile}</p>
              )}
            </div>

            {/* Title */}
            <div className="space-y-2">
              <Label htmlFor="title">
                Title <span className="text-destructive">*</span>
              </Label>
              <Input
                id="title"
                name="title"
                type="text"
                value={formData.title}
                onChange={handleInputChange}
                placeholder="Document title"
                disabled={submitting}
                className={errors.title ? 'border-destructive' : ''}
              />
              {errors.title && (
                <p className="text-sm text-destructive">{errors.title}</p>
              )}
            </div>

            {/* Author */}
            <div className="space-y-2">
              <Label htmlFor="author">
                Author <span className="text-destructive">*</span>
              </Label>
              <Input
                id="author"
                name="author"
                type="text"
                value={formData.author}
                onChange={handleInputChange}
                placeholder="Author name"
                disabled={submitting}
                className={errors.author ? 'border-destructive' : ''}
              />
              {errors.author && (
                <p className="text-sm text-destructive">{errors.author}</p>
              )}
            </div>

            {/* Year (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="year">
                Publication Year <span className="text-muted-foreground text-sm font-normal">(optional)</span>
              </Label>
              <Input
                id="year"
                name="year"
                type="number"
                value={formData.year}
                onChange={handleInputChange}
                placeholder="2023"
                disabled={submitting}
                className={errors.year ? 'border-destructive' : ''}
              />
              {errors.year && (
                <p className="text-sm text-destructive">{errors.year}</p>
              )}
            </div>

            {/* Mode Selection */}
            <div className="space-y-3">
              <Label>Execution Mode</Label>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="relative">
                  <input
                    type="radio"
                    name="mode"
                    id="mode-automatic"
                    value="automatic"
                    checked={formData.mode === 'automatic'}
                    onChange={(e) => handleModeChange(e.target.value as 'automatic' | 'manual')}
                    disabled={submitting}
                    className="peer sr-only"
                  />
                  <Label
                    htmlFor="mode-automatic"
                    className="flex flex-col items-start gap-2 rounded-md border-2 border-muted p-4 hover:bg-accent hover:text-accent-foreground peer-checked:border-green-600 peer-checked:bg-green-50 cursor-pointer"
                  >
                    <div className="font-semibold">Automatic</div>
                    <div className="text-sm text-muted-foreground">
                      Pipeline runs automatically using LLM. No manual intervention required.
                    </div>
                  </Label>
                </div>

                <div className="relative">
                  <input
                    type="radio"
                    name="mode"
                    id="mode-manual"
                    value="manual"
                    checked={formData.mode === 'manual'}
                    onChange={(e) => handleModeChange(e.target.value as 'automatic' | 'manual')}
                    disabled={submitting}
                    className="peer sr-only"
                  />
                  <Label
                    htmlFor="mode-manual"
                    className="flex flex-col items-start gap-2 rounded-md border-2 border-muted p-4 hover:bg-accent hover:text-accent-foreground peer-checked:border-green-600 peer-checked:bg-green-50 cursor-pointer"
                  >
                    <div className="font-semibold">Manual</div>
                    <div className="text-sm text-muted-foreground">
                      Copy prompt, paste into your own LLM, and submit the result.
                    </div>
                  </Label>
                </div>
              </div>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{errorMessage}</AlertDescription>
              </Alert>
            )}

            {/* Submit Button */}
            <div className="flex justify-end gap-2">
              <Button
                type="submit"
                disabled={submitting || inputFiles.length === 0}
                className="bg-green-600 hover:bg-green-700"
              >
                {submitting ? (
                  <>
                    <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                    Starting Conversion...
                  </>
                ) : (
                  'Start Conversion'
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
      )}

      {/* Show automatic execution status */}
      {autoExecuting && (
        <Card>
          <CardContent className="pt-6 flex flex-col items-center justify-center space-y-4">
            <Loader2Icon className="h-8 w-8 animate-spin text-primary" />
            <p className="text-lg font-medium">{autoStatus}</p>
            <p className="text-sm text-muted-foreground">
              Processing your document automatically...
            </p>
          </CardContent>
        </Card>
      )}

      {/* Show automatic execution error */}
      {autoError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{autoError}</AlertDescription>
          <div className="mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setAutoError(null);
                setAutoResults(null);
                setAutoExecuting(false);
              }}
            >
              Try Again
            </Button>
          </div>
        </Alert>
      )}

      {/* Show automatic execution results */}
      {autoResults && !autoExecuting && (
        <div className="space-y-6 animate-in fade-in duration-500">
          <Alert className="border-green-500 bg-green-50 text-green-900">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertTitle>Success</AlertTitle>
            <AlertDescription>
              Automatic conversion completed successfully!
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
                  <p className="font-medium">{autoResults.title}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground">Author</h4>
                  <p className="font-medium">{autoResults.author}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground">Classification</h4>
                  <Badge variant="secondary" className="uppercase">{autoResults.classification}</Badge>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground">Token Count</h4>
                  <p className="font-mono">{autoResults.token_count.toLocaleString()}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground">Chunks Created</h4>
                  <p className="font-mono">{autoResults.chunk_count}</p>
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button
                  onClick={() => {
                    setAutoResults(null);
                    setAutoError(null);
                    setAutoExecuting(false);
                  }}
                >
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
                  {autoResults.chunks.map((chunk) => (
                    <div key={chunk.id} className="border rounded-lg p-4 bg-card hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div className="flex items-center gap-2">
                          <Badge className="bg-primary text-primary-foreground">H{chunk.heading_level}</Badge>
                          <h4 className="font-semibold text-lg">{chunk.heading_text}</h4>
                        </div>
                        <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
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

      {/* History Section - Always visible below the form */}
      <div className="space-y-4">
        <div className="border-t pt-6">
          <h3 className="text-2xl font-bold tracking-tight mb-2">Past Conversions</h3>
          <p className="text-muted-foreground text-sm mb-4">
            View your previous simple conversion works
          </p>

          {/* Loading State */}
          {loadingHistory && (
            <div className="flex items-center justify-center h-32" data-testid="history-loading">
              <Loader2Icon className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          )}

          {/* Error State */}
          {historyError && !loadingHistory && (
            <Alert variant="destructive" data-testid="history-error">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{historyError}</AlertDescription>
              <div className="mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={fetchHistory}
                  data-testid="history-retry-button"
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Retry
                </Button>
              </div>
            </Alert>
          )}

          {/* Empty State */}
          {!loadingHistory && !historyError && historyWorks.length === 0 && (
            <div className="text-center py-12 border rounded-lg bg-muted/10" data-testid="history-empty">
              <p className="text-muted-foreground">No past conversions yet</p>
              <p className="text-sm text-muted-foreground mt-1">
                Start a new conversion above to see it appear here
              </p>
            </div>
          )}

          {/* History Table */}
          {!loadingHistory && !historyError && historyWorks.length > 0 && (
            <div className="border rounded-lg" data-testid="history-list">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Author</TableHead>
                    <TableHead>Classification</TableHead>
                    <TableHead>Mode</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {historyWorks.map((work) => {
                    const formatDate = (dateString: string): string => {
                      const date = new Date(dateString);
                      return date.toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric'
                      });
                    };

                    return (
                      <TableRow
                        key={work.work_id}
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => router.push(`/simple-conversion/history/${work.work_id}`)}
                        data-testid={`history-row-${work.work_id}`}
                      >
                        <TableCell className="font-medium">{work.title}</TableCell>
                        <TableCell>{work.author}</TableCell>
                        <TableCell>
                          <Badge
                            variant={work.classification === 'small' ? 'default' : 'secondary'}
                            className={work.classification === 'small' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-purple-600 hover:bg-purple-700 text-white'}
                            data-testid="classification-badge"
                          >
                            {work.classification === 'small' ? 'Small' : 'Large'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" data-testid="mode-badge">
                            {work.mode === 'automatic' ? 'Automatic' : 'Manual'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {work.status === 'success' ? (
                            <div className="flex items-center gap-2 text-green-600">
                              <CheckCircle2 className="h-4 w-4" data-testid="status-success" />
                              <span>Success</span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2 text-red-600">
                              <AlertCircle className="h-4 w-4" data-testid="status-error" />
                              <span>Error</span>
                            </div>
                          )}
                        </TableCell>
                        <TableCell className="text-muted-foreground" data-testid="created-date">
                          {formatDate(work.created_at)}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
