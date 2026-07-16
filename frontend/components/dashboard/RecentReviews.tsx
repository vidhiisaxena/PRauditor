import Link from "next/link";
import { ChevronRight, FileWarning } from "lucide-react";

import { formatRelativeTime } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/common/EmptyState";
import type { RecentReview } from "@/types";

/** List of the most recently reviewed pull requests. */
export function RecentReviews({ reviews }: { reviews: RecentReview[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Recent reviews</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {reviews.length === 0 ? (
          <EmptyState
            icon={FileWarning}
            title="No reviews yet"
            description="Open a pull request on a connected repository to trigger the first review."
            className="border-0 bg-transparent py-10"
          />
        ) : (
          <ul className="divide-y">
            {reviews.map((review) => (
              <li key={review.prId}>
                <Link
                  href={`/prs/${review.prId}`}
                  className="group flex items-center justify-between gap-4 py-3 transition-colors"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">
                      {review.title ?? `Pull request #${review.prNumber}`}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      {review.repoFullName} · #{review.prNumber} ·{" "}
                      {formatRelativeTime(review.reviewedAt)}
                    </p>
                  </div>
                  <div className="flex flex-shrink-0 items-center gap-3">
                    <span className="text-xs text-muted-foreground">
                      {review.issueCount} issue
                      {review.issueCount === 1 ? "" : "s"}
                    </span>
                    {review.criticalCount > 0 ? (
                      <span className="rounded-md bg-red-50 px-2 py-0.5 text-xs font-medium text-red-600 dark:bg-red-950/40 dark:text-red-400">
                        {review.criticalCount} critical
                      </span>
                    ) : null}
                    <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
