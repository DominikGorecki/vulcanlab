"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { AlertCircle, CheckCircle2, Loader2Icon, Zap } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function VectorizationPage() {
  // State management
  const [count, setCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [vectorizing, setVectorizing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showWarningModal, setShowWarningModal] = useState(false);

  // Fetch eligible chunks count
  const fetchCount = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/vec/eligible`);

      if (!response.ok) {
        throw new Error("Failed to fetch eligible chunks count");
      }

      const data = await response.json();
      setCount(data.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load eligible chunks count");
    } finally {
      setLoading(false);
    }
  };

  // Fetch count on mount
  useEffect(() => {
    fetchCount();
  }, []);

  // Vectorize chunks
  const handleVectorize = async (limit: number | null) => {
    setVectorizing(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_BASE_URL}/vec/vectorize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          limit: limit,
          work_id: null, // All works
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to vectorize chunks");
      }

      const result = await response.json();

      // Show success message
      setSuccess(
        `Vectorization complete: ${result.success} successful, ${result.failed} failed out of ${result.processed} processed`
      );

      // Refresh count
      await fetchCount();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to vectorize chunks");
    } finally {
      setVectorizing(false);
    }
  };

  // Handle "Vectorize All" click
  const handleVectorizeAll = () => {
    if (count > 500) {
      setShowWarningModal(true);
    } else {
      handleVectorize(null);
    }
  };

  // Handle "Vectorize 500" click
  const handleVectorize500 = () => {
    handleVectorize(500);
  };

  // Handle modal confirm
  const handleModalConfirm = () => {
    setShowWarningModal(false);
    handleVectorize(null);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Vectorization</h2>
        <p className="text-muted-foreground">Generate embeddings for chunks.</p>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Process Chunks</CardTitle>
          <CardDescription>Convert text chunks into vector embeddings.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <div className="grid gap-1">
                  <p className="text-sm font-medium">Pending Chunks</p>
                  <p className="text-2xl font-bold">{count.toLocaleString()}</p>
                </div>
                <div className="flex gap-3">
                  <Button
                    onClick={handleVectorize500}
                    disabled={count === 0 || vectorizing}
                    variant="outline"
                    className="gap-2"
                  >
                    {vectorizing ? (
                      <>
                        <Loader2Icon className="h-4 w-4 animate-spin" />
                        Vectorizing...
                      </>
                    ) : (
                      <>
                        <Zap className="h-4 w-4" />
                        Vectorize 500
                      </>
                    )}
                  </Button>
                  <Button
                    onClick={handleVectorizeAll}
                    disabled={count === 0 || vectorizing}
                    className="gap-2"
                  >
                    {vectorizing ? (
                      <>
                        <Loader2Icon className="h-4 w-4 animate-spin" />
                        Vectorizing...
                      </>
                    ) : (
                      <>
                        <Zap className="h-4 w-4" />
                        Vectorize All
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {count === 0 && !loading && (
                <div className="text-sm text-muted-foreground">
                  No chunks available for vectorization. Create chunks from the Chunk page first.
                </div>
              )}

              {vectorizing && (
                <div className="text-sm text-muted-foreground">
                  Vectorization in progress. This may take several minutes depending on the number of chunks...
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Warning Modal */}
      <Dialog open={showWarningModal} onOpenChange={setShowWarningModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>High Volume Warning</DialogTitle>
            <DialogDescription>
              You are about to vectorize {count.toLocaleString()} chunks
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <p className="font-medium mb-2">This is a large batch that may:</p>
                <ul className="text-sm space-y-1 ml-4 list-disc">
                  <li>Take 15-30+ minutes to complete</li>
                  <li>Incur significant API costs for embeddings</li>
                  <li>Potentially hit rate limits (RPM) with your provider</li>
                  <li>Block the UI while processing</li>
                </ul>
                <p className="text-sm mt-3">
                  Consider using &quot;Vectorize 500&quot; to process in smaller batches.
                </p>
              </AlertDescription>
            </Alert>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowWarningModal(false)}
              disabled={vectorizing}
            >
              Cancel
            </Button>
            <Button onClick={handleModalConfirm} disabled={vectorizing}>
              Continue Anyway
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
