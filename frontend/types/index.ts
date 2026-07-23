/**
 * Domain types shared across the frontend.
 *
 * The API-facing interfaces (Repository, PullRequest, ReviewIssue) mirror the
 * FastAPI response models exactly. The unions below (Severity, IssueKind, ...)
 * describe the *known* values; components must still tolerate unknown strings
 * coming from the backend, so helpers accept `string` and normalise.
 */

// ---------------------------------------------------------------------------
// Enums / unions
// ---------------------------------------------------------------------------

export const SEVERITIES = ["info", "minor", "major", "critical"] as const;
export type Severity = (typeof SEVERITIES)[number];

export const ISSUE_KINDS = [
  "logic",
  "readability",
  "performance",
  "security",
] as const;
export type IssueKind = (typeof ISSUE_KINDS)[number];

export const PR_STATES = ["open", "closed", "merged"] as const;
export type PRState = (typeof PR_STATES)[number];

export const RISK_LEVELS = ["low", "medium", "high", "critical"] as const;
export type RiskLevel = (typeof RISK_LEVELS)[number];

// ---------------------------------------------------------------------------
// API response models (must match backend/schema.py)
// ---------------------------------------------------------------------------

export interface Repository {
  id: number;
  full_name: string;
  installation_id?: number | null;
}

export interface PullRequest {
  id: number;
  pr_number: number;
  title: string | null;
  state: string | null;
  head_sha: string | null;
  last_reviewed_at: string | null;
}

export interface ReviewIssue {
  id: number;
  file_path: string;
  line: number | null;
  kind: string;
  severity: string;
  message: string;
  suggestion: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

/** The signed-in user, as returned by GET /api/auth/me. */
export interface AuthUser {
  id: number;
  username: string;
  name: string | null;
  email: string | null;
  avatar_url: string | null;
}

// ---------------------------------------------------------------------------
// Derived / view-model types (computed on the frontend)
// ---------------------------------------------------------------------------

/** Aggregated counts for a single review, derived from its issues. */
export interface ReviewSummary {
  total: number;
  critical: number;
  major: number;
  minor: number;
  info: number;
  /** Placeholder until a Risk Scoring agent exists on the backend. */
  riskScore: number | null;
  riskLevel: RiskLevel | null;
  /** Latest issue timestamp, used as the review time. */
  reviewedAt: string | null;
}

/** Issues bucketed by file for the collapsible review view. */
export interface FileIssueGroup {
  filePath: string;
  issues: ReviewIssue[];
  counts: Pick<ReviewSummary, "critical" | "major" | "minor" | "info">;
}

export interface DashboardStats {
  totalRepositories: number;
  prsReviewed: number;
  issuesFound: number;
  criticalIssues: number;
  recentReviews: RecentReview[];
}

export interface RecentReview {
  prId: number;
  prNumber: number;
  repoId: number;
  repoFullName: string;
  title: string | null;
  issueCount: number;
  criticalCount: number;
  reviewedAt: string | null;
}

// ---------------------------------------------------------------------------
// Review comments
// ---------------------------------------------------------------------------

/** A human (or bot) comment attached to a specific review finding. */
export interface ReviewComment {
  id: number;
  issueId: number;
  author: {
    login: string;
    avatarUrl: string | null;
  };
  body: string;
  createdAt: string;
}

export interface AddCommentInput {
  issueId: number;
  body: string;
}
