"use client";

import { useQuery } from "@tanstack/react-query";

import { dashboardService } from "@/services/dashboard";
import { queryKeys } from "@/hooks/queryKeys";
import type { DashboardStats } from "@/types";

/**
 * Dashboard KPIs + recent reviews.
 * TODO(backend): switch to a single GET /api/dashboard call (see dashboardService).
 */
export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: queryKeys.dashboard,
    queryFn: () => dashboardService.getDashboardStats(),
  });
}
