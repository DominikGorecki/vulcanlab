"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, ChevronLeft, Loader2Icon, FileText } from "lucide-react";
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

interface FormErrors {
  title?: string;
  year?: string;
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
  const fileId = params.id as string;

  const [formData, setFormData] = useState<FormData>({
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
  });

  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [markdownContent, setMarkdownContent] = useState<string>("");
  const [loadingContent, setLoadingContent] = useState(true);

  // Citation dialog state
  const [citationDialogOpen, setCitationDialogOpen] = useState(false);
  const [citationStyle, setCitationStyle] = useState<CitationStyle>("MLA");
  const [citationText, setCitationText] = useState<string>("");
  const [citationError, setCitationError] = useState<string | null>(null);
  const [llmParsing, setLlmParsing] = useState(false);
  const [llmError, setLlmError] = useState<string | null>(null);

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

  const validateForm = (): boolean => {
    const errors: FormErrors = {};

    // Title is required
    if (!formData.title.trim()) {
      errors.title = "Title is required";
    } else if (formData.title.length > 500) {
      errors.title = "Title must be 500 characters or less";
    }

    // Year must be 4 digits if provided
    if (formData.year.trim()) {
      const yearNum = parseInt(formData.year);
      if (isNaN(yearNum) || yearNum < 1000 || yearNum > 9999) {
        errors.year = "Year must be a 4-digit number (1000-9999)";
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    try {
      // Prepare request body
      const requestBody: any = {
        title: formData.title.trim(),
      };

      // Add optional fields only if they have values
      if (formData.authors.trim()) {
        requestBody.authors = formData.authors.trim();
      }
      if (formData.year.trim()) {
        requestBody.year = parseInt(formData.year);
      }
      if (formData.publisher.trim()) {
        requestBody.publisher = formData.publisher.trim();
      }
      if (formData.isbn.trim()) {
        requestBody.isbn = formData.isbn.trim();
      }
      if (formData.edition.trim()) {
        requestBody.edition = formData.edition.trim();
      }
      if (formData.volume.trim()) {
        requestBody.volume = formData.volume.trim();
      }
      if (formData.issue.trim()) {
        requestBody.issue = formData.issue.trim();
      }
      if (formData.pages.trim()) {
        requestBody.pages = formData.pages.trim();
      }
      if (formData.url.trim()) {
        requestBody.url = formData.url.trim();
      }
      if (formData.city.trim()) {
        requestBody.city = formData.city.trim();
      }
      if (formData.institution.trim()) {
        requestBody.institution = formData.institution.trim();
      }
      if (formData.editor.trim()) {
        requestBody.editor = formData.editor.trim();
      }

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
        throw new Error(errorData.detail || `Failed to add work: ${response.statusText}`);
      }

      const data: AddWorkResponse = await response.json();
      
      // Show success message
      setSuccess(true);
      
      // Navigate to sanitization page for the new work after a short delay
      setTimeout(() => {
        router.push(`/sanitization/${data.work_id}`);
      }, 2000);
      
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to add work to database");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    router.push(`/conv/${fileId}`);
  };

  const handleFieldChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing
    if (formErrors[field as keyof FormErrors]) {
      setFormErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field as keyof FormErrors];
        return newErrors;
      });
    }
  };

  // Citation parsing functions
  const parseMLACitation = (citation: string): ParsedCitation => {
    const result: ParsedCitation = {
      title: "",
      authors: "",
      year: "",
      publisher: "",
      edition: "",
      volume: "",
      issue: "",
      pages: "",
      url: "",
      city: "",
      institution: "",
      editor: "",
    };

    // MLA: Author(s). "Title." Journal/Publisher Volume.Issue (Year): Pages.
    // Example: Friston, Karl. "Prediction, perception and agency." International Journal of Psychophysiology 83.2 (2012): 248-252.
    // Multiple authors: Smith, John, and Jane Doe. "Title." Journal 1.2 (2020): 1-10.

    const trimmed = citation.trim();
    
    // Extract year: look for (YYYY) pattern
    const yearMatch = trimmed.match(/\((\d{4})\)/);
    if (yearMatch) {
      result.year = yearMatch[1];
    }

    // Handle both straight and curly quotes
    // Split by first period followed by space to separate author from title
    // Match: Author(s). "Title." Rest
    // Try to find the pattern: Author. "Title." Rest
    const authorMatch = trimmed.match(/^(.+?)\.\s*(.+)$/);
    if (authorMatch) {
      const authors = authorMatch[1].trim();
      const afterAuthors = authorMatch[2].trim();
      
      // Try to find quoted title
      const quoteMatch = afterAuthors.match(/^(["'""])(.+?)\1\.\s*(.+)$/);
      if (quoteMatch) {
        result.authors = authors;
        // Title is in group 2, extract it cleanly
        result.title = quoteMatch[2].trim();
        
        // Rest is in group 3
        let rest = quoteMatch[3].trim();
        // Remove any leading quotes or spaces
        rest = rest.replace(/^["'""\s]+/, "").trim();
        
        // Extract volume.issue pattern before year (e.g., "83.2 (2012)")
        const volumeIssueMatch = rest.match(/(.+?)\s+(\d+\.\d+)\s*\(/);
        if (volumeIssueMatch) {
          result.publisher = volumeIssueMatch[1].trim();
          result.edition = volumeIssueMatch[2].trim();
        } else {
          // Try without issue number (e.g., "83 (2012)")
          const volumeMatch = rest.match(/(.+?)\s+(\d+)\s*\(/);
          if (volumeMatch) {
            result.publisher = volumeMatch[1].trim();
            result.edition = volumeMatch[2].trim();
          } else {
            // Just publisher, no volume
            result.publisher = rest.replace(/\s*\(.*$/, "").trim();
          }
        }
      } else {
        // No quoted title found, try fallback
        const noQuoteMatch = trimmed.match(/^(.+?)\.\s*(.+?)\.\s*(.+)$/);
        if (noQuoteMatch) {
          result.authors = noQuoteMatch[1].trim();
          const titleRest = noQuoteMatch[2];
          const titleMatch = titleRest.match(/^(.+?)(?:\s+\d|,\s*(?:Inc|Press|Publishers|Books|University|College))/i);
          if (titleMatch) {
            result.title = titleMatch[1].trim();
          } else {
            result.title = titleRest.trim();
          }
          const rest = noQuoteMatch[3];
          const volumeIssueMatch = rest.match(/(.+?)\s+(\d+\.\d+)\s*\(/);
          if (volumeIssueMatch) {
            result.publisher = volumeIssueMatch[1].trim();
            result.edition = volumeIssueMatch[2].trim();
          } else {
            const volumeMatch = rest.match(/(.+?)\s+(\d+)\s*\(/);
            if (volumeMatch) {
              result.publisher = volumeMatch[1].trim();
              result.edition = volumeMatch[2].trim();
            } else {
              result.publisher = rest.replace(/\s*\(.*$/, "").trim();
            }
          }
        }
      }
    } else {
      // Fallback: try without quotes (for book titles in italics or plain text)
      // Pattern: Author(s). Title. Publisher/Journal Volume (Year)
      const noQuoteMatch = trimmed.match(/^(.+?)\.\s*(.+?)\.\s*(.+)$/);
      if (noQuoteMatch) {
        result.authors = noQuoteMatch[1].trim();
        
        // Try to find title (usually ends before volume number or publisher)
        const titleRest = noQuoteMatch[2];
        // Title might end before a number (volume) or before common publisher words
        const titleMatch = titleRest.match(/^(.+?)(?:\s+\d|,\s*(?:Inc|Press|Publishers|Books|University|College))/i);
        if (titleMatch) {
          result.title = titleMatch[1].trim();
        } else {
          result.title = titleRest.trim();
        }
        
        const rest = noQuoteMatch[3];
        // Extract volume.issue pattern before year
        const volumeIssueMatch = rest.match(/(.+?)\s+(\d+\.\d+)\s*\(/);
        if (volumeIssueMatch) {
          result.publisher = volumeIssueMatch[1].trim();
          result.edition = volumeIssueMatch[2].trim();
        } else {
          const volumeMatch = rest.match(/(.+?)\s+(\d+)\s*\(/);
          if (volumeMatch) {
            result.publisher = volumeMatch[1].trim();
            result.edition = volumeMatch[2].trim();
          } else {
            result.publisher = rest.replace(/\s*\(.*$/, "").trim();
          }
        }
      }
    }

    return result;
  };

  const parseAPACitation = (citation: string): ParsedCitation => {
    const result: ParsedCitation = {
      title: "",
      authors: "",
      year: "",
      publisher: "",
      edition: "",
      volume: "",
      issue: "",
      pages: "",
      url: "",
      city: "",
      institution: "",
      editor: "",
    };

    // APA: Author(s). (Year). Title. Journal/Publisher, Volume(Issue), Pages.
    // Example: Friston, K. (2012). Prediction, perception and agency. International Journal of Psychophysiology, 83(2), 248-252.
    // Multiple authors: Smith, J., & Doe, J. (2020). Title. Journal, 1(2), 1-10.

    const trimmed = citation.trim();
    
    // Extract year: look for (YYYY) pattern
    const yearMatch = trimmed.match(/\((\d{4})\)/);
    if (yearMatch) {
      result.year = yearMatch[1];
    }

    // Split by first period followed by space and (Year)
    // Pattern: Author(s). (Year). Title. Publisher, Volume(Issue), Pages
    const authorMatch = trimmed.match(/^(.+?)\.\s*\(/);
    if (authorMatch) {
      result.authors = authorMatch[1].trim();
      
      // Extract title: between ). and the comma before publisher
      // Pattern: ). Title. Publisher,
      const titleMatch = trimmed.match(/\)\.\s*(.+?)\.\s*(.+?),/);
      if (titleMatch) {
        result.title = titleMatch[1].trim();
        
        // Extract publisher and volume(issue)
        // Pattern: Publisher, Volume(Issue) or Publisher, Volume
        const pubVolMatch = trimmed.match(/\)\.\s*.+?\.\s*(.+?),\s*(\d+)\((\d+)\)/);
        if (pubVolMatch) {
          result.publisher = pubVolMatch[1].trim();
          result.edition = `${pubVolMatch[2]}.${pubVolMatch[3]}`;
        } else {
          // Try without issue: Publisher, Volume
          const pubVolMatch2 = trimmed.match(/\)\.\s*.+?\.\s*(.+?),\s*(\d+)/);
          if (pubVolMatch2) {
            result.publisher = pubVolMatch2[1].trim();
            result.edition = pubVolMatch2[2].trim();
          } else {
            // Just get publisher (for books)
            const pubMatch = trimmed.match(/\)\.\s*.+?\.\s*(.+?),/);
            if (pubMatch) {
              result.publisher = pubMatch[1].trim();
            }
          }
        }
      } else {
        // Fallback: try to extract title without the comma pattern
        const titleMatch2 = trimmed.match(/\)\.\s*(.+?)\.\s*(.+)$/);
        if (titleMatch2) {
          result.title = titleMatch2[1].trim();
          result.publisher = titleMatch2[2].replace(/,\s*\d+.*$/, "").trim();
        }
      }
    }

    return result;
  };

  const parseChicagoCitation = (citation: string): ParsedCitation => {
    const result: ParsedCitation = {
      title: "",
      authors: "",
      year: "",
      publisher: "",
      edition: "",
      volume: "",
      issue: "",
      pages: "",
      url: "",
      city: "",
      institution: "",
      editor: "",
    };

    // Chicago: Author(s). "Title." Journal/Publisher Volume, no. Issue (Year): Pages.
    // Example: Friston, Karl. "Prediction, perception and agency." International Journal of Psychophysiology 83, no. 2 (2012): 248-252.
    // Multiple authors: Smith, John, and Jane Doe. "Title." Journal 1, no. 2 (2020): 1-10.

    const trimmed = citation.trim();
    
    // Extract year: look for (YYYY) pattern
    const yearMatch = trimmed.match(/\((\d{4})\)/);
    if (yearMatch) {
      result.year = yearMatch[1];
    }

    // Handle both straight and curly quotes
    // Split by first period followed by space to separate author from title
    // Match: Author(s). "Title." Rest
    // Try to find the pattern: Author. "Title." Rest
    const authorMatch = trimmed.match(/^(.+?)\.\s*(.+)$/);
    if (authorMatch) {
      const authors = authorMatch[1].trim();
      const afterAuthors = authorMatch[2].trim();
      
      // Try to find quoted title
      const quoteMatch = afterAuthors.match(/^(["'""])(.+?)\1\.\s*(.+)$/);
      if (quoteMatch) {
        result.authors = authors;
        // Title is in group 2, extract it cleanly
        result.title = quoteMatch[2].trim();
        
        // Rest is in group 3
        let rest = quoteMatch[3].trim();
        // Remove any leading quotes or spaces
        rest = rest.replace(/^["'""\s]+/, "").trim();
        
        // Extract volume, no. issue pattern before year
        // Pattern: Publisher Volume, no. Issue (Year)
        const volumeIssueMatch = rest.match(/(.+?)\s+(\d+),\s*no\.\s*(\d+)\s*\(/i);
        if (volumeIssueMatch) {
          result.publisher = volumeIssueMatch[1].trim();
          result.edition = `${volumeIssueMatch[2]}.${volumeIssueMatch[3]}`;
        } else {
          // Try without "no." (some Chicago citations omit it)
          const volumeMatch = rest.match(/(.+?)\s+(\d+)\s*\(/);
          if (volumeMatch) {
            result.publisher = volumeMatch[1].trim();
            result.edition = volumeMatch[2].trim();
          } else {
            // Just publisher (for books)
            result.publisher = rest.replace(/\s*\(.*$/, "").trim();
          }
        }
      } else {
        // No quoted title found, try fallback
        const noQuoteMatch = trimmed.match(/^(.+?)\.\s*(.+?)\.\s*(.+)$/);
        if (noQuoteMatch) {
          result.authors = noQuoteMatch[1].trim();
          const titleRest = noQuoteMatch[2];
          const titleMatch = titleRest.match(/^(.+?)(?:\s+\d|,\s*(?:Inc|Press|Publishers|Books|University|College))/i);
          if (titleMatch) {
            result.title = titleMatch[1].trim();
          } else {
            result.title = titleRest.trim();
          }
          const rest = noQuoteMatch[3];
          const volumeIssueMatch = rest.match(/(.+?)\s+(\d+),\s*no\.\s*(\d+)\s*\(/i);
          if (volumeIssueMatch) {
            result.publisher = volumeIssueMatch[1].trim();
            result.edition = `${volumeIssueMatch[2]}.${volumeIssueMatch[3]}`;
          } else {
            const volumeMatch = rest.match(/(.+?)\s+(\d+)\s*\(/);
            if (volumeMatch) {
              result.publisher = volumeMatch[1].trim();
              result.edition = volumeMatch[2].trim();
            } else {
              result.publisher = rest.replace(/\s*\(.*$/, "").trim();
            }
          }
        }
      }
    } else {
      // Fallback: try without quotes (for book titles in italics or plain text)
      const noQuoteMatch = trimmed.match(/^(.+?)\.\s*(.+?)\.\s*(.+)$/);
      if (noQuoteMatch) {
        result.authors = noQuoteMatch[1].trim();
        const titleRest = noQuoteMatch[2];
        // Title might end before a number (volume) or before common publisher words
        const titleMatch = titleRest.match(/^(.+?)(?:\s+\d|,\s*(?:Inc|Press|Publishers|Books|University|College))/i);
        if (titleMatch) {
          result.title = titleMatch[1].trim();
        } else {
          result.title = titleRest.trim();
        }
        
        const rest = noQuoteMatch[3];
        const volumeIssueMatch = rest.match(/(.+?)\s+(\d+),\s*no\.\s*(\d+)\s*\(/i);
        if (volumeIssueMatch) {
          result.publisher = volumeIssueMatch[1].trim();
          result.edition = `${volumeIssueMatch[2]}.${volumeIssueMatch[3]}`;
        } else {
          const volumeMatch = rest.match(/(.+?)\s+(\d+)\s*\(/);
          if (volumeMatch) {
            result.publisher = volumeMatch[1].trim();
            result.edition = volumeMatch[2].trim();
          } else {
            result.publisher = rest.replace(/\s*\(.*$/, "").trim();
          }
        }
      }
    }

    return result;
  };

  const parseCitation = (citation: string, style: CitationStyle): ParsedCitation => {
    switch (style) {
      case "MLA":
        return parseMLACitation(citation);
      case "APA":
        return parseAPACitation(citation);
      case "Chicago":
        return parseChicagoCitation(citation);
      default:
        return { title: "", authors: "", year: "", publisher: "", edition: "", volume: "", issue: "", pages: "", url: "", city: "", institution: "", editor: "" };
    }
  };

  const handleCitationApply = () => {
    if (!citationText.trim()) {
      setCitationError("Please paste a citation");
      return;
    }

    setCitationError(null);

    try {
      const parsed = parseCitation(citationText.trim(), citationStyle);

      // Fill form fields
      if (parsed.title) {
        handleFieldChange("title", parsed.title);
      }
      if (parsed.authors) {
        handleFieldChange("authors", parsed.authors);
      }
      if (parsed.year) {
        handleFieldChange("year", parsed.year);
      }
      if (parsed.publisher) {
        handleFieldChange("publisher", parsed.publisher);
      }
      if (parsed.edition) {
        handleFieldChange("edition", parsed.edition);
      }
      if (parsed.volume) {
        handleFieldChange("volume", parsed.volume);
      }
      if (parsed.issue) {
        handleFieldChange("issue", parsed.issue);
      }
      if (parsed.pages) {
        handleFieldChange("pages", parsed.pages);
      }
      if (parsed.url) {
        handleFieldChange("url", parsed.url);
      }
      if (parsed.city) {
        handleFieldChange("city", parsed.city);
      }
      if (parsed.institution) {
        handleFieldChange("institution", parsed.institution);
      }
      if (parsed.editor) {
        handleFieldChange("editor", parsed.editor);
      }

      // Close dialog and reset
      setCitationDialogOpen(false);
      setCitationText("");
      setCitationError(null);
    } catch (error) {
      setCitationError("Failed to parse citation. Please check the format.");
    }
  };

  const handleLlmParse = async () => {
    if (!citationText.trim()) {
      setCitationError("Please paste a citation");
      return;
    }

    setLlmParsing(true);
    setLlmError(null);
    setCitationError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/conv/parse-citation-llm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          citation_text: citationText.trim(),
          citation_format: citationStyle,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to parse citation with LLM");
      }

      const parsed = await response.json();

      // Fill form fields (similar to handleCitationApply)
      if (parsed.title) {
        handleFieldChange("title", parsed.title);
      }
      // Join authors array to string
      if (parsed.authors && Array.isArray(parsed.authors)) {
        handleFieldChange("authors", parsed.authors.join(", "));
      }
      if (parsed.year) {
        handleFieldChange("year", parsed.year.toString());
      }
      if (parsed.publisher) {
        handleFieldChange("publisher", parsed.publisher);
      }
      if (parsed.isbn) {
        handleFieldChange("isbn", parsed.isbn);
      }
      // Map volume and issue to their own fields now
      if (parsed.volume) {
        handleFieldChange("volume", parsed.volume.toString());
      }
      if (parsed.issue) {
        handleFieldChange("issue", parsed.issue.toString());
      }
      if (parsed.pages) {
        handleFieldChange("pages", parsed.pages);
      }
      if (parsed.url) {
        handleFieldChange("url", parsed.url);
      }
      if (parsed.city) {
        handleFieldChange("city", parsed.city);
      }
      if (parsed.institution) {
        handleFieldChange("institution", parsed.institution);
      }
      if (parsed.editor && Array.isArray(parsed.editor)) {
        handleFieldChange("editor", parsed.editor.join(", "));
      } else if (parsed.editor) {
        handleFieldChange("editor", parsed.editor);
      }

      // Close dialog and reset
      setCitationDialogOpen(false);
      setCitationText("");
      setLlmError(null);
    } catch (error) {
      setLlmError(error instanceof Error ? error.message : "Failed to parse citation");
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
    <div className="container max-w-[95vw] py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <Button
            onClick={handleCancel}
            variant="ghost"
            size="sm"
            className="gap-1"
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>
          <Button
            onClick={() => setCitationDialogOpen(true)}
            variant="outline"
            size="sm"
            className="gap-2"
          >
            <FileText className="h-4 w-4" />
            Citation
          </Button>
        </div>
        
        <h1 className="text-3xl font-bold tracking-tight">Add to Database</h1>
        <p className="text-muted-foreground mt-2">
          Enter bibliographic information for this work
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-250px)]">
        {/* Form Card */}
        <div className="overflow-y-auto">
          <Card>
            <CardHeader>
              <CardTitle>Work Metadata</CardTitle>
              <CardDescription>
                File ID: <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{fileId}</code>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Title - Required */}
                <div className="space-y-2">
                  <Label htmlFor="title" className="required">
                    Title <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="title"
                    type="text"
                    value={formData.title}
                    onChange={(e) => handleFieldChange("title", e.target.value)}
                    placeholder="Enter work title"
                    className={formErrors.title ? "border-destructive" : ""}
                  />
                  {formErrors.title && (
                    <p className="text-sm text-destructive">{formErrors.title}</p>
                  )}
                </div>

                {/* Authors - Optional */}
                <div className="space-y-2">
                  <Label htmlFor="authors">Authors</Label>
                  <Input
                    id="authors"
                    type="text"
                    value={formData.authors}
                    onChange={(e) => handleFieldChange("authors", e.target.value)}
                    placeholder="e.g., John Smith, Jane Doe"
                  />
                  <p className="text-xs text-muted-foreground">
                    Optional: Enter author names separated by commas
                  </p>
                </div>

                {/* Year - Optional */}
                <div className="space-y-2">
                  <Label htmlFor="year">Year</Label>
                  <Input
                    id="year"
                    type="number"
                    value={formData.year}
                    onChange={(e) => handleFieldChange("year", e.target.value)}
                    placeholder="e.g., 2020"
                    min="1000"
                    max="9999"
                    className={formErrors.year ? "border-destructive" : ""}
                  />
                  {formErrors.year && (
                    <p className="text-sm text-destructive">{formErrors.year}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Optional: 4-digit year of publication
                  </p>
                </div>

                {/* Publisher - Optional */}
                <div className="space-y-2">
                  <Label htmlFor="publisher">Publisher</Label>
                  <Input
                    id="publisher"
                    type="text"
                    value={formData.publisher}
                    onChange={(e) => handleFieldChange("publisher", e.target.value)}
                    placeholder="e.g., Psychology Press"
                  />
                  <p className="text-xs text-muted-foreground">
                    Optional: Publisher name
                  </p>
                </div>

                {/* ISBN - Optional */}
                <div className="space-y-2">
                  <Label htmlFor="isbn">ISBN</Label>
                  <Input
                    id="isbn"
                    type="text"
                    value={formData.isbn}
                    onChange={(e) => handleFieldChange("isbn", e.target.value)}
                    placeholder="e.g., 978-0-12-345678-9"
                  />
                  <p className="text-xs text-muted-foreground">
                    Optional: ISBN for books
                  </p>
                </div>

                {/* Edition - Optional */}
                <div className="space-y-2">
                  <Label htmlFor="edition">Edition</Label>
                  <Input
                    id="edition"
                    type="text"
                    value={formData.edition}
                    onChange={(e) => handleFieldChange("edition", e.target.value)}
                    placeholder="e.g., 3rd Edition"
                  />
                  <p className="text-xs text-muted-foreground">
                    Optional: Edition information
                  </p>
                </div>

                {/* Volume - Optional */}
                <div className="space-y-2">
                  <Label htmlFor="volume">Volume</Label>
                  <Input
                    id="volume"
                    type="text"
                    value={formData.volume}
                    onChange={(e) => handleFieldChange("volume", e.target.value)}
                    placeholder="e.g., 83"
                  />
                  <p className="text-xs text-muted-foreground">
                    Optional: Volume number for journals/periodicals
                  </p>
                </div>

                {/* Issue - Optional */}
                <div className="space-y-2">
                  <Label htmlFor="issue">Issue</Label>
                  <Input
                    id="issue"
                    type="text"
                    value={formData.issue}
                    onChange={(e) => handleFieldChange("issue", e.target.value)}
                    placeholder="e.g., 2"
                  />
                  <p className="text-xs text-muted-foreground">
                    Optional: Issue number for journals/periodicals
                  </p>
                </div>

                {/* Pages - Optional */}
                <div className="space-y-2">
                  <Label htmlFor="pages">Pages</Label>
                  <Input
                    id="pages"
                    type="text"
                    value={formData.pages}
                    onChange={(e) => handleFieldChange("pages", e.target.value)}
                    placeholder="e.g., 248-252"
                  />
                  <p className="text-xs text-muted-foreground">
                    Optional: Page range
                  </p>
                </div>

                {/* URL - Optional */}
                <div className="space-y-2">
                  <Label htmlFor="url">URL</Label>
                  <Input
                    id="url"
                    type="text"
                    value={formData.url}
                    onChange={(e) => handleFieldChange("url", e.target.value)}
                    placeholder="e.g., https://doi.org/10.1016/..."
                  />
                  <p className="text-xs text-muted-foreground">
                    Optional: URL or DOI link
                  </p>
                </div>

                {/* City - Optional */}
                <div className="space-y-2">
                  <Label htmlFor="city">City</Label>
                  <Input
                    id="city"
                    type="text"
                    value={formData.city}
                    onChange={(e) => handleFieldChange("city", e.target.value)}
                    placeholder="e.g., New York"
                  />
                  <p className="text-xs text-muted-foreground">
                    Optional: City of publication
                  </p>
                </div>

                {/* Institution - Optional */}
                <div className="space-y-2">
                  <Label htmlFor="institution">Institution</Label>
                  <Input
                    id="institution"
                    type="text"
                    value={formData.institution}
                    onChange={(e) => handleFieldChange("institution", e.target.value)}
                    placeholder="e.g., University of London"
                  />
                  <p className="text-xs text-muted-foreground">
                    Optional: Institution for theses/dissertations
                  </p>
                </div>

                {/* Editor - Optional */}
                <div className="space-y-2">
                  <Label htmlFor="editor">Editor(s)</Label>
                  <Input
                    id="editor"
                    type="text"
                    value={formData.editor}
                    onChange={(e) => handleFieldChange("editor", e.target.value)}
                    placeholder="e.g., Karl Friston, Christopher Frith"
                  />
                  <p className="text-xs text-muted-foreground">
                    Optional: Editor(s) of the work
                  </p>
                </div>


                {/* Error Display */}
                {submitError && (
                  <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                    <div className="flex items-start gap-2 text-destructive">
                      <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                      <p className="text-sm">{submitError}</p>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCancel}
                    disabled={submitting}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={submitting}
                    className="flex-1"
                  >
                    {submitting ? (
                      <>
                        <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                        Adding...
                      </>
                    ) : (
                      "Add to Database"
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Markdown Preview Card */}
        <div className="h-full flex flex-col">
          <Card className="h-full flex flex-col overflow-hidden">
            <CardHeader className="py-4">
              <CardTitle className="text-lg">Content Preview</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-0 overflow-hidden">
              {loadingContent ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <div className="h-full">
                  <MarkdownEditor
                    content={markdownContent}
                    readOnly={true}
                    viewMode="markdown-only"
                    className="h-full"
                    scrollMode="container"
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Citation Dialog */}
      <Dialog open={citationDialogOpen} onOpenChange={setCitationDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Parse Citation</DialogTitle>
            <DialogDescription>
              Paste a citation below and select the citation style to automatically fill the form fields.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="citation-style">Citation Style</Label>
              <Select value={citationStyle} onValueChange={(value) => setCitationStyle(value as CitationStyle)}>
                <SelectTrigger id="citation-style">
                  <SelectValue placeholder="Select citation style" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MLA">MLA</SelectItem>
                  <SelectItem value="APA">APA</SelectItem>
                  <SelectItem value="Chicago">Chicago</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="citation-text">Citation Text</Label>
              <Textarea
                id="citation-text"
                placeholder={`Paste ${citationStyle} citation here...\n\nExample:\n${
                  citationStyle === "MLA"
                    ? 'Friston, Karl. "Prediction, perception and agency." International Journal of Psychophysiology 83.2 (2012): 248-252.'
                    : citationStyle === "APA"
                    ? "Friston, K. (2012). Prediction, perception and agency. International Journal of Psychophysiology, 83(2), 248-252."
                    : 'Friston, Karl. "Prediction, perception and agency." International Journal of Psychophysiology 83, no. 2 (2012): 248-252.'
                }`}
                value={citationText}
                onChange={(e) => {
                  setCitationText(e.target.value);
                  setCitationError(null);
                }}
                className="min-h-32 font-mono text-sm"
              />
            </div>

            {citationError && (
              <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                <div className="flex items-start gap-2 text-destructive">
                  <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                  <p className="text-sm">{citationError}</p>
                </div>
              </div>
            )}

            {llmError && (
              <div className="p-3 rounded-lg bg-yellow-50 border border-yellow-200 dark:bg-yellow-900/20">
                <div className="flex items-start gap-2 text-yellow-800 dark:text-yellow-200">
                  <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">LLM Parsing Error</p>
                    <p className="text-sm">{llmError}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <DialogFooter className="flex justify-between items-center">
            <div className="flex gap-2">
              <Button
                variant="secondary"
                onClick={handleLlmParse}
                disabled={llmParsing}
              >
                {llmParsing ? (
                  <>
                    <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                    Parsing with AI...
                  </>
                ) : (
                  "LLM Parse"
                )}
              </Button>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setCitationDialogOpen(false);
                  setCitationText("");
                  setCitationError(null);
                  setLlmError(null);
                }}
              >
                Cancel
              </Button>
              <Button onClick={handleCitationApply}>
                Apply (Regex)
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}



