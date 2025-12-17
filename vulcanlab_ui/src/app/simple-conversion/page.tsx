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
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Loader2Icon, AlertCircle, CheckCircle2, RefreshCw } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { HistoryErrorBoundary } from "@/components/simple-conversion/HistoryErrorBoundary";

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

      // Branch based on mode and redirect to appropriate page
      if (mode === 'manual') {
        router.push(`/simple-conversion/manual/${work_id}`);
      } else {
        // Automatic mode: Redirect to automatic execution page
        router.push(`/simple-conversion/automatic/${work_id}`);
      }

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

      {/* Show form unless submitting */}
      {!submitting && (
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

      {/* Show loading during redirect */}
      {submitting && (
        <Card>
          <CardContent className="pt-6 flex flex-col items-center justify-center space-y-4">
            <Loader2Icon className="h-8 w-8 animate-spin text-primary" />
            <p className="text-lg font-medium">Starting conversion...</p>
          </CardContent>
        </Card>
      )}

      {/* History Section - Always visible below the form */}
      <HistoryErrorBoundary>
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
            <div className="border rounded-lg overflow-hidden" data-testid="history-list">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="min-w-[200px] w-[30%]">Title</TableHead>
                      <TableHead className="min-w-[150px] w-[20%]">Author</TableHead>
                      <TableHead className="min-w-[120px] w-[15%]">Classification</TableHead>
                      <TableHead className="min-w-[110px] w-[15%]">Mode</TableHead>
                      <TableHead className="min-w-[110px] w-[12%]">Status</TableHead>
                      <TableHead className="min-w-[100px] w-[8%]">Created</TableHead>
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
                          <TableCell className="font-medium min-w-[200px] max-w-[300px] break-words whitespace-normal">{work.title}</TableCell>
                          <TableCell className="min-w-[150px] max-w-[200px] break-words whitespace-normal">{work.author}</TableCell>
                          <TableCell className="min-w-[120px]">
                            <Badge
                              variant={work.classification === 'small' ? 'default' : 'secondary'}
                              className={work.classification === 'small' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-purple-600 hover:bg-purple-700 text-white'}
                              data-testid="classification-badge"
                            >
                              {work.classification === 'small' ? 'Small' : 'Large'}
                            </Badge>
                          </TableCell>
                          <TableCell className="min-w-[110px]">
                            <Badge
                              variant="outline"
                              className={work.mode === 'automatic' ? 'border-green-600 text-green-700' : 'border-amber-600 text-amber-700'}
                              data-testid="mode-badge"
                            >
                              {work.mode === 'automatic' ? 'Automatic' : 'Manual'}
                            </Badge>
                          </TableCell>
                          <TableCell className="min-w-[110px]">
                            {work.status === 'success' ? (
                              <div className="flex items-center gap-2 text-green-600 whitespace-nowrap">
                                <CheckCircle2 className="h-4 w-4 flex-shrink-0" data-testid="status-success" />
                                <span>Success</span>
                              </div>
                            ) : (
                              <div className="flex items-center gap-2 text-red-600 whitespace-nowrap">
                                <AlertCircle className="h-4 w-4 flex-shrink-0" data-testid="status-error" />
                                <span>Error</span>
                              </div>
                            )}
                          </TableCell>
                          <TableCell className="text-muted-foreground min-w-[100px] whitespace-nowrap" data-testid="created-date">
                            {formatDate(work.created_at)}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
          </div>
        </div>
      </HistoryErrorBoundary>
    </div>
  );
}
