"use client";

import Link from "next/link";
import { ArrowRight, GitPullRequest } from "lucide-react";

import { usePullRequests } from "@/hooks/usePullRequests";
import { formatRelativeTime } from "@/lib/format";
import { splitRepoName } from "@/lib/format";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { PullRequest, Repository } from "@/types";

function lastReviewedAt(prs: PullRequest[]): string | null {
  let latest = 0;
  for (const pr of prs) {
    if (!pr.last_reviewed_at) continue;
    const t = new Date(pr.last_reviewed_at).getTime();
    if (!Number.isNaN(t) && t > latest) latest = t;
  }
  return latest ? new Date(latest).toISOString() : null;
}

/**
 * Repository summary card. Fetches its own PR list to show a live count + last
 * reviewed time. Cached by TanStack Query, so opening the repo is instant.
 */
export function RepositoryCard({ repository }: { repository: Repository }) {
  const { data: prs, isPending } = usePullRequests(repository.id);
  const { owner, name } = splitRepoName(repository.full_name);

  return (
    <Card className="flex flex-col justify-between p-5 transition-colors hover:border-foreground/20">
      <div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="truncate">{owner}</span>
        </div>
        <h3 className="mt-0.5 truncate text-base font-semibold tracking-tight">
          {name}
        </h3>

        <div className="mt-4 flex items-center gap-4 text-sm text-muted-foreground">
          {isPending ? (
            <Skeleton className="h-4 w-32" />
          ) : (
            <>
              <span className="inline-flex items-center gap-1.5">
                <GitPullRequest className="h-4 w-4" />
                {prs?.length ?? 0} PR{(prs?.length ?? 0) === 1 ? "" : "s"}
              </span>
              <span>·</span>
              <span>Reviewed {formatRelativeTime(lastReviewedAt(prs ?? []))}</span>
            </>
          )}
        </div>
      </div>

      <div className="mt-5">
        <Button asChild variant="outline" size="sm">
          <Link href={`/repos/${repository.id}`}>
            Open
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    </Card>
  );
}
