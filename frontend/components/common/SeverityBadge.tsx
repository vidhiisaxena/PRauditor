import { AlertOctagon, AlertTriangle, Info, ShieldAlert } from "lucide-react";

import { cn } from "@/lib/utils";
import { normalizeSeverity } from "@/lib/review";
import type { Severity } from "@/types";

interface SeverityBadgeProps {
  severity: string;
  className?: string;
  showIcon?: boolean;
}

const SEVERITY_STYLES: Record<
  Severity,
  { label: string; className: string; Icon: typeof Info }
> = {
  critical: {
    label: "Critical",
    className:
      "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-900/50",
    Icon: ShieldAlert,
  },
  major: {
    label: "Major",
    className:
      "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950/40 dark:text-orange-400 dark:border-orange-900/50",
    Icon: AlertOctagon,
  },
  minor: {
    label: "Minor",
    className:
      "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-900/50",
    Icon: AlertTriangle,
  },
  info: {
    label: "Info",
    className:
      "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-900/50",
    Icon: Info,
  },
};

/** Colour-coded severity pill used across issue lists and summaries. */
export function SeverityBadge({
  severity,
  className,
  showIcon = true,
}: SeverityBadgeProps) {
  const key = normalizeSeverity(severity);
  const { label, className: variantClass, Icon } = SEVERITY_STYLES[key];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium",
        variantClass,
        className,
      )}
    >
      {showIcon && <Icon className="h-3 w-3" />}
      {label}
    </span>
  );
}
