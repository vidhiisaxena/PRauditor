"use client";

import { useState } from "react";
import { ChevronDown, FileCode } from "lucide-react";

import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { IssueCard } from "@/components/reviews/IssueCard";
import type { FileIssueGroup } from "@/types";

interface FileIssueSectionProps {
  prId: number;
  group: FileIssueGroup;
  defaultOpen?: boolean;
}

/** Collapsible per-file section listing that file's issues. Keyboard accessible. */
export function FileIssueSection({
  prId,
  group,
  defaultOpen = true,
}: FileIssueSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const { critical, major, minor, info } = group.counts;
  const contentId = `file-issues-${group.filePath.replace(/[^a-z0-9]/gi, "-")}`;

  return (
    <Card className="overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={contentId}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition-colors hover:bg-muted/40"
      >
        <div className="flex min-w-0 items-center gap-2">
          <FileCode className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
          <span className="truncate font-mono text-sm font-medium">
            {group.filePath}
          </span>
        </div>
        <div className="flex flex-shrink-0 items-center gap-3">
          <span className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex">
            {critical > 0 && <CountPill className="text-red-600 dark:text-red-400" label={`${critical} critical`} />}
            {major > 0 && <CountPill className="text-orange-600 dark:text-orange-400" label={`${major} major`} />}
            {minor > 0 && <CountPill className="text-amber-600 dark:text-amber-400" label={`${minor} minor`} />}
            {info > 0 && <CountPill className="text-blue-600 dark:text-blue-400" label={`${info} info`} />}
          </span>
          <span className="text-xs text-muted-foreground">
            {group.issues.length}
          </span>
          <ChevronDown
            className={cn(
              "h-4 w-4 text-muted-foreground transition-transform",
              open && "rotate-180",
            )}
          />
        </div>
      </button>

      {open ? (
        <div id={contentId}>
          {group.issues.map((issue) => (
            <IssueCard key={issue.id} prId={prId} issue={issue} />
          ))}
        </div>
      ) : null}
    </Card>
  );
}

function CountPill({ label, className }: { label: string; className?: string }) {
  return <span className={cn("font-medium", className)}>{label}</span>;
}
