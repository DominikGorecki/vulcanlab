"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2Icon, RefreshCw, AlertTriangle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UpdateRetrieveConsolidateButtonProps {
  queryId: number;
  onSuccess?: () => void;
  className?: string;
  size?: "default" | "sm" | "lg" | "icon";
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  disabled?: boolean;
}

export function UpdateRetrieveConsolidateButton({
  queryId,
  onSuccess,
  className,
  size = "sm",
  variant = "outline",
  disabled = false,
}: UpdateRetrieveConsolidateButtonProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpdate = async () => {
    setLoading(true);
    setError(null);

    try {
      // First call retrieve endpoint
      const retrieveResponse = await fetch(`${API_BASE_URL}/rag/queries/${queryId}/retrieve`, {
        method: "POST",
      });

      if (!retrieveResponse.ok) {
        const errorData = await retrieveResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to retrieve");
      }

      // Then call consolidate endpoint
      const consolidateResponse = await fetch(`${API_BASE_URL}/rag/queries/${queryId}/consolidate`, {
        method: "POST",
      });

      if (!consolidateResponse.ok) {
        const errorData = await consolidateResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to consolidate");
      }

      setOpen(false);
      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update retrieval and consolidation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button
        size={size}
        variant={variant}
        onClick={() => setOpen(true)}
        disabled={disabled || loading}
        className={cn("gap-1", className)}
        title="Update Retrieval & Consolidation"
      >
        {loading ? (
          <Loader2Icon className="h-3 w-3 animate-spin" />
        ) : (
          <RefreshCw className="h-3 w-3" />
        )}
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Retrieval & Consolidation</DialogTitle>
            <DialogDescription>
              This will re-run retrieval and consolidation for this query.
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription className="font-bold">
                CLEAN RETRIEVAL DATA WILL BE REGENERATED -- if you modified it, you will lose your changes.
              </AlertDescription>
            </Alert>
            
            {error && (
               <Alert variant="destructive" className="mt-4">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button onClick={handleUpdate} disabled={loading}>
              {loading ? (
                <>
                  <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                  Updating...
                </>
              ) : (
                "Confirm & Update"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

