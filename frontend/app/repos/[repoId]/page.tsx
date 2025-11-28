import { apiGet } from "@/lib/api";
import { Repository, PullRequest } from "@/types";
import PRCard from "@/components/PRCard";
import Link from "next/link";

interface RepoDetailPageProps {
  params: {
    repoId: string;
  };
}

export default async function RepoDetailPage({ params }: RepoDetailPageProps) {
  const repoId = parseInt(params.repoId);
  let repo: Repository | null = null;
  let prs: PullRequest[] = [];
  let error: string | null = null;

  try {
    // Fetch repos to get the repo name
    const repos = await apiGet<Repository[]>("/api/repos");
    repo = repos.find((r) => r.id === repoId) || null;

    // Fetch PRs for this repo
    prs = await apiGet<PullRequest[]>(`/api/repos/${repoId}/prs`);
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to load pull requests";
  }

  return (
    <div className="px-4 py-8">
      <div className="mb-6">
        <Link
          href="/repos"
          className="text-sm text-blue-400 hover:text-blue-300 mb-2 inline-block"
        >
          ← Back to Repositories
        </Link>
        <h1 className="text-3xl font-bold text-slate-100">
          {repo ? repo.full_name : `Repository #${repoId}`}
        </h1>
        <p className="text-slate-400 mt-2">Pull Requests</p>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 mb-6">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {prs.length === 0 && !error && (
        <div className="bg-slate-800 shadow rounded-lg border border-slate-700 p-8 text-center">
          <p className="text-slate-400">No pull requests found</p>
        </div>
      )}

      <div className="grid gap-4">
        {prs.map((pr) => (
          <PRCard key={pr.id} pr={pr} />
        ))}
      </div>
    </div>
  );
}
