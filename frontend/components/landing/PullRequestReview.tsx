import {
  CheckCircle2,
  FileCode2,
  GaugeCircle,
  GitPullRequest,
  ShieldCheck,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";

type Category = "Security" | "Performance" | "Logic" | "Readability";
type Severity = "critical" | "major" | "minor" | "info";

interface ReviewLine {
  category: Category;
  severity: Severity;
  file: string;
  line: number;
  comment: string;
}

const CATEGORY_ICON: Record<Category, LucideIcon> = {
  Security: ShieldCheck,
  Performance: GaugeCircle,
  Logic: FileCode2,
  Readability: Sparkles,
};

const SEVERITY_STYLE: Record<Severity, string> = {
  critical:
    "text-red-600 bg-red-50 border-red-200 dark:text-red-400 dark:bg-red-950/40 dark:border-red-900/50",
  major:
    "text-orange-600 bg-orange-50 border-orange-200 dark:text-orange-400 dark:bg-orange-950/40 dark:border-orange-900/50",
  minor:
    "text-amber-600 bg-amber-50 border-amber-200 dark:text-amber-400 dark:bg-amber-950/40 dark:border-amber-900/50",
  info: "text-blue-600 bg-blue-50 border-blue-200 dark:text-blue-400 dark:bg-blue-950/40 dark:border-blue-900/50",
};

const LINES: ReviewLine[] = [
  {
    category: "Security",
    severity: "critical",
    file: "auth/session.py",
    line: 42,
    comment:
      "Session token compared with `==`; use a constant-time compare to avoid timing attacks.",
  },
  {
    category: "Performance",
    severity: "major",
    file: "api/orders.py",
    line: 88,
    comment:
      "Query runs inside the loop — an N+1. Fetch all orders in one query before iterating.",
  },
  {
    category: "Logic",
    severity: "major",
    file: "utils/dates.py",
    line: 15,
    comment: "Off-by-one on the range end — the last day is excluded from the report.",
  },
  {
    category: "Readability",
    severity: "minor",
    file: "components/Table.tsx",
    line: 120,
    comment: "Deeply nested ternary; extract to a small helper for clarity.",
  },
];

/** A realistic, static PR review card for the hero. No data fetching. */
export function PullRequestReview() {
  return (
    <Card className="overflow-hidden shadow-sm">
      <div className="flex items-center justify-between border-b bg-muted/40 px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <GitPullRequest className="h-4 w-4 text-primary" />
          <span className="truncate text-sm font-medium">Add checkout flow</span>
          <span className="text-xs text-muted-foreground">#128</span>
        </div>
        <span className="rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
          PRAuditor
        </span>
      </div>

      <div className="flex items-center gap-4 border-b px-4 py-2.5 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">4 findings</span>
        <span>1 critical</span>
        <span>2 major</span>
        <span>1 minor</span>
      </div>

      <div className="divide-y">
        {LINES.map((l) => {
          const Icon = CATEGORY_ICON[l.category];
          return (
            <div key={l.file} className="px-4 py-3">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={cn(
                    "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium",
                    SEVERITY_STYLE[l.severity],
                  )}
                >
                  <Icon className="h-3 w-3" />
                  {l.category}
                </span>
                <span className="font-mono text-xs text-muted-foreground">
                  {l.file}:{l.line}
                </span>
              </div>
              <p className="mt-1.5 text-sm leading-relaxed">{l.comment}</p>
            </div>
          );
        })}
      </div>

      <div className="flex items-center gap-2 border-t bg-muted/30 px-4 py-2.5 text-xs text-muted-foreground">
        <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
        Review posted to the pull request
      </div>
    </Card>
  );
}
