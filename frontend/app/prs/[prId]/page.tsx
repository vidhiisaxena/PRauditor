import { apiGet } from "@/lib/api";
import { ReviewIssue, PullRequest, Repository } from "@/types";
import IssueCard from "@/components/IssueCard";
import Link from "next/link";
import RefreshButton from "@/components/RefreshButton";
import TriggerReviewButton from "@/components/TriggerReviewButton";

interface PRDetailPageProps {
  params: {
    prId: string;
  };
}

export default async function PRDetailPage({ params }: PRDetailPageProps) {
  const prId = parseInt(params.prId);
  let issues: ReviewIssue[] = [];
  let pr: PullRequest | null = null;
  let repoName: string | null = null;
  let error: string | null = null;

  try {
    issues = await apiGet<ReviewIssue[]>(`/api/prs/${prId}/issues`);

    // Try to find the PR and repo info
    try {
      const repos = await apiGet<Repository[]>("/api/repos");
      for (const repo of repos) {
        const repoPRs = await apiGet<PullRequest[]>(
          `/api/repos/${repo.id}/prs`
        );
        const foundPR = repoPRs.find((p) => p.id === prId);
        if (foundPR) {
          pr = foundPR;
          repoName = repo.full_name;
          break;
        }
      }
    } catch {
      // Ignore errors when fetching PR/repo info
    }
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to load review issues";
  }

  // Calculate summary statistics
  const totalIssues = issues.length;
  const issuesByKind: Record<string, number> = {};
  const issuesBySeverity: Record<string, number> = {};

  issues.forEach((issue) => {
    issuesByKind[issue.kind] = (issuesByKind[issue.kind] || 0) + 1;
    issuesBySeverity[issue.severity] =
      (issuesBySeverity[issue.severity] || 0) + 1;
  });

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
          PR Review #{pr?.pr_number || prId}
        </h1>
        {repoName && <p className="text-slate-400 mt-1">{repoName}</p>}
        {pr?.title && <p className="text-slate-500 mt-1">{pr.title}</p>}
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 mb-6">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Summary Section */}
      <div className="bg-slate-800 shadow rounded-lg border border-slate-700 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-slate-100">Summary</h2>
          <div className="flex space-x-2">
            <RefreshButton />
            <TriggerReviewButton prId={prId} />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-slate-400">Total Issues</p>
            <p className="text-2xl font-bold text-slate-100">{totalIssues}</p>
          </div>
          <div>
            <p className="text-sm text-slate-400">By Kind</p>
            <div className="mt-1 space-y-1">
              {Object.entries(issuesByKind).map(([kind, count]) => (
                <p key={kind} className="text-sm text-slate-300">
                  {kind}: {count}
                </p>
              ))}
            </div>
          </div>
          <div>
            <p className="text-sm text-slate-400">By Severity</p>
            <div className="mt-1 space-y-1">
              {Object.entries(issuesBySeverity).map(([severity, count]) => (
                <p key={severity} className="text-sm text-slate-300">
                  {severity}: {count}
                </p>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Issues List */}
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-slate-100 mb-4">
          Review Issues ({totalIssues})
        </h2>
      </div>

      {issues.length === 0 && !error && (
        <div className="bg-slate-800 shadow rounded-lg border border-slate-700 p-8 text-center">
          <p className="text-slate-400">No issues found</p>
        </div>
      )}

      <div className="grid gap-4">
        {issues.map((issue) => (
          <IssueCard key={issue.id} issue={issue} />
        ))}
      </div>
    </div>
  );
}
