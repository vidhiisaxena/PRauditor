import { cn } from "@/lib/utils";
import type { PRState } from "@/types";

interface StatusBadgeProps {
  state: string | null;
  className?: string;
}

const STATE_STYLES: Record<PRState, { label: string; className: string }> = {
  open: {
    label: "Open",
    className:
      "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900/50",
  },
  merged: {
    label: "Merged",
    className:
      "bg-violet-50 text-violet-700 border-violet-200 dark:bg-violet-950/40 dark:text-violet-400 dark:border-violet-900/50",
  },
  closed: {
    label: "Closed",
    className:
      "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-900/50",
  },
};

function normalizeState(state: string | null): PRState {
  const lower = state?.toLowerCase();
  if (lower === "open" || lower === "merged" || lower === "closed") {
    return lower;
  }
  return "open";
}

/** Pull request state pill (open / merged / closed). */
export function StatusBadge({ state, className }: StatusBadgeProps) {
  const key = normalizeState(state);
  const { label, className: variantClass } = STATE_STYLES[key];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium",
        variantClass,
        className,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}
