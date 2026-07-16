import type { ComponentType } from "react";
import type { LucideProps } from "lucide-react";

import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";

interface StatsCardProps {
  label: string;
  value: number | string;
  icon: ComponentType<LucideProps>;
  /** Optional emphasis, e.g. for critical counts. */
  tone?: "default" | "critical";
  hint?: string;
}

/** Single KPI tile for the dashboard. Reusable across future analytics views. */
export function StatsCard({
  label,
  value,
  icon: Icon,
  tone = "default",
  hint,
}: StatsCardProps) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        <div
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-md",
            tone === "critical"
              ? "bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-400"
              : "bg-muted text-muted-foreground",
          )}
        >
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <p
        className={cn(
          "mt-3 text-3xl font-semibold tracking-tight",
          tone === "critical" && "text-red-600 dark:text-red-400",
        )}
      >
        {value}
      </p>
      {hint ? (
        <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
      ) : null}
    </Card>
  );
}
