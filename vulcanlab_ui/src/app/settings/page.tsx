"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CheckCircleIcon, Loader2Icon, AlertCircle, XCircle, CheckCircle2 } from "lucide-react";
import { TemplatesTabContent } from "@/components/settings/templates-tab";
import { RagConfigTab } from "@/components/settings/rag-config-tab";
import { ConversionTab } from "@/components/settings/conversion-tab";

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
  const defaultTab = tabParam && ["init", "models", "database", "paths", "conversion", "templates", "rag"].includes(tabParam)
    ? tabParam
    : "init";

  const [config, setConfig] = useState<AppConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  // Form state for editing
  const [dbForm, setDbForm] = useState<DatabaseConfig | null>(null);
  const [llmForm, setLlmForm] = useState<LLMConfig | null>(null);
  const [pathsForm, setPathsForm] = useState<PathsConfig | null>(null);

  // Init/Status state
  const [dbSettings, setDbSettings] = useState<DatabaseConfig | null>(null);
  const [dbSettingsError, setDbSettingsError] = useState<string | null>(null);
  const [healthResults, setHealthResults] = useState<DbHealthCheckResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [initLoading, setInitLoading] = useState(false);
  const [initError, setInitError] = useState<string | null>(null);

  // Check if required DB settings are present
  const hasRequiredDbSettings = dbSettings &&
    dbSettings.db_name &&
    dbSettings.app_user &&
    dbSettings.admin_user;

  // Fetch settings on mount
  useEffect(() => {
    fetchSettings();
  }, []);

  // Fetch health checks when settings are available
  useEffect(() => {
    if (hasRequiredDbSettings) {
      fetchHealthChecks();
    }
  }, [hasRequiredDbSettings]);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/settings/`);
      if (!response.ok) {
        throw new Error(`Failed to fetch settings: ${response.statusText}`);
      }
      const data: AppConfig = await response.json();
      setConfig(data);
      setDbForm(data.database);
      setLlmForm(data.llm);
      setPathsForm(data.paths);
      setDbSettings(data.database);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
      setDbSettingsError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

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
    if (!dbForm) return;
    try {
      setSaving(true);
      setSaveSuccess(null);
      const response = await fetch(`${API_BASE_URL}/settings/database`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dbForm),
      });
      if (!response.ok) {
        throw new Error(`Failed to save: ${response.statusText}`);
      }
      const data: DatabaseConfig = await response.json();
      setConfig((prev) => prev ? { ...prev, database: data } : null);
      setDbForm(data);
      setDbSettings(data);
      setSaveSuccess("database");
      setTimeout(() => setSaveSuccess(null), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const saveLlmSettings = async () => {
    if (!llmForm) return;
    try {
      setSaving(true);
      setSaveSuccess(null);
      const response = await fetch(`${API_BASE_URL}/settings/llm`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: llmForm.provider,
          openai_light: llmForm.models.openai.light,
          openai_full: llmForm.models.openai.full,
          gemini_light: llmForm.models.gemini.light,
          gemini_full: llmForm.models.gemini.full,
        }),
      });
      if (!response.ok) {
        throw new Error(`Failed to save: ${response.statusText}`);
      }
      const data: LLMConfig = await response.json();
      setConfig((prev) => prev ? { ...prev, llm: data } : null);
      setLlmForm(data);
      setSaveSuccess("llm");
      setTimeout(() => setSaveSuccess(null), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const savePathsSettings = async () => {
    if (!pathsForm) return;

    // Frontend validation for absolute paths
    const isAbsoluteWindows = (path: string) => /^[A-Za-z]:\\/.test(path);
    const isAbsoluteUnix = (path: string) => path.startsWith('/');
    const isAbsolute = (path: string) => isAbsoluteWindows(path) || isAbsoluteUnix(path);

    if (!isAbsolute(pathsForm.input_dir)) {
      setError("Input directory must be an absolute path (e.g., C:\\path\\to\\input or /path/to/input)");
      return;
    }

    if (!isAbsolute(pathsForm.output_dir)) {
      setError("Output directory must be an absolute path (e.g., C:\\path\\to\\output or /path/to/output)");
      return;
    }

    try {
      setSaving(true);
      setSaveSuccess(null);
      const response = await fetch(`${API_BASE_URL}/settings/paths`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pathsForm),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to save: ${response.statusText}`);
      }
      const data: PathsConfig = await response.json();
      setConfig((prev) => prev ? { ...prev, paths: data } : null);
      setPathsForm(data);
      setSaveSuccess("paths");
      setTimeout(() => setSaveSuccess(null), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const setActiveProvider = (provider: "openai" | "gemini") => {
    if (!llmForm) return;
    setLlmForm({ ...llmForm, provider });
  };

  const updateModelConfig = (
    provider: "openai" | "gemini",
    field: "light" | "full",
    value: string
  ) => {
    if (!llmForm) return;
    setLlmForm({
      ...llmForm,
      models: {
        ...llmForm.models,
        [provider]: {
          ...llmForm.models[provider],
          [field]: value,
        },
      },
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error && !config) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
          <p className="text-muted-foreground">Manage configuration and preferences.</p>
        </div>
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
            <Button onClick={fetchSettings} className="mt-4">
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
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">Manage configuration and preferences.</p>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-md text-sm">
          {error}
        </div>
      )}

      <Tabs defaultValue={defaultTab} className="w-full">
        <TabsList>
          <TabsTrigger value="init">Init/Status</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="database">Database</TabsTrigger>
          <TabsTrigger value="paths">Paths</TabsTrigger>
          <TabsTrigger value="conversion">Conversion</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="rag">RAG Settings</TabsTrigger>
        </TabsList>

        {/* Init/Status Tab */}
        <TabsContent value="init" className="mt-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Database Health Card */}
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Database Health</CardTitle>
                <CardDescription>
                  {dbSettings ? (
                    <span>
                      {dbSettings.db_name} @ {dbSettings.host}:{dbSettings.port}
                    </span>
                  ) : (
                    "Connection status and schema checks"
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Show error if settings failed to load */}
                {dbSettingsError && (
                  <div className="flex items-center gap-2 text-destructive mb-4">
                    <AlertCircle className="h-4 w-4" />
                    <span className="text-sm">{dbSettingsError}</span>
                  </div>
                )}

                {/* Show warning if required settings are missing */}
                {!hasRequiredDbSettings && !dbSettingsError && (
                  <div className="flex items-center justify-between py-4 border-b">
                    <div className="flex items-center gap-3">
                      <AlertCircle className="h-5 w-5 text-amber-500" />
                      <span className="text-sm">Database settings incomplete</span>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const url = new URL(window.location.href);
                        url.searchParams.set('tab', 'database');
                        router.push(url.pathname + url.search);
                      }}
                    >
                      Configure Database
                    </Button>
                  </div>
                )}

                {/* Health check results */}
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
                        <Button variant="ghost" size="sm" onClick={fetchHealthChecks}>
                          Retry
                        </Button>
                      </div>
                    )}

                    {healthResults && (
                      <div className="space-y-6">
                        {/* Group results by table */}
                        {(() => {
                          // Extract table names and group results
                          const tableGroups: Record<string, DbHealthCheckResult[]> = {};
                          const systemChecks: DbHealthCheckResult[] = [];

                          healthResults.results.forEach((result) => {
                            // System-level checks (Connection, Extension)
                            if (result.name.startsWith("Connection") || result.name.startsWith("Extension")) {
                              systemChecks.push(result);
                            } else {
                              // Extract table name from result.name
                              // Patterns: "Table: tablename", "Columns: tablename", "Index: indexname", "Trigger: triggername", "Read: tablename", "Write: tablename"
                              const match = result.name.match(/^(?:Table|Columns|Index|Trigger|Read|Write):\s*(.+)/);
                              if (match) {
                                let tableName = match[1].trim();

                                // For indexes and triggers, extract table name from the identifier
                                if (result.name.startsWith("Index:")) {
                                  // Map index names to tables
                                  if (tableName.includes("chunks")) tableName = "chunks";
                                  else if (tableName.includes("queries")) tableName = "queries";
                                  else if (tableName.includes("prompt_meta")) tableName = "prompt_meta";
                                  else if (tableName.includes("rag_config")) tableName = "rag_config";
                                  else if (tableName.includes("prompt_templates")) tableName = "prompt_templates";
                                } else if (result.name.startsWith("Trigger:")) {
                                  // Map trigger names to tables
                                  if (tableName.includes("tsvector_update")) tableName = "chunks";
                                  else if (tableName.includes("prompt_meta")) tableName = "prompt_meta";
                                  else if (tableName.includes("rag_config")) tableName = "rag_config";
                                }

                                if (!tableGroups[tableName]) {
                                  tableGroups[tableName] = [];
                                }
                                tableGroups[tableName].push(result);
                              } else {
                                systemChecks.push(result);
                              }
                            }
                          });

                          const tableOrder = ["works", "chunks", "queries", "results", "io_files", "prompt_templates", "prompt_meta", "rag_config"];
                          const sortedTables = tableOrder.filter(t => tableGroups[t]);

                          return (
                            <>
                              {/* System Checks */}
                              {systemChecks.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold mb-2 text-muted-foreground">System</h4>
                                  <div className="border rounded-lg overflow-hidden">
                                    <div className="divide-y">
                                      {systemChecks.map((result, index) => (
                                        <div key={index} className="flex items-center gap-3 px-3 py-2 hover:bg-muted/50">
                                          <div className="w-5 flex items-center justify-center flex-shrink-0">
                                            {result.passed ? (
                                              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                                            ) : (
                                              <XCircle className="h-4 w-4 text-destructive" />
                                            )}
                                          </div>
                                          <div className="flex-1 min-w-0">
                                            <div className="text-sm font-medium">{result.name}</div>
                                            <div className="text-xs text-muted-foreground truncate">{result.message}</div>
                                            {result.details && (
                                              <div className="text-xs text-destructive mt-1">{result.details}</div>
                                            )}
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              )}

                              {/* Table Groups */}
                              {sortedTables.map((tableName) => {
                                const checks = tableGroups[tableName];
                                const allPassed = checks.every(c => c.passed);

                                return (
                                  <div key={tableName}>
                                    <div className="flex items-center gap-2 mb-2">
                                      <h4 className="text-sm font-semibold text-muted-foreground">{tableName}</h4>
                                      {allPassed ? (
                                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                                      ) : (
                                        <XCircle className="h-3.5 w-3.5 text-destructive" />
                                      )}
                                    </div>
                                    <div className="border rounded-lg overflow-hidden">
                                      <div className="divide-y">
                                        {checks.map((result, index) => (
                                          <div key={index} className="flex items-center gap-3 px-3 py-2 hover:bg-muted/50">
                                            <div className="w-5 flex items-center justify-center flex-shrink-0">
                                              {result.passed ? (
                                                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                                              ) : (
                                                <XCircle className="h-4 w-4 text-destructive" />
                                              )}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                              <div className="text-sm font-medium">{result.name.split(":")[0]}</div>
                                              <div className="text-xs text-muted-foreground truncate">{result.message}</div>
                                              {result.details && (
                                                <div className="text-xs text-destructive mt-1">{result.details}</div>
                                              )}
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  </div>
                                );
                              })}
                            </>
                          );
                        })()}
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            {/* Actions Card */}
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
                <CardDescription>Setup and maintenance tasks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {/* Show "Add DB Settings" if settings are missing */}
                {!hasRequiredDbSettings && (
                  <Button
                    className="w-full"
                    variant="default"
                    onClick={() => {
                      const url = new URL(window.location.href);
                      url.searchParams.set('tab', 'database');
                      router.push(url.pathname + url.search);
                    }}
                  >
                    Configure Database
                  </Button>
                )}

                {/* Show "Initialize" if connection succeeds but tables are missing */}
                {hasRequiredDbSettings && healthResults && healthResults.connection_ok && !healthResults.all_passed && (
                  <div className="space-y-2">
                    <Button
                      className="w-full cursor-pointer"
                      variant="default"
                      onClick={handleInitialize}
                      disabled={initLoading}
                    >
                      {initLoading ? (
                        <>
                          <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                          Initializing Database...
                        </>
                      ) : (
                        "Initialize Database"
                      )}
                    </Button>
                    {initError && (
                      <p className="text-sm text-destructive px-1">{initError}</p>
                    )}
                  </div>
                )}

                {/* Show "Check Connections" button */}
                {hasRequiredDbSettings && (
                  <Button
                    className="w-full"
                    variant="outline"
                    onClick={fetchHealthChecks}
                    disabled={healthLoading}
                  >
                    {healthLoading ? (
                      <>
                        <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                        Checking...
                      </>
                    ) : (
                      "Check Connections"
                    )}
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
              <CardDescription>
                Configure language model providers. Click a provider tab to view/edit its models,
                or click &quot;Set Active&quot; to switch the active provider.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {llmForm && (
                <Tabs defaultValue={llmForm.provider} className="w-full">
                  <TabsList className="mb-4">
                    <TabsTrigger value="gemini" className="gap-2">
                      Gemini
                      {llmForm.provider === "gemini" && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-500 font-medium">
                          active
                        </span>
                      )}
                    </TabsTrigger>
                    <TabsTrigger value="openai" className="gap-2">
                      OpenAI
                      {llmForm.provider === "openai" && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-500 font-medium">
                          active
                        </span>
                      )}
                    </TabsTrigger>
                  </TabsList>

                  {/* Gemini Tab */}
                  <TabsContent value="gemini" className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="gemini-light">Light Model (Fast)</Label>
                        <Input
                          id="gemini-light"
                          value={llmForm.models.gemini.light}
                          onChange={(e) => updateModelConfig("gemini", "light", e.target.value)}
                          placeholder="e.g., gemini-flash-latest"
                        />
                        <p className="text-xs text-muted-foreground">
                          Used for quick, simple tasks
                        </p>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="gemini-full">Full Model (Complex)</Label>
                        <Input
                          id="gemini-full"
                          value={llmForm.models.gemini.full}
                          onChange={(e) => updateModelConfig("gemini", "full", e.target.value)}
                          placeholder="e.g., gemini-2.5-pro"
                        />
                        <p className="text-xs text-muted-foreground">
                          Used for complex reasoning tasks
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 pt-2">
                      {llmForm.provider !== "gemini" && (
                        <Button
                          variant="outline"
                          onClick={() => setActiveProvider("gemini")}
                        >
                          Set as Active Provider
                        </Button>
                      )}
                      <Button onClick={saveLlmSettings} disabled={saving}>
                        {saving ? (
                          <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                        ) : saveSuccess === "llm" ? (
                          <CheckCircleIcon className="h-4 w-4 mr-2 text-emerald-500" />
                        ) : null}
                        Save Changes
                      </Button>
                    </div>
                  </TabsContent>

                  {/* OpenAI Tab */}
                  <TabsContent value="openai" className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="openai-light">Light Model (Fast)</Label>
                        <Input
                          id="openai-light"
                          value={llmForm.models.openai.light}
                          onChange={(e) => updateModelConfig("openai", "light", e.target.value)}
                          placeholder="e.g., gpt-4o-mini"
                        />
                        <p className="text-xs text-muted-foreground">
                          Used for quick, simple tasks
                        </p>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="openai-full">Full Model (Complex)</Label>
                        <Input
                          id="openai-full"
                          value={llmForm.models.openai.full}
                          onChange={(e) => updateModelConfig("openai", "full", e.target.value)}
                          placeholder="e.g., gpt-4o"
                        />
                        <p className="text-xs text-muted-foreground">
                          Used for complex reasoning tasks
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 pt-2">
                      {llmForm.provider !== "openai" && (
                        <Button
                          variant="outline"
                          onClick={() => setActiveProvider("openai")}
                        >
                          Set as Active Provider
                        </Button>
                      )}
                      <Button onClick={saveLlmSettings} disabled={saving}>
                        {saving ? (
                          <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                        ) : saveSuccess === "llm" ? (
                          <CheckCircleIcon className="h-4 w-4 mr-2 text-emerald-500" />
                        ) : null}
                        Save Changes
                      </Button>
                    </div>
                  </TabsContent>
                </Tabs>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Database Tab */}
        <TabsContent value="database" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Database Settings</CardTitle>
              <CardDescription>
                PostgreSQL connection configuration. Changes are saved to vulcanlab.config.json.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {dbForm && (
                <>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="db-host">Host</Label>
                      <Input
                        id="db-host"
                        value={dbForm.host}
                        onChange={(e) => setDbForm({ ...dbForm, host: e.target.value })}
                        placeholder="127.0.0.1"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="db-port">Port</Label>
                      <Input
                        id="db-port"
                        type="number"
                        value={dbForm.port}
                        onChange={(e) => setDbForm({ ...dbForm, port: parseInt(e.target.value) || 5432 })}
                        placeholder="5432"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="db-name">Database Name</Label>
                    <Input
                      id="db-name"
                      value={dbForm.db_name}
                      onChange={(e) => setDbForm({ ...dbForm, db_name: e.target.value })}
                      placeholder="psych_rag"
                    />
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="db-admin-user">Admin User</Label>
                      <Input
                        id="db-admin-user"
                        value={dbForm.admin_user}
                        onChange={(e) => setDbForm({ ...dbForm, admin_user: e.target.value })}
                        placeholder="postgres"
                      />
                      <p className="text-xs text-muted-foreground">
                        Used for database/user creation
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="db-app-user">Application User</Label>
                      <Input
                        id="db-app-user"
                        value={dbForm.app_user}
                        onChange={(e) => setDbForm({ ...dbForm, app_user: e.target.value })}
                        placeholder="psych_rag_app_user"
                      />
                      <p className="text-xs text-muted-foreground">
                        Used by the application at runtime
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 pt-2">
                    <Button onClick={saveDbSettings} disabled={saving}>
                      {saving ? (
                        <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                      ) : saveSuccess === "database" ? (
                        <CheckCircleIcon className="h-4 w-4 mr-2 text-emerald-500" />
                      ) : null}
                      Save Changes
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Paths Tab */}
        <TabsContent value="paths" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>File System Paths</CardTitle>
              <CardDescription>
                Configure input and output directory paths. Must be absolute paths.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {pathsForm && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="paths-input">Input Directory</Label>
                    <Input
                      id="paths-input"
                      value={pathsForm.input_dir}
                      onChange={(e) => setPathsForm({ ...pathsForm, input_dir: e.target.value })}
                      placeholder="C:\code\python\vulcanlab-test\input"
                    />
                    <p className="text-xs text-muted-foreground">
                      Absolute path to the input directory (e.g., C:\path\to\input or /path/to/input)
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="paths-output">Output Directory</Label>
                    <Input
                      id="paths-output"
                      value={pathsForm.output_dir}
                      onChange={(e) => setPathsForm({ ...pathsForm, output_dir: e.target.value })}
                      placeholder="C:\code\python\vulcanlab-test\output"
                    />
                    <p className="text-xs text-muted-foreground">
                      Absolute path to the output directory (e.g., C:\path\to\output or /path/to/output)
                    </p>
                  </div>
                  <div className="flex items-center gap-3 pt-2">
                    <Button onClick={savePathsSettings} disabled={saving}>
                      {saving ? (
                        <Loader2Icon className="h-4 w-4 animate-spin mr-2" />
                      ) : saveSuccess === "paths" ? (
                        <CheckCircleIcon className="h-4 w-4 mr-2 text-emerald-500" />
                      ) : null}
                      Save Changes
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Conversion Tab */}
        <TabsContent value="conversion" className="mt-4">
          <ConversionTab />
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="mt-4">
          <TemplatesTabContent />
        </TabsContent>

        {/* RAG Settings Tab */}
        <TabsContent value="rag" className="mt-4">
          <RagConfigTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-64">
        <Loader2Icon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    }>
      <SettingsContent />
    </Suspense>
  );
}
