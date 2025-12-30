"use client";

import { useState } from "react";
import { Bot, AlertCircle } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ProviderSelectionDialog } from "./provider-selection-dialog";
import { ConfirmDialog } from "@/components";

interface AutoModeToggleProps {
  experimentId: number;
  enabled: boolean;
  answerProvider: string | null;
  judgeProvider: string | null;
  onUpdate: () => void;
  onError: (error: string) => void;
}

export function AutoModeToggle({
  experimentId,
  enabled,
  answerProvider,
  judgeProvider,
  onUpdate,
  onError,
}: AutoModeToggleProps) {
  const [showProviderDialog, setShowProviderDialog] = useState(false);
  const [showDisableConfirm, setShowDisableConfirm] = useState(false);

  const handleToggle = (checked: boolean) => {
    if (checked) {
      // Enabling - show provider selection dialog
      setShowProviderDialog(true);
    } else {
      // Disabling - show confirmation dialog
      setShowDisableConfirm(true);
    }
  };

  const handleDisableConfirm = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/eval/experiments/${experimentId}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            auto_mode_enabled: false,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to disable automatic mode");
      }

      setShowDisableConfirm(false);
      onUpdate();
    } catch (error) {
      onError(error instanceof Error ? error.message : "Failed to disable automatic mode");
      setShowDisableConfirm(false);
    }
  };

  return (
    <>
      <div className="flex items-center justify-between p-4 border rounded-lg bg-card">
        <div className="flex items-center gap-3">
          <Bot className="h-5 w-5 text-muted-foreground" />
          <div className="flex flex-col gap-1">
            <Label htmlFor="auto-mode-toggle" className="text-sm font-medium cursor-pointer">
              Automatic Evaluation Mode
            </Label>
            {enabled && answerProvider && judgeProvider ? (
              <p className="text-xs text-muted-foreground">
                Answer: {answerProvider === "openai" ? "OpenAI" : "Gemini"} • Judge:{" "}
                {judgeProvider === "openai" ? "OpenAI" : "Gemini"}
              </p>
            ) : (
              <p className="text-xs text-muted-foreground">
                Use different providers for answer generation and judging
              </p>
            )}
          </div>
        </div>
        <Switch
          id="auto-mode-toggle"
          checked={enabled}
          onCheckedChange={handleToggle}
        />
      </div>

      {enabled && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Automatic mode is enabled. New evaluations will use {answerProvider === "openai" ? "OpenAI" : "Gemini"} for
            answers and {judgeProvider === "openai" ? "OpenAI" : "Gemini"} for judging.
          </AlertDescription>
        </Alert>
      )}

      <ProviderSelectionDialog
        experimentId={experimentId}
        open={showProviderDialog}
        onOpenChange={setShowProviderDialog}
        onSuccess={onUpdate}
        onError={onError}
      />

      <ConfirmDialog
        open={showDisableConfirm}
        onOpenChange={setShowDisableConfirm}
        onConfirm={handleDisableConfirm}
        title="Disable Automatic Mode"
        description="Are you sure you want to disable automatic evaluation mode? Existing grouped prompts will be preserved, but new evaluations will use manual workflow."
        confirmText="Disable"
        variant="default"
      />
    </>
  );
}
