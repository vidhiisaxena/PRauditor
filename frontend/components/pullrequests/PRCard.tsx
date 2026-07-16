import Link from "next/link";
import { ArrowRight, GitPullRequest } from "lucide-react";

import { formatRelativeTime } from "@/lib/format";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/common/StatusBadge";
import { RiskScore } from "@/components/common/RiskScore";
import type { PullRequest } from "@/types";

/**
 * Row-style card for a pull request within a repository.
 * Risk is a placeholder until the backend Risk Scoring agent exists.
 */
export function PRCard({ pr }: { pr: PullRequest }) {
  const reviewed = pr.last_reviewed_at !== null;

  return (
    <Card className="flex flex-col gap-4 p-4 transition-colors hover:border-foreground/20 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 items-start gap-3">
        <div className="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
          <GitPullRequest className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground">
              #{pr.pr_number}
            </span>
            <StatusBadge state={pr.state} />
          </div>
          <p className="mt-0.5 truncate text-sm font-medium">
            {pr.title ?? `Pull request #${pr.pr_number}`}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {reviewed
              ? `Reviewed ${formatRelativeTime(pr.last_reviewed_at)}`
              : "Not reviewed yet"}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between gap-6 sm:justify-end">
        {/* TODO(backend): real risk from Risk Scoring agent. */}
        <div className="w-28">
          <RiskScore score={null} level={reviewed ? "low" : null} />
        </div>
        <Button asChild variant="outline" size="sm" disabled={!reviewed}>
          {reviewed ? (
            <Link href={`/prs/${pr.id}`}>
              Review
              <ArrowRight className="h-4 w-4" />
            </Link>
          ) : (
            <span>Review</span>
          )}
        </Button>
      </div>
    </Card>
  );
}
