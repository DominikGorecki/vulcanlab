"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";
import { Search, ChevronLeft, ChevronRight, Trash2, Loader2, AlertCircle, Eye } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChunkSearchResult {
  id: number;
  content_preview: string;
  heading_breadcrumbs: string | null;
  level: string;
  work_id: number;
  start_line: number;
  end_line: number;
}

interface PaginationInfo {
  page: number;
  page_size: number;
  total_results: number;
  has_next: boolean;
  has_prev: boolean;
}

interface ChunkSearchResponse {
  results: ChunkSearchResult[];
  pagination: PaginationInfo;
}

interface DescendantInfo {
  id: number;
  level: string;
  heading_breadcrumbs: string | null;
}

interface DescendantsResponse {
  descendants: DescendantInfo[];
  total_count: number;
}

interface ChunkDetailResponse {
  id: number;
  content: string;
  heading_breadcrumbs: string | null;
  level: string;
  work_id: number;
  start_line: number;
  end_line: number;
}

export default function CleanupPage() {
  const { toast } = useToast();

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [headingsOnly, setHeadingsOnly] = useState(false);
  const [results, setResults] = useState<ChunkSearchResult[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  // Delete state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedChunkId, setSelectedChunkId] = useState<number | null>(null);
  const [selectedChunk, setSelectedChunk] = useState<ChunkSearchResult | null>(null);
  const [descendants, setDescendants] = useState<DescendantInfo[]>([]);
  const [descendantsLoading, setDescendantsLoading] = useState(false);
  const [descendantsError, setDescendantsError] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // View modal state
  const [viewModalOpen, setViewModalOpen] = useState(false);
  const [viewChunkDetail, setViewChunkDetail] = useState<ChunkDetailResponse | null>(null);
  const [viewLoading, setViewLoading] = useState(false);
  const [viewError, setViewError] = useState<string | null>(null);

  const handleSearch = async (page: number = 1) => {
    const query = searchQuery.trim();
    if (!query) {
      setError("Please enter a search term");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/v1/chunks/search?q=${encodeURIComponent(query)}&page=${page}&headings_only=${headingsOnly}`
      );

      if (!response.ok) {
        if (response.status === 422 || response.status === 400) {
          throw new Error("Invalid search query. Please enter a valid search term.");
        }
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data: ChunkSearchResponse = await response.json();
      setResults(data.results);
      setPagination(data.pagination);
      setHasSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to search chunks");
      setResults([]);
      setPagination(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(1);
  };

  const handlePreviousPage = () => {
    if (pagination?.has_prev) {
      handleSearch(pagination.page - 1);
    }
  };

  const handleNextPage = () => {
    if (pagination?.has_next) {
      handleSearch(pagination.page + 1);
    }
  };

  const handleDeleteClick = async (chunk: ChunkSearchResult) => {
    setSelectedChunkId(chunk.id);
    setSelectedChunk(chunk);
    setDeleteModalOpen(true);
    setDescendantsError(null);
    setDeleteError(null);
    setDescendants([]);

    // Fetch descendants
    try {
      setDescendantsLoading(true);
      const response = await fetch(
        `${API_BASE_URL}/api/v1/chunks/${chunk.id}/descendants`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Chunk not found. It may have been deleted already.");
        }
        throw new Error(`Failed to load descendants: ${response.statusText}`);
      }

      const data: DescendantsResponse = await response.json();
      setDescendants(data.descendants);
    } catch (err) {
      setDescendantsError(err instanceof Error ? err.message : "Failed to load descendants");
    } finally {
      setDescendantsLoading(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!selectedChunkId) return;

    try {
      setDeleteLoading(true);
      setDeleteError(null);

      const response = await fetch(
        `${API_BASE_URL}/api/v1/chunks/${selectedChunkId}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Chunk not found. It may have been deleted already.");
        }
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Failed to delete chunk: ${response.statusText}`);
      }

      // Success: remove chunk from results and update pagination
      setResults(prevResults => prevResults.filter(r => r.id !== selectedChunkId));
      if (pagination) {
        setPagination({
          ...pagination,
          total_results: pagination.total_results - (descendants.length + 1),
        });
      }

      // Close modal and reset state
      setDeleteModalOpen(false);
      setSelectedChunkId(null);
      setSelectedChunk(null);
      setDescendants([]);

      // Show success toast
      toast({
        title: "Chunk deleted",
        description: selectedChunk?.heading_breadcrumbs
          ? `Deleted: ${selectedChunk.heading_breadcrumbs}`
          : `Chunk ${selectedChunkId} and ${descendants.length} descendant(s) deleted successfully`,
      });
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete chunk");
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleCancelDelete = () => {
    setDeleteModalOpen(false);
    setSelectedChunkId(null);
    setSelectedChunk(null);
    setDescendants([]);
    setDescendantsError(null);
    setDeleteError(null);
  };

  const handleViewClick = async (chunkId: number) => {
    setViewModalOpen(true);
    setViewError(null);
    setViewChunkDetail(null);

    try {
      setViewLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/chunks/${chunkId}`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Chunk not found. It may have been deleted.");
        }
        throw new Error(`Failed to load chunk: ${response.statusText}`);
      }

      const data: ChunkDetailResponse = await response.json();
      setViewChunkDetail(data);
    } catch (err) {
      setViewError(err instanceof Error ? err.message : "Failed to load chunk");
    } finally {
      setViewLoading(false);
    }
  };

  const handleCloseView = () => {
    setViewModalOpen(false);
    setViewChunkDetail(null);
    setViewError(null);
  };

  const getLevelBadgeVariant = (level: string): "default" | "secondary" | "outline" => {
    if (level.startsWith("H")) return "default";
    if (level === "sentence") return "secondary";
    return "outline";
  };

  // Calculate total chunks to be deleted
  const totalToDelete = selectedChunkId ? descendants.length + 1 : 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Trash2 className="h-8 w-8 text-primary" />
          <h2 className="text-3xl font-bold tracking-tight">Chunk Cleanup</h2>
        </div>
        <p className="text-muted-foreground">
          Search and remove unwanted chunks from the database
        </p>
      </div>

      {/* Search Form */}
      <Card>
        <CardHeader>
          <CardTitle>Search Chunks</CardTitle>
          <CardDescription>
            Search for chunks by title or content. Results are ranked by relevance.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="Search chunks by title or content..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1"
                disabled={loading}
              />
              <Button type="submit" disabled={loading || !searchQuery.trim()}>
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-4 w-4" />
                    Search
                  </>
                )}
              </Button>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="headings-only"
                checked={headingsOnly}
                onCheckedChange={(checked) => setHeadingsOnly(checked === true)}
                disabled={loading}
              />
              <Label
                htmlFor="headings-only"
                className="text-sm font-normal cursor-pointer"
              >
                Search headings only (H1-H5)
              </Label>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Empty State - Initial */}
      {!loading && !hasSearched && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Search className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                Enter a search term to find chunks
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Search by heading title or content to get started
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State - No Results */}
      {!loading && hasSearched && results.length === 0 && !error && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Search className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                No chunks found matching &quot;{searchQuery}&quot;
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Try a different search term
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Display */}
      {!loading && results.length > 0 && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Search Results</CardTitle>
              <CardDescription>
                Showing {pagination?.total_results || 0} result(s)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {results.map((chunk) => (
                <Card key={chunk.id} className="p-4 relative">
                  {/* Action Buttons */}
                  <div className="absolute top-4 right-4 flex gap-1">
                    <button
                      onClick={() => handleViewClick(chunk.id)}
                      className="p-2 rounded hover:bg-primary/10 transition-colors group"
                      aria-label="View chunk"
                    >
                      <Eye className="h-4 w-4 text-muted-foreground group-hover:text-primary" />
                    </button>
                    <button
                      onClick={() => handleDeleteClick(chunk)}
                      className="p-2 rounded hover:bg-destructive/10 transition-colors group"
                      aria-label="Delete chunk"
                    >
                      <Trash2 className="h-4 w-4 text-muted-foreground group-hover:text-destructive" />
                    </button>
                  </div>

                  {/* Heading Breadcrumbs */}
                  {chunk.heading_breadcrumbs && (
                    <p className="text-sm text-muted-foreground mb-2 pr-24">
                      {chunk.heading_breadcrumbs}
                    </p>
                  )}

                  {/* Content Preview */}
                  <p className="text-sm mb-3 pr-24">
                    {chunk.content_preview}
                    {chunk.content_preview.length === 100 && "..."}
                  </p>

                  {/* Metadata Row */}
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <Badge variant={getLevelBadgeVariant(chunk.level)}>
                      {chunk.level}
                    </Badge>
                    <span>Work ID: {chunk.work_id}</span>
                    <span>Lines {chunk.start_line}-{chunk.end_line}</span>
                    <span className="ml-auto">ID: {chunk.id}</span>
                  </div>
                </Card>
              ))}
            </CardContent>
          </Card>

          {/* Pagination Controls */}
          {pagination && (
            <div className="flex items-center justify-between">
              <Button
                variant="outline"
                onClick={handlePreviousPage}
                disabled={!pagination.has_prev || loading}
              >
                <ChevronLeft className="mr-2 h-4 w-4" />
                Previous
              </Button>

              <div className="text-sm text-muted-foreground">
                Page {pagination.page} of {Math.ceil(pagination.total_results / pagination.page_size)}
              </div>

              <Button
                variant="outline"
                onClick={handleNextPage}
                disabled={!pagination.has_next || loading}
              >
                Next
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <AlertDialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
        <AlertDialogContent className="max-w-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Chunk</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete this chunk and all its descendants. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>

          <div className="space-y-4 py-4">
            {/* Selected Chunk Info */}
            {selectedChunk && (
              <div className="rounded-lg border p-3 bg-muted/30">
                <p className="text-sm font-medium mb-1">Chunk to delete:</p>
                <p className="text-sm text-muted-foreground">
                  {selectedChunk.heading_breadcrumbs || `Chunk ID ${selectedChunk.id}`}
                </p>
              </div>
            )}

            {/* Descendants Loading */}
            {descendantsLoading && (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                <span className="ml-2 text-sm text-muted-foreground">Loading descendants...</span>
              </div>
            )}

            {/* Descendants Error */}
            {descendantsError && (
              <div className="rounded-lg border border-destructive p-3 bg-destructive/10">
                <div className="flex items-center gap-2 text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  <p className="text-sm">{descendantsError}</p>
                </div>
              </div>
            )}

            {/* Descendants List */}
            {!descendantsLoading && !descendantsError && (
              <div>
                <p className="text-sm font-medium mb-2">
                  {descendants.length === 0 ? (
                    "No descendant chunks will be deleted"
                  ) : (
                    `Descendants to be deleted (${descendants.length}):`
                  )}
                </p>
                {descendants.length > 0 && (
                  <ScrollArea className="h-[200px] rounded-md border p-3">
                    <div className="space-y-2">
                      {descendants.slice(0, 50).map((desc) => (
                        <div key={desc.id} className="flex items-center gap-2 text-sm py-1">
                          <Badge variant={getLevelBadgeVariant(desc.level)} className="text-xs">
                            {desc.level}
                          </Badge>
                          <span className="text-muted-foreground">ID: {desc.id}</span>
                          {desc.heading_breadcrumbs && (
                            <span className="text-xs text-muted-foreground truncate flex-1">
                              {desc.heading_breadcrumbs}
                            </span>
                          )}
                        </div>
                      ))}
                      {descendants.length > 50 && (
                        <p className="text-xs text-muted-foreground italic">
                          and {descendants.length - 50} more...
                        </p>
                      )}
                    </div>
                  </ScrollArea>
                )}
              </div>
            )}

            {/* Total Count */}
            {!descendantsLoading && !descendantsError && (
              <div className="rounded-lg border p-3 bg-muted/30">
                <p className="text-sm font-medium">
                  Total: {totalToDelete} chunk{totalToDelete !== 1 ? "s" : ""} will be deleted
                </p>
              </div>
            )}

            {/* Delete Error */}
            {deleteError && (
              <div className="rounded-lg border border-destructive p-3 bg-destructive/10">
                <div className="flex items-center gap-2 text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  <p className="text-sm">{deleteError}</p>
                </div>
              </div>
            )}
          </div>

          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelDelete} disabled={deleteLoading}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault();
                handleConfirmDelete();
              }}
              disabled={deleteLoading || descendantsLoading || !!descendantsError}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Confirm Delete"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* View Chunk Modal */}
      <Dialog open={viewModalOpen} onOpenChange={setViewModalOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>View Chunk</DialogTitle>
            <DialogDescription>
              Full content of the selected chunk
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Loading State */}
            {viewLoading && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <span className="ml-3 text-muted-foreground">Loading chunk...</span>
              </div>
            )}

            {/* Error State */}
            {viewError && (
              <div className="rounded-lg border border-destructive p-4 bg-destructive/10">
                <div className="flex items-center gap-3 text-destructive">
                  <AlertCircle className="h-5 w-5" />
                  <p>{viewError}</p>
                </div>
              </div>
            )}

            {/* Chunk Details */}
            {!viewLoading && !viewError && viewChunkDetail && (
              <div className="space-y-4">
                {/* Metadata */}
                <div className="flex items-center gap-3 flex-wrap pb-3 border-b">
                  <Badge variant={getLevelBadgeVariant(viewChunkDetail.level)}>
                    {viewChunkDetail.level}
                  </Badge>
                  <span className="text-sm text-muted-foreground">ID: {viewChunkDetail.id}</span>
                  <span className="text-sm text-muted-foreground">Work ID: {viewChunkDetail.work_id}</span>
                  <span className="text-sm text-muted-foreground">
                    Lines {viewChunkDetail.start_line}-{viewChunkDetail.end_line}
                  </span>
                </div>

                {/* Heading Breadcrumbs */}
                {viewChunkDetail.heading_breadcrumbs && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Heading Path:</p>
                    <p className="text-sm text-muted-foreground">
                      {viewChunkDetail.heading_breadcrumbs}
                    </p>
                  </div>
                )}

                {/* Full Content */}
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-2">Content:</p>
                  <ScrollArea className="h-[400px] rounded-md border p-4">
                    <pre className="text-sm whitespace-pre-wrap font-sans">
                      {viewChunkDetail.content}
                    </pre>
                  </ScrollArea>
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end pt-4">
            <Button onClick={handleCloseView} variant="outline">
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
