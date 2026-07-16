"use client";

import Link from "next/link";
import { useMemo } from "react";
import { CheckCircle2, ChevronLeft } from "lucide-react";

import { useReviewIssues } from "@/hooks/useReviewIssues";
import { groupIssuesByFile, summarizeIssues } from "@/lib/review";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorCard } from "@/components/common/ErrorCard";
import { ReviewSkeleton } from "@/components/common/LoadingSkeleton";
import { ReviewSummarySidebar } from "@/components/reviews/ReviewSummarySidebar";
import { FileIssueSection } from "@/components/reviews/FileIssueSection";

interface ReviewDetailViewProps {
  prId: number;
}

/**
 * Review detail route container — the primary screen. Two-column layout:
 * a sticky summary rail and the file-grouped issue list.
 *
 * NOTE: There is no single-PR endpoint yet, so PR title/number are not shown
 * here. TODO(backend): fetch GET /api/prs/{prId} to render richer PR metadata.
 */
export function ReviewDetailView({ prId }: ReviewDetailViewProps) {
  const { data: issues, isPending, isError, error, refetch } =
    useReviewIssues(prId);

  const summary = useMemo(() => summarizeIssues(issues ?? []), [issues]);
  const groups = useMemo(() => groupIssuesByFile(issues ?? []), [issues]);

  return (
    <div>
      <PageHeader
        eyebrow={
          <Link
            href="/repos"
            className="inline-flex items-center gap-1 text-muted-foreground transition-colors hover:text-foreground"
          >
            <ChevronLeft className="h-4 w-4" />
            Repositories
          </Link>
        }
        title="Code review"
        description="AI multi-agent review grouped by file. Expand a file to inspect its findings."
      />

      {isError ? (
        <ErrorCard error={error} onRetry={() => refetch()} />
      ) : isPending ? (
        <ReviewSkeleton />
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[280px_1fr]">
          <ReviewSummarySidebar prId={prId} summary={summary} />

          <div className="space-y-3">
            {groups.length === 0 ? (
              <EmptyState
                icon={CheckCircle2}
                title="No issues found"
                description="The reviewer did not flag anything on this pull request."
              />
            ) : (
              groups.map((group) => (
                <FileIssueSection key={group.filePath} prId={prId} group={group} />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
