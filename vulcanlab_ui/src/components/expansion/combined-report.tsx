"use client";

import { MarkdownEditor } from "@/components/markdown-editor";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CombinedReportProps {
  report: string;
  originalResultLink?: string;
}

export function CombinedReport({ report, originalResultLink }: CombinedReportProps) {
  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between border-b bg-muted/30">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          <CardTitle>Final Combined Report</CardTitle>
        </div>
        {originalResultLink && (
          <Button variant="outline" size="sm" asChild className="gap-2">
            <a href={originalResultLink}>
              <ArrowLeft className="h-4 w-4" />
              Original Answer
            </a>
          </Button>
        )}
      </CardHeader>
      <CardContent className="p-0">
        <div className="prose prose-sm dark:prose-invert max-w-none p-6 md:p-10 min-h-[500px]">
          <MarkdownEditor
            content={report}
            readOnly={true}
            viewMode="preview"
            scrollMode="page"
            processSources={true}
          />
        </div>
      </CardContent>
    </Card>
  );
}
