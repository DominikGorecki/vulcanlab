"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, Loader2Icon, FileText, Clock, XCircle } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface WorkListItem {
  id: number;
  title: string;
  authors: string | null;
  year: number | null;
  work_type: string | null;
  has_sanitized: boolean;
  heading_chunks_status: string | null;
  content_chunks_status: string | null;
}

interface WorkListResponse {
  works: WorkListItem[];
  total: number;
}

export default function ChunkingPage() {
  const router = useRouter();
  const [works, setWorks] = useState<WorkListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({ total: 0 });

  useEffect(() => {
    fetchWorks();
  }, []);

  const fetchWorks = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/chunk/works`);

      if (!response.ok) {
        throw new Error(`Failed to load works: ${response.statusText}`);
      }

      const data: WorkListResponse = await response.json();
      setWorks(data.works);
      setStats({
        total: data.total,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load works");
    } finally {
      setLoading(false);
    }
  };

  const handleWorkClick = (workId: number) => {
    router.push(`/chunk/${workId}`);
  };

  const getStatusBadge = (status: string | null) => {
    if (status === "completed") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <CheckCircle2 className="h-3 w-3" />
          Completed
        </span>
      );
    } else if (status === "pending") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          <Clock className="h-3 w-3" />
          Pending
        </span>
      );
    } else if (status === "failed") {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
          <XCircle className="h-3 w-3" />
          Failed
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
          Not Started
        </span>
      );
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Chunking</h2>
          <p className="text-muted-foreground">Split documents into semantic chunks.</p>
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
          <h2 className="text-3xl font-bold tracking-tight">Chunking</h2>
          <p className="text-muted-foreground">Split documents into semantic chunks.</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
            <Button onClick={fetchWorks} variant="outline" className="mt-4">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Chunking</h2>
        <p className="text-muted-foreground">Split documents into semantic chunks.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Works</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">
              Works with sanitized files
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Works Ready for Chunking</CardTitle>
          <CardDescription>
            Select a work to view chunking status and apply chunking operations.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {works.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No works with sanitized files found.</p>
              <p className="text-sm mt-2">Complete sanitization first to enable chunking.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Authors</TableHead>
                  <TableHead>Year</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Heading Chunks</TableHead>
                  <TableHead>Content Chunks</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {works.map((work) => (
                  <TableRow key={work.id} className="cursor-pointer hover:bg-muted/50">
                    <TableCell className="font-medium" onClick={() => handleWorkClick(work.id)}>
                      {work.title}
                    </TableCell>
                    <TableCell onClick={() => handleWorkClick(work.id)}>
                      {work.authors || "—"}
                    </TableCell>
                    <TableCell onClick={() => handleWorkClick(work.id)}>
                      {work.year || "—"}
                    </TableCell>
                    <TableCell onClick={() => handleWorkClick(work.id)}>
                      {work.work_type || "—"}
                    </TableCell>
                    <TableCell onClick={() => handleWorkClick(work.id)}>
                      {getStatusBadge(work.heading_chunks_status)}
                    </TableCell>
                    <TableCell onClick={() => handleWorkClick(work.id)}>
                      {getStatusBadge(work.content_chunks_status)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleWorkClick(work.id)}
                      >
                        View Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

