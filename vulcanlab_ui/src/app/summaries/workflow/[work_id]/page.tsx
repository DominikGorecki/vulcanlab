"use client"

import * as React from "react"
import { useParams, useRouter } from "next/navigation"
import { useCallback, useState } from "react"
import {
  Copy,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Eye,
  LayoutGrid
} from "lucide-react"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Progress } from "@/components/ui/progress"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import { usePageData } from "@/hooks/use-page-data"
import { StickyDetailHeader } from "@/components/sticky-detail-header"
import { PageLoadingState } from "@/components/page-loading-state"
import { PageErrorState } from "@/components/page-error-state"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Workflow states for the summarization process
 */
type WorkflowState =
  | "PREPARE"
  | "GENERATING"
  | "PROMPT_DISPLAY"
  | "SUBMITTING"
  | "COMPLETE"
  | "ERROR"

interface HeadingPreview {
  chunk_id: number
  level: number
  title: string
  start_line: number
  content_word_count: number
}

interface PrepareResponse {
  headings: HeadingPreview[]
  total_prompts: number
  estimated_tokens: number
  has_existing_summaries: boolean
}

interface Prompt {
  prompt_index: number
  content: string
  heading_ids: number[]
}

interface GeneratePromptsResponse {
  prompts: Prompt[]
}

interface SubmitResponseResponse {
  success: boolean
  summaries_saved: number
  errors: string[]
}

export default function SummarizationWorkflowPage() {
  const { work_id } = useParams<{ work_id: string }>()
  const router = useRouter()
  const { toast } = useToast()

  // State Management
  const [workflowState, setWorkflowState] = useState<WorkflowState>("PREPARE")
  const [regenerate, setRegenerate] = useState(false)
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [currentPromptIndex, setCurrentPromptIndex] = useState(0)
  const [llmResponse, setLlmResponse] = useState("")
  const [summariesSavedTotal, setSummariesSavedTotal] = useState(0)
  const [submitError, setSubmitError] = useState<string | null>(null)

  // Initial Data Fetching (Prepare Phase)
  const fetchPrepareData = useCallback(async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/summarize/works/${work_id}/prepare`, {
      method: "POST",
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "Failed to prepare summarization")
    }
    return response.json() as Promise<PrepareResponse>
  }, [work_id])

  const { data: prepareData, loading: prepareLoading, error: prepareError, refetch: refetchPrepare } = usePageData(fetchPrepareData)

  // Handlers
  const handleGeneratePrompts = async () => {
    setWorkflowState("GENERATING")
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/summarize/works/${work_id}/generate-prompts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ regenerate_all: regenerate }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Failed to generate prompts")
      }

      const data = (await response.json()) as GeneratePromptsResponse
      setPrompts(data.prompts)
      setCurrentPromptIndex(0)
      setWorkflowState("PROMPT_DISPLAY")
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : String(err))
      setWorkflowState("ERROR")
    }
  }

  const handleCopyPrompt = () => {
    const currentPrompt = prompts[currentPromptIndex]
    if (currentPrompt) {
      navigator.clipboard.writeText(currentPrompt.content)
      toast({
        title: "Copied to clipboard",
        description: "The prompt has been copied to your clipboard.",
      })
    }
  }

  const handleSubmitResponse = async () => {
    if (!llmResponse.trim()) {
      toast({
        title: "Empty response",
        description: "Please paste the LLM response before submitting.",
        variant: "destructive",
      })
      return
    }

    setWorkflowState("SUBMITTING")
    setSubmitError(null)

    try {
      // Parse LLM response to ensure it's valid JSON
      let responseJson: any
      try {
        // Try to extract JSON if it's wrapped in markdown code blocks
        const jsonMatch = llmResponse.match(/```json\n([\s\S]*?)\n```/) || llmResponse.match(/```\n([\s\S]*?)\n```/)
        const jsonText = jsonMatch ? jsonMatch[1] : llmResponse
        responseJson = JSON.parse(jsonText)
      } catch (e) {
        throw new Error("Failed to parse LLM response as JSON. Please ensure the response is valid JSON.")
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/summarize/works/${work_id}/submit-response`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt_index: prompts[currentPromptIndex].prompt_index,
          response_json: JSON.stringify(responseJson),
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Failed to submit response")
      }

      const result = (await response.json()) as SubmitResponseResponse
      
      if (!result.success) {
        setSubmitError(result.errors.join(", "))
        setWorkflowState("PROMPT_DISPLAY")
        return
      }

      setSummariesSavedTotal((prev) => prev + result.summaries_saved)
      setLlmResponse("")

      if (currentPromptIndex < prompts.length - 1) {
        setCurrentPromptIndex((prev) => prev + 1)
        setWorkflowState("PROMPT_DISPLAY")
        toast({
          title: "Response saved",
          description: `Saved ${result.summaries_saved} summaries. Moving to next prompt.`,
        })
      } else {
        setWorkflowState("COMPLETE")
      }
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : String(err))
      setWorkflowState("PROMPT_DISPLAY")
      toast({
        title: "Submission failed",
        description: err instanceof Error ? err.message : String(err),
        variant: "destructive",
      })
    }
  }

  // Render Logic
  if (prepareLoading) {
    return <PageLoadingState title="Preparing Summarization..." />
  }

  if (prepareError) {
    return <PageErrorState error={prepareError} onRetry={refetchPrepare} />
  }

  if (!prepareData) {
    return null
  }

  const progressValue = prompts.length > 0 ? ((currentPromptIndex) / prompts.length) * 100 : 0

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <StickyDetailHeader
        title="Summarization Workflow"
        subtitle={`Work ID: ${work_id}`}
        backUrl="/corpus"
        backLabel="Back to Corpus"
      />

      <main className="flex-1 p-6 max-w-5xl mx-auto w-full space-y-6">
        {/* PREPARE PHASE */}
        {workflowState === "PREPARE" && (
          <Card>
            <CardHeader>
              <CardTitle>Prepare Summarization</CardTitle>
              <CardDescription>
                Review the scope of the summarization task before generating prompts.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 border rounded-lg bg-muted/30">
                  <div className="text-sm text-muted-foreground">Headings to Summarize</div>
                  <div className="text-2xl font-bold">{prepareData.headings.length}</div>
                </div>
                <div className="p-4 border rounded-lg bg-muted/30">
                  <div className="text-sm text-muted-foreground">Estimated Prompts</div>
                  <div className="text-2xl font-bold">{prepareData.total_prompts}</div>
                </div>
                <div className="p-4 border rounded-lg bg-muted/30">
                  <div className="text-sm text-muted-foreground">Estimated Tokens</div>
                  <div className="text-2xl font-bold">{prepareData.estimated_tokens.toLocaleString()}</div>
                </div>
              </div>

              {prepareData.has_existing_summaries && (
                <div className="flex items-center space-x-2 p-4 border border-yellow-200 bg-yellow-50 dark:bg-yellow-950/20 dark:border-yellow-900/50 rounded-lg text-yellow-800 dark:text-yellow-200">
                  <Checkbox
                    id="regenerate"
                    checked={regenerate}
                    onCheckedChange={(checked) => setRegenerate(checked === true)}
                  />
                  <label
                    htmlFor="regenerate"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                  >
                    Regenerate all summaries (existing summaries for this work will be deleted)
                  </label>
                </div>
              )}

              <div className="space-y-2">
                <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Heading Preview</h3>
                <div className="max-h-[300px] overflow-y-auto border rounded-md divide-y">
                  {prepareData.headings.map((h) => (
                    <div key={h.chunk_id} className="p-3 flex justify-between items-center text-sm">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground font-mono text-xs">L{h.level}</span>
                        <span className="font-medium truncate max-w-[400px]">{h.title}</span>
                      </div>
                      <span className="text-muted-foreground text-xs">{h.content_word_count} words</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button onClick={handleGeneratePrompts} className="w-full sm:w-auto">
                Generate Prompts
              </Button>
            </CardFooter>
          </Card>
        )}

        {/* GENERATING PHASE */}
        {workflowState === "GENERATING" && (
          <Card className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
            <CardTitle>Assembling Prompts...</CardTitle>
            <CardDescription>Ranking chunks and building your summarization workflow.</CardDescription>
          </Card>
        )}

        {/* PROMPT DISPLAY PHASE */}
        {(workflowState === "PROMPT_DISPLAY" || workflowState === "SUBMITTING") && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h2 className="text-xl font-bold">Step {currentPromptIndex + 1} of {prompts.length}</h2>
                <p className="text-sm text-muted-foreground">
                  Follow the instructions below to generate summaries with your LLM.
                </p>
              </div>
              <div className="text-right">
                <span className="text-sm font-medium">{Math.round(progressValue)}% Complete</span>
              </div>
            </div>
            
            <Progress value={progressValue} className="h-2" />

            {submitError && (
              <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive flex gap-3 items-start">
                <AlertCircle className="size-5 shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-bold">Submission Error</p>
                  <p>{submitError}</p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 gap-6">
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg">1. Copy Prompt</CardTitle>
                      <CardDescription>Copy this content and paste it into your external LLM (Claude, ChatGPT, etc.)</CardDescription>
                    </div>
                    <Button variant="outline" size="sm" onClick={handleCopyPrompt} className="gap-2">
                      <Copy className="size-4" />
                      Copy to Clipboard
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <Textarea
                    readOnly
                    value={prompts[currentPromptIndex]?.content || ""}
                    className="font-mono text-xs bg-muted/50 h-[300px] resize-none"
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">2. Paste LLM Response</CardTitle>
                  <CardDescription>Copy the JSON response from your LLM and paste it here.</CardDescription>
                </CardHeader>
                <CardContent>
                  <Textarea
                    placeholder='Paste JSON response here... e.g. [{"chunk_id": 123, "summary_content": "..."}]'
                    value={llmResponse}
                    onChange={(e) => setLlmResponse(e.target.value)}
                    className="font-mono text-xs h-[200px]"
                    disabled={workflowState === "SUBMITTING"}
                  />
                </CardContent>
                <CardFooter>
                  <Button 
                    onClick={handleSubmitResponse} 
                    className="w-full gap-2" 
                    disabled={workflowState === "SUBMITTING" || !llmResponse.trim()}
                  >
                    {workflowState === "SUBMITTING" ? (
                      <>
                        <Loader2 className="size-4 animate-spin" />
                        Saving Summaries...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="size-4" />
                        Submit Response
                      </>
                    )}
                  </Button>
                </CardFooter>
              </Card>
            </div>
          </div>
        )}

        {/* COMPLETE PHASE */}
        {workflowState === "COMPLETE" && (
          <Card className="text-center py-12">
            <CardHeader>
              <div className="flex justify-center mb-4">
                <div className="p-4 bg-green-100 dark:bg-green-900/30 rounded-full">
                  <CheckCircle2 className="size-12 text-green-600 dark:text-green-400" />
                </div>
              </div>
              <CardTitle className="text-3xl">Summarization Complete!</CardTitle>
              <CardDescription className="text-lg">
                Successfully processed all prompts and saved summaries.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="p-6 bg-muted/30 rounded-lg inline-block text-left">
                <div className="flex items-center gap-6">
                  <div>
                    <div className="text-sm text-muted-foreground">Total Sections Summarized</div>
                    <div className="text-3xl font-bold">{summariesSavedTotal}</div>
                  </div>
                  <div className="h-12 w-px bg-border" />
                  <div>
                    <div className="text-sm text-muted-foreground">Status</div>
                    <div className="text-xl font-medium">All Sections Saved</div>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button asChild className="gap-2">
                <Link href={`/summaries/${work_id}`}>
                  <Eye className="size-4" />
                  View Summary
                </Link>
              </Button>
              <Button asChild variant="outline" className="gap-2">
                <Link href="/corpus">
                  <LayoutGrid className="size-4" />
                  Return to Corpus
                </Link>
              </Button>
            </CardFooter>
          </Card>
        )}

        {/* ERROR STATE */}
        {workflowState === "ERROR" && (
          <Card className="border-destructive">
            <CardHeader>
              <div className="flex items-center gap-2 text-destructive">
                <AlertCircle className="size-5" />
                <CardTitle>An error occurred</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{submitError || "A failure occurred during the workflow."}</p>
            </CardContent>
            <CardFooter>
              <Button onClick={() => setWorkflowState("PREPARE")} variant="outline">
                Back to Preparation
              </Button>
            </CardFooter>
          </Card>
        )}
      </main>
    </div>
  )
}
