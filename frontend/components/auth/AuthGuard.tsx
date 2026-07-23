"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { GitPullRequest } from "lucide-react";

import { useAuth } from "@/components/auth/AuthProvider";

/**
 * Wraps the authenticated app. Shows a splash while the session resolves and
 * redirects to /login if the user isn't signed in. Children render only when
 * authenticated.
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { loading, authenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !authenticated) {
      router.replace("/login");
    }
  }, [loading, authenticated, router]);

  if (loading || !authenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex items-center gap-2 text-muted-foreground">
          <GitPullRequest className="h-5 w-5 animate-pulse text-primary" />
          <span className="text-sm">Loading your workspace…</span>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
