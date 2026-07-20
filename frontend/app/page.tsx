import { LandingNavbar } from "@/components/landing/LandingNavbar";
import { Hero } from "@/components/landing/Hero";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { Features } from "@/components/landing/Features";
// import { ArchitectureDiagram } from "@/components/landing/ArchitectureDiagram"; // internals kept private for now
import { InteractiveDemo } from "@/components/landing/InteractiveDemo";
// import { OpenSource } from "@/components/landing/OpenSource"; // hidden for now
import { CTA } from "@/components/landing/CTA";
import { LandingFooter } from "@/components/landing/LandingFooter";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <LandingNavbar />
      <main>
        <Hero />
        <HowItWorks />
        <Features />
        {/* <ArchitectureDiagram /> */}
        <InteractiveDemo />
        {/* <OpenSource /> */}
        <CTA />
      </main>
      <LandingFooter />
    </div>
  );
}
