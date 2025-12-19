"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, ChevronLeft, Loader2Icon, FileText, Sparkles } from "lucide-react";
import { MarkdownEditor } from "@/components/markdown-editor";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { FormField, PageHeader } from "@/components";
import { useToast } from "@/hooks/use-toast";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FileContentResponse {
  content: string;
  filename: string;
}

interface FormData {
  title: string;
  authors: string;
  year: string;
  publisher: string;
  isbn: string;
  edition: string;
  volume: string;
  issue: string;
  pages: string;
  url: string;
  city: string;
  institution: string;
  editor: string;
}

interface AddWorkResponse {
  success: boolean;
  message: string;
  work_id: number;
}

type CitationStyle = "MLA" | "APA" | "Chicago";

interface ParsedCitation {
  title: string;
  authors: string;
  year: string;
  publisher: string;
  edition: string;
  volume: string;
  issue: string;
  pages: string;
  url: string;
  city: string;
  institution: string;
  editor: string;
}

export default function AddWorkPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const fileId = params.id as string;

  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [markdownContent, setMarkdownContent] = useState<string>("");
  const [loadingContent, setLoadingContent] = useState(true);

  // Citation dialog state
  const [citationDialogOpen, setCitationDialogOpen] = useState(false);
  const [citationStyle, setCitationStyle] = useState<CitationStyle>("MLA");
  const [citationText, setCitationText] = useState<string>("");
  const [llmParsing, setLlmParsing] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      title: "",
      authors: "",
      year: "",
      publisher: "",
      isbn: "",
      edition: "",
      volume: "",
      issue: "",
      pages: "",
      url: "",
      city: "",
      institution: "",
      editor: "",
    },
  });

  useEffect(() => {
    const fetchMarkdown = async () => {
      try {
        setLoadingContent(true);
        const response = await fetch(`${API_BASE_URL}/conv/original-markdown/${fileId}`);
        if (response.ok) {
          const data: FileContentResponse = await response.json();
          setMarkdownContent(data.content);
        }
      } catch (err) {
        console.error("Failed to load markdown preview", err);
      } finally {
        setLoadingContent(false);
      }
    };

    if (fileId) {
      fetchMarkdown();
    }
  }, [fileId]);

  const onSubmit = async (data: FormData) => {
    setSubmitting(true);
    try {
      const requestBody: any = {
        title: data.title.trim(),
      };

      // Map fields to API request
      Object.entries(data).forEach(([key, value]) => {
        if (key === "title") return;
        if (value && value.trim()) {
          if (key === "year") {
            requestBody[key] = parseInt(value, 10);
          } else {
            requestBody[key] = value.trim();
          }
        }
      });

      const response = await fetch(
        `${API_BASE_URL}/conv/add-to-database/${fileId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestBody),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to add work");
      }

      const resData: AddWorkResponse = await response.json();
      setSuccess(true);
      toast({
        title: "Work added",
        description: `Work successfully added to the database with ID: ${resData.work_id}`,
      });

      setTimeout(() => {
        router.push(`/sanitization/${resData.work_id}`);
      }, 2000);
    } catch (err) {
      toast({
        title: "Submission failed",
        description: err instanceof Error ? err.message : "An error occurred",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Citation parsing logic (regex-based) - kept from original
  const parseMLACitation = (citation: string): ParsedCitation => {
    const result: ParsedCitation = { title: "", authors: "", year: "", publisher: "", edition: "", volume: "", issue: "", pages: "", url: "", city: "", institution: "", editor: "" };
    const trimmed = citation.trim();
    const yearMatch = trimmed.match(/\((\d{4})\)/);
    if (yearMatch) result.year = yearMatch[1];
    const authorMatch = trimmed.match(/^(.+?)\.\s*(.+)$/);
    if (authorMatch) {
      const authors = authorMatch[1].trim();
      const afterAuthors = authorMatch[2].trim();
      const quoteMatch = afterAuthors.match(/^(["'""])(.+?)\1\.\s*(.+)$/);
      if (quoteMatch) {
        result.authors = authors;
        result.title = quoteMatch[2].trim();
        let rest = quoteMatch[3].trim().replace(/^["'""\s]+/, "").trim();
        const volumeMatch = rest.match(/(.+?)\s+(\d+(?:\.\d+)?)\s*\(/);
        if (volumeMatch) {
          result.publisher = volumeMatch[1].trim();
          result.edition = volumeMatch[2].trim();
        } else {
          result.publisher = rest.replace(/\s*\(.*$/, "").trim();
        }
      }
    }
    return result;
  };

  const parseAPACitation = (citation: string): ParsedCitation => {
    const result: ParsedCitation = { title: "", authors: "", year: "", publisher: "", edition: "", volume: "", issue: "", pages: "", url: "", city: "", institution: "", editor: "" };
    const trimmed = citation.trim();
    const yearMatch = trimmed.match(/\((\d{4})\)/);
    if (yearMatch) result.year = yearMatch[1];
    const authorMatch = trimmed.match(/^(.+?)\.\s*\(/);
    if (authorMatch) {
      result.authors = authorMatch[1].trim();
      const titleMatch = trimmed.match(/\)\.\s*(.+?)\.\s*(.+?),/);
      if (titleMatch) {
        result.title = titleMatch[1].trim();
        const pubVolMatch = trimmed.match(/\)\.\s*.+?\.\s*(.+?),\s*(\d+)\((\d+)\)/);
        if (pubVolMatch) {
          result.publisher = pubVolMatch[1].trim();
          result.edition = `${pubVolMatch[2]}.${pubVolMatch[3]}`;
        }
      }
    }
    return result;
  };

  const parseChicagoCitation = (citation: string): ParsedCitation => {
    const result: ParsedCitation = { title: "", authors: "", year: "", publisher: "", edition: "", volume: "", issue: "", pages: "", url: "", city: "", institution: "", editor: "" };
    const trimmed = citation.trim();
    const yearMatch = trimmed.match(/\((\d{4})\)/);
    if (yearMatch) result.year = yearMatch[1];
    const authorMatch = trimmed.match(/^(.+?)\.\s*(.+)$/);
    if (authorMatch) {
      result.authors = authorMatch[1].trim();
      const afterAuthors = authorMatch[2].trim();
      const quoteMatch = afterAuthors.match(/^(["'""])(.+?)\1\.\s*(.+)$/);
      if (quoteMatch) {
        result.title = quoteMatch[2].trim();
        let rest = quoteMatch[3].trim().replace(/^["'""\s]+/, "").trim();
        const volumeIssueMatch = rest.match(/(.+?)\s+(\d+),\s*no\.\s*(\d+)\s*\(/i);
        if (volumeIssueMatch) {
          result.publisher = volumeIssueMatch[1].trim();
          result.edition = `${volumeIssueMatch[2]}.${volumeIssueMatch[3]}`;
        }
      }
    }
    return result;
  };

  const handleCitationApply = () => {
    if (!citationText.trim()) return;
    let parsed: ParsedCitation;
    if (citationStyle === "MLA") parsed = parseMLACitation(citationText);
    else if (citationStyle === "APA") parsed = parseAPACitation(citationText);
    else parsed = parseChicagoCitation(citationText);

    Object.entries(parsed).forEach(([key, value]) => {
      if (value) setValue(key as keyof FormData, value);
    });
    setCitationDialogOpen(false);
    setCitationText("");
  };

  const handleLlmParse = async () => {
    if (!citationText.trim()) return;
    setLlmParsing(true);
    try {
      const response = await fetch(`${API_BASE_URL}/conv/parse-citation-llm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          citation_text: citationText.trim(),
          citation_format: citationStyle,
        }),
      });

      if (!response.ok) throw new Error("LLM Parsing failed");
      const parsed = await response.json();
      
      Object.entries(parsed).forEach(([key, value]) => {
        if (value) {
          if (Array.isArray(value)) setValue(key as keyof FormData, value.join(", "));
          else setValue(key as keyof FormData, value.toString());
        }
      });
      setCitationDialogOpen(false);
      setCitationText("");
    } catch (error) {
      toast({
        title: "AI Parsing failed",
        description: error instanceof Error ? error.message : "Failed to parse citation",
        variant: "destructive",
      });
    } finally {
      setLlmParsing(false);
    }
  };

  if (success) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center space-y-4">
          <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto" />
          <h2 className="text-2xl font-bold">Work Added Successfully!</h2>
          <p className="text-muted-foreground">Redirecting...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container max-w-[98vw] py-8">
      <div className="mb-6 flex items-start justify-between">
        <div className="space-y-1">
          <Button
            onClick={() => router.push(`/conv/${fileId}`)}
            variant="ghost"
            size="sm"
            className="mb-2 -ml-2 h-8 gap-1 text-muted-foreground"
          >
            <ChevronLeft className="h-4 w-4" />
            Back to File
          </Button>
          <PageHeader 
            title="Add to Database" 
            description="Enter bibliographic information for this work to add it to the corpus."
          />
        </div>
        <Button
          onClick={() => setCitationDialogOpen(true)}
          variant="outline"
          size="sm"
          className="gap-2"
        >
          <Sparkles className="h-4 w-4 text-primary" />
          Parse Citation
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-200px)]">
        <div className="overflow-y-auto pr-2">
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-lg">Work Metadata</CardTitle>
              <CardDescription>
                File ID: <code className="text-xs bg-muted px-1 py-0.5 rounded">{fileId}</code>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <FormField 
                    label="Title" 
                    required 
                    error={errors.title?.message}
                    className="md:col-span-2"
                  >
                    <Input {...register("title", { required: "Title is required", maxLength: { value: 500, message: "Title too long" } })} placeholder="Enter work title" />
                  </FormField>

                  <FormField label="Authors" description="Separated by commas">
                    <Input {...register("authors")} placeholder="e.g., John Smith, Jane Doe" />
                  </FormField>

                  <FormField label="Year" error={errors.year?.message}>
                    <Input 
                      {...register("year", {
                        pattern: { value: /^\d{4}$/, message: "Must be 4 digits" }
                      })} 
                      placeholder="e.g., 2020" 
                    />
                  </FormField>

                  <FormField label="Publisher">
                    <Input {...register("publisher")} placeholder="Psychology Press" />
                  </FormField>

                  <FormField label="ISBN">
                    <Input {...register("isbn")} placeholder="978-0-12-345678-9" />
                  </FormField>

                  <FormField label="Edition">
                    <Input {...register("edition")} placeholder="3rd Edition" />
                  </FormField>

                  <FormField label="Volume">
                    <Input {...register("volume")} placeholder="e.g., 83" />
                  </FormField>

                  <FormField label="Issue">
                    <Input {...register("issue")} placeholder="e.g., 2" />
                  </FormField>

                  <FormField label="Pages">
                    <Input {...register("pages")} placeholder="248-252" />
                  </FormField>

                  <FormField label="URL / DOI" className="md:col-span-2">
                    <Input {...register("url")} placeholder="https://doi.org/10.1016/..." />
                  </FormField>

                  <FormField label="City">
                    <Input {...register("city")} placeholder="New York" />
                  </FormField>

                  <FormField label="Institution">
                    <Input {...register("institution")} placeholder="University of London" />
                  </FormField>
                  
                  <FormField label="Editor(s)" className="md:col-span-2">
                    <Input {...register("editor")} placeholder="Karl Friston, Christopher Frith" />
                  </FormField>
                </div>

                <div className="flex gap-4 pt-4 sticky bottom-0 bg-card py-4 border-t mt-8">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => router.push(`/conv/${fileId}`)}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={submitting}
                    className="flex-1"
                  >
                    {submitting ? "Adding..." : "Add to Database"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>

        <div className="h-full">
          <Card className="h-full flex flex-col overflow-hidden">
            <CardHeader className="py-4 border-b">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <FileText className="h-4 w-4 text-muted-foreground" />
                Original Content Preview
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-0 overflow-hidden">
              {loadingContent ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <MarkdownEditor
                  content={markdownContent}
                  readOnly={true}
                  viewMode="markdown-only"
                  className="h-full"
                  scrollMode="container"
                />
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <Dialog open={citationDialogOpen} onOpenChange={setCitationDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Parse Citation</DialogTitle>
            <DialogDescription>
              Paste a citation and select a style or use AI to automatically fill the metadata.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
             <FormField label="Citation Style">
              <Select value={citationStyle} onValueChange={(v) => setCitationStyle(v as CitationStyle)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MLA">MLA</SelectItem>
                  <SelectItem value="APA">APA</SelectItem>
                  <SelectItem value="Chicago">Chicago</SelectItem>
                </SelectContent>
              </Select>
            </FormField>

            <FormField label="Citation Text">
              <Textarea
                placeholder="Paste citation here..."
                value={citationText}
                onChange={(e) => setCitationText(e.target.value)}
                className="min-h-32 font-mono text-sm"
              />
            </FormField>
          </div>

          <DialogFooter className="flex justify-between sm:justify-between items-center w-full">
            <Button
              variant="secondary"
              onClick={handleLlmParse}
              disabled={llmParsing || !citationText.trim()}
              className="gap-2"
            >
              {llmParsing ? (
                <>
                  <Loader2Icon className="h-4 w-4 animate-spin" />
                  Using AI...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  AI Parse
                </>
              )}
            </Button>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setCitationDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleCitationApply} disabled={!citationText.trim()}>Apply (Regex)</Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
