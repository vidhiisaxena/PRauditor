/**
 * Centralised TanStack Query keys. Keeping them in one place makes cache
 * invalidation predictable and avoids typo-driven cache misses.
 */
export const queryKeys = {
  dashboard: ["dashboard"] as const,
  repositories: ["repositories"] as const,
  pullRequests: (repoId: number) => ["repositories", repoId, "prs"] as const,
  reviewIssues: (prId: number) => ["prs", prId, "issues"] as const,
  reviewComments: (prId: number) => ["prs", prId, "comments"] as const,
};
