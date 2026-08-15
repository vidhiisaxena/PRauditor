"use client";

import { useQuery } from "@tanstack/react-query";

import { repositoriesService } from "@/services/repositories";
import { queryKeys } from "@/hooks/queryKeys";
import type { Repository } from "@/types";

/** Fetch the repositories visible to the signed-in user's GitHub installation. */
export function useRepositories() {
  return useQuery<Repository[]>({
    queryKey: queryKeys.repositories,
    queryFn: () => repositoriesService.getRepositories(),
    refetchInterval: (query) => {
      const repositories = query.state.data;
      if (!repositories || repositories.length === 0) {
        return 3000;
      }
      return false;
    },
    retry: 1,
  });
}
