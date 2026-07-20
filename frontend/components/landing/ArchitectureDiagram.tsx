import { ArrowDown } from "lucide-react";

import { FadeIn } from "@/components/landing/motion";
import { Section, SectionHeading } from "@/components/landing/sections";
import { ARCHITECTURE_NODES } from "@/components/landing/config";

export function ArchitectureDiagram() {
  return (
    <Section className="border-t">
      <SectionHeading
        eyebrow="Architecture"
        title="How a review flows through the system"
        description="Open source and self-hostable, end to end."
      />

      <div className="mx-auto mt-14 flex max-w-md flex-col items-center">
        {ARCHITECTURE_NODES.map((node, i) => (
          <div key={node} className="flex w-full flex-col items-center">
            <FadeIn delay={i * 0.06} className="w-full">
              <div className="rounded-lg border bg-card px-5 py-3 text-center text-sm font-medium shadow-sm">
                {node}
              </div>
            </FadeIn>
            {i < ARCHITECTURE_NODES.length - 1 ? (
              <ArrowDown className="my-2 h-4 w-4 text-muted-foreground" />
            ) : null}
          </div>
        ))}
      </div>
    </Section>
  );
}
