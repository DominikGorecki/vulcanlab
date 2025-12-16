/**
 * Error Boundary for Simple Conversion History Section
 *
 * Catches rendering errors in history components to prevent full page crash.
 * Displays user-friendly fallback UI with error message.
 */

"use client";

import React, { Component, ReactNode } from 'react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class HistoryErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to console for debugging
    console.error('History section error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="py-8" data-testid="history-error-boundary">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Unable to load conversion history</AlertTitle>
            <AlertDescription>
              An error occurred while displaying the conversion history. Please refresh the page to try again.
              {this.state.error && (
                <div className="mt-2 text-xs font-mono opacity-75">
                  {this.state.error.message}
                </div>
              )}
            </AlertDescription>
          </Alert>
        </div>
      );
    }

    return this.props.children;
  }
}
