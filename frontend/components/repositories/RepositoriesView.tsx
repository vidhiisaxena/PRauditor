"use client";

import { useMemo, useState } from "react";
import { FolderGit2 } from "lucide-react";

import { useRepositories } from "@/hooks/useRepositories";
import { PageHeader } from "@/components/common/PageHeader";
import { SearchInput } from "@/components/common/SearchInput";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorCard } from "@/components/common/ErrorCard";
import { CardGridSkeleton } from "@/components/common/LoadingSkeleton";
import { RepositoryCard } from "@/components/repositories/RepositoryCard";

/** Repositories route container: search + responsive card grid. */
export function RepositoriesView() {
  const { data, isPending, isError, error, refetch } = useRepositories();
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toLowerCase();
    if (!q) return data;
    return data.filter((repo) => repo.full_name.toLowerCase().includes(q));
  }, [data, query]);

  return (
    <div>
      <PageHeader
        title="Repositories"
        description="Repositories connected to PRAuditor via your GitHub App installation."
        actions={
          data && data.length > 0 ? (
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

      {isError ? (
        <ErrorCard error={error} onRetry={() => refetch()} />
      ) : isPending ? (
        <CardGridSkeleton count={6} />
      ) : data.length === 0 ? (
        <EmptyState
          icon={FolderGit2}
          title="No repositories yet"
          description="Install the PRAuditor GitHub App on a repository to start reviewing pull requests."
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
