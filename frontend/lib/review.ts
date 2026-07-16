import {
  type FileIssueGroup,
  type ReviewIssue,
  type ReviewSummary,
  type RiskLevel,
  type Severity,
} from "@/types";

/**
 * Review domain logic: normalising backend strings and aggregating issues into
 * view-models. Kept out of components so it is unit-testable and reusable.
 */

const KNOWN_SEVERITIES: readonly Severity[] = [
  "info",
  "minor",
  "major",
  "critical",
];

const SEVERITY_RANK: Record<Severity, number> = {
  info: 0,
  minor: 1,
  major: 2,
  critical: 3,
};

/** Coerce an arbitrary backend severity string into a known Severity. */
export function normalizeSeverity(value: string): Severity {
  const lower = value?.toLowerCase();
  return (KNOWN_SEVERITIES as readonly string[]).includes(lower)
    ? (lower as Severity)
    : "minor";
}

export function compareSeverity(a: string, b: string): number {
  return SEVERITY_RANK[normalizeSeverity(b)] - SEVERITY_RANK[normalizeSeverity(a)];
}

/** Aggregate a list of issues into per-severity counts + a risk placeholder. */
export function summarizeIssues(issues: ReviewIssue[]): ReviewSummary {
  const summary: ReviewSummary = {
    total: issues.length,
    critical: 0,
    major: 0,
    minor: 0,
    info: 0,
    riskScore: null,
    riskLevel: null,
    reviewedAt: null,
  };

  let latest = 0;
  for (const issue of issues) {
    summary[normalizeSeverity(issue.severity)] += 1;
    const t = new Date(issue.created_at).getTime();
    if (!Number.isNaN(t) && t > latest) latest = t;
  }

  summary.reviewedAt = latest ? new Date(latest).toISOString() : null;
  summary.riskLevel = deriveRiskLevel(summary);
  return summary;
}

/**
 * Coarse risk level derived from severity mix. This is a UI-side placeholder;
 * TODO: replace with the backend Risk Scoring agent (see Stage 4 roadmap)
 * once `riskScore` is returned by the API.
 */
function deriveRiskLevel(summary: ReviewSummary): RiskLevel | null {
  if (summary.total === 0) return "low";
  if (summary.critical > 0) return "critical";
  if (summary.major >= 3) return "high";
  if (summary.major > 0) return "medium";
  return "low";
}

/** Bucket issues by file and sort each bucket by severity (worst first). */
export function groupIssuesByFile(issues: ReviewIssue[]): FileIssueGroup[] {
  const byFile = new Map<string, ReviewIssue[]>();

  for (const issue of issues) {
    const key = issue.file_path || "(unknown file)";
    const bucket = byFile.get(key) ?? [];
    bucket.push(issue);
    byFile.set(key, bucket);
  }

  const groups: FileIssueGroup[] = [];
  for (const [filePath, fileIssues] of byFile) {
    const sorted = [...fileIssues].sort((a, b) =>
      compareSeverity(a.severity, b.severity),
    );
    groups.push({
      filePath,
      issues: sorted,
      counts: {
        critical: sorted.filter((i) => normalizeSeverity(i.severity) === "critical").length,
        major: sorted.filter((i) => normalizeSeverity(i.severity) === "major").length,
        minor: sorted.filter((i) => normalizeSeverity(i.severity) === "minor").length,
        info: sorted.filter((i) => normalizeSeverity(i.severity) === "info").length,
      },
    });
  }

  // Files with the most severe issues float to the top.
  return groups.sort(
    (a, b) => b.counts.critical - a.counts.critical || b.counts.major - a.counts.major,
  );
}
