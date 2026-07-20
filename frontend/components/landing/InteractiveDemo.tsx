"use client";

import { useState } from "react";
import { ChevronDown, FileCode2, Lightbulb } from "lucide-react";

import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Section, SectionHeading } from "@/components/landing/sections";

type Severity = "critical" | "major" | "minor";

interface DemoIssue {
  id: string;
  severity: Severity;
  category: string;
  line: number;
  message: string;
  remove: string;
  add: string;
}

const DIFF: { type: "ctx" | "add" | "del"; text: string }[] = [
  { type: "ctx", text: "def verify_token(token, expected):" },
  { type: "del", text: "    if token == expected:" },
  { type: "add", text: "    if hmac.compare_digest(token, expected):" },
  { type: "ctx", text: "        return True" },
  { type: "ctx", text: "    return False" },
];

const SEVERITY_STYLE: Record<Severity, string> = {
  critical:
    "text-red-600 bg-red-50 border-red-200 dark:text-red-400 dark:bg-red-950/40 dark:border-red-900/50",
  major:
    "text-orange-600 bg-orange-50 border-orange-200 dark:text-orange-400 dark:bg-orange-950/40 dark:border-orange-900/50",
  minor:
    "text-amber-600 bg-amber-50 border-amber-200 dark:text-amber-400 dark:bg-amber-950/40 dark:border-amber-900/50",
};

const ISSUES: DemoIssue[] = [
  {
    id: "sec",
    severity: "critical",
    category: "Security",
    line: 2,
    message:
      "Token compared with `==` — vulnerable to timing attacks. Use a constant-time comparison.",
    remove: "if token == expected:",
    add: "if hmac.compare_digest(token, expected):",
  },
  {
    id: "read",
    severity: "minor",
    category: "Readability",
    line: 4,
    message: "Comparing a boolean to `True` is redundant — check the value directly.",
    remove: "if match == True:",
    add: "if match:",
  },
];

export function InteractiveDemo() {
  const [openId, setOpenId] = useState<string | null>(ISSUES[0].id);

  return (
    <Section className="border-t">
      <SectionHeading
        eyebrow="Live example"
        title="See a review, end to end"
        description="Changed code, the AI's findings, and a suggested fix — no backend required."
      />

      <div className="mx-auto mt-14 grid max-w-4xl gap-4 lg:grid-cols-2">
        <Card className="overflow-hidden">
          <div className="flex items-center gap-2 border-b bg-muted/40 px-4 py-2.5">
            <FileCode2 className="h-4 w-4 text-muted-foreground" />
            <span className="font-mono text-xs">auth/session.py</span>
          </div>
          <pre className="overflow-x-auto p-3 font-mono text-xs leading-relaxed">
            {DIFF.map((l, i) => (
              <div
                key={i}
                className={cn(
                  "whitespace-pre px-1",
                  l.type === "add" && "bg-primary/10",
                  l.type === "del" && "bg-destructive/10",
                )}
              >
                <span
                  className={cn(
                    "mr-2 select-none",
                    l.type === "add"
                      ? "text-primary"
                      : l.type === "del"
                        ? "text-destructive"
                        : "text-muted-foreground",
                  )}
                >
                  {l.type === "add" ? "+" : l.type === "del" ? "-" : " "}
                </span>
                {l.text}
              </div>
            ))}
          </pre>
        </Card>

        <div className="space-y-3">
          {ISSUES.map((issue) => {
            const isOpen = openId === issue.id;
            return (
              <Card key={issue.id} className="overflow-hidden">
                <button
                  type="button"
                  onClick={() => setOpenId(isOpen ? null : issue.id)}
                  aria-expanded={isOpen}
                  className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left transition-colors hover:bg-muted/40"
                >
                  <span className="flex flex-wrap items-center gap-2">
                    <span
                      className={cn(
                        "rounded-md border px-2 py-0.5 text-xs font-medium",
                        SEVERITY_STYLE[issue.severity],
                      )}
                    >
                      {issue.category}
                    </span>
                    <span className="font-mono text-xs text-muted-foreground">
                      line {issue.line}
                    </span>
                  </span>
                  <ChevronDown
                    className={cn(
                      "h-4 w-4 flex-shrink-0 text-muted-foreground transition-transform",
                      isOpen && "rotate-180",
                    )}
                  />
                </button>

                {isOpen ? (
                  <div className="border-t px-4 py-3">
                    <p className="text-sm leading-relaxed">{issue.message}</p>
                    <div className="mt-3 overflow-hidden rounded-md border">
                      <div className="flex items-center gap-1.5 border-b bg-muted/50 px-3 py-1.5 text-xs font-medium text-muted-foreground">
                        <Lightbulb className="h-3.5 w-3.5 text-amber-500" />
                        Suggested fix
                      </div>
                      <pre className="overflow-x-auto bg-card p-3 font-mono text-xs leading-relaxed">
                        <div className="whitespace-pre bg-destructive/10">
                          <span className="mr-2 select-none text-destructive">-</span>
                          {issue.remove}
                        </div>
                        <div className="whitespace-pre bg-primary/10">
                          <span className="mr-2 select-none text-primary">+</span>
                          {issue.add}
                        </div>
                      </pre>
                    </div>
                  </div>
                ) : null}
              </Card>
            );
          })}
        </div>
      </div>
    </Section>
  );
}
