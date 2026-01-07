"use client";

import { useState, useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useToast } from "@/hooks/use-toast";
import { Search, ChevronLeft, ChevronRight, Loader2, AlertCircle, Settings2 } from "lucide-react";
import { SearchResultCard, type SearchResult } from "./SearchResultCard";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type SearchMode = "lexical" | "dense" | "hybrid";

interface RRFStats {
  dense_candidates: number;
  lexical_candidates: number;
  fused_count: number;
  rrf_k: number;
}

interface PaginationInfo {
  page: number;
  page_size: number;
  total_results: number;
  has_next: boolean;
  has_prev: boolean;
}

interface SearchResponse {
  results: SearchResult[];
  pagination: PaginationInfo;
  rrf_stats?: RRFStats;
}

export default function SearchPage() {
  const { toast } = useToast();

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [lexicalEnabled, setLexicalEnabled] = useState(true);
  const [denseEnabled, setDenseEnabled] = useState(false);
  const [headingsOnly, setHeadingsOnly] = useState(false);
  const [maxPreviewWords, setMaxPreviewWords] = useState(100);

  // RRF Params
  const [rrfK, setRrfK] = useState(60);
  const [denseTopK, setDenseTopK] = useState(20);
  const [lexicalTopK, setLexicalTopK] = useState(20);
  const [denseWeight, setDenseWeight] = useState(0.5);
  const [lexicalWeight, setLexicalWeight] = useState(0.5);

  const [results, setResults] = useState<SearchResult[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [rrfStats, setRrfStats] = useState<RRFStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const searchMode = useMemo(() => {
    if (lexicalEnabled && denseEnabled) return "hybrid";
    if (lexicalEnabled) return "lexical";
    if (denseEnabled) return "dense";
    return null;
  }, [lexicalEnabled, denseEnabled]);

  const handleSearch = useCallback(async (page: number = 1) => {
    const query = searchQuery.trim();
    if (!query) {
      setError("Please enter a search term");
      return;
    }

    if (!searchMode) {
      setError("Please select at least one search mode");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setRrfStats(null);

      let url = `${API_BASE_URL}/api/v1/search/${searchMode}?q=${encodeURIComponent(query)}&page=${page}&page_size=20&headings_only=${headingsOnly}`;
      
      if (searchMode === "hybrid") {
        url += `&rrf_k=${rrfK}&dense_top_k=${denseTopK}&lexical_top_k=${lexicalTopK}&dense_weight=${denseWeight}&lexical_weight=${lexicalWeight}`;
      }

      const response = await fetch(url);

      if (!response.ok) {
        if (response.status === 422 || response.status === 400) {
          throw new Error("Invalid search parameters. Please check your settings.");
        }
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data: SearchResponse = await response.json();
      setResults(data.results);
      setPagination(data.pagination);
      if (data.rrf_stats) {
        setRrfStats(data.rrf_stats);
      }
      setHasSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to search chunks");
      setResults([]);
      setPagination(null);
      setRrfStats(null);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, searchMode, headingsOnly, rrfK, denseTopK, lexicalTopK, denseWeight, lexicalWeight]);

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

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Search className="h-8 w-8 text-primary" />
          <h2 className="text-3xl font-bold tracking-tight">Search Corpus</h2>
        </div>
        <p className="text-muted-foreground">
          Explore the document corpus using lexical and semantic search techniques.
        </p>
      </div>

      {/* Search Form */}
      <Card>
        <CardHeader>
          <CardTitle>Search Configuration</CardTitle>
          <CardDescription>
            Configure your search mode and parameters. Combine both for hybrid RRF fusion.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder={
                  searchMode === "lexical"
                    ? "Keywords (e.g., memory, attention)..."
                    : searchMode === "dense"
                    ? "Semantic query (e.g., how does memory work?)..."
                    : "Hybrid query (e.g., attention mechanisms in cognition)..."
                }
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1"
                disabled={loading}
              />
              <Button type="submit" disabled={loading || !searchQuery.trim() || !searchMode}>
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left Column: Modes and Basic Filters */}
              <div className="space-y-4">
                <div className="space-y-3">
                  <Label className="text-sm font-semibold">Search Modes</Label>
                  <div className="flex flex-wrap gap-6">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="mode-lexical"
                        checked={lexicalEnabled}
                        onCheckedChange={(checked) => setLexicalEnabled(checked === true)}
                        disabled={loading}
                      />
                      <Label htmlFor="mode-lexical" className="text-sm font-normal cursor-pointer">
                        Lexical Search
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="mode-dense"
                        checked={denseEnabled}
                        onCheckedChange={(checked) => setDenseEnabled(checked === true)}
                        disabled={loading}
                      />
                      <Label htmlFor="mode-dense" className="text-sm font-normal cursor-pointer">
                        Dense Search
                      </Label>
                    </div>
                  </div>
                  {!searchMode && (
                    <p className="text-[10px] text-destructive flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      Select at least one search mode
                    </p>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="headings-only"
                    checked={headingsOnly}
                    onCheckedChange={(checked) => setHeadingsOnly(checked === true)}
                    disabled={loading}
                  />
                  <Label htmlFor="headings-only" className="text-sm font-normal cursor-pointer">
                    Search headings only (H1-H5)
                  </Label>
                </div>
              </div>

              {/* Right Column: Preview Slider */}
              <div className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <Label className="text-sm font-semibold">Max Preview Words</Label>
                    <span className="text-xs text-muted-foreground font-mono">{maxPreviewWords} words</span>
                  </div>
                  <Slider
                    value={[maxPreviewWords]}
                    onValueChange={(vals) => setMaxPreviewWords(vals[0])}
                    min={50}
                    max={500}
                    step={10}
                    disabled={loading}
                  />
                  <p className="text-[10px] text-muted-foreground">
                    Controls how much content is displayed for each result card.
                  </p>
                </div>
              </div>
            </div>

            {/* Advanced Settings - Only for Hybrid */}
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="advanced" className="border-none">
                <AccordionTrigger className="py-2 text-xs hover:no-underline text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Settings2 className="h-3.5 w-3.5" />
                    Advanced RRF Settings {searchMode !== "hybrid" && "(Only for Hybrid Mode)"}
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4 px-1 pb-1">
                    <div className="space-y-2">
                      <Label htmlFor="rrf-k" className="text-xs">RRF k Constant</Label>
                      <Input
                        id="rrf-k"
                        type="number"
                        min={1}
                        max={200}
                        value={rrfK}
                        onChange={(e) => setRrfK(parseInt(e.target.value) || 60)}
                        className="h-8 text-xs"
                        disabled={loading || searchMode !== "hybrid"}
                      />
                      <p className="text-[10px] text-muted-foreground">Smoothing factor for ranks.</p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="dense-topk" className="text-xs">Dense Top-k</Label>
                      <Input
                        id="dense-topk"
                        type="number"
                        min={1}
                        max={100}
                        value={denseTopK}
                        onChange={(e) => setDenseTopK(parseInt(e.target.value) || 20)}
                        className="h-8 text-xs"
                        disabled={loading || searchMode !== "hybrid"}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="lexical-topk" className="text-xs">Lexical Top-k</Label>
                      <Input
                        id="lexical-topk"
                        type="number"
                        min={1}
                        max={100}
                        value={lexicalTopK}
                        onChange={(e) => setLexicalTopK(parseInt(e.target.value) || 20)}
                        className="h-8 text-xs"
                        disabled={loading || searchMode !== "hybrid"}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="dense-weight" className="text-xs">Dense Weight</Label>
                      <Input
                        id="dense-weight"
                        type="number"
                        step={0.1}
                        min={0}
                        max={1}
                        value={denseWeight}
                        onChange={(e) => setDenseWeight(parseFloat(e.target.value) || 0)}
                        className="h-8 text-xs"
                        disabled={loading || searchMode !== "hybrid"}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="lexical-weight" className="text-xs">Lexical Weight</Label>
                      <Input
                        id="lexical-weight"
                        type="number"
                        step={0.1}
                        min={0}
                        max={1}
                        value={lexicalWeight}
                        onChange={(e) => setLexicalWeight(parseFloat(e.target.value) || 0)}
                        className="h-8 text-xs"
                        disabled={loading || searchMode !== "hybrid"}
                      />
                    </div>
                    
                    {(denseWeight === 0 && lexicalWeight === 0) && (
                      <div className="md:col-span-3 text-[10px] text-destructive flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" />
                        Weights cannot both be zero
                      </div>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
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
                Enter search keywords to find relevant documents
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Search uses lexical matching across all chunk content
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
                No results found for &quot;{searchQuery}&quot;
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Try different keywords or remove filters
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Display */}
      {!loading && results.length > 0 && (
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-xl">Search Results</CardTitle>
              <CardDescription>
                Showing {pagination?.total_results || 0} matching result(s)
                {rrfStats && (
                  <span className="block mt-1.5 text-[10px] text-muted-foreground bg-muted/50 p-2 rounded-sm">
                    <span className="font-semibold text-foreground">Fusion Stats:</span> {rrfStats.fused_count} results combined from {rrfStats.dense_candidates} dense and {rrfStats.lexical_candidates} lexical candidates (k={rrfStats.rrf_k})
                  </span>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="flex flex-col gap-4 p-6">
                {results.map((result) => (
                  <SearchResultCard 
                    key={result.id} 
                    result={result} 
                    searchMode={searchMode!} 
                    maxPreviewWords={maxPreviewWords}
                  />
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Pagination Controls */}
          {pagination && pagination.total_results > pagination.page_size && (
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
    </div>
  );
}
