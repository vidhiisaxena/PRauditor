"use client";

import { useMemo, useState } from "react";
import { FolderGit2, RefreshCw, Rocket } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { useRepositories } from "@/hooks/useRepositories";
import { PageHeader } from "@/components/common/PageHeader";
import { SearchInput } from "@/components/common/SearchInput";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorCard } from "@/components/common/ErrorCard";
import { CardGridSkeleton } from "@/components/common/LoadingSkeleton";
import { RepositoryCard } from "@/components/repositories/RepositoryCard";
import { apiClient } from "@/lib/api-client";
import { Button } from "@/components/ui/button";

interface InstallationStatus {
  installed: boolean;
  installations: Array<{
    github_installation_id: number;
    account_login?: string | null;
  }>;
}

/** Repositories route container: search + responsive card grid. */
export function RepositoriesView() {
  const installationQuery = useQuery<InstallationStatus>({
    queryKey: ["installations", "status"],
    queryFn: () => apiClient.get<InstallationStatus>("/api/installations"),
    retry: 1,
  });
  const repositoriesQuery = useRepositories();
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!repositoriesQuery.data) return [];
    const q = query.trim().toLowerCase();
    if (!q) return repositoriesQuery.data;
    return repositoriesQuery.data.filter((repo) =>
      repo.full_name.toLowerCase().includes(q),
    );
  }, [repositoriesQuery.data, query]);

  const installed = Boolean(installationQuery.data?.installed);
  const isSyncing =
    installed &&
    (!repositoriesQuery.data || repositoriesQuery.data.length === 0) &&
    (repositoriesQuery.isPending || repositoriesQuery.isFetching);

  return (
    <div>
      <PageHeader
        title="Repositories"
        description="Repositories connected to PRAuditor via your GitHub App installation."
        actions={
          repositoriesQuery.data && repositoriesQuery.data.length > 0 ? (
            <SearchInput
              value={query}
              onChange={setQuery}
              placeholder="Search repositories…"
              aria-label="Search repositories"
              className="w-full sm:w-64"
            />
          ) : null
        }
      />

      {installationQuery.isError ? (
        <ErrorCard
          error={installationQuery.error}
          onRetry={() => installationQuery.refetch()}
        />
      ) : installationQuery.isPending ? (
        <CardGridSkeleton count={3} />
      ) : !installed ? (
        <EmptyState
          icon={Rocket}
          title="GitHub App not installed"
          description="Connect PRAuditor to a GitHub App installation to view repositories and pull requests."
          action={
            <Button variant="outline" asChild>
              <a
                href="https://github.com/settings/installations"
                target="_blank"
                rel="noreferrer"
              >
                Open GitHub App settings
              </a>
            </Button>
          }
        />
      ) : repositoriesQuery.isError ? (
        <ErrorCard
          error={repositoriesQuery.error}
          onRetry={() => repositoriesQuery.refetch()}
        />
      ) : isSyncing ? (
        <div className="space-y-3">
          <div className="rounded-lg border border-dashed bg-card/50 p-6 text-center text-sm text-muted-foreground">
            Syncing repositories from GitHub…
          </div>
          <CardGridSkeleton count={3} />
          <div className="flex justify-center">
            <Button
              variant="outline"
              size="sm"
              onClick={() => repositoriesQuery.refetch()}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </div>
        </div>
      ) : (repositoriesQuery.data?.length ?? 0) === 0 ? (
        <EmptyState
          icon={FolderGit2}
          title="No repositories available"
          description="This installation is connected, but PRAuditor has not found any repositories yet."
          action={
            <Button
              variant="outline"
              size="sm"
              onClick={() => repositoriesQuery.refetch()}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry sync
            </Button>
          }
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={FolderGit2}
          title="No matches"
          description={`No repositories match “${query}”.`}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((repo) => (
            <RepositoryCard key={repo.id} repository={repo} />
          ))}
        </div>
      )}
    </div>
  );
}
