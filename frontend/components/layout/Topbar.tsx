"use client";

import Link from "next/link";
import { GitPullRequest } from "lucide-react";

import { ThemeToggle } from "@/components/layout/ThemeToggle";

/**
 * Top bar. On mobile it carries the brand (sidebar is hidden); on desktop it
 * holds global actions. Structured to host a user menu / notifications later.
 */
export function Topbar() {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b bg-background/80 px-4 backdrop-blur sm:px-6">
      <Link href="/" className="flex items-center gap-2 lg:hidden">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <GitPullRequest className="h-4 w-4" />
        </div>
        <span className="text-sm font-semibold">PRAuditor</span>
      </Link>

      <div className="hidden lg:block" />

      <div className="flex items-center gap-1.5">
        {/* TODO(notifications): bell + dropdown once the notifications feature lands. */}
        <ThemeToggle />
      </div>
    </header>
  );
}
