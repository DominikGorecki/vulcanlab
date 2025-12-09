"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  AlertCircle,
  ChevronLeft,
  Loader2Icon,
} from "lucide-react";
import { MarkdownEditor } from "@/components/markdown-editor";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface WorkContentResponse {
  content: string;
  filename: string;
  work_id: number;
  work_title: string;
}

export default function CorpusWorkViewerPage() {
  const params = useParams();
  const router = useRouter();
  const workId = params.id as string;

  const [content, setContent] = useState<string>("");
  const [filename, setFilename] = useState<string>("");
  const [workTitle, setWorkTitle] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchContent();
  }, [workId]);

  const fetchContent = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/corpus/work/${workId}/content`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Work not found or sanitized content not available.");
        }
        throw new Error(`Failed to load content: ${response.statusText}`);
      }

      const data: WorkContentResponse = await response.json();
      setContent(data.content);
      setFilename(data.filename);
      setWorkTitle(data.work_title);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load content");
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    router.push("/corpus");
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
            <Button onClick={fetchContent}>Retry</Button>
            <Button variant="outline" onClick={handleBack}>
              Back to Corpus
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
            onClick={handleBack}
            variant="ghost"
            size="sm"
            className="gap-1"
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>

          <div className="border-l h-8" />

          <div>
            <h1 className="text-xl font-bold">Corpus Work</h1>
            <p className="text-sm text-muted-foreground max-w-2xl truncate">
              {workTitle}
            </p>
          </div>
        </div>

        <div className="text-sm text-muted-foreground">
          {filename}
        </div>
      </div>

      {/* Content - natural scroll */}
      <div className="p-6">
        <MarkdownEditor
          content={content}
          onChange={() => {}} // No-op: read-only
          viewMode="both"
          readOnly={true}
          scrollMode="page"
        />
      </div>
    </div>
  );
}
