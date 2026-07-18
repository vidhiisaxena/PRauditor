import {apiClient, NotImplementedError } from "@/lib/api-client";
import type { PullRequest } from "@/types";

//The shape the backend sends back when you trigger a re-review
export interface RerunReviewResponse {
  pr_id: number;
  reviewed: boolean;
  issues: number;
}

export const pullRequestsService = {
  getPullRequests(repoId: number): Promise<PullRequest[]> {
    return apiClient.get(`/api/repos/${repoId}/prs`);
  },

  getPullRequest(prId: number): Promise<PullRequest> {
    throw new NotImplementedError(`GET /api/prs/${prId}`);
  },

  rerunReview(prId: number): Promise<RerunReviewResponse> {
    throw new NotImplementedError(`POST /api/prs/${prId}/rerun`);
  }, 

  mergePullRequest(prId: number): Promise<{merged:boolean}>{
    throw new NotImplementedError(`POST /api/prs/${prId}/merge`);
  },
};