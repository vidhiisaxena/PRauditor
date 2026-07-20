import Link from "next/link";
import { GitFork, Github, Map, Scale, Server, Star, type LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FadeIn } from "@/components/landing/motion";
import { Section } from "@/components/landing/sections";
import { LINKS } from "@/components/landing/config";

const HIGHLIGHTS: { icon: LucideIcon; title: string; description: string }[] = [
  { icon: Scale, title: "MIT License", description: "Use it, fork it, ship it." },
  { icon: GitFork, title: "Open for contributions", description: "Issues and PRs welcome." },
  { icon: Server, title: "Self-hostable", description: "Own your data and models." },
  { icon: Map, title: "Public roadmap", description: "Risk scoring, inline comments, and more." },
];

export function OpenSource() {
  return (
    <Section id="open-source" className="border-t">
      <FadeIn>
        <Card className="overflow-hidden">
          <div className="grid gap-8 p-8 sm:p-10 lg:grid-cols-2 lg:items-center">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium text-muted-foreground">
                <Github className="h-3.5 w-3.5" />
                Open source
              </span>
              <h2 className="mt-4 text-3xl font-semibold tracking-tight">
                Built in the open, yours to run.
              </h2>
              <p className="mt-3 text-muted-foreground">
                PRAuditor is MIT-licensed and self-hostable. Read the code, open
                an issue, or send a pull request — it gets reviewed too.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Button asChild size="lg">
                  <Link href={LINKS.github} target="_blank" rel="noreferrer">
                    <Star className="h-4 w-4" />
                    Star on GitHub
                  </Link>
                </Button>
                <Button asChild size="lg" variant="outline">
                  <Link href={LINKS.docs}>
                    <Map className="h-4 w-4" />
                    Roadmap
                  </Link>
                </Button>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {HIGHLIGHTS.map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="rounded-lg border bg-card p-4">
                    <Icon className="h-5 w-5 text-primary" />
                    <h3 className="mt-3 text-sm font-semibold">{item.title}</h3>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {item.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      </FadeIn>
    </Section>
  );
}
