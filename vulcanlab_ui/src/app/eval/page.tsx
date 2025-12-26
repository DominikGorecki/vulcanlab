"use client";

import { useRouter } from "next/navigation";
import { Plus, Flask, Calendar, ListChecks } from "lucide-react";
import {
  PageHeader,
  DataTable,
  DataTableColumn,
  EmptyState,
  PageLoadingState,
  PageErrorState,
} from "@/components";
import { usePageData } from "@/hooks/use-page-data";
import { useCallback } from "react";
import { Button } from "@/components/ui/button";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ExperimentListItem {
  id: number;
  name: string;
  description_x: string | null;
  description_y: string | null;
  created_at: string;
  prompt_count: number;
  eval_count: number;
}

export default function EvalPage() {
  const router = useRouter();

  const fetchData = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/eval/experiments`);

    if (!response.ok) {
      throw new Error("Failed to load experiments");
    }

    const experiments: ExperimentListItem[] = await response.json();
    return experiments;
  }, []);

  const { data, loading, error, refetch } = usePageData<ExperimentListItem[]>(fetchData);

  const handleRowClick = (experiment: ExperimentListItem) => {
    router.push(`/eval/${experiment.id}`);
  };

  const handleNewExperiment = () => {
    router.push("/eval/new");
  };

  if (loading) {
    return <PageLoadingState title="Loading experiments..." />;
  }

  if (error) {
    return <PageErrorState error={error} onRetry={refetch} />;
  }

  if (!data || data.length === 0) {
    return (
      <div className="container mx-auto p-6">
        <PageHeader
          title="Evaluation Experiments"
          description="Compare and evaluate LLM responses using blind testing"
          icon={<Flask className="h-6 w-6" />}
          actions={
            <Button onClick={handleNewExperiment}>
              <Plus className="mr-2 h-4 w-4" />
              New Experiment
            </Button>
          }
        />
        <EmptyState
          title="No experiments yet"
          description="Create your first evaluation experiment to compare LLM responses"
          icon={<Flask className="h-12 w-12" />}
          actions={[
            {
              label: "New Experiment",
              onClick: handleNewExperiment,
              variant: "default",
            },
          ]}
        />
      </div>
    );
  }

  const columns: DataTableColumn<ExperimentListItem>[] = [
    {
      key: "name",
      label: "Experiment Name",
      sortable: true,
    },
    {
      key: "description_x",
      label: "Answer Set X",
      render: (value) => value || <span className="text-muted-foreground">Not specified</span>,
    },
    {
      key: "description_y",
      label: "Answer Set Y",
      render: (value) => value || <span className="text-muted-foreground">Not specified</span>,
    },
    {
      key: "prompt_count",
      label: "Prompts",
      render: (value) => (
        <div className="flex items-center gap-1">
          <ListChecks className="h-4 w-4 text-muted-foreground" />
          <span>{value as number}</span>
        </div>
      ),
      sortable: true,
    },
    {
      key: "eval_count",
      label: "Evaluations",
      render: (value) => (
        <div className="flex items-center gap-1">
          <Flask className="h-4 w-4 text-muted-foreground" />
          <span>{value as number}</span>
        </div>
      ),
      sortable: true,
    },
    {
      key: "created_at",
      label: "Created",
      render: (value) => (
        <div className="flex items-center gap-1">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <span>{new Date(value as string).toLocaleDateString()}</span>
        </div>
      ),
      sortable: true,
    },
  ];

  return (
    <div className="container mx-auto p-6">
      <PageHeader
        title="Evaluation Experiments"
        description="Compare and evaluate LLM responses using blind testing"
        icon={<Flask className="h-6 w-6" />}
        actions={
          <Button onClick={handleNewExperiment}>
            <Plus className="mr-2 h-4 w-4" />
            New Experiment
          </Button>
        }
      />

      <DataTable
        data={data}
        columns={columns}
        onRowClick={handleRowClick}
        searchable
        searchPlaceholder="Search experiments..."
      />
    </div>
  );
}
