"use client";

import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { PageHeader, FormField } from "@/components";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, FileText, ArrowLeft } from "lucide-react";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";

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

export default function AddSanitizedMarkdownPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      title: "",
      authors: "",
      year: "",
      publisher: "",
      isbn: "",
      edition: "",
      filename: "",
      content: "",
    },
  });

  const titleValue = watch("title");

  const generateFilename = () => {
    if (titleValue) {
      const filename = titleValue
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, "")
        .replace(/\s+/g, "_")
        .substring(0, 50);
      setValue("filename", filename);
    }
  };

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    try {
      const payload = {
        ...data,
        authors: data.authors.trim() || null,
        year: data.year ? parseInt(data.year, 10) : null,
        publisher: data.publisher.trim() || null,
        isbn: data.isbn.trim() || null,
        edition: data.edition.trim() || null,
        filename: data.filename.trim(),
        content: data.content,
      };

      const response = await fetch(`${API_BASE_URL}/sanitization/add-sanitized`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to create work");
      }

      const resData = await response.json();
      setSuccess(true);
      toast({
        title: "Work created",
        description: `Work ID: ${resData.work_id} created successfully.`,
      });

      setTimeout(() => {
        router.push(`/sanitization/${resData.work_id}`);
      }, 1500);
    } catch (err) {
      toast({
        title: "Creation failed",
        description: err instanceof Error ? err.message : "An error occurred",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center space-y-4">
          <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto" />
          <h2 className="text-2xl font-bold text-foreground">Work Created Successfully!</h2>
          <p className="text-muted-foreground">Redirecting...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push("/sanitization")}
          aria-label="Back to Sanitization"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <PageHeader 
          title="Add Sanitized Markdown" 
          description="Add a pre-sanitized document directly to the corpus to start chunking."
        />
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8 max-w-5xl">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Bibliographic Information
            </CardTitle>
            <CardDescription>
              Enter the metadata for this work. Only title is required.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FormField 
                label="Title" 
                required 
                error={errors.title?.message}
                className="md:col-span-2"
              >
                <Input 
                  {...register("title", { required: "Title is required" })}
                  placeholder="Cognitive Psychology: A Student's Handbook"
                />
              </FormField>

              <FormField label="Authors" error={errors.authors?.message}>
                <Input 
                  {...register("authors")}
                  placeholder="Michael W. Eysenck, Mark T. Keane"
                />
              </FormField>

              <FormField label="Year" error={errors.year?.message}>
                <Input 
                  {...register("year", {
                    pattern: {
                      value: /^\d{4}$/,
                      message: "Year must be a 4-digit number"
                    }
                  })}
                  placeholder="2020"
                />
              </FormField>

              <FormField label="Publisher" error={errors.publisher?.message}>
                <Input 
                  {...register("publisher")}
                  placeholder="Psychology Press"
                />
              </FormField>

              <FormField label="ISBN" error={errors.isbn?.message}>
                <Input 
                  {...register("isbn")}
                  placeholder="978-1138482210"
                />
              </FormField>

              <FormField label="Edition" error={errors.edition?.message} className="md:col-span-2">
                <Input 
                  {...register("edition")}
                  placeholder="8th Edition"
                />
              </FormField>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>File Details</CardTitle>
            <CardDescription>
              Specify the filename and content.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-end">
              <FormField 
                label="Filename" 
                required 
                error={errors.filename?.message}
                className="flex-1 w-full"
                description="Only letters, numbers, underscores, and hyphens"
              >
                <div className="relative">
                  <Input 
                    {...register("filename", {
                      required: "Filename is required",
                      pattern: {
                        value: /^[a-zA-Z0-9_-]+$/,
                        message: "Invalid characters in filename"
                      }
                    })}
                    placeholder="cognitive_psychology"
                    className="pr-32"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                    .sanitized.md
                  </span>
                </div>
              </FormField>
              <Button
                type="button"
                variant="outline"
                onClick={generateFilename}
                disabled={!titleValue}
                className="w-full sm:w-auto"
              >
                Generate from Title
              </Button>
            </div>

            <FormField 
              label="Sanitized Markdown Content" 
              required 
              error={errors.content?.message}
              description="Clean, well-structured markdown ready for chunking"
            >
              <div className="space-y-2">
                <Textarea 
                  {...register("content", { required: "Content is required" })}
                  placeholder="# Chapter 1: Introduction..."
                  className="min-h-[400px] font-mono text-sm leading-relaxed"
                />
                <p className="text-xs text-muted-foreground text-right italic">
                  {(watch("content") || "").length.toLocaleString()} characters
                </p>
              </div>
            </FormField>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push("/sanitization")}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={loading} className="min-w-[120px]">
            {loading ? "Creating..." : "Create Work"}
          </Button>
        </div>
      </form>
    </div>
  );
}
