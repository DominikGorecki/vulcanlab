"use client";

import { useCallback, useMemo, useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  FolderOpen,
  ArrowLeft,
  Calendar,
  Clock,
  Trash2,
  ExternalLink,
  Save,
  Edit2,
  X,
  Loader2,
  CheckCircle2,
  AlertCircle,
  MoreVertical,
  ChevronDown,
  ChevronRight,
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
import { useToast } from "@/hooks/use-toast";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { MetadataCard } from "@/components/collections/MetadataCard";
import { DeepResearchModal } from "@/components/research/DeepResearchModal";
import { AutomatedResearchProgress } from "@/components/research/AutomatedResearchProgress";
import { ResearchReportList } from "@/components/research/ResearchReportList";
import { cn } from "@/lib/utils";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CollectionItem {
  id: number;
  collection_id: number;
  item_type: string;
  link: string;
  note: string | null;
  order: number;
  date_added: string;
  last_modified: string;
}

interface Collection {
  id: number;
  name: string;
  description: string | null;
  tags: string[];
  item_count: number;
  items: CollectionItem[];
  created_at: string;
  updated_at: string;
}

/**
 * Inline editable text component
 */
function InlineEdit({
  value,
  onSave,
  type = "text",
  placeholder = "Click to edit...",
  className = "",
}: {
  value: string;
  onSave: (newValue: string) => Promise<void>;
  type?: "text" | "textarea" | "number";
  placeholder?: string;
  className?: string;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [currentValue, setCurrentValue] = useState(value);
  const [isSaving, setIsSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  useEffect(() => {
    setCurrentValue(value);
  }, [value]);

  const handleSave = async () => {
    if (currentValue === value) {
      setIsEditing(false);
      return;
    }

    setIsSaving(true);
    try {
      await onSave(currentValue);
      setIsEditing(false);
    } catch (err) {
      // Keep editing if error occurs? Or revert?
      // Usually better to show error toast from parent
    } finally {
      setIsSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && type !== "textarea") {
      handleSave();
    } else if (e.key === "Escape") {
      setCurrentValue(value);
      setIsEditing(false);
    }
  };

  if (isEditing) {
    return (
      <div className="flex items-center gap-2 w-full" onClick={(e) => e.stopPropagation()}>
        {type === "textarea" ? (
          <Textarea
            ref={inputRef as any}
            value={currentValue}
            onChange={(e) => setCurrentValue(e.target.value)}
            onBlur={handleSave}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className={cn("min-h-[80px]", className)}
            autoFocus
          />
        ) : (
          <Input
            ref={inputRef as any}
            type={type}
            value={currentValue}
            onChange={(e) => setCurrentValue(e.target.value)}
            onBlur={handleSave}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className={cn("h-8", className)}
            step={type === "number" ? "0.001" : undefined}
            autoFocus
          />
        )}
        {isSaving && <Loader2 className="h-3 w-3 animate-spin shrink-0" />}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "cursor-pointer hover:bg-muted/50 rounded px-1 -mx-1 transition-colors min-h-[1.5rem] flex items-center py-1",
        !value && "text-muted-foreground italic",
        className
      )}
      onClick={(e) => {
        e.stopPropagation();
        setIsEditing(true);
      }}
    >
      <span className={cn(
        "max-w-full",
        type === "textarea" ? "whitespace-normal break-words line-clamp-3" : "truncate"
      )}>
        {value || placeholder}
      </span>
    </div>
  );
}

export default function CollectionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const id = parseInt(params.id as string);

  const [isEditingDescription, setIsEditingDescription] = useState(false);
  const [description, setDescription] = useState("");
  const [isSavingDesc, setIsSavingDesc] = useState(false);

  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());
  const [isDeepResearchModalOpen, setIsDeepResearchModalOpen] = useState(false);
  const [resumeSessionId, setResumeSessionId] = useState<number | undefined>();
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());
  const [isDeletingItems, setIsDeletingItems] = useState(false);
  const [showDeleteConfirm, setShowShowDeleteConfirm] = useState(false);
  const [reportsKey, setReportsKey] = useState(0);

  const fetchCollection = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/collections/${id}`);
    if (!response.ok) {
      throw new Error(`Failed to load collection: ${response.statusText}`);
    }
    const data = await response.json();
    setDescription(data.description || "");
    return data;
  }, [id]);

  const { data, loading, error, refetch } = usePageData<Collection>(fetchCollection);

  const fetchSessions = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/collections/${id}/research-sessions`);
    if (!response.ok) return [];
    const data = await response.json();
    return data.sessions.filter((s: any) => s.status === 'in_progress');
  }, [id]);

  const { data: sessions, loading: loadingSessions, refetch: refetchSessions } = usePageData<any[]>(fetchSessions);

  const manualSessions = useMemo(() => sessions?.filter(s => s.session_type === 'manual') || [], [sessions]);
  const automatedSessions = useMemo(() => sessions?.filter(s => s.session_type === 'automated') || [], [sessions]);

  const handleResumeSession = async (sessionId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research-sessions/${sessionId}/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      
      if (!response.ok) throw new Error("Failed to resume session");
      
      setResumeSessionId(sessionId);
      setIsDeepResearchModalOpen(true);
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to resume session.",
        variant: "destructive",
      });
    }
  };

  const handleSaveDescription = async () => {
    setIsSavingDesc(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/collections/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description }),
      });

      if (!response.ok) throw new Error("Failed to update description");
      
      setIsEditingDescription(false);
      toast({
        title: "Success",
        description: "Collection description updated.",
      });
      await refetch();
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to update description.",
        variant: "destructive",
      });
    } finally {
      setIsSavingDesc(false);
    }
  };

  const handleUpdateItem = async (itemId: number, updates: Partial<CollectionItem>) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/collections/${id}/items/${itemId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });

      if (!response.ok) throw new Error("Failed to update item");
      
      toast({
        title: "Updated",
        description: "Item updated successfully.",
      });
      await refetch();
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to update item.",
        variant: "destructive",
      });
      throw err;
    }
  };

  const handleBulkDelete = async () => {
    setIsDeletingItems(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/collections/${id}/items`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_ids: Array.from(selectedItems) }),
      });

      if (!response.ok) throw new Error("Failed to delete items");
      
      const result = await response.json();
      toast({
        title: "Deleted",
        description: `Successfully deleted ${result.deleted_count} items.`,
      });
      setSelectedItems(new Set());
      setShowShowDeleteConfirm(false);
      await refetch();
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to delete items.",
        variant: "destructive",
      });
    } finally {
      setIsDeletingItems(false);
    }
  };

  const toggleExpand = (itemId: number) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const columns = useMemo((): DataTableColumn<CollectionItem>[] => [
    {
      key: "id",
      header: "",
      className: "w-10",
      cell: (item) => (
        <Checkbox
          checked={selectedItems.has(item.id)}
          onCheckedChange={(checked) => {
            const newSelected = new Set(selectedItems);
            if (checked) newSelected.add(item.id);
            else newSelected.delete(item.id);
            setSelectedItems(newSelected);
          }}
          onClick={(e) => e.stopPropagation()}
        />
      ),
    },
    {
      key: "order",
      header: "Order",
      sortable: true,
      className: "w-24",
      cell: (item) => (
        <InlineEdit
          value={item.order.toString()}
          type="number"
          onSave={(val) => handleUpdateItem(item.id, { order: parseFloat(val) })}
        />
      ),
    },
    {
      key: "item_type",
      header: "Type",
      sortable: true,
      className: "w-32",
      cell: (item) => (
        <Badge variant="outline" className="capitalize">
          {item.item_type.replace("_", " ")}
        </Badge>
      ),
    },
    {
      key: "link",
      header: "Resource",
      className: "min-w-[200px] max-w-[250px] md:max-w-[400px] lg:max-w-[600px] whitespace-normal",
      cell: (item) => {
        const isExpanded = expandedItems.has(item.id);
        return (
          <div className="space-y-2 w-full">
            <div className="flex items-center gap-2 group w-full">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleExpand(item.id);
                }}
                className="hover:bg-muted p-0.5 rounded transition-colors shrink-0"
              >
                {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </button>
              <div className="flex items-center gap-1 min-w-0 flex-1">
                <span className="text-xs font-mono text-muted-foreground flex-1 break-all">
                  {item.link}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push(item.link);
                  }}
                >
                  <ExternalLink className="h-3 w-3" />
                </Button>
              </div>
            </div>
            {isExpanded && (
              <div className="ml-6 border-l-2 border-primary/10 pl-4 py-2 w-full" onClick={(e) => e.stopPropagation()}>
                <MetadataCard collectionId={id} itemId={item.id} />
              </div>
            )}
          </div>
        );
      },
    },
    {
      key: "note",
      header: "Note",
      className: "min-w-[150px] whitespace-normal",
      cell: (item) => (
        <InlineEdit
          value={item.note || ""}
          type="textarea"
          placeholder="Add a note..."
          onSave={(val) => handleUpdateItem(item.id, { note: val })}
        />
      ),
    },
  ], [selectedItems, expandedItems, id, router]);

  if (loading) return <PageLoadingState />;
  if (error) return <PageErrorState error={error} onRetry={refetch} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={() => router.push("/collections")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <PageHeader
          title={data.name}
          description={`Created ${new Date(data.created_at).toLocaleDateString()}`}
          actions={
            data.item_count >= 5 && (
              <Button onClick={() => {
                setResumeSessionId(undefined);
                setIsDeepResearchModalOpen(true);
              }}>
                Deep Research
              </Button>
            )
          }
        />
      </div>

      {(manualSessions.length > 0 || automatedSessions.length > 0) && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold tracking-tight">In-Progress Research</h3>
            <Badge variant="secondary" className="bg-orange-500/10 text-orange-600 border-orange-500/20">
              {manualSessions.length + automatedSessions.length}
            </Badge>
          </div>

          {manualSessions.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {manualSessions.map((session: any) => (
                <Card key={session.id} className="border-orange-500/20 bg-orange-500/5">
                  <CardHeader className="py-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-sm font-bold capitalize">
                          {session.session_type} Research
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Started {new Date(session.created_at).toLocaleDateString()}
                        </CardDescription>
                      </div>
                      <Badge variant="outline" className="capitalize bg-background">
                        {session.current_phase?.replace('_', ' ') || 'Planning'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="flex justify-end pt-0 pb-4">
                    <Button 
                      size="sm" 
                      variant="outline"
                      className="h-8 border-orange-500/30 hover:bg-orange-500/10 hover:text-orange-700"
                      onClick={() => handleResumeSession(session.id)}
                    >
                      Resume Session
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {automatedSessions.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {automatedSessions.map((session: any) => (
                <AutomatedResearchProgress 
                  key={session.id} 
                  sessionId={session.id} 
                  onComplete={refetchSessions}
                />
              ))}
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between py-4">
            <CardTitle className="text-base font-semibold">Description</CardTitle>
            {!isEditingDescription ? (
              <Button variant="ghost" size="sm" onClick={() => setIsEditingDescription(true)}>
                <Edit2 className="h-3.5 w-3.5 mr-1.5" />
                Edit
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={() => setIsEditingDescription(false)} disabled={isSavingDesc}>
                  <X className="h-3.5 w-3.5 mr-1.5" />
                  Cancel
                </Button>
                <Button size="sm" onClick={handleSaveDescription} disabled={isSavingDesc}>
                  {isSavingDesc ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" /> : <Save className="h-3.5 w-3.5 mr-1.5" />}
                  Save
                </Button>
              </div>
            )}
          </CardHeader>
          <CardContent>
            {isEditingDescription ? (
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="min-h-[100px] resize-none"
                placeholder="Add a description for this collection..."
              />
            ) : (
              <p className={cn("text-sm leading-relaxed", !data.description && "text-muted-foreground italic")}>
                {data.description || "No description provided."}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="py-4">
            <CardTitle className="text-base font-semibold">Metadata</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Tags</span>
              <div className="flex flex-wrap gap-1.5">
                {data.tags.map((tag) => (
                  <Badge key={tag} variant="secondary">
                    {tag}
                  </Badge>
                ))}
                {data.tags.length === 0 && <span className="text-sm text-muted-foreground italic">No tags</span>}
              </div>
            </div>
            
            <div className="flex items-center justify-between pt-2 border-t">
              <span className="text-sm text-muted-foreground">Total Items</span>
              <Badge variant="outline" className="font-mono">{data.item_count}</Badge>
            </div>
            
            <div className="flex items-center justify-between pt-2 border-t">
              <span className="text-sm text-muted-foreground">Last Modified</span>
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {new Date(data.updated_at).toLocaleDateString()}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold tracking-tight">Collection Items</h3>
          {selectedItems.size > 0 && (
            <div className="flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
              <span className="text-sm text-muted-foreground">
                {selectedItems.size} item{selectedItems.size > 1 ? 's' : ''} selected
              </span>
              <Button
                variant="destructive"
                size="sm"
                className="gap-2"
                onClick={() => setShowShowDeleteConfirm(true)}
              >
                <Trash2 className="h-4 w-4" />
                Delete Selected
              </Button>
            </div>
          )}
        </div>

        <DataTable
          data={data.items || []}
          columns={columns}
          emptyState={{
            title: "No items in this collection",
            description: "Items can be added from search results, RAG results, or query history.",
            icon: FolderOpen,
          }}
        />
      </div>

      <div id="reports">
        <ResearchReportList key={reportsKey} collectionId={id} />
      </div>

      <ConfirmDialog
        open={showDeleteConfirm}
        onOpenChange={setShowShowDeleteConfirm}
        title="Delete Items"
        description={`Are you sure you want to remove ${selectedItems.size} selected item(s) from this collection? This action cannot be undone.`}
        confirmText="Delete"
        variant="destructive"
        onConfirm={handleBulkDelete}
        isLoading={isDeletingItems}
      />

      <DeepResearchModal
        isOpen={isDeepResearchModalOpen}
        onClose={() => {
          setIsDeepResearchModalOpen(false);
          setResumeSessionId(undefined);
          refetchSessions();
          setReportsKey(prev => prev + 1);
        }}
        collectionId={id}
        initialSessionId={resumeSessionId}
      />
    </div>
  );
}

