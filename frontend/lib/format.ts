/** Formatting helpers for dates and text. Pure, framework-agnostic. */

/** Human-friendly relative time, e.g. "3h ago", "2d ago". Falls back to a date. */
export function formatRelativeTime(iso: string | null | undefined): string {
  if (!iso) return "Never";

  const date = new Date(iso);
  const ms = date.getTime();
  if (Number.isNaN(ms)) return "Unknown";

  const diffSeconds = Math.round((Date.now() - ms) / 1000);

  if (diffSeconds < 45) return "just now";
  const units: Array<[Intl.RelativeTimeFormatUnit, number]> = [
    ["year", 60 * 60 * 24 * 365],
    ["month", 60 * 60 * 24 * 30],
    ["week", 60 * 60 * 24 * 7],
    ["day", 60 * 60 * 24],
    ["hour", 60 * 60],
    ["minute", 60],
  ];

  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  for (const [unit, seconds] of units) {
    const value = Math.round(diffSeconds / seconds);
    if (Math.abs(value) >= 1) {
      return rtf.format(-value, unit);
    }
  }
  return "just now";
}

/** Absolute, readable timestamp for tooltips / detail lines. */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

/** Split "owner/repo" into its parts. */
export function splitRepoName(fullName: string): {
  owner: string;
  name: string;
} {
  const [owner, ...rest] = fullName.split("/");
  return { owner, name: rest.join("/") || owner };
}
