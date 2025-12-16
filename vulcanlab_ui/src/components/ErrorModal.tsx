"use client";

import { AlertCircle } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface ErrorModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  message: string;
  error?: string;
}

export function ErrorModal({
  isOpen,
  onClose,
  title,
  message,
  error,
}: ErrorModalProps) {
  return (
    <AlertDialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <AlertDialogContent data-testid="error-modal">
        <AlertDialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex-shrink-0">
              <AlertCircle className="h-6 w-6 text-destructive" data-testid="error-icon" />
            </div>
            <AlertDialogTitle className="text-destructive">{title}</AlertDialogTitle>
          </div>
          <AlertDialogDescription className="text-foreground font-medium">
            {message}
          </AlertDialogDescription>
        </AlertDialogHeader>

        {error && (
          <div className="p-4 rounded-md bg-destructive/10 border border-destructive/20">
            <p className="text-sm text-muted-foreground font-mono break-words" data-testid="error-details">
              {error}
            </p>
          </div>
        )}

        <AlertDialogFooter>
          <AlertDialogAction onClick={onClose} data-testid="close-button">
            Close
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
