"use client";

import { GitMerge, MessageSquarePlus, RefreshCw } from "lucide-react";
import type { ComponentType } from "react";
import type { LucideProps } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface ActionDef {
  key: string;
  label: string;
  icon: ComponentType<LucideProps>;
  /** The backend endpoint this button will call once implemented. */
  endpoint: string;
}

const ACTIONS: ActionDef[] = [
  { key: "rerun", label: "Review again", icon: RefreshCw, endpoint: "POST /api/prs/{id}/rerun" },
  { key: "comment", label: "Post comment", icon: MessageSquarePlus, endpoint: "POST /api/prs/{id}/comment" },
  { key: "merge", label: "Merge PR", icon: GitMerge, endpoint: "POST /api/prs/{id}/merge" },
];

/**
 * Action panel for a review.
 *
 * All actions are intentionally DISABLED — the backend endpoints do not exist
 * yet. Wiring guide once they do:
 *   1. Add a mutation hook (e.g. useRerunReview) calling the matching service
 *      method in services/pullRequests.ts / services/reviews.ts.
 *   2. On success, invalidate queryKeys.reviewIssues(prId) (and dashboard).
 *   3. Wrap destructive actions (Merge) in <ConfirmDialog/>.
 */
export function ReviewActions({ prId }: { prId: number }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 pt-0">
        {ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <Button
              key={action.key}
              variant="outline"
              className="w-full justify-start"
              disabled
              title={`TODO: integrate ${action.endpoint.replace("{id}", String(prId))}`}
            >
              <Icon className="h-4 w-4" />
              {action.label}
            </Button>
          );
        })}
        <p className="pt-1 text-xs text-muted-foreground">
          Actions unlock once the backend endpoints ship.
        </p>
      </CardContent>
    </Card>
  );
}
