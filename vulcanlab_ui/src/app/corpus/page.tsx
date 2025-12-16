"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, Loader2Icon, Database, Trash2 } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ConfirmDeleteModal } from "@/components/ConfirmDeleteModal";
import { ErrorModal } from "@/components/ErrorModal";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChunkVectorStats {
  no_vec: number;
  to_vec: number;
  vec: number;
  vec_err: number;
}

interface CorpusStats {
  total_works: number;
  chunk_stats: ChunkVectorStats;
}

interface CorpusWork {
  id: number;
  title: string;
  authors: string | null;
}

interface CorpusWorksResponse {
  works: CorpusWork[];
  total: number;
}

export default function CorpusPage() {
  const router = useRouter();
  const [stats, setStats] = useState<CorpusStats | null>(null);
  const [works, setWorks] = useState<CorpusWork[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [workToDelete, setWorkToDelete] = useState<CorpusWork | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<{ title: string; message: string; detail?: string } | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch stats and works in parallel
      const [statsResponse, worksResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/corpus/stats`),
        fetch(`${API_BASE_URL}/corpus/works`),
      ]);

      if (!statsResponse.ok) {
        throw new Error(`Failed to load statistics: ${statsResponse.statusText}`);
      }

      if (!worksResponse.ok) {
        throw new Error(`Failed to load works: ${worksResponse.statusText}`);
      }

      const statsData: CorpusStats = await statsResponse.json();
      const worksData: CorpusWorksResponse = await worksResponse.json();

      setStats(statsData);
      setWorks(worksData.works);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load corpus data");
    } finally {
      setLoading(false);
    }
  };

  const handleWorkClick = (workId: number) => {
    router.push(`/corpus/${workId}`);
  };

  const handleDeleteClick = (work: CorpusWork, event: React.MouseEvent) => {
    event.stopPropagation();
    setWorkToDelete(work);
  };

  const handleDeleteCancel = () => {
    setWorkToDelete(null);
  };

  const handleDeleteConfirm = async () => {
    if (!workToDelete) return;

    try {
      setIsDeleting(true);
      const response = await fetch(
        `${API_BASE_URL}/api/v1/corpus/works/${workToDelete.id}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        // Parse error response
        let errorDetail: string | undefined;
        let errorMessage: string;
        let errorTitle: string;

        if (response.status === 404) {
          errorTitle = "Work Not Found";
          errorMessage = "This work may have already been deleted.";
        } else if (response.status === 500) {
          errorTitle = "Deletion Failed";
          errorMessage = "An internal server error occurred while deleting the work.";

          // Try to parse error detail from response
          try {
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
              const errorData = await response.json();
              if (errorData.detail) {
                // Remove file paths from error details
                errorDetail = String(errorData.detail).replace(/\/[^\s]+\.py/g, "[file]");
              }
            }
          } catch {
            // Ignore JSON parsing errors
          }
        } else {
          errorTitle = "Deletion Failed";
          errorMessage = `Failed to delete work: ${response.statusText}`;
        }

        // Close confirmation modal and show error modal
        setWorkToDelete(null);
        setDeleteError({ title: errorTitle, message: errorMessage, detail: errorDetail });
        return;
      }

      // Success: close modal and refresh data
      setWorkToDelete(null);
      await fetchData();
    } catch (err) {
      // Handle network errors
      console.error("Error deleting work:", err);
      setWorkToDelete(null);
      setDeleteError({
        title: "Connection Error",
        message: "Failed to connect to server. Please check your network connection and try again.",
        detail: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleErrorClose = () => {
    setDeleteError(null);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Corpus</h2>
          <p className="text-muted-foreground">Works ready for vectorization and RAG.</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Corpus</h2>
          <p className="text-muted-foreground">Works ready for vectorization and RAG.</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
            <Button onClick={fetchData} className="mt-4">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Corpus</h2>
          <p className="text-muted-foreground">
            Works ready for vectorization and RAG.
          </p>
        </div>
      </div>

      {/* Overview Statistics Card */}
      <Card>
        <CardHeader>
          <CardTitle>Embeddings Overview</CardTitle>
          <CardDescription>Corpus statistics and embedding vectorization status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Total Works</p>
              <p className="text-2xl font-bold">{stats?.total_works || 0}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Not Queued</p>
              <p className="text-2xl font-bold text-muted-foreground">
                {stats?.chunk_stats.no_vec || 0}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">To Vectorize</p>
              <p className="text-2xl font-bold text-amber-500">
                {stats?.chunk_stats.to_vec || 0}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Vectorized</p>
              <p className="text-2xl font-bold text-green-500">
                {stats?.chunk_stats.vec || 0}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Errors</p>
              <p className="text-2xl font-bold text-red-500">
                {stats?.chunk_stats.vec_err || 0}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Works Table */}
      <Card>
        <CardHeader>
          <CardTitle>Works</CardTitle>
          <CardDescription>
            Click on a work to view its sanitized content
          </CardDescription>
        </CardHeader>
        <CardContent>
          {works.length === 0 ? (
            <div className="text-center py-12">
              <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No corpus works found.</p>
              <p className="text-sm text-muted-foreground mt-2">
                Works must complete chunking before appearing here.
              </p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[60px]">ID</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Authors</TableHead>
                    <TableHead className="w-[80px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {works.map((work) => (
                    <TableRow
                      key={work.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleWorkClick(work.id)}
                    >
                      <TableCell className="font-medium">{work.id}</TableCell>
                      <TableCell className="max-w-md truncate">
                        {work.title}
                      </TableCell>
                      <TableCell className="max-w-xs truncate text-muted-foreground">
                        {work.authors || "-"}
                      </TableCell>
                      <TableCell>
                        <button
                          onClick={(e) => handleDeleteClick(work, e)}
                          className="p-2 rounded hover:bg-muted transition-colors"
                          aria-label="Delete work"
                          data-testid="delete-icon"
                        >
                          <Trash2
                            size={16}
                            className="text-muted-foreground hover:text-destructive"
                          />
                        </button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <ConfirmDeleteModal
        work={workToDelete}
        isOpen={!!workToDelete}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        isDeleting={isDeleting}
      />

      <ErrorModal
        isOpen={!!deleteError}
        onClose={handleErrorClose}
        title={deleteError?.title || "Error"}
        message={deleteError?.message || "An error occurred"}
        error={deleteError?.detail}
      />
    </div>
  );
}
