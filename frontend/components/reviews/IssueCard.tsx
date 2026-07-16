import { SeverityBadge } from "@/components/common/SeverityBadge";
import { SuggestionPatch } from "@/components/reviews/SuggestionPatch";
import { CommentThread } from "@/components/reviews/CommentThread";
import type { ReviewIssue } from "@/types";

interface IssueCardProps {
  prId: number;
  issue: ReviewIssue;
}

/**
 * A single review finding: severity, category, message, a suggested-fix patch,
 * and an inline comment thread pinned to this finding.
 */
export function IssueCard({ prId, issue }: IssueCardProps) {
  return (
    <div className="border-t px-4 py-4 first:border-t-0">
      <div className="flex flex-wrap items-center gap-2">
        <SeverityBadge severity={issue.severity} />
        <span className="rounded-md bg-muted px-2 py-0.5 text-xs font-medium capitalize text-muted-foreground">
          {issue.kind}
        </span>
        {issue.line !== null ? (
          <span className="font-mono text-xs text-muted-foreground">
            {issue.file_path}:{issue.line}
          </span>
        ) : null}
      </div>

      <p className="mt-2 text-sm leading-relaxed text-foreground">
        {issue.message}
      </p>

      {issue.suggestion ? (
        <div className="mt-3">
          <SuggestionPatch suggestion={issue.suggestion} />
        </div>
      ) : null}

      <CommentThread prId={prId} issueId={issue.id} />
    </div>
  );
}
