"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { FileIcon, FileTextIcon, ChevronRightIcon, Loader2Icon, AlertCircle } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ProcessedFileData {
  basename: string;
  id: string;
  variants: string[];
}

interface IOFolderData {
  input_files: string[];
  processed_files: string[];
}

export default function ConversionPage() {
  const router = useRouter();
  
  // State management
  const [inputFiles, setInputFiles] = useState<string[]>([]);
  const [processedFiles, setProcessedFiles] = useState<ProcessedFileData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [converting, setConverting] = useState(false);
  const [conversionError, setConversionError] = useState<string | null>(null);
  
  // Modal state
  const [selectedInputFile, setSelectedInputFile] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Fetch IO folder data on mount
  useEffect(() => {
    fetchIOData();
  }, []);

  const fetchIOData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/conv/io-folder-data`);
      if (!response.ok) {
        throw new Error(`Failed to fetch IO data: ${response.statusText}`);
      }
      
      const data: IOFolderData = await response.json();
      
      // Parse input files (just filenames)
      setInputFiles(data.input_files);
      
      // Parse processed files (pipe-separated format: basename|id|variant1|variant2|...)
      const parsedProcessedFiles: ProcessedFileData[] = data.processed_files.map((pipeStr) => {
        const parts = pipeStr.split("|");
        return {
          basename: parts[0] || "",
          id: parts[1] || "",
          variants: parts.slice(2).filter(v => v.length > 0),
        };
      });
      
      setProcessedFiles(parsedProcessedFiles);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load IO folder data");
    } finally {
      setLoading(false);
    }
  };

  const handleInputFileClick = (fileName: string) => {
    if (converting) return; // Prevent interaction during conversion
    setSelectedInputFile(fileName);
    setConversionError(null);
    setIsModalOpen(true);
  };

  const handleConvertedFileClick = (id: string) => {
    if (converting) return; // Prevent interaction during conversion
    router.push(`/conv/${id}`);
  };

  const handleStartConversion = async () => {
    if (!selectedInputFile || converting) return;
    
    try {
      setConverting(true);
      setConversionError(null);
      
      const response = await fetch(`${API_BASE_URL}/conv/convert-file`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: selectedInputFile }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Conversion failed: ${response.statusText}`);
      }
      
      // Conversion successful - refresh IO data
      await fetchIOData();
      
      // Close modal and reset state
      setIsModalOpen(false);
      setSelectedInputFile(null);
    } catch (err) {
      setConversionError(err instanceof Error ? err.message : "Conversion failed");
      // Keep modal open to show error
    } finally {
      setConverting(false);
    }
  };

  // Helper function to format variant names for display
  const formatVariantTag = (variant: string): string => {
    // Remove leading dot and convert to display format
    // e.g., ".style.md" -> "style", ".toc_titles.md" -> "toc_titles"
    let tag = variant.startsWith(".") ? variant.substring(1) : variant;
    // Remove file extensions
    tag = tag.replace(/\.md$/, "").replace(/\.pdf$/, "");
    return tag;
  };

  // Helper function to get color for variant tag
  const getVariantColor = (variant: string): string => {
    const tag = formatVariantTag(variant);
    if (tag === "style") return "bg-blue-500/10 text-blue-500";
    if (tag === "hier") return "bg-purple-500/10 text-purple-500";
    if (tag.includes("toc")) return "bg-amber-500/10 text-amber-500";
    if (tag === "pdf") return "bg-red-500/10 text-red-500";
    return "bg-gray-500/10 text-gray-500";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Conversion</h2>
          <p className="text-muted-foreground">Convert documents to markdown format.</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
            <Button onClick={fetchIOData} className="mt-4">
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
        <h2 className="text-3xl font-bold tracking-tight">Conversion</h2>
        <p className="text-muted-foreground">Convert documents to markdown format.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Left Panel - Input Files */}
        <Card>
          <CardHeader>
            <CardTitle>Input Files</CardTitle>
            <CardDescription>Select a file to convert to markdown.</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px] pr-4">
              {inputFiles.length === 0 ? (
                <div className="text-sm text-muted-foreground py-8 text-center">
                  No files in input folder.
                </div>
              ) : (
                <div className="space-y-1">
                  {inputFiles.map((filename) => {
                    // Extract name and extension
                    const lastDot = filename.lastIndexOf(".");
                    const name = lastDot !== -1 ? filename.substring(0, lastDot) : filename;
                    const extension = lastDot !== -1 ? filename.substring(lastDot + 1) : "";
                    
                    return (
                      <button
                        key={filename}
                        onClick={() => handleInputFileClick(filename)}
                        disabled={converting}
                        className="w-full flex items-center gap-3 p-3 rounded-md hover:bg-accent transition-colors text-left group disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <div className="flex-shrink-0 p-2 rounded bg-red-500/10 text-red-500">
                          <FileIcon className="h-4 w-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{name}</p>
                          <p className="text-xs text-muted-foreground uppercase">.{extension}</p>
                        </div>
                        <ChevronRightIcon className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </button>
                    );
                  })}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Right Panel - Converted Files (Not in DB) */}
        <Card>
          <CardHeader>
            <CardTitle>Pending Completion</CardTitle>
            <CardDescription>Converted files awaiting database addition.</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px] pr-4">
              {processedFiles.length === 0 ? (
                <div className="text-sm text-muted-foreground py-8 text-center">
                  No converted files pending review.
                </div>
              ) : (
                <div className="space-y-1">
                  {processedFiles.map((file) => (
                    <button
                      key={file.id || file.basename}
                      onClick={() => handleConvertedFileClick(file.id)}
                      disabled={converting}
                      className="w-full flex items-center gap-3 p-3 rounded-md hover:bg-accent transition-colors text-left group disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <div className="flex-shrink-0 p-2 rounded bg-emerald-500/10 text-emerald-500">
                        <FileTextIcon className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{file.basename}</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {file.variants.map((variant) => (
                            <span
                              key={variant}
                              className={`text-[10px] px-1.5 py-0.5 rounded ${getVariantColor(variant)}`}
                            >
                              {formatVariantTag(variant)}
                            </span>
                          ))}
                        </div>
                      </div>
                      <ChevronRightIcon className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Confirmation Modal for Input Files */}
      <Dialog open={isModalOpen} onOpenChange={(open) => !converting && setIsModalOpen(open)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Start Conversion</DialogTitle>
            <DialogDescription>
              Convert <span className="font-medium text-foreground">{selectedInputFile}</span> to markdown format?
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-3">
            <p className="text-sm text-muted-foreground">
              This will process the PDF and generate markdown files for review.
            </p>
            <div className="flex items-start gap-2 p-3 rounded-md bg-amber-500/10 border border-amber-500/20">
              <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-amber-600">
                <strong>Warning:</strong> This process can take several minutes. Please do not close this window or navigate away during conversion.
              </p>
            </div>
            {conversionError && (
              <div className="flex items-start gap-2 p-3 rounded-md bg-destructive/10 border border-destructive/20">
                <AlertCircle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
                <p className="text-xs text-destructive">{conversionError}</p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setIsModalOpen(false)}
              disabled={converting}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleStartConversion}
              disabled={converting}
            >
              {converting ? (
                <>
                  <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                  Converting...
                </>
              ) : (
                "Start Conversion"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
