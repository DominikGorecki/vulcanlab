"use client";

import { useCallback, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  FolderOpen,
  Calendar,
  Clock,
  Tag as TagIcon,
  Trash2,
  ExternalLink,
  MessageSquare,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import {
  PageHeader,
  PageLoadingState,
  PageErrorState,
  DataTable,
  StatusBadge,
  ConfirmDialog,
  type DataTableColumn,
} from "@/components";
import { usePageData } from "@/hooks/use-page-data";
import { NewCollectionModal } from "@/components/collections/NewCollectionModal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Collection {
  id: number;
  name: string;
  description: string | null;
  tags: string[];
  item_count: number;
  created_at: string;
  updated_at: string;
}

interface CollectionListResponse {
  collections: Collection[];
  total: int;
  page: int;
  page_size: int;
}

export default function CollectionsPage() {
  const router = useRouter();
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const fetchCollections = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/collections/`);
    if (!response.ok) {
      throw new Error(`Failed to load collections: ${response.statusText}`);
    }
    return response.json();
  }, []);

  const { data, loading, error: fetchError, refetch } = usePageData<CollectionListResponse>(fetchCollections);

  const handleDelete = useCallback(async () => {
    if (deleteId === null) return;

    setIsDeleting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/collections/${deleteId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete collection");
      }

      setSuccess("Collection deleted successfully");
      await refetch();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete collection");
    } finally {
      setIsDeleting(false);
      setDeleteId(null);
    }
  }, [deleteId, refetch]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const columns = useMemo((): DataTableColumn<Collection>[] => [
    {
      key: "name",
      header: "Name",
      sortable: true,
      cell: (collection) => (
        <div className="flex flex-col">
          <span className="font-medium">{collection.name}</span>
          {collection.description && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                    {collection.description}
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs">{collection.description}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      ),
    },
    {
      key: "tags",
      header: "Tags",
      cell: (collection) => (
        <div className="flex flex-wrap gap-1">
          {collection.tags.map((tag) => (
            <Badge key={tag} variant="secondary" className="text-[10px] px-1.5 py-0 h-4">
              {tag}
            </Badge>
          ))}
          {collection.tags.length === 0 && <span className="text-xs text-muted-foreground">-</span>}
        </div>
      ),
    },
    {
      key: "item_count",
      header: "Items",
      className: "text-center",
      cell: (collection) => (
        <Badge variant="outline" className="font-mono">
          {collection.item_count}
        </Badge>
      ),
    },
    {
      key: "created_at",
      header: "Created",
      sortable: true,
      cell: (collection) => (
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground whitespace-nowrap">
          <Calendar className="h-3 w-3" />
          {formatDate(collection.created_at)}
        </div>
      ),
    },
    {
      key: "updated_at",
      header: "Modified",
      sortable: true,
      cell: (collection) => (
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground whitespace-nowrap">
          <Clock className="h-3 w-3" />
          {formatDate(collection.updated_at)}
        </div>
      ),
    },
    {
      key: "id",
      header: "Actions",
      className: "text-right",
      cell: (collection) => (
        <div className="flex justify-end gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push(`/collections/${collection.id}`)}
            title="View Details"
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setDeleteId(collection.id)}
            className="text-destructive hover:text-destructive hover:bg-destructive/10"
            title="Delete Collection"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ], [router]);

  if (loading) return <PageLoadingState />;
  if (fetchError) return <PageErrorState error={fetchError} onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Collections"
        description="Organize your research findings, excerpts, and RAG results into themed collections."
        actions={
          <NewCollectionModal onSuccess={() => {
            setSuccess("Collection created successfully");
            refetch();
          }} />
        }
      />

      {success && (
        <Alert className="bg-green-500/10 text-green-600 dark:text-green-500 border-green-500/20">
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

      <DataTable
        data={data?.collections || []}
        columns={columns}
        onRowClick={(collection) => router.push(`/collections/${collection.id}`)}
        emptyState={{
          title: "No collections yet",
          description: "Create your first collection to start organizing your research.",
          icon: FolderOpen,
          action: (
            <NewCollectionModal onSuccess={() => {
              setSuccess("Collection created successfully");
              refetch();
            }} />
          ),
        }}
      />

      <ConfirmDialog
        open={deleteId !== null}
        onOpenChange={(open) => !open && setDeleteId(null)}
        title="Delete Collection"
        description="Are you sure you want to delete this collection? This will not delete the actual source items, but will remove all links and notes within this collection. This action cannot be undone."
        confirmText="Delete"
        variant="destructive"
        onConfirm={handleDelete}
        isLoading={isDeleting}
      />
    </div>
  );
}

