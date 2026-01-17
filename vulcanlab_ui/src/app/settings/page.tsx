"use client";

import { useEffect, useState, Suspense, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CheckCircleIcon, Loader2Icon, AlertCircle, XCircle, CheckCircle2, Star } from "lucide-react";
import { TemplatesTabContent } from "@/components/settings/templates-tab";
import { RagConfigTab } from "@/components/settings/rag-config-tab";
import { ConversionTab } from "@/components/settings/conversion-tab";
import { SummarizeTab } from "@/components/settings/summarize-tab";
import { usePageData } from "@/hooks";
import { PageHeader, PageLoadingState, PageErrorState, FormField } from "@/components";
import { useForm } from "react-hook-form";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types matching API schemas
interface ModelConfig {
  light: string;
  full: string;
}

interface LLMModelsConfig {
  openai: ModelConfig;
  gemini: ModelConfig;
}

interface LLMConfig {
  provider: "openai" | "gemini";
  models: LLMModelsConfig;
}

interface DatabaseConfig {
  admin_user: string;
  host: string;
  port: number;
  db_name: string;
  app_user: string;
}

interface PathsConfig {
  input_dir: string;
  output_dir: string;
}

interface AppConfig {
  database: DatabaseConfig;
  llm: LLMConfig;
  paths: PathsConfig;
}

// Init/Status types
interface DbHealthCheckResult {
  name: string;
  passed: boolean;
  message: string;
  details: string | null;
}

interface DbHealthCheckResponse {
  results: DbHealthCheckResult[];
  all_passed: boolean;
  connection_ok: boolean;
}

function SettingsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tabParam = searchParams.get("tab");
  const defaultTab = tabParam && ["init", "models", "database", "paths", "conversion", "templates", "rag", "summarize"].includes(tabParam)
    ? tabParam
    : "init";

  const fetchSettingsFn = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/settings/`);
    if (!response.ok) throw new Error(`Failed to fetch settings: ${response.statusText}`);
    return response.json();
  }, []);

  const { data: config, loading, error, refetch: fetchSettings } = usePageData<AppConfig>(
    fetchSettingsFn
  );

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  // Health check state
  const [healthResults, setHealthResults] = useState<DbHealthCheckResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [initLoading, setInitLoading] = useState(false);
  const [initError, setInitError] = useState<string | null>(null);

  // Form setup
  const { register, reset: resetForm, getValues, setValue, watch, formState: { errors } } = useForm<AppConfig>();

  useEffect(() => {
    if (config) {
      resetForm(config);
    }
  }, [config, resetForm]);

  const hasRequiredDbSettings = config?.database &&
    config.database.db_name &&
    config.database.app_user &&
    config.database.admin_user;

  // Fetch health checks when settings are available
  useEffect(() => {
    if (hasRequiredDbSettings) {
      fetchHealthChecks();
    }
  }, [hasRequiredDbSettings]);

  const fetchHealthChecks = async () => {
    try {
      setHealthLoading(true);
      setHealthError(null);
      const response = await fetch(`${API_BASE_URL}/init/db-health`);
      if (!response.ok) {
        throw new Error(`Failed to fetch health: ${response.statusText}`);
      }
      const data: DbHealthCheckResponse = await response.json();
      setHealthResults(data);
    } catch (err) {
      setHealthError(err instanceof Error ? err.message : "Failed to check health");
    } finally {
      setHealthLoading(false);
    }
  };

  const handleInitialize = async () => {
    try {
      setInitLoading(true);
      setInitError(null);

      const response = await fetch(`${API_BASE_URL}/init/database`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reset: false }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Initialization failed: ${response.statusText}`);
      }

      // Refresh health checks after successful initialization
      await fetchHealthChecks();

    } catch (err) {
      setInitError(err instanceof Error ? err.message : "Failed to initialize database");
    } finally {
      setInitLoading(false);
    }
  };

  const saveDbSettings = async () => {
    const dbData = getValues("database");
    if (!dbData) return;
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE_URL}/settings/database`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dbData),
      });
      if (!response.ok) {
        throw new Error(`Failed to save: ${response.statusText}`);
      }
      const data: DatabaseConfig = await response.json();
      setValue("database", data);
      setSaveSuccess("database");
      setTimeout(() => setSaveSuccess(null), 2000);
      fetchSettings();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const saveLlmSettings = async () => {
    const llmData = getValues("llm");
    if (!llmData) return;
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE_URL}/settings/llm`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: llmData.provider,
          openai_light: llmData.models.openai.light,
          openai_full: llmData.models.openai.full,
          gemini_light: llmData.models.gemini.light,
          gemini_full: llmData.models.gemini.full,
        }),
      });
      if (!response.ok) {
        throw new Error(`Failed to save: ${response.statusText}`);
      }
      const data: LLMConfig = await response.json();
      setValue("llm", data);
      setSaveSuccess("llm");
      setTimeout(() => setSaveSuccess(null), 2000);
      fetchSettings();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const savePathsSettings = async () => {
    const pathsData = getValues("paths");
    if (!pathsData) return;

    // Frontend validation for absolute paths
    const isAbsoluteWindows = (path: string) => /^[A-Za-z]:\\/.test(path);
    const isAbsoluteUnix = (path: string) => path.startsWith('/');
    const isAbsolute = (path: string) => isAbsoluteWindows(path) || isAbsoluteUnix(path);

    if (!isAbsolute(pathsData.input_dir) || !isAbsolute(pathsData.output_dir)) {
      return;
    }

    try {
      setSaving(true);
      const response = await fetch(`${API_BASE_URL}/settings/paths`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pathsData),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to save: ${response.statusText}`);
      }
      const data: PathsConfig = await response.json();
      setValue("paths", data);
      setSaveSuccess("paths");
      setTimeout(() => setSaveSuccess(null), 2000);
      fetchSettings();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const currentProvider = watch("llm.provider");

  if (loading) return <PageLoadingState />;
  if (error) return <PageErrorState title="Failed to load settings" error={error} onRetry={fetchSettings} />;
  if (!config) return null;

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Settings" 
        description="Manage configuration and preferences."
      />

      <Tabs defaultValue={defaultTab} className="w-full">
        <TabsList>
          <TabsTrigger value="init">Init/Status</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="database">Database</TabsTrigger>
          <TabsTrigger value="paths">Paths</TabsTrigger>
          <TabsTrigger value="conversion">Conversion</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="rag">RAG Settings</TabsTrigger>
          <TabsTrigger value="summarize">Summarize</TabsTrigger>
        </TabsList>

        {/* Init/Status Tab */}
        <TabsContent value="init" className="mt-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Database Health</CardTitle>
                <CardDescription>
                  {config.database ? `${config.database.db_name} @ ${config.database.host}:${config.database.port}` : "Connection status and schema checks"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!hasRequiredDbSettings && (
                  <div className="flex items-center justify-between py-4 border-b">
                    <div className="flex items-center gap-3">
                      <AlertCircle className="h-5 w-5 text-amber-500" />
                      <span className="text-sm">Database settings incomplete</span>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => router.push("/settings?tab=database")}>
                      Configure Database
                    </Button>
                  </div>
                )}

                {hasRequiredDbSettings && (
                  <>
                    {healthLoading && (
                      <div className="flex items-center gap-2 py-4">
                        <Loader2Icon className="h-4 w-4 animate-spin" />
                        <span className="text-sm text-muted-foreground">Running health checks...</span>
                      </div>
                    )}

                    {healthError && (
                      <div className="flex items-center gap-2 text-destructive py-4">
                        <XCircle className="h-4 w-4" />
                        <span className="text-sm">{healthError}</span>
                        <Button variant="ghost" size="sm" onClick={fetchHealthChecks}>Retry</Button>
                      </div>
                    )}

                    {healthResults && (
                      <div className="space-y-6">
                        {/* Health results grouping logic... simplified for now but keeping the core */}
                        <div className="grid gap-4">
                          {healthResults.results.map((result, i) => (
                            <div key={i} className="flex items-center gap-3 px-3 py-2 border rounded-lg">
                              {result.passed ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> : <XCircle className="h-4 w-4 text-destructive" />}
                              <div>
                                <div className="text-sm font-medium">{result.name}</div>
                                <div className="text-xs text-muted-foreground">{result.message}</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
                <CardDescription>Setup and maintenance tasks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {!hasRequiredDbSettings && (
                  <Button className="w-full" onClick={() => router.push("/settings?tab=database")}>Configure Database</Button>
                )}
                {hasRequiredDbSettings && healthResults && healthResults.connection_ok && !healthResults.all_passed && (
                  <Button className="w-full" onClick={handleInitialize} disabled={initLoading}>
                    {initLoading ? <Loader2Icon className="h-4 w-4 animate-spin mr-2" /> : null}
                    Initialize Database
                  </Button>
                )}
                {hasRequiredDbSettings && (
                  <Button className="w-full" variant="outline" onClick={fetchHealthChecks} disabled={healthLoading}>
                    {healthLoading ? <Loader2Icon className="h-4 w-4 animate-spin mr-2" /> : "Check Connections"}
                  </Button>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Models Tab */}
        <TabsContent value="models" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>LLM Configuration</CardTitle>
              <CardDescription>Configure language model providers.</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue={currentProvider} value={currentProvider} onValueChange={(v) => setValue("llm.provider", v as any)}>
                <TabsList className="mb-4">
                  <TabsTrigger value="gemini">Gemini</TabsTrigger>
                  <TabsTrigger value="openai">OpenAI</TabsTrigger>
                </TabsList>

                <TabsContent value="gemini" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField label="Light Model">
                      <Input {...register("llm.models.gemini.light")} />
                    </FormField>
                    <FormField label="Full Model">
                      <Input {...register("llm.models.gemini.full")} />
                    </FormField>
                  </div>
                  <Button onClick={saveLlmSettings} disabled={saving}>
                    {saving && <Loader2Icon className="h-4 w-4 animate-spin mr-2" />}
                    {saveSuccess === "llm" ? "Saved!" : "Save Changes"}
                  </Button>
                </TabsContent>

                <TabsContent value="openai" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField label="Light Model">
                      <Input {...register("llm.models.openai.light")} />
                    </FormField>
                    <FormField label="Full Model">
                      <Input {...register("llm.models.openai.full")} />
                    </FormField>
                  </div>
                  <Button onClick={saveLlmSettings} disabled={saving}>
                    {saving && <Loader2Icon className="h-4 w-4 animate-spin mr-2" />}
                    {saveSuccess === "llm" ? "Saved!" : "Save Changes"}
                  </Button>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Database Tab */}
        <TabsContent value="database" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Database Settings</CardTitle>
              <CardDescription>PostgreSQL connection configuration.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <FormField label="Host">
                  <Input {...register("database.host")} />
                </FormField>
                <FormField label="Port">
                  <Input type="number" {...register("database.port", { valueAsNumber: true })} />
                </FormField>
              </div>
              <FormField label="Database Name">
                <Input {...register("database.db_name")} />
              </FormField>
              <div className="grid gap-4 md:grid-cols-2">
                <FormField label="Admin User">
                  <Input {...register("database.admin_user")} />
                </FormField>
                <FormField label="Application User">
                  <Input {...register("database.app_user")} />
                </FormField>
              </div>
              <Button onClick={saveDbSettings} disabled={saving}>
                {saving && <Loader2Icon className="h-4 w-4 animate-spin mr-2" />}
                {saveSuccess === "database" ? "Saved!" : "Save Changes"}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Paths Tab */}
        <TabsContent value="paths" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>File System Paths</CardTitle>
              <CardDescription>Configure input and output directory paths.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField label="Input Directory">
                <Input {...register("paths.input_dir")} />
              </FormField>
              <FormField label="Output Directory">
                <Input {...register("paths.output_dir")} />
              </FormField>
              <Button onClick={savePathsSettings} disabled={saving}>
                {saving && <Loader2Icon className="h-4 w-4 animate-spin mr-2" />}
                {saveSuccess === "paths" ? "Saved!" : "Save Changes"}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="conversion" className="mt-4"><ConversionTab /></TabsContent>
        <TabsContent value="templates" className="mt-4"><TemplatesTabContent /></TabsContent>
        <TabsContent value="rag" className="mt-4"><RagConfigTab /></TabsContent>
        <TabsContent value="summarize" className="mt-4"><SummarizeTab /></TabsContent>
      </Tabs>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Suspense fallback={<PageLoadingState />}>
      <SettingsContent />
    </Suspense>
  );
}
