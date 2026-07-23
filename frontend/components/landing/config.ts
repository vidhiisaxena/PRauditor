import {
  Boxes,
  FileCode2,
  GaugeCircle,
  GitBranch,
  History,
  ListChecks,
  ShieldCheck,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

/** External + internal links used across the landing page. */
export const LINKS = {
  github: "https://github.com/vidhiisaxena/PRauditor",
  docs: "/docs",
  login: "/login",
  getStarted: "/login",
};

export const NAV_LINKS = [
  { label: "Features", href: "#features" },
  { label: "How It Works", href: "#how-it-works" },
  // { label: "Open Source", href: "#open-source" }, // hidden for now
  { label: "Docs", href: LINKS.docs },
];

export interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
  soon?: boolean;
}

export const FEATURES: Feature[] = [
  {
    icon: ShieldCheck,
    title: "Security Analysis",
    description:
      "Flags injection, unsafe deserialization, hard-coded secrets, and missing auth checks before they ship.",
  },
  {
    icon: GaugeCircle,
    title: "Performance Review",
    description:
      "Catches N+1 queries, needless loops, and expensive work in hot paths on changed code.",
  },
  {
    icon: FileCode2,
    title: "Logic Detection",
    description:
      "Surfaces incorrect conditions, missing edge cases, and regressions a tired reviewer would miss.",
  },
  {
    icon: Sparkles,
    title: "Readability Improvements",
    description:
      "Suggests clearer names, less nesting, and comments where the logic actually gets hard.",
  },
  {
    icon: ListChecks,
    title: "Structured Markdown Reviews",
    description:
      "Posts a clean, grouped review comment back to the PR — by file, severity, and category.",
  },
  {
    icon: GitBranch,
    title: "GitHub Integration",
    description:
      "Installs as a GitHub App. Reviews every pull request automatically via webhooks.",
  },
  {
    icon: History,
    title: "Review History",
    description:
      "Every review is stored, so you can revisit findings across a repository over time.",
  },
  {
    icon: Boxes,
    title: "Risk Scoring",
    description:
      "A single score per PR from severity mix, complexity, and file count.",
    soon: true,
  },
];

export interface Step {
  title: string;
  description: string;
}

export const STEPS: Step[] = [
  {
    title: "Connect your repositories",
    description:
      "Install the GitHub App on the repos you care about — two clicks, no config files, nothing to wire into CI.",
  },
  {
    title: "Open a pull request",
    description:
      "Keep working exactly how you do today. The moment a PR opens or gets new commits, PRAuditor quietly wakes up.",
  },
  {
    title: "Get a real review",
    description:
      "It reads every changed line and leaves clear, categorized feedback right on the PR — security, logic, performance, and readability.",
  },
  {
    title: "Merge with confidence",
    description:
      "No more rubber-stamping code nobody actually read. Ship knowing it was genuinely reviewed.",
  },
];

export const ARCHITECTURE_NODES = [
  "GitHub",
  "Webhook",
  "FastAPI",
  "Review Engine",
  "PostgreSQL",
  "GitHub Comment",
  "Dashboard",
];
