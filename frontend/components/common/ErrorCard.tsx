"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";

import { cn } from "@/lib/utils";
import { ApiError, NotImplementedError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";

interface ErrorCardProps {
  error?: unknown;
  title?: string;
  onRetry?: () => void;
  className?: string;
}

function messageFor(error: unknown): string {
  if (error instanceof NotImplementedError) {
    return "This feature is waiting on a backend endpoint.";
  }
  if (error instanceof ApiError) {
    if (error.status === 0) {
      return "Could not reach the backend. Is the API running?";
    }
    return `The server responded with ${error.status}.`;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong while loading this data.";
}

/** Inline error panel with an optional retry action. */
export function ErrorCard({
  error,
  title = "Failed to load",
  onRetry,
  className,
}: ErrorCardProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-destructive/30 bg-destructive/5 px-6 py-12 text-center",
        className,
      )}
    >
      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-full bg-destructive/10 text-destructive">
        <AlertTriangle className="h-5 w-5" />
      </div>
      <h3 className="text-sm font-medium text-foreground">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">
        {messageFor(error)}
      </p>
      {onRetry ? (
        <Button variant="outline" size="sm" className="mt-5" onClick={onRetry}>
          <RefreshCw className="h-4 w-4" />
          Try again
        </Button>
      ) : null}
    </div>
  );
}
