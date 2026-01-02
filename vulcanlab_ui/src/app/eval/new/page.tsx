"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm, useFieldArray } from "react-hook-form";
import { ChevronLeft, FlaskConical, Loader2, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FormField } from "@/components";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Core dimensions that are always present (read-only)
const CORE_DIMENSIONS = [
  "factual_correctness",
  "completeness",
  "coherence",
  "hallucination_risk",
  "academic_response"
];

interface Template {
  id: number;
  function_tag: string;
  title: string;
  version: number;
  template_type: string | null;
}

interface DimensionField {
  id: string;
  name: string;
}

interface ExperimentFormData {
  name: string;
  description: string;
  description_x: string;
  description_y: string;
  model_x: string;
  model_y: string;
  judge_model: string;
  eval_template_id: string;
  additional_dimensions: DimensionField[];
}

export default function NewExperimentPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(true);

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<ExperimentFormData>({
    defaultValues: {
      additional_dimensions: []
    }
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "additional_dimensions"
  });

  // Fetch eval templates on mount
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/settings/templates?template_type=eval`);
        if (response.ok) {
          const data = await response.json();

          // For each template group, fetch the full template details to get IDs
          const allTemplates: Template[] = [];
          for (const group of data.templates) {
            try {
              // Fetch detailed template info for this function_tag
              const detailResponse = await fetch(
                `${API_BASE_URL}/api/v1/settings/templates/${group.function_tag}`
              );
              if (detailResponse.ok) {
                const templates = await detailResponse.json();
                // Add only active templates
                templates.forEach((template: any) => {
                  if (template.is_active && template.template_type === "eval") {
                    allTemplates.push({
                      id: template.id,
                      function_tag: template.function_tag,
                      title: template.title,
                      version: template.version,
                      template_type: template.template_type
                    });
                  }
                });
              }
            } catch (err) {
              console.error(`Failed to fetch details for ${group.function_tag}:`, err);
            }
          }
          setTemplates(allTemplates);
        }
      } catch (err) {
        console.error("Failed to fetch templates:", err);
      } finally {
        setLoadingTemplates(false);
      }
    };

    fetchTemplates();
  }, []);

  const onSubmit = async (data: ExperimentFormData) => {
    setSubmitting(true);
    setError(null);

    try {
      // Extract additional dimension names
      const dimension_names = data.additional_dimensions
        .map(d => d.name.trim())
        .filter(name => name.length > 0);

      // Check for duplicates with core dimensions
      const duplicates = dimension_names.filter(name =>
        CORE_DIMENSIONS.includes(name.toLowerCase())
      );

      if (duplicates.length > 0) {
        throw new Error(`Cannot add core dimensions: ${duplicates.join(", ")}`);
      }

      // Check for duplicates within additional dimensions
      const uniqueNames = new Set(dimension_names);
      if (uniqueNames.size !== dimension_names.length) {
        throw new Error("Duplicate dimension names are not allowed");
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/eval/experiments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: data.name,
          description: data.description || null,
          description_x: data.description_x || null,
          description_y: data.description_y || null,
          model_x: data.model_x || null,
          model_y: data.model_y || null,
          judge_model: data.judge_model || null,
          eval_template_id: data.eval_template_id ? parseInt(data.eval_template_id) : null,
          dimension_names: dimension_names.length > 0 ? dimension_names : null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create experiment: ${response.statusText}`);
      }

      const experiment = await response.json();

      toast({
        title: "Experiment created",
        description: `"${experiment.name}" has been created successfully.`,
      });

      router.push(`/eval/${experiment.id}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create experiment";
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => router.push("/eval")}
          className="mb-4"
        >
          <ChevronLeft className="mr-2 h-4 w-4" />
          Back to Experiments
        </Button>
        <div className="flex items-center gap-3 mb-2">
          <FlaskConical className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold">New Experiment</h1>
        </div>
        <p className="text-muted-foreground">
          Create a new evaluation experiment to compare LLM responses
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        <Card>
          <CardHeader>
            <CardTitle>Experiment Configuration</CardTitle>
            <CardDescription>
              Set up your experiment details. Answer sets X and Y will be randomly assigned to A and B for blind evaluation.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <FormField
              label="Experiment Name"
              required
              error={errors.name?.message}
              description="A descriptive name for this experiment"
            >
              <input
                {...register("name", {
                  required: "Experiment name is required",
                  minLength: {
                    value: 1,
                    message: "Name must be at least 1 character",
                  },
                  maxLength: {
                    value: 255,
                    message: "Name must be less than 255 characters",
                  },
                })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="e.g., GPT-4 vs Claude Comparison"
              />
            </FormField>

            <FormField
              label="Experiment Description"
              error={errors.description?.message}
              description="Overall description of what this experiment is testing"
            >
              <textarea
                {...register("description")}
                className="flex min-h-20 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="e.g., Comparing GPT-4 and Claude Sonnet 3.5 responses to academic prompts"
                rows={3}
              />
            </FormField>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Answer Set X</h3>
                <FormField
                  label="Description"
                  description="What is answer set X? (e.g., GPT-4 answers)"
                >
                  <input
                    {...register("description_x")}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    placeholder="e.g., GPT-4 answers"
                  />
                </FormField>

                <FormField
                  label="Model Name"
                  description="Model used for answer set X"
                >
                  <input
                    {...register("model_x")}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    placeholder="e.g., gpt-4"
                  />
                </FormField>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Answer Set Y</h3>
                <FormField
                  label="Description"
                  description="What is answer set Y? (e.g., Claude answers)"
                >
                  <input
                    {...register("description_y")}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    placeholder="e.g., Claude Sonnet 3.5 answers"
                  />
                </FormField>

                <FormField
                  label="Model Name"
                  description="Model used for answer set Y"
                >
                  <input
                    {...register("model_y")}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    placeholder="e.g., claude-sonnet-3.5"
                  />
                </FormField>
              </div>
            </div>

            <FormField
              label="Judge Model"
              description="Model that will evaluate and compare the answers"
            >
              <input
                {...register("judge_model")}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="e.g., gpt-4o"
              />
            </FormField>

            <FormField
              label="Evaluation Template"
              description="Template used for generating evaluation prompts (optional, uses default if not selected)"
            >
              <select
                {...register("eval_template_id")}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={loadingTemplates}
              >
                <option value="">Default Template</option>
                {templates.map((template) => (
                  <option key={`${template.function_tag}-${template.version}`} value={template.id}>
                    {template.title} (v{template.version})
                  </option>
                ))}
              </select>
            </FormField>

            <div className="space-y-4 pt-4 border-t">
              <div>
                <h3 className="text-lg font-semibold mb-2">Evaluation Dimensions</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Core dimensions are always included. You can add additional custom dimensions below.
                </p>
              </div>

              {/* Core dimensions (read-only) */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Core Dimensions (Required)</label>
                <div className="space-y-2">
                  {CORE_DIMENSIONS.map((dimension) => (
                    <div
                      key={dimension}
                      className="flex items-center gap-2 p-3 rounded-md bg-muted/50 border border-border"
                    >
                      <span className="text-sm font-mono text-muted-foreground flex-1">
                        {dimension}
                      </span>
                      <span className="text-xs text-muted-foreground italic">Required</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Additional dimensions (editable) */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Additional Dimensions (Optional)</label>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => append({ id: crypto.randomUUID(), name: "" })}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Dimension
                  </Button>
                </div>

                {fields.length > 0 && (
                  <div className="space-y-2">
                    {fields.map((field, index) => (
                      <div key={field.id} className="flex items-center gap-2">
                        <input
                          {...register(`additional_dimensions.${index}.name`, {
                            validate: (value) => {
                              if (!value || !value.trim()) return true; // Allow empty (will be filtered)
                              if (CORE_DIMENSIONS.includes(value.trim().toLowerCase())) {
                                return "Cannot duplicate core dimensions";
                              }
                              return true;
                            }
                          })}
                          className="flex h-10 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                          placeholder="e.g., citation_quality"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => remove(index)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}

                {fields.length === 0 && (
                  <p className="text-sm text-muted-foreground italic">
                    No additional dimensions. Click "Add Dimension" to add custom evaluation criteria.
                  </p>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-4 pt-6 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push("/eval")}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Create Experiment
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
