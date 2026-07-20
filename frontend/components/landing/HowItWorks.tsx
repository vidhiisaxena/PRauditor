"use client";

import { useRef } from "react";
import { motion, useScroll, useSpring } from "framer-motion";
import {
  Download,
  GitMerge,
  GitPullRequest,
  ScanSearch,
  type LucideIcon,
} from "lucide-react";

import { FadeIn } from "@/components/landing/motion";
import { Section, SectionHeading } from "@/components/landing/sections";
import { STEPS } from "@/components/landing/config";

const STEP_ICONS: LucideIcon[] = [Download, GitPullRequest, ScanSearch, GitMerge];

/**
 * The client-side journey as a vertical timeline. The connecting line "draws
 * in" as the section scrolls into view (scroll-linked, spring-smoothed).
 * Written from the developer's point of view — not a flowchart.
 */
export function HowItWorks() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start 85%", "end 55%"],
  });
  const scaleY = useSpring(scrollYProgress, {
    stiffness: 90,
    damping: 30,
    restDelta: 0.001,
  });

  return (
    <Section id="how-it-works" className="border-t">
      <SectionHeading
        eyebrow="The workflow"
        title="What using PRAuditor actually feels like"
        description="The whole journey lives inside the GitHub flow you already use — no new tools, no context switching."
      />

      <div ref={ref} className="relative mx-auto mt-16 max-w-2xl">
        {/* Faint full-height track */}
        <div
          aria-hidden
          className="absolute bottom-5 left-5 top-5 w-px -translate-x-1/2 bg-border"
        />
        {/* Primary line that draws in with scroll */}
        <motion.div
          aria-hidden
          style={{ scaleY }}
          className="absolute bottom-5 left-5 top-5 w-px -translate-x-1/2 origin-top bg-primary"
        />

        <div className="space-y-10">
          {STEPS.map((step, i) => {
            const Icon = STEP_ICONS[i];
            return (
              <div key={step.title} className="relative flex gap-5">
                <span className="relative z-10 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border bg-card text-primary shadow-sm">
                  <Icon className="h-5 w-5" />
                </span>
                <FadeIn delay={i * 0.06} className="pt-1">
                  <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Step {i + 1}
                  </div>
                  <h3 className="mt-1 text-lg font-semibold tracking-tight">
                    {step.title}
                  </h3>
                  <p className="mt-2 max-w-md leading-relaxed text-muted-foreground">
                    {step.description}
                  </p>
                </FadeIn>
              </div>
            );
          })}
        </div>
      </div>
    </Section>
  );
}
