/**
 * Simple Conversion Page
 *
 * Entry point for the simple conversion workflow. Fetches available files
 * from input folder, collects metadata, and execution mode, then initiates
 * the conversion process.
 */

"use client";

import React, { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Loader2Icon, AlertCircle, CheckCircle2, RefreshCw, FileText, User, Calendar, Settings } from "lucide-react";
import { HistoryErrorBoundary } from "@/components/simple-conversion/HistoryErrorBoundary";
import { PageHeader } from "@/components/page-header";
import { DataTable, DataTableColumn } from "@/components/data-table";
import { StatusBadge, StatusConfig } from "@/components/status-badge";
import { FormField } from "@/components/form-field";
import { usePageData } from "@/hooks/use-page-data";
import { PageLoadingState } from "@/components/page-loading-state";
import { PageErrorState } from "@/components/page-error-state";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FormData {
  selectedFile: string;
  title: string;
  author: string;
  year: string;
  mode: 'automatic' | 'manual';
}

interface HistoryWorkAPI {
  work_id: number;
  title: string;
  author: string;
  classification: 'small' | 'large' | null;
  mode: 'automatic' | 'manual';
  status: 'complete' | 'failed' | 'converting' | 'sanitized';
  created_at: string;
  error_message?: string | null;
}

const statusConfig: Record<string, StatusConfig> = {
  complete: {
    label: "Complete",
    variant: "default",
    icon: CheckCircle2,
  },
  failed: {
    label: "Failed",
    variant: "destructive",
    icon: AlertCircle,
  },
  converting: {
    label: "Converting",
    variant: "secondary",
    icon: Loader2Icon,
  },
  sanitized: {
    label: "Sanitized",
    variant: "secondary",
    icon: RefreshCw,
  },
};

export default function SimpleConversionPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const { 
    register, 
    handleSubmit, 
    setValue, 
    watch, 
    formState: { errors } 
  } = useForm<FormData>({
    defaultValues: {
      selectedFile: '',
      title: '',
      author: '',
      year: '',
      mode: 'automatic'
    }
  });

  const selectedFile = watch('selectedFile');
  const selectedMode = watch('mode');

  // Memoized fetch functions to avoid infinite loops in usePageData
  const fetchFiles = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/conv/io-folder-data`);
    if (!response.ok) {
      throw new Error(`Failed to fetch files: ${response.statusText}`);
    }
    const data = await response.json();
    return (data.input_files || []) as string[];
  }, []);

  const fetchHistory = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/simple-conversion/history`);
    if (!response.ok) {
      throw new Error(`Failed to fetch history: ${response.statusText}`);
    }
    const data = await response.json();
    return (data.items || []) as HistoryWorkAPI[];
  }, []);

  // Fetch input files
  const { 
    data: inputFiles, 
    loading: loadingFiles, 
    error: filesFetchError, 
    refetch: refetchFiles 
  } = usePageData(fetchFiles);

  // Fetch history
  const { 
    data: historyWorks, 
    loading: loadingHistory, 
    error: historyError, 
    refetch: refetchHistory 
  } = usePageData(fetchHistory);

  const onSubmit = async (formData: FormData) => {
    setSubmitting(true);
    setSubmitError(null);

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

      if (mode === 'manual') {
        router.push(`/simple-conversion/manual/${work_id}`);
      } else {
        router.push(`/simple-conversion/automatic/${work_id}`);
      }
    } catch (err) {
      console.error('Failed to start conversion:', err);
      const message = err instanceof Error ? err.message : 'Failed to start conversion';
      setSubmitError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const columns: DataTableColumn<HistoryWorkAPI>[] = [
    {
      key: 'title',
      header: 'Title',
      sortable: true,
      className: "min-w-[200px] w-[30%] break-words whitespace-normal font-medium",
    },
    {
      key: 'author',
      header: 'Author',
      sortable: true,
      className: "min-w-[150px] w-[20%] break-words whitespace-normal",
    },
    {
      key: 'classification',
      header: 'Classification',
      className: "min-w-[120px] w-[15%]",
      cell: (work) => (
        <Badge
          variant={work.classification === 'small' ? 'default' : 'secondary'}
          className={work.classification === 'small' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-purple-600 hover:bg-purple-700 text-white'}
        >
          {work.classification ? (work.classification.charAt(0).toUpperCase() + work.classification.slice(1)) : 'N/A'}
        </Badge>
      )
    },
    {
      key: 'mode',
      header: 'Mode',
      className: "min-w-[110px] w-[15%]",
      cell: (work) => (
        <Badge
          variant="outline"
          className={work.mode === 'automatic' ? 'border-green-600 text-green-700' : 'border-amber-600 text-amber-700'}
        >
          {work.mode.charAt(0).toUpperCase() + work.mode.slice(1)}
        </Badge>
      )
    },
    {
      key: 'status',
      header: 'Status',
      className: "min-w-[110px] w-[12%]",
      cell: (work) => (
        <StatusBadge status={work.status} statusConfig={statusConfig} />
      )
    },
    {
      key: 'created_at',
      header: 'Created',
      sortable: true,
      className: "min-w-[100px] w-[8%] text-muted-foreground whitespace-nowrap",
      cell: (work) => {
        const date = new Date(work.created_at);
        return date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });
      }
    }
  ];

  if (loadingFiles) {
    return <PageLoadingState />;
  }

  if (filesFetchError) {
    return (
      <PageErrorState 
        error={filesFetchError} 
        title="Failed to load input files"
        onRetry={refetchFiles}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Simple Conversion"
        description="Convert your PDF or EPUB document in a streamlined single-page workflow. Select a file from the input folder and provide metadata."
      />

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
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* File Selection */}
              <FormField 
                label="Select File" 
                required 
                error={errors.selectedFile?.message}
              >
                <Select
                  value={selectedFile}
                  onValueChange={(value) => setValue('selectedFile', value, { shouldValidate: true })}
                  disabled={submitting || !inputFiles || inputFiles.length === 0}
                >
                  <SelectTrigger className={errors.selectedFile ? 'border-destructive' : ''}>
                    <SelectValue placeholder="Choose a file from input folder" />
                  </SelectTrigger>
                  <SelectContent>
                    {!inputFiles || inputFiles.length === 0 ? (
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
                <input type="hidden" {...register('selectedFile', { required: 'Please select a file' })} />
              </FormField>

              {/* Title */}
              <FormField 
                label="Title" 
                required 
                error={errors.title?.message}
              >
                <div className="relative">
                  <FileText className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    {...register('title', { required: 'Title is required' })}
                    placeholder="Document title"
                    disabled={submitting}
                    className={cn("pl-10", errors.title && "border-destructive")}
                  />
                </div>
              </FormField>

              {/* Author */}
              <FormField 
                label="Author" 
                required 
                error={errors.author?.message}
              >
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    {...register('author', { required: 'Author is required' })}
                    placeholder="Author name"
                    disabled={submitting}
                    className={cn("pl-10", errors.author && "border-destructive")}
                  />
                </div>
              </FormField>

              {/* Year (Optional) */}
              <FormField 
                label="Publication Year" 
                description="(optional)"
                error={errors.year?.message}
              >
                <div className="relative">
                  <Calendar className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="number"
                    {...register('year', { 
                      validate: value => {
                        if (!value) return true;
                        const yearNum = parseInt(value, 10);
                        if (isNaN(yearNum) || yearNum < 1000 || yearNum > new Date().getFullYear() + 1) {
                          return 'Please enter a valid year';
                        }
                        return true;
                      }
                    })}
                    placeholder="2023"
                    disabled={submitting}
                    className={cn("pl-10", errors.year && "border-destructive")}
                  />
                </div>
              </FormField>

              {/* Mode Selection */}
              <div className="space-y-3">
                <Label>Execution Mode</Label>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="relative">
                    <input
                      type="radio"
                      id="mode-automatic"
                      value="automatic"
                      checked={selectedMode === 'automatic'}
                      {...register('mode')}
                      disabled={submitting}
                      className="peer sr-only"
                    />
                    <Label
                      htmlFor="mode-automatic"
                      className="flex flex-col items-start gap-2 rounded-md border-2 border-muted p-4 hover:bg-accent hover:text-accent-foreground peer-checked:border-primary peer-checked:bg-accent/50 cursor-pointer"
                    >
                      <div className="font-semibold flex items-center gap-2">
                        <Settings className="h-4 w-4" />
                        Automatic
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Pipeline runs automatically using LLM. No manual intervention required.
                      </div>
                    </Label>
                  </div>

                  <div className="relative">
                    <input
                      type="radio"
                      id="mode-manual"
                      value="manual"
                      checked={selectedMode === 'manual'}
                      {...register('mode')}
                      disabled={submitting}
                      className="peer sr-only"
                    />
                    <Label
                      htmlFor="mode-manual"
                      className="flex flex-col items-start gap-2 rounded-md border-2 border-muted p-4 hover:bg-accent hover:text-accent-foreground peer-checked:border-primary peer-checked:bg-accent/50 cursor-pointer"
                    >
                      <div className="font-semibold flex items-center gap-2">
                        <User className="h-4 w-4" />
                        Manual
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Copy prompt, paste into your own LLM, and submit the result.
                      </div>
                    </Label>
                  </div>
                </div>
              </div>

              {/* Error Message */}
              {submitError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{submitError}</AlertDescription>
                </Alert>
              )}

              {/* Submit Button */}
              <div className="flex justify-end gap-2">
                <Button
                  type="submit"
                  disabled={submitting || !inputFiles || inputFiles.length === 0}
                  className="w-full sm:w-auto"
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

            {historyError ? (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {historyError.message}
                  <Button
                    variant="link"
                    size="sm"
                    className="h-auto p-0 ml-2"
                    onClick={() => refetchHistory()}
                  >
                    Retry
                  </Button>
                </AlertDescription>
              </Alert>
            ) : (
              <DataTable
                columns={columns}
                data={historyWorks || []}
                loading={loadingHistory}
                onRowClick={(work) => router.push(`/simple-conversion/history/${work.work_id}`)}
                emptyState={{
                  title: "No past conversions yet",
                  description: "Start a new conversion above to see it appear here",
                }}
              />
            )}
          </div>
        </div>
      </HistoryErrorBoundary>
    </div>
  );
}
