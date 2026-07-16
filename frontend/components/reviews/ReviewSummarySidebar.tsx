import { Clock } from "lucide-react";

import { cn } from "@/lib/utils";
import { formatDateTime } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { RiskScore } from "@/components/common/RiskScore";
import type { ReviewSummary } from "@/types";
import { ReviewActions } from "@/components/reviews/ReviewActions";

interface ReviewSummarySidebarProps {
  prId: number;
  summary: ReviewSummary;
}

const ROWS: Array<{ key: keyof ReviewSummary; label: string; dot: string }> = [
  { key: "critical", label: "Critical", dot: "bg-red-500" },
  { key: "major", label: "Major", dot: "bg-orange-500" },
  { key: "minor", label: "Minor", dot: "bg-amber-500" },
  { key: "info", label: "Info", dot: "bg-blue-500" },
];

/** Sticky left rail: totals, severity breakdown, risk, timestamp, actions. */
export function ReviewSummarySidebar({ prId, summary }: ReviewSummarySidebarProps) {
  return (
    <div className="space-y-4 lg:sticky lg:top-20">
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-base">Review summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 pt-0">
          <div>
            <p className="text-3xl font-semibold tracking-tight">
              {summary.total}
            </p>
            <p className="text-sm text-muted-foreground">
              total issue{summary.total === 1 ? "" : "s"}
            </p>
          </div>

          <Separator />

          <ul className="space-y-2">
            {ROWS.map((row) => (
              <li
                key={row.key}
                className="flex items-center justify-between text-sm"
              >
                <span className="flex items-center gap-2 text-muted-foreground">
                  <span className={cn("h-2 w-2 rounded-full", row.dot)} />
                  {row.label}
                </span>
                <span className="font-medium tabular-nums">
                  {summary[row.key] as number}
                </span>
              </li>
            ))}
          </ul>

          <Separator />

          <div className="space-y-1.5">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Risk score
            </p>
            {/* TODO(backend): populated by the Risk Scoring agent (Stage 4). */}
            <RiskScore score={summary.riskScore} level={summary.riskLevel} />
          </div>

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="h-3.5 w-3.5" />
            Reviewed {formatDateTime(summary.reviewedAt)}
          </div>
        </CardContent>
      </Card>

      <ReviewActions prId={prId} />
    </div>
  );
}
