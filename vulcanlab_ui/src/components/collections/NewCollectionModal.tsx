"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { Plus, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { FormField } from "@/components/form-field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CollectionFormValues {
  name: string;
  description: string;
  tags: string;
}

interface NewCollectionModalProps {
  onSuccess?: () => void;
}

export function NewCollectionModal({ onSuccess }: NewCollectionModalProps) {
  const [open, setOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CollectionFormValues>({
    defaultValues: {
      name: "",
      description: "",
      tags: "",
    },
  });

  const onSubmit = async (values: CollectionFormValues) => {
    setIsSubmitting(true);
    setError(null);

    try {
      // Process tags from comma-separated string to list
      const tagList = values.tags
        ? values.tags.split(",").map((t) => t.trim()).filter((t) => t !== "")
        : [];

      const response = await fetch(`${API_BASE_URL}/api/v1/collections/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: values.name,
          description: values.description,
          tags: tagList,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to create collection");
      }

      setOpen(false);
      reset();
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(val) => {
      setOpen(val);
      if (!val) {
        reset();
        setError(null);
      }
    }}>
      <DialogTrigger asChild>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          New Collection
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create New Collection</DialogTitle>
          <DialogDescription>
            Group related research items, excerpts, and RAG results.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-4">
          <FormField
            label="Name"
            error={errors.name?.message}
            required
          >
            <Input
              {...register("name", { 
                required: "Name is required",
                maxLength: { value: 255, message: "Name must be less than 255 characters" }
              })}
              placeholder="e.g., Working Memory Research"
              disabled={isSubmitting}
            />
          </FormField>

          <FormField
            label="Description"
            error={errors.description?.message}
          >
            <Textarea
              {...register("description")}
              placeholder="Optional description of this collection..."
              className="resize-none"
              disabled={isSubmitting}
            />
          </FormField>

          <FormField
            label="Tags"
            error={errors.tags?.message}
            description="Comma-separated list of tags"
          >
            <Input
              {...register("tags")}
              placeholder="e.g., psychology, thesis, draft"
              disabled={isSubmitting}
            />
          </FormField>

          {error && (
            <div className="text-sm font-medium text-destructive">
              {error}
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Collection"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

