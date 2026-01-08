"use client";

import { useState, useCallback, useEffect } from "react";
import { useForm } from "react-hook-form";
import { 
  Search, 
  Plus, 
  Loader2, 
  Check, 
  ChevronLeft, 
  ChevronRight,
  FolderPlus,
  List
} from "lucide-react";
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { FormField } from "@/components/form-field";
import { usePageData } from "@/hooks/use-page-data";
import { useDebounce } from "@/hooks/use-debounce";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Collection {
  id: number;
  name: string;
  description: string | null;
  tags: string[];
  item_count: number;
}

interface CollectionListResponse {
  collections: Collection[];
  total: number;
  page: number;
  page_size: number;
}

interface AddToCollectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  itemType: string;
  itemLink: string;
  onSuccess?: () => void;
}

interface CreateCollectionFormValues {
  name: string;
  description: string;
  tags: string;
}

export function AddToCollectionModal({
  isOpen,
  onClose,
  itemType,
  itemLink,
  onSuccess,
}: AddToCollectionModalProps) {
  const { toast } = useToast();
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [isAdding, setIsAdding] = useState(false);

  // --- List Collections logic ---
  const fetchCollections = useCallback(async () => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: "10",
    });
    if (debouncedSearch) params.append("search", debouncedSearch);

    const response = await fetch(`${API_BASE_URL}/api/v1/collections/?${params.toString()}`);
    if (!response.ok) throw new Error("Failed to load collections");
    return response.json() as Promise<CollectionListResponse>;
  }, [page, debouncedSearch]);

  const { data, loading, error, refetch } = usePageData<CollectionListResponse>(fetchCollections, {
    autoFetch: isOpen,
  });

  useEffect(() => {
    if (isOpen) {
      setPage(1);
      setSelectedId(null);
      setShowCreateForm(false);
      setSearch("");
    }
  }, [isOpen]);

  // Reset to page 1 on search change
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  // --- Create Collection logic ---
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting: isCreating },
  } = useForm<CreateCollectionFormValues>();

  const onCreateSubmit = async (values: CreateCollectionFormValues) => {
    try {
      const tagList = values.tags
        ? values.tags.split(",").map((t) => t.trim()).filter((t) => t !== "")
        : [];

      const response = await fetch(`${API_BASE_URL}/api/v1/collections/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: values.name,
          description: values.description,
          tags: tagList,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create collection");
      }

      const newCollection = await response.json();
      toast({ title: "Success", description: "Collection created." });
      
      // Auto-select and switch back to list
      await refetch();
      setSelectedId(newCollection.id);
      setShowCreateForm(false);
      reset();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to create collection",
        variant: "destructive",
      });
    }
  };

  // --- Add Item logic ---
  const handleAdd = async () => {
    if (!selectedId) return;

    setIsAdding(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/collections/${selectedId}/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          item_type: itemType,
          link: itemLink,
          note: "", // Users add notes on detail page
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to add item to collection");
      }

      toast({
        title: "Added to Collection",
        description: "The item has been successfully added.",
      });
      onSuccess?.();
      onClose();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to add item",
        variant: "destructive",
      });
    } finally {
      setIsAdding(false);
    }
  };

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 0;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[550px] flex flex-col max-h-[85vh]">
        <DialogHeader>
          <DialogTitle>Add to Collection</DialogTitle>
          <DialogDescription>
            Select a research collection to store this item.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col py-4 gap-4">
          <div className="flex items-center justify-between gap-4">
            {!showCreateForm ? (
              <>
                <div className="relative flex-1">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search collections..."
                    className="pl-9 h-9"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="gap-2"
                  onClick={() => setShowCreateForm(true)}
                >
                  <Plus className="h-4 w-4" />
                  New
                </Button>
              </>
            ) : (
              <Button 
                variant="ghost" 
                size="sm" 
                className="gap-2 -ml-2"
                onClick={() => setShowCreateForm(false)}
              >
                <ChevronLeft className="h-4 w-4" />
                Back to List
              </Button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto min-h-[300px]">
            {showCreateForm ? (
              <form id="create-collection-form" onSubmit={handleSubmit(onCreateSubmit)} className="space-y-4 px-1">
                <FormField label="Name" error={errors.name?.message} required>
                  <Input
                    {...register("name", { required: "Name is required" })}
                    placeholder="e.g., Working Memory Research"
                    disabled={isCreating}
                  />
                </FormField>
                <FormField label="Description" error={errors.description?.message}>
                  <Textarea
                    {...register("description")}
                    placeholder="Optional description..."
                    className="resize-none h-24"
                    disabled={isCreating}
                  />
                </FormField>
                <FormField label="Tags" error={errors.tags?.message} description="Comma-separated">
                  <Input
                    {...register("tags")}
                    placeholder="tag1, tag2..."
                    disabled={isCreating}
                  />
                </FormField>
              </form>
            ) : (
              <div className="space-y-2 px-1">
                {loading && (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                )}

                {error && (
                  <div className="text-center py-12 text-destructive">
                    <p>Error loading collections.</p>
                    <Button variant="link" onClick={() => refetch()}>Try again</Button>
                  </div>
                )}

                {!loading && !error && data?.collections.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    <FolderPlus className="h-12 w-12 mx-auto mb-4 opacity-20" />
                    <p>No collections found.</p>
                    {search && <p className="text-xs">Try a different search term.</p>}
                  </div>
                )}

                {!loading && data?.collections.map((collection) => (
                  <div
                    key={collection.id}
                    onClick={() => setSelectedId(collection.id)}
                    className={cn(
                      "flex items-start justify-between p-3 rounded-lg border-2 cursor-pointer transition-all hover:bg-accent group",
                      selectedId === collection.id 
                        ? "border-primary bg-primary/5" 
                        : "border-transparent bg-muted/30"
                    )}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-sm truncate">{collection.name}</span>
                        <Badge variant="outline" className="text-[10px] h-4 font-mono px-1">
                          {collection.item_count} items
                        </Badge>
                      </div>
                      {collection.description && (
                        <p className="text-xs text-muted-foreground line-clamp-1 mb-2">
                          {collection.description}
                        </p>
                      )}
                      <div className="flex flex-wrap gap-1">
                        {collection.tags.map(tag => (
                          <Badge key={tag} variant="secondary" className="text-[9px] px-1 py-0 h-3.5">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div className={cn(
                      "h-5 w-5 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5 transition-colors",
                      selectedId === collection.id ? "bg-primary border-primary" : "border-muted-foreground/30"
                    )}>
                      {selectedId === collection.id && <Check className="h-3 w-3 text-primary-foreground" />}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {!showCreateForm && totalPages > 1 && (
            <div className="flex items-center justify-between border-t pt-4">
              <span className="text-xs text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <div className="flex gap-1">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7"
                  disabled={page === 1 || loading}
                  onClick={() => setPage(p => p - 1)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7"
                  disabled={page === totalPages || loading}
                  onClick={() => setPage(p => p + 1)}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="border-t pt-4">
          <Button variant="outline" onClick={onClose} disabled={isAdding || isCreating}>
            Cancel
          </Button>
          {showCreateForm ? (
            <Button type="submit" form="create-collection-form" disabled={isCreating}>
              {isCreating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <FolderPlus className="h-4 w-4 mr-2" />}
              Create & Select
            </Button>
          ) : (
            <Button 
              onClick={handleAdd} 
              disabled={!selectedId || isAdding || loading}
              className="min-w-[100px]"
            >
              {isAdding ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Add to Collection
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

