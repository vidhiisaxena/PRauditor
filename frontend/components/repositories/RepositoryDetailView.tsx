"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ChevronLeft } from "lucide-react";

import { useRepositories } from "@/hooks/useRepositories";
import { usePullRequests } from "@/hooks/usePullRequests";
import { PageHeader } from "@/components/common/PageHeader";
import { SearchInput } from "@/components/common/SearchInput";
import { ErrorCard } from "@/components/common/ErrorCard";
import { ListSkeleton } from "@/components/common/LoadingSkeleton";
import { PullRequestList } from "@/components/pullrequests/PullRequestList";
import type { PullRequest } from "@/types";

interface RepositoryDetailViewProps {
  repoId: number;
}

function matches(pr: PullRequest, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return (
    (pr.title?.toLowerCase().includes(q) ?? false) ||
    String(pr.pr_number).includes(q)
  );
}

/** Repository detail route container: repo header + its pull requests. */
export function RepositoryDetailView({ repoId }: RepositoryDetailViewProps) {
  // No single-repo endpoint yet; resolve the name from the cached list.
  // TODO(backend): replace with GET /api/repos/{repoId} when available.
  const { data: repositories } = useRepositories();
  const repo = repositories?.find((r) => r.id === repoId);

  const { data: prs, isPending, isError, error, refetch } =
    usePullRequests(repoId);
  const [query, setQuery] = useState("");

  const filtered = useMemo(
    () => (prs ?? []).filter((pr) => matches(pr, query)),
    [prs, query],
  );

  return (
    <div>
      <PageHeader
        eyebrow={
          <Link
            href="/repos"
            className="inline-flex items-center gap-1 text-muted-foreground transition-colors hover:text-foreground"
          >
            <ChevronLeft className="h-4 w-4" />
            Repositories
          </Link>
        }
        title={repo?.full_name ?? `Repository #${repoId}`}
        description="Pull requests reviewed by PRAuditor in this repository."
        actions={
          prs && prs.length > 0 ? (
            <SearchInput
              value={query}
              onChange={setQuery}
              placeholder="Search pull requests…"
              aria-label="Search pull requests"
              className="w-full sm:w-64"
            />
          ) : null
        }
      />

      {isError ? (
        <ErrorCard error={error} onRetry={() => refetch()} />
      ) : isPending ? (
        <ListSkeleton count={5} />
      ) : (
        <PullRequestList pullRequests={filtered} />
      )}
    </div>
  );
}
