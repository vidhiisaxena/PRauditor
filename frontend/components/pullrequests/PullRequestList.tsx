import { GitPullRequest } from "lucide-react";

import { EmptyState } from "@/components/common/EmptyState";
import { PRCard } from "@/components/pullrequests/PRCard";
import type { PullRequest } from "@/types";

/** Vertical list of pull request cards. */
export function PullRequestList({ pullRequests }: { pullRequests: PullRequest[] }) {
  if (pullRequests.length === 0) {
    return (
      <EmptyState
        icon={GitPullRequest}
        title="No pull requests"
        description="PRAuditor will list pull requests here as they are opened and reviewed."
      />
    );
  }

  return (
    <div className="space-y-3">
      {pullRequests.map((pr) => (
        <PRCard key={pr.id} pr={pr} />
      ))}
    </div>
  );
}
