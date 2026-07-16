"use client";

import {
  AlertOctagon,
  FileSearch,
  FolderGit2,
  GitPullRequest,
} from "lucide-react";

import { useDashboardStats } from "@/hooks/useDashboardStats";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorCard } from "@/components/common/ErrorCard";
import { CardGridSkeleton } from "@/components/common/LoadingSkeleton";
import { Skeleton } from "@/components/ui/skeleton";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { RecentReviews } from "@/components/dashboard/RecentReviews";

/** Dashboard route container. Owns data-fetching so the page stays thin. */
export function DashboardView() {
  const { data, isPending, isError, error, refetch } = useDashboardStats();

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="An overview of review activity across your connected repositories."
      />

      {isError ? (
        <ErrorCard error={error} onRetry={() => refetch()} />
      ) : isPending ? (
        <div className="space-y-8">
          <CardGridSkeleton count={4} className="lg:grid-cols-4" />
          <Skeleton className="h-64 w-full rounded-lg" />
        </div>
      ) : (
        <div className="space-y-8">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatsCard
              label="Repositories"
              value={data.totalRepositories}
              icon={FolderGit2}
            />
            <StatsCard
              label="PRs reviewed"
              value={data.prsReviewed}
              icon={GitPullRequest}
            />
            <StatsCard
              label="Issues found"
              value={data.issuesFound}
              icon={FileSearch}
            />
            <StatsCard
              label="Critical issues"
              value={data.criticalIssues}
              icon={AlertOctagon}
              tone="critical"
            />
          </div>

          <RecentReviews reviews={data.recentReviews} />
        </div>
      )}
    </div>
  );
}
