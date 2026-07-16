"use client";

import { useQuery } from "@tanstack/react-query";

import { reviewsService } from "@/services/reviews";
import { queryKeys } from "@/hooks/queryKeys";
import type { ReviewIssue } from "@/types";

/** Fetch the review issues for a pull request. */
export function useReviewIssues(prId: number | undefined) {
  return useQuery<ReviewIssue[]>({
    queryKey: prId ? queryKeys.reviewIssues(prId) : ["prs", "pending", "issues"],
    queryFn: () => reviewsService.getReviewIssues(prId as number),
    enabled: typeof prId === "number" && !Number.isNaN(prId),
  });
}
