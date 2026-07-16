import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/types";

interface RiskScoreProps {
  /** 0–100 score, or null when the backend has not produced one yet. */
  score: number | null;
  level: RiskLevel | null;
  className?: string;
}

const LEVEL_STYLES: Record<RiskLevel, { label: string; dot: string; text: string }> = {
  low: { label: "Low", dot: "bg-emerald-500", text: "text-emerald-600 dark:text-emerald-400" },
  medium: { label: "Medium", dot: "bg-amber-500", text: "text-amber-600 dark:text-amber-400" },
  high: { label: "High", dot: "bg-orange-500", text: "text-orange-600 dark:text-orange-400" },
  critical: { label: "Critical", dot: "bg-red-500", text: "text-red-600 dark:text-red-400" },
};

/**
 * Risk score display.
 * TODO(backend): `score` is a placeholder until the Risk Scoring agent exists
 * (roadmap Stage 4). Until then we show the derived qualitative level only.
 */
export function RiskScore({ score, level, className }: RiskScoreProps) {
  const style = level ? LEVEL_STYLES[level] : null;

  return (
    <div className={cn("flex items-center justify-between", className)}>
      <div className="flex items-center gap-2">
        <span className={cn("h-2 w-2 rounded-full", style?.dot ?? "bg-muted-foreground")} />
        <span className={cn("text-sm font-medium", style?.text ?? "text-muted-foreground")}>
          {style?.label ?? "Unknown"}
        </span>
      </div>
      <span className="font-mono text-sm text-muted-foreground">
        {score !== null ? `${score}/100` : "—"}
      </span>
    </div>
  );
}
