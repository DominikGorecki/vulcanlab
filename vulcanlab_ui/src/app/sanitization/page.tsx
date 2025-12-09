"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, Loader2Icon, FileText, Plus } from "lucide-react";
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
  has_original_markdown: boolean;
}

interface WorkListResponse {
  works: WorkListItem[];
  total: number;
  needs_sanitization: number;
}

export default function SanitizationPage() {
  const router = useRouter();
  const [works, setWorks] = useState<WorkListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({ total: 0, needs_sanitization: 0 });

  useEffect(() => {
    fetchWorks();
  }, []);

  const fetchWorks = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/sanitization/works`);

      if (!response.ok) {
        throw new Error(`Failed to load works: ${response.statusText}`);
      }

      const data: WorkListResponse = await response.json();
      setWorks(data.works);
      setStats({
        total: data.total,
        needs_sanitization: data.needs_sanitization,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load works");
    } finally {
      setLoading(false);
    }
  };

  const handleWorkClick = (workId: number) => {
    router.push(`/sanitization/${workId}`);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Sanitization</h2>
          <p className="text-muted-foreground">Clean and structure markdown content.</p>
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
          <h2 className="text-3xl font-bold tracking-tight">Sanitization</h2>
          <p className="text-muted-foreground">Clean and structure markdown content.</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
            <Button onClick={fetchWorks} className="mt-4">
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
          <h2 className="text-3xl font-bold tracking-tight">Sanitization</h2>
          <p className="text-muted-foreground">Clean and structure markdown content.</p>
        </div>
        <Button onClick={() => router.push("/sanitization/add")} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Sanitized Markdown
        </Button>
      </div>

      {/* Stats Card */}
      <Card>
        <CardHeader>
          <CardTitle>Overview</CardTitle>
          <CardDescription>Works sanitization status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Total Works</p>
              <p className="text-2xl font-bold">{stats.total}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Need Sanitization</p>
              <p className="text-2xl font-bold text-amber-500">{stats.needs_sanitization}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Completed</p>
              <p className="text-2xl font-bold text-green-500">
                {stats.total - stats.needs_sanitization}
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
            Click on a work to view its sanitization workflow
          </CardDescription>
        </CardHeader>
        <CardContent>
          {works.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No works found in the database.</p>
              <p className="text-sm text-muted-foreground mt-2">
                Convert some documents first to see them here.
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
                    <TableHead className="w-[100px]">Year</TableHead>
                    <TableHead className="w-[120px]">Type</TableHead>
                    <TableHead className="w-[140px]">Status</TableHead>
                    <TableHead className="w-[100px]">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {works.map((work) => (
                    <TableRow key={work.id} className="cursor-pointer hover:bg-muted/50">
                      <TableCell className="font-medium">{work.id}</TableCell>
                      <TableCell className="max-w-md truncate">
                        <button
                          onClick={() => handleWorkClick(work.id)}
                          className="text-left hover:underline w-full"
                        >
                          {work.title}
                        </button>
                      </TableCell>
                      <TableCell className="max-w-xs truncate text-muted-foreground">
                        {work.authors || "-"}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {work.year || "-"}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {work.work_type || "-"}
                      </TableCell>
                      <TableCell>
                        {!work.has_original_markdown ? (
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <AlertCircle className="h-4 w-4" />
                            <span className="text-xs">No markdown</span>
                          </div>
                        ) : work.has_sanitized ? (
                          <div className="flex items-center gap-2 text-green-600">
                            <CheckCircle2 className="h-4 w-4" />
                            <span className="text-xs">Sanitized</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 text-amber-600">
                            <AlertCircle className="h-4 w-4" />
                            <span className="text-xs">Needs work</span>
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant={work.has_sanitized ? "outline" : "default"}
                          onClick={() => handleWorkClick(work.id)}
                          disabled={!work.has_original_markdown}
                        >
                          {work.has_sanitized ? "View" : "Sanitize"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
