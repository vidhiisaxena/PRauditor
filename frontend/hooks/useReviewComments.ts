"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { reviewsService } from "@/services/reviews";
import { queryKeys } from "@/hooks/queryKeys";
import type { AddCommentInput, ReviewComment } from "@/types";

/** All comments for a PR's review (filter by issueId in the component). */
export function useReviewComments(prId: number) {
  return useQuery<ReviewComment[]>({
    queryKey: queryKeys.reviewComments(prId),
    queryFn: () => reviewsService.getComments(prId),
  });
}

/** Add a comment to a finding and refresh the thread. */
export function useAddComment(prId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: AddCommentInput) =>
      reviewsService.addComment(prId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.reviewComments(prId),
      });
    },
  });
}
