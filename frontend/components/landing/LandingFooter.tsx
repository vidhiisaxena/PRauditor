import Link from "next/link";
import { GitPullRequest } from "lucide-react";

import { LINKS } from "@/components/landing/config";

const FOOTER_LINKS = [
  { label: "Docs", href: LINKS.docs },
  { label: "GitHub", href: LINKS.github },
  { label: "License", href: `${LINKS.github}/blob/main/LICENSE` },
  { label: "Privacy", href: "#" },
  { label: "Roadmap", href: LINKS.docs },
];

export function LandingFooter() {
  return (
    <footer className="border-t">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-10 sm:flex-row sm:px-6">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <GitPullRequest className="h-3.5 w-3.5" />
          </div>
          <span className="text-sm font-medium">PRAuditor</span>
          <span className="text-xs text-muted-foreground">· MIT Licensed</span>
        </div>

        <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
          {FOOTER_LINKS.map((l) => (
            <Link
              key={l.label}
              href={l.href}
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
