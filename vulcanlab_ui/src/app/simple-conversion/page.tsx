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
import { Loader2Icon, AlertCircle } from "lucide-react";

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

  // Fetch input files on mount
  useEffect(() => {
    fetchInputFiles();
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

      // Navigate to appropriate workflow page
      if (mode === 'automatic') {
        router.push(`/simple-conversion/automatic/${work_id}`);
      } else {
        router.push(`/simple-conversion/manual/${work_id}`);
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
    </div>
  );
}
