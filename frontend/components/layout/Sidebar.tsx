"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { GitPullRequest, LayoutDashboard, FolderGit2 } from "lucide-react";
import type { LucideProps } from "lucide-react";
import type { ComponentType } from "react";

import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: ComponentType<LucideProps>;
  /** Match nested routes (e.g. /repos/123) as active too. */
  matchPrefix?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Repositories", href: "/repos", icon: FolderGit2, matchPrefix: true },
];

function isActive(pathname: string, item: NavItem): boolean {
  if (item.href === "/") return pathname === "/";
  return item.matchPrefix
    ? pathname === item.href || pathname.startsWith(`${item.href}/`)
    : pathname === item.href;
}

/** Persistent left navigation. Structured to accept future sections (Analytics, Settings). */
export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-60 flex-shrink-0 flex-col border-r bg-card/40 lg:flex">
      <div className="flex h-14 items-center gap-2 border-b px-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <GitPullRequest className="h-4 w-4" />
        </div>
        <span className="text-sm font-semibold tracking-tight">PRAuditor</span>
      </div>

      <nav className="flex-1 space-y-1 p-3" aria-label="Primary">
        {NAV_ITEMS.map((item) => {
          const active = isActive(pathname, item);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-secondary text-secondary-foreground"
                  : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* TODO(auth): user / organization switcher will live here once GitHub login exists. */}
      <div className="border-t p-3">
        <div className="rounded-md bg-muted/60 px-3 py-2 text-xs text-muted-foreground">
          Connected via GitHub App
        </div>
      </div>
    </aside>
  );
}
