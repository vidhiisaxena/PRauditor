import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { FadeIn } from "@/components/landing/motion";
import { Section } from "@/components/landing/sections";
import { LINKS } from "@/components/landing/config";

export function CTA() {
  return (
    <Section className="border-t">
      <FadeIn className="mx-auto max-w-2xl text-center">
        <h2 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl">
          Ready to improve every pull request?
        </h2>
        <p className="mt-4 text-muted-foreground">
          Install the GitHub App and get your first AI review in minutes.
        </p>
        <div className="mt-8 flex justify-center">
          <Button asChild size="lg">
            <Link href={LINKS.getStarted}>
              Get Started
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </FadeIn>
    </Section>
  );
}
