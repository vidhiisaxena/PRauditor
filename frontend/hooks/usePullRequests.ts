"use client";

import { useQuery } from "@tanstack/react-query";

import { pullRequestsService } from "@/services/pullRequests";
import { queryKeys } from "@/hooks/queryKeys";
import type { PullRequest } from "@/types";

/** Fetch pull requests for a repository. */
export function usePullRequests(repoId: number | undefined) {
  return useQuery<PullRequest[]>({
    queryKey: repoId ? queryKeys.pullRequests(repoId) : ["repositories", "pending", "prs"],
    queryFn: () => pullRequestsService.getPullRequests(repoId as number),
    enabled: typeof repoId === "number" && !Number.isNaN(repoId),
  });
}
