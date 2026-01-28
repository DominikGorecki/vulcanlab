"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Sparkles, ClipboardCopy } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CreateExpansionModalProps {
  /**
   * Whether the modal is open
   */
  isOpen: boolean;
  /**
   * Callback when the modal is closed
   */
  onClose: () => void;
  /**
   * The result ID to create an expansion for
   */
  resultId: number;
  /**
   * Optional callback on successful creation
   */
  onSuccess?: () => void;
}

type ExpansionMode = "automatic" | "manual";

interface ModeOption {
  value: ExpansionMode;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const modeOptions: ModeOption[] = [
  {
    value: "automatic",
    label: "Automatic",
    description: "System will process all sections automatically using AI",
    icon: Sparkles,
  },
  {
    value: "manual",
    label: "Manual",
    description: "You will copy each section prompt and paste AI responses",
    icon: ClipboardCopy,
  },
];

/**
 * CreateExpansionModal allows users to initiate an expansion for a RAG result.
 * Users can choose between Automatic and Manual modes.
 *
 * @example
 * ```tsx
 * <CreateExpansionModal
 *   isOpen={showModal}
 *   onClose={() => setShowModal(false)}
 *   resultId={123}
 * />
 * ```
 */
export function CreateExpansionModal({
  isOpen,
  onClose,
  resultId,
  onSuccess,
}: CreateExpansionModalProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [selectedMode, setSelectedMode] = useState<ExpansionMode>("automatic");
  const [isCreating, setIsCreating] = useState(false);

  const handleCreate = async () => {
    setIsCreating(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/expansions/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          result_id: resultId,
          mode: selectedMode,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create expansion");
      }

      const expansion = await response.json();
      toast({
        title: "Expansion Created",
        description: `Expansion started in ${selectedMode} mode.`,
      });
      onSuccess?.();
      onClose();
      router.push(`/expansions/${expansion.expansion_id}`);
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to create expansion",
        variant: "destructive",
      });
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[450px]">
        <DialogHeader>
          <DialogTitle>Expand Answer</DialogTitle>
          <DialogDescription>
            Create an expansion to break down this answer into detailed sections.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <Label className="text-sm font-medium mb-3 block">Expansion Mode</Label>
          <div className="space-y-2">
            {modeOptions.map((option) => {
              const Icon = option.icon;
              const isSelected = selectedMode === option.value;
              return (
                <div
                  key={option.value}
                  onClick={() => setSelectedMode(option.value)}
                  className={cn(
                    "flex items-start gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all hover:bg-accent",
                    isSelected
                      ? "border-primary bg-primary/5"
                      : "border-transparent bg-muted/30"
                  )}
                >
                  <div
                    className={cn(
                      "h-8 w-8 rounded-md flex items-center justify-center shrink-0",
                      isSelected ? "bg-primary text-primary-foreground" : "bg-muted"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{option.label}</span>
                      {option.value === "automatic" && (
                        <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                          Recommended
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {option.description}
                    </p>
                  </div>
                  <div
                    className={cn(
                      "h-4 w-4 rounded-full border-2 flex items-center justify-center shrink-0 mt-1",
                      isSelected ? "border-primary" : "border-muted-foreground/30"
                    )}
                  >
                    {isSelected && (
                      <div className="h-2 w-2 rounded-full bg-primary" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isCreating}>
            Cancel
          </Button>
          <Button onClick={handleCreate} disabled={isCreating}>
            {isCreating && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
            Create Expansion
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
