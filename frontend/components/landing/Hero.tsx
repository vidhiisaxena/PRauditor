import Link from "next/link";
import { ArrowRight, Github } from "lucide-react";

import { Button } from "@/components/ui/button";
import { FadeIn } from "@/components/landing/motion";
import { PullRequestReview } from "@/components/landing/PullRequestReview";
import { LINKS } from "@/components/landing/config";

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="mx-auto grid max-w-6xl gap-12 px-4 pb-20 pt-10 sm:px-6 sm:pb-28 sm:pt-14 lg:grid-cols-2 lg:items-center lg:gap-10">
        <FadeIn className="max-w-xl">
          <span className="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            Open-source AI code review
          </span>
          <h1 className="mt-5 text-balance text-4xl font-semibold tracking-tight sm:text-5xl lg:leading-[1.05]">
            Review pull requests with AI that thinks like an experienced engineer.
          </h1>
          <p className="mt-5 text-lg text-muted-foreground">
            PRAuditor runs a multi-agent review over every pull request —
            security, performance, logic, and readability — and posts clear,
            structured feedback before you merge.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button asChild size="lg">
              <Link href={LINKS.getStarted}>
                Get Started
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href={LINKS.github} target="_blank" rel="noreferrer">
                <Github className="h-4 w-4" />
                View GitHub
              </Link>
            </Button>
          </div>
        </FadeIn>

        <FadeIn delay={0.15}>
          <PullRequestReview />
        </FadeIn>
      </div>
    </section>
  );
}
