import { apiClient } from "@/lib/api-client";
import type { Repository } from "@/types";

export const repositoriesService = {
  getRepositories(): Promise<Repository[]> {
    return apiClient.get<Repository[]>("/api/repos/repositories");
  },
};
