"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { ChevronLeft, FlaskConical, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FormField } from "@/components";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ExperimentFormData {
  name: string;
  description_x: string;
  description_y: string;
  model_x: string;
  model_y: string;
  judge_model: string;
}

export default function NewExperimentPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ExperimentFormData>();

  const onSubmit = async (data: ExperimentFormData) => {
    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/eval/experiments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: data.name,
          description_x: data.description_x || null,
          description_y: data.description_y || null,
          model_x: data.model_x || null,
          model_y: data.model_y || null,
          judge_model: data.judge_model || null,
          eval_template_id: null, // T06 will add template selection
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
