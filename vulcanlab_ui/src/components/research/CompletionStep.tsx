"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, FileText, ArrowRight, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { MarkdownRenderer } from "@/components/markdown-renderer";

interface CompletionStepProps {
  collectionId: number;
  sessionId: number;
  reportContent: string;
  onClose: () => void;
  onRestart: () => void;
}

export function CompletionStep({
  collectionId,
  sessionId,
  reportContent,
  onClose,
  onRestart,
}: CompletionStepProps) {
  const router = useRouter();
  const previewContent = reportContent.slice(0, 500) + (reportContent.length > 500 ? "..." : "");

  return (
    <div className="flex flex-col items-center justify-center space-y-8 py-8 max-w-2xl mx-auto">
      <div className="text-center space-y-3">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 mb-2">
          <CheckCircle2 className="h-10 w-10" />
        </div>
        <h2 className="text-3xl font-bold tracking-tight">Research Completed!</h2>
        <p className="text-muted-foreground text-lg">
          Your final research report has been synthesized and saved to the collection.
        </p>
      </div>

      <Card className="w-full border-primary/10">
        <CardHeader className="bg-muted/30 pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <FileText className="h-4 w-4 text-primary" />
            Report Preview
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="prose prose-sm dark:prose-invert max-h-60 overflow-y-auto">
            <MarkdownRenderer content={previewContent} />
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
        <Button 
          variant="default" 
          className="w-full py-6 text-lg" 
          onClick={() => {
            onClose();
            router.push(`/collections/${collectionId}/report/${sessionId}`);
          }}
        >
          View Full Report
          <ArrowRight className="h-5 w-5 ml-2" />
        </Button>
        <Button variant="outline" onClick={onRestart} className="w-full py-6 text-lg">
          Start New Research
        </Button>
      </div>

      <Button variant="ghost" onClick={onClose} className="text-muted-foreground">
        <X className="h-4 w-4 mr-2" />
        Close Wizard
      </Button>
    </div>
  );
}
