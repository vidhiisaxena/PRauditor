import type { DashboardStats, RecentReview } from "@/types";
import { normalizeSeverity } from "@/lib/review";
import { repositoriesService } from "@/services/repositories";
import { pullRequestsService } from "@/services/pullRequests";
import { reviewsService } from "@/services/reviews";

const RECENT_REVIEWS_LIMIT = 8;

/**
 * Dashboard service.
 *
 * TODO(backend): Replace the client-side aggregation below with a single
 * `GET /api/dashboard -> DashboardStats` call once the backend implements it
 * (roadmap Stage 7). Fanning out across repos/PRs/issues is fine for a small
 * install but does not scale — the dedicated endpoint should compute these
 * counts in SQL.
 */
export const dashboardService = {
  async getDashboardStats(): Promise<DashboardStats> {
    const repositories = await repositoriesService.getRepositories();

    // Fetch PRs for every repo in parallel.
    const prsByRepo = await Promise.all(
      repositories.map(async (repo) => ({
        repo,
        prs: await pullRequestsService.getPullRequests(repo.id),
      })),
    );

    const reviewedPrs = prsByRepo.flatMap(({ repo, prs }) =>
      prs
        .filter((pr) => pr.last_reviewed_at !== null)
        .map((pr) => ({ repo, pr })),
    );

    // Fetch issues for reviewed PRs in parallel.
    const issuesByPr = await Promise.all(
      reviewedPrs.map(async ({ repo, pr }) => {
        const issues = await reviewsService.getReviewIssues(pr.id);
        return { repo, pr, issues };
      }),
    );

    let issuesFound = 0;
    let criticalIssues = 0;
    const recent: RecentReview[] = [];

    for (const { repo, pr, issues } of issuesByPr) {
      const criticalCount = issues.filter(
        (issue) => normalizeSeverity(issue.severity) === "critical",
      ).length;

      issuesFound += issues.length;
      criticalIssues += criticalCount;

      recent.push({
        prId: pr.id,
        prNumber: pr.pr_number,
        repoId: repo.id,
        repoFullName: repo.full_name,
        title: pr.title,
        issueCount: issues.length,
        criticalCount,
        reviewedAt: pr.last_reviewed_at,
      });
    }

    recent.sort(sortByReviewedAtDesc);

    return {
      totalRepositories: repositories.length,
      prsReviewed: reviewedPrs.length,
      issuesFound,
      criticalIssues,
      recentReviews: recent.slice(0, RECENT_REVIEWS_LIMIT),
    };
  },
};

function sortByReviewedAtDesc(a: RecentReview, b: RecentReview): number {
  const ta = a.reviewedAt ? new Date(a.reviewedAt).getTime() : 0;
  const tb = b.reviewedAt ? new Date(b.reviewedAt).getTime() : 0;
  return tb - ta;
}
