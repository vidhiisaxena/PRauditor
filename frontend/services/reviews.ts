import { apiClient, NotImplementedError } from "@/lib/api-client";
import type { AddCommentInput, ReviewComment, ReviewIssue } from "@/types";

/**
 * Reviews service. `getReviewIssues` is live. Comments map to endpoints the
 * backend does not have yet.
 */
export const reviewsService = {
  /**
   * GET /api/prs/{prId}/issues  ->  ReviewIssue[]
   * Implemented: exists on the backend today.
   */
  getReviewIssues(prId: number): Promise<ReviewIssue[]> {
    return apiClient.get<ReviewIssue[]>(`/api/prs/${prId}/issues`);
  },

  /**
   * List comments for a PR's review.
   * TODO(backend): GET /api/prs/{prId}/comments -> ReviewComment[]
   * Comments are non-critical, so failures resolve to [] rather than erroring
   * the whole review screen.
   */
  async getComments(prId: number): Promise<ReviewComment[]> {
    try {
      return await apiClient.get<ReviewComment[]>(`/api/prs/${prId}/comments`);
    } catch {
      return [];
    }
  },

  /**
   * Add a comment to a finding.
   * TODO(backend): POST /api/prs/{prId}/comments  body: { issueId, body }
   */
  async addComment(prId: number, input: AddCommentInput): Promise<ReviewComment> {
    // return apiClient.post<ReviewComment>(`/api/prs/${prId}/comments`, input);
    void input;
    throw new NotImplementedError(`POST /api/prs/${prId}/comments`);
  },

  /**
   * Apply a suggested fix (commit the patch to the PR branch).
   * TODO(backend): POST /api/prs/{prId}/issues/{issueId}/apply -> { committed: boolean }
   */
  applySuggestion(prId: number, issueId: number): Promise<{ committed: boolean }> {
    throw new NotImplementedError(
      `POST /api/prs/${prId}/issues/${issueId}/apply`,
    );
  },
};
