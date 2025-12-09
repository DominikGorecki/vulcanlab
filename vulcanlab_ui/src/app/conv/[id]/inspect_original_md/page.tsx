"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  AlertCircle,
  ChevronLeft,
  Loader2Icon,
  Save,
} from "lucide-react";
import { MarkdownEditor } from "@/components/markdown-editor";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FileContentResponse {
  content: string;
  filename: string;
}

export default function InspectOriginalMarkdownPage() {
  const params = useParams();
  const router = useRouter();
  const fileId = params.id as string; // This is the IOFile ID of the markdown file

  const [content, setContent] = useState<string>("");
  const [filename, setFilename] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, [fileId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/conv/original-markdown/${fileId}`);
      if (!response.ok) {
        throw new Error("Failed to load file content");
      }
      const data: FileContentResponse = await response.json();
      setContent(data.content);
      setFilename(data.filename);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/conv/original-markdown/${fileId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ content }),
      });

      if (!response.ok) {
        throw new Error("Failed to save file content");
      }
      
      const data: FileContentResponse = await response.json();
      setContent(data.content);
      // Optional: Show success toast/message

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save data");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
          <p className="text-destructive">{error}</p>
          <div className="flex gap-3 justify-center">
            <Button onClick={fetchData}>Retry</Button>
            <Button variant="outline" onClick={() => router.back()}>
              Back
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Sticky Header */}
      <div className="sticky top-0 z-10 border-b bg-card p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <Button
            onClick={() => router.back()}
            variant="ghost"
            size="sm"
            className="gap-1"
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>
          <div className="border-l h-8" />
          <div>
            <h1 className="text-xl font-bold">Inspect Original Markdown</h1>
            <p className="text-sm text-muted-foreground max-w-2xl truncate">
              {filename}
            </p>
          </div>
        </div>

        {/* Save Button */}
        <Button
          onClick={handleSave}
          className="gap-1"
          disabled={saving}
        >
          {saving ? (
            <Loader2Icon className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          {saving ? "Saving..." : "Save"}
        </Button>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Read-only MarkdownEditor  */}
          <MarkdownEditor 
          content={content} 
          onChange={setContent}
          viewMode="both"
          scrollMode="page"
        />
      </div>
    </div>
  );
}
