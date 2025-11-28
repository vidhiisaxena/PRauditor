import { apiGet } from "@/lib/api";
import { Repository } from "@/types";
import RepoCard from "@/components/RepoCard";

export default async function ReposPage() {
  let repos: Repository[] = [];
  let error: string | null = null;

  try {
    repos = await apiGet<Repository[]>("/api/repos");
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to load repositories";
  }

  return (
    <div className="px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-100">Repositories</h1>
        <p className="text-slate-400 mt-2">
          Select a repository to view its pull requests
        </p>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 mb-6">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {repos.length === 0 && !error && (
        <div className="bg-slate-800 shadow rounded-lg border border-slate-700 p-8 text-center">
          <p className="text-slate-400">No repositories found</p>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {repos.map((repo) => (
          <RepoCard key={repo.id} repo={repo} />
        ))}
      </div>
    </div>
  );
}
