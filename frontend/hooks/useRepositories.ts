"use client";

import { useQuery } from "@tanstack/react-query";

import { repositoriesService } from "@/services/repositories";
import { queryKeys } from "@/hooks/queryKeys";
import type { Repository } from "@/types";

/** Fetch all repositories known to PRAuditor. */
export function useRepositories() {
  return useQuery<Repository[]>({
    queryKey: queryKeys.repositories,
    queryFn: () => repositoriesService.getRepositories(),
  });
}
