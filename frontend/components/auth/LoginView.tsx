"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Github, GitPullRequest } from "lucide-react";

import { useAuth } from "@/components/auth/AuthProvider";
import { authService } from "@/services/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

/** Sign-in screen. "Continue with GitHub" navigates to the backend, which
 * redirects to GitHub's consent screen. */
export function LoginView() {
  const { loading, authenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && authenticated) router.replace("/dashboard");
  }, [loading, authenticated, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-md space-y-8">
        <div className="flex flex-col items-center text-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <GitPullRequest className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Sign in to PRAuditor
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Continue with your GitHub account to review pull requests with AI.
          </p>
        </div>

        <Card>
          <CardContent className="p-6">
            <Button asChild className="w-full" size="lg">
              {/* Full-page navigation (not fetch) — OAuth must be a top-level redirect. */}
              <a href={authService.loginUrl()}>
                <Github className="h-4 w-4" />
                Continue with GitHub
              </a>
            </Button>
            <p className="mt-4 text-center text-xs text-muted-foreground">
              You&apos;ll authorize PRAuditor on GitHub and be redirected back.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
