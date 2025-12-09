"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, CheckCircle2, Loader2Icon, ArrowLeft, FileText } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FormData {
  title: string;
  authors: string;
  year: string;
  publisher: string;
  isbn: string;
  edition: string;
  filename: string;
  content: string;
}

interface FormErrors {
  title?: string;
  filename?: string;
  content?: string;
  year?: string;
}

export default function AddSanitizedMarkdownPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>({
    title: "",
    authors: "",
    year: "",
    publisher: "",
    isbn: "",
    edition: "",
    filename: "",
    content: "",
  });
  const [formErrors, setFormErrors] = useState<FormErrors>({});

  const validateForm = (): boolean => {
    const errors: FormErrors = {};

    if (!formData.title.trim()) {
      errors.title = "Title is required";
    }

    if (!formData.filename.trim()) {
      errors.filename = "Filename is required";
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.filename)) {
      errors.filename = "Filename must contain only letters, numbers, underscores, and hyphens";
    }

    if (!formData.content.trim()) {
      errors.content = "Content is required";
    }

    if (formData.year && !/^\d{4}$/.test(formData.year)) {
      errors.year = "Year must be a 4-digit number";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (formErrors[name as keyof FormErrors]) {
      setFormErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const generateFilename = () => {
    if (formData.title) {
      const filename = formData.title
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, "")
        .replace(/\s+/g, "_")
        .substring(0, 50);
      setFormData((prev) => ({ ...prev, filename }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const payload = {
        title: formData.title.trim(),
        authors: formData.authors.trim() || null,
        year: formData.year ? parseInt(formData.year, 10) : null,
        publisher: formData.publisher.trim() || null,
        isbn: formData.isbn.trim() || null,
        edition: formData.edition.trim() || null,
        filename: formData.filename.trim(),
        content: formData.content,
      };

      const response = await fetch(`${API_BASE_URL}/sanitization/add-sanitized`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed: ${response.statusText}`);
      }

      const data = await response.json();
      setSuccess(`Work created successfully! ID: ${data.work_id}`);

      // Redirect to the work's sanitization page after a short delay
      setTimeout(() => {
        router.push(`/sanitization/${data.work_id}`);
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add sanitized markdown");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push("/sanitization")}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Add Sanitized Markdown</h2>
          <p className="text-muted-foreground">
            Add a pre-sanitized document directly to start chunking.
          </p>
        </div>
      </div>

      {/* Success Message */}
      {success && (
        <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-700 dark:text-green-300">
            {success}
          </AlertDescription>
        </Alert>
      )}

      {/* Error Message */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        {/* Bibliographic Information */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Bibliographic Information
            </CardTitle>
            <CardDescription>
              Enter the metadata for this work. Only Title is required.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Title */}
              <div className="md:col-span-2 space-y-2">
                <Label htmlFor="title" className="flex items-center gap-1">
                  Title <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  placeholder="Cognitive Psychology: A Student's Handbook"
                  className={formErrors.title ? "border-red-500" : ""}
                />
                {formErrors.title && (
                  <p className="text-sm text-red-500">{formErrors.title}</p>
                )}
              </div>

              {/* Authors */}
              <div className="space-y-2">
                <Label htmlFor="authors">Authors</Label>
                <Input
                  id="authors"
                  name="authors"
                  value={formData.authors}
                  onChange={handleInputChange}
                  placeholder="Michael W. Eysenck, Mark T. Keane"
                />
              </div>

              {/* Year */}
              <div className="space-y-2">
                <Label htmlFor="year">Year</Label>
                <Input
                  id="year"
                  name="year"
                  value={formData.year}
                  onChange={handleInputChange}
                  placeholder="2020"
                  maxLength={4}
                  className={formErrors.year ? "border-red-500" : ""}
                />
                {formErrors.year && (
                  <p className="text-sm text-red-500">{formErrors.year}</p>
                )}
              </div>

              {/* Publisher */}
              <div className="space-y-2">
                <Label htmlFor="publisher">Publisher</Label>
                <Input
                  id="publisher"
                  name="publisher"
                  value={formData.publisher}
                  onChange={handleInputChange}
                  placeholder="Psychology Press"
                />
              </div>

              {/* ISBN */}
              <div className="space-y-2">
                <Label htmlFor="isbn">ISBN</Label>
                <Input
                  id="isbn"
                  name="isbn"
                  value={formData.isbn}
                  onChange={handleInputChange}
                  placeholder="978-1138482210"
                />
              </div>

              {/* Edition */}
              <div className="md:col-span-2 space-y-2">
                <Label htmlFor="edition">Edition</Label>
                <Input
                  id="edition"
                  name="edition"
                  value={formData.edition}
                  onChange={handleInputChange}
                  placeholder="8th Edition"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* File Information */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>File Details</CardTitle>
            <CardDescription>
              Specify the filename for the sanitized markdown file.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="filename" className="flex items-center gap-1">
                Filename <span className="text-red-500">*</span>
              </Label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Input
                    id="filename"
                    name="filename"
                    value={formData.filename}
                    onChange={handleInputChange}
                    placeholder="cognitive_psychology"
                    className={formErrors.filename ? "border-red-500 pr-32" : "pr-32"}
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                    .sanitized.md
                  </span>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  onClick={generateFilename}
                  disabled={!formData.title}
                >
                  Generate from Title
                </Button>
              </div>
              {formErrors.filename && (
                <p className="text-sm text-red-500">{formErrors.filename}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Only letters, numbers, underscores, and hyphens are allowed.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Content */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Sanitized Markdown Content</CardTitle>
            <CardDescription>
              Paste the sanitized markdown content below. This should be clean,
              well-structured markdown ready for chunking.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Label htmlFor="content" className="flex items-center gap-1">
                Content <span className="text-red-500">*</span>
              </Label>
              <Textarea
                id="content"
                name="content"
                value={formData.content}
                onChange={handleInputChange}
                placeholder="# Chapter 1: Introduction

This is the introduction to the document...

## 1.1 Background

Background content here..."
                className={`min-h-[400px] font-mono text-sm ${
                  formErrors.content ? "border-red-500" : ""
                }`}
              />
              {formErrors.content && (
                <p className="text-sm text-red-500">{formErrors.content}</p>
              )}
              <p className="text-xs text-muted-foreground">
                {formData.content.length.toLocaleString()} characters
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-between">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push("/sanitization")}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            {loading ? (
              <>
                <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              "Create Work"
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}



