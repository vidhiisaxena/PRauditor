import { apiClient, NotImplementedError } from "@/lib/api-client";
import type { PullRequest } from "@/types";

/** Request payload for the future rerun endpoint. */
export interface RerunReviewResponse {
  pr_id: number;
  reviewed: boolean;
  issues: number;
}

/**
 * Pull request service. `getPullRequests` is live; action endpoints are
 * stubbed until the backend implements them (see roadmap Stage 3–5).
 */
export const pullRequestsService = {
  /**
   * GET /api/repos/{repoId}/prs  ->  PullRequest[]
   * Implemented: exists on the backend today.
   */
  getPullRequests(repoId: number): Promise<PullRequest[]> {
    return apiClient.get<PullRequest[]>(`/api/repos/${repoId}/prs`);
  },

  // TODO(backend): No single-PR endpoint exists yet. The review page currently
  // derives PR metadata from its issues. Wire this up when available.
  // Expected: GET /api/prs/{prId} -> PullRequest
  getPullRequest(prId: number): Promise<PullRequest> {
    throw new NotImplementedError(`GET /api/prs/${prId}`);
  },

  /**
   * TODO(backend): Trigger a fresh review.
   * Expected: POST /api/prs/{prId}/rerun -> RerunReviewResponse
   */
  rerunReview(prId: number): Promise<RerunReviewResponse> {
    // return apiClient.post<RerunReviewResponse>(`/api/prs/${prId}/rerun`);
    throw new NotImplementedError(`POST /api/prs/${prId}/rerun`);
  },

  /**
   * TODO(backend): Merge the pull request.
   * Expected: POST /api/prs/{prId}/merge -> { merged: boolean }
   */
  mergePullRequest(prId: number): Promise<{ merged: boolean }> {
    // return apiClient.post<{ merged: boolean }>(`/api/prs/${prId}/merge`);
    throw new NotImplementedError(`POST /api/prs/${prId}/merge`);
  },
};
