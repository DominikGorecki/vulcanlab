"use client";

import { AlertCircle, Loader2Icon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface ConfirmDeleteModalProps {
  work: {
    title: string;
    authors: string | null;
  } | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isDeleting: boolean;
}

export function ConfirmDeleteModal({
  work,
  isOpen,
  onClose,
  onConfirm,
  isDeleting,
}: ConfirmDeleteModalProps) {
  if (!work) return null;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && !isDeleting && onClose()}>
      <DialogContent data-testid="confirm-delete-modal">
        <DialogHeader>
          <DialogTitle>Delete Work</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete this work? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <div className="flex items-start gap-3 p-4 rounded-md bg-destructive/10 border border-destructive/20">
            <AlertCircle className="h-5 w-5 text-destructive mt-0.5 flex-shrink-0" />
            <div className="space-y-1 min-w-0 flex-1">
              <p className="text-sm font-medium">
                <span className="text-muted-foreground">Title:</span>{" "}
                <span className="break-words">{work.title}</span>
              </p>
              {work.authors && (
                <p className="text-sm font-medium">
                  <span className="text-muted-foreground">Authors:</span>{" "}
                  <span className="break-words">{work.authors}</span>
                </p>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isDeleting}
            data-testid="cancel-button"
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={onConfirm}
            disabled={isDeleting}
            data-testid="delete-button"
          >
            {isDeleting ? (
              <>
                <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                Deleting...
              </>
            ) : (
              "Delete"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
