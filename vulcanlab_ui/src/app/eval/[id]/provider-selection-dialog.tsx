"use client";

import { useState } from "react";
import { Bot, AlertCircle } from "lucide-react";
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
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface ProviderSelectionDialogProps {
  experimentId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
  onError: (error: string) => void;
}

export function ProviderSelectionDialog({
  experimentId,
  open,
  onOpenChange,
  onSuccess,
  onError,
}: ProviderSelectionDialogProps) {
  const [selectedProvider, setSelectedProvider] = useState<"openai" | "gemini">("openai");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/eval/experiments/${experimentId}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            auto_mode_enabled: true,
            auto_answer_provider: selectedProvider,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to enable automatic mode");
      }

      onOpenChange(false);
      onSuccess();
    } catch (error) {
      onError(error instanceof Error ? error.message : "Failed to enable automatic mode");
    } finally {
      setLoading(false);
    }
  };

  const getJudgeProvider = () => {
    return selectedProvider === "openai" ? "Gemini" : "OpenAI";
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Enable Automatic Evaluation Mode
          </DialogTitle>
          <DialogDescription>
            Choose which provider to use for answer generation. The judge will automatically use the opposite provider
            for unbiased evaluation.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-3">
            <Label>Answer Provider</Label>
            <RadioGroup value={selectedProvider} onValueChange={(value) => setSelectedProvider(value as "openai" | "gemini")}>
              <div className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-accent cursor-pointer">
                <RadioGroupItem value="openai" id="openai" />
                <Label htmlFor="openai" className="flex-1 cursor-pointer">
                  <div className="font-medium">OpenAI</div>
                  <div className="text-xs text-muted-foreground">
                    Use OpenAI for answer generation (Judge will use Gemini)
                  </div>
                </Label>
              </div>
              <div className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-accent cursor-pointer">
                <RadioGroupItem value="gemini" id="gemini" />
                <Label htmlFor="gemini" className="flex-1 cursor-pointer">
                  <div className="font-medium">Gemini</div>
                  <div className="text-xs text-muted-foreground">
                    Use Gemini for answer generation (Judge will use OpenAI)
                  </div>
                </Label>
              </div>
            </RadioGroup>
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Judge provider will be automatically set to <strong>{getJudgeProvider()}</strong> to ensure unbiased
              evaluation.
            </AlertDescription>
          </Alert>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs">
              Both OpenAI and Gemini API keys must be configured in your environment to use automatic mode.
            </AlertDescription>
          </Alert>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? "Enabling..." : "Enable Automatic Mode"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
