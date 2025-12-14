"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { InfoIcon } from "lucide-react";

/**
 * Simple Conversion Page (Placeholder)
 *
 * This is a temporary placeholder component for T08 testing.
 * Will be fully implemented in T09.
 */
export default function SimpleConversionPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Simple Conversion</h2>
        <p className="text-muted-foreground">Streamlined document conversion workflow.</p>
      </div>

      <Card className="border-amber-500/20 bg-amber-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-amber-600">
            <InfoIcon className="h-5 w-5" />
            Coming Soon
          </CardTitle>
          <CardDescription>
            This page is currently under development.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            The Simple Conversion workflow is being implemented and will provide:
          </p>
          <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground ml-4">
            <li>Single-page conversion workflow</li>
            <li>Automatic document processing</li>
            <li>Streamlined sanitization and chunking</li>
            <li>Both automatic and manual execution modes</li>
          </ul>
          <div className="pt-4 border-t border-border mt-6">
            <p className="text-xs text-muted-foreground italic">
              Placeholder for T08 testing. Full implementation coming in T09.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>What to Expect</CardTitle>
          <CardDescription>
            Features planned for the Simple Conversion workflow
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-500/10 flex items-center justify-center text-green-600 font-semibold text-sm">
              1
            </div>
            <div>
              <h4 className="font-medium text-sm">Upload Document</h4>
              <p className="text-sm text-muted-foreground">
                Select and upload your PDF or EPUB file with metadata
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-500/10 flex items-center justify-center text-green-600 font-semibold text-sm">
              2
            </div>
            <div>
              <h4 className="font-medium text-sm">Automatic Processing</h4>
              <p className="text-sm text-muted-foreground">
                Choose between fully automatic or manual LLM-guided sanitization
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-500/10 flex items-center justify-center text-green-600 font-semibold text-sm">
              3
            </div>
            <div>
              <h4 className="font-medium text-sm">View Results</h4>
              <p className="text-sm text-muted-foreground">
                Review generated chunks and proceed to vectorization
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
