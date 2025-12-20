"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Loader2Icon, ChevronLeft } from "lucide-react";
import { PageErrorState } from "@/components";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AutoRAGPage() {
  const router = useRouter();
  const [queryText, setQueryText] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<string>("Initializing...");
  const hasRun = useRef(false); // Guard against double execution in Strict Mode

  useEffect(() => {
    // Prevent double execution in React Strict Mode (development)
    if (hasRun.current) return;
    hasRun.current = true;

    // Read query text from sessionStorage
    const storedQuery = sessionStorage.getItem("vulcanlab_auto_query_text");

    if (!storedQuery) {
      setError("No query text provided. Please use the Auto button on the RAG page.");
      return;
    }

    setQueryText(storedQuery);
    // Start the automation process
    runAutomation(storedQuery);
  }, []);

  const runAutomation = async (query: string) => {
    setLoading(true);
    setError(null);

    try {
      // Show step-by-step messages (simulated progress since backend is synchronous)
      setCurrentStep("Expanding query...");

      // Call the auto endpoint
      const response = await fetch(`${API_BASE_URL}/rag/auto`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || `Request failed: ${response.statusText}`);
      }

      const data = await response.json();

      // Clear sessionStorage
      sessionStorage.removeItem("vulcanlab_auto_query_text");

      // Immediately redirect to the query detail page
      router.push(`/rag/${data.query_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process query");
      setLoading(false);
    }
  };

  const handleBackToQueries = () => {
    // Clear sessionStorage
    sessionStorage.removeItem("vulcanlab_auto_query_text");
    router.push("/rag");
  };

  const handleRetry = () => {
    if (queryText) {
      runAutomation(queryText);
    }
  };

  // Show error state if no query text
  if (error && !queryText) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-4">
          <PageErrorState 
            error={error} 
            title="Missing Query"
          />
          <Button
            onClick={handleBackToQueries}
            variant="outline"
          >
            Back to Queries
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <Card className="max-w-md w-full">
        <CardContent className="pt-6 space-y-6">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-2">Automating RAG Query</h1>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {queryText}
            </p>
          </div>

          {loading && (
            <div className="flex flex-col items-center gap-4 py-8">
              <Loader2Icon className="h-12 w-12 animate-spin text-primary" />
              <div className="text-center">
                <p className="font-medium">{currentStep}</p>
                <p className="text-sm text-muted-foreground mt-1">
                  This may take up to 60 seconds...
                </p>
              </div>
            </div>
          )}

          {error && queryText && (
            <div className="space-y-4">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
              <div className="flex gap-2">
                <Button
                  onClick={handleRetry}
                  variant="default"
                  className="flex-1"
                >
                  Retry
                </Button>
                <Button
                  onClick={handleBackToQueries}
                  variant="outline"
                  className="gap-2 flex-1"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Back
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
