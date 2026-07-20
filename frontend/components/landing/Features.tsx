import { Card } from "@/components/ui/card";
import { FadeIn } from "@/components/landing/motion";
import { Section, SectionHeading } from "@/components/landing/sections";
import { FEATURES } from "@/components/landing/config";

export function Features() {
  return (
    <Section id="features" className="border-t">
      <SectionHeading
        eyebrow="Features"
        title="Everything a thorough reviewer checks"
        description="Four review agents, plus the workflow and history around them."
      />

      <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((feature, i) => {
          const Icon = feature.icon;
          return (
            <FadeIn key={feature.title} delay={(i % 4) * 0.06}>
              <Card className="h-full p-5 transition-colors hover:border-foreground/20">
                <div className="flex items-center justify-between">
                  <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  {feature.soon ? (
                    <span className="rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                      Coming soon
                    </span>
                  ) : null}
                </div>
                <h3 className="mt-4 text-sm font-semibold">{feature.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                  {feature.description}
                </p>
              </Card>
            </FadeIn>
          );
        })}
      </div>
    </Section>
  );
}
