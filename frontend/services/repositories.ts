import { apiClient } from "@/lib/api-client";
import type { Repository } from "@/types";

/**
 * Repository service. Maps 1:1 to backend repository endpoints.
 * Pages/components must go through hooks, never call this directly.
 */
export const repositoriesService = {
  /**
   * GET /api/repos  ->  Repository[]
   * Implemented: this endpoint exists on the backend today.
   */
  getRepositories(): Promise<Repository[]> {
    return apiClient.get<Repository[]>("/api/repos");
  },

  // TODO(backend): No single-repository endpoint exists yet.
  // Expected: GET /api/repos/{repoId} -> Repository
  // getRepository(repoId: number): Promise<Repository> {
  //   return apiClient.get<Repository>(`/api/repos/${repoId}`);
  // },
};
