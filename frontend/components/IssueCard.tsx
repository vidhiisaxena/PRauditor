import SeverityBadge from "./SeverityBadge";
import { ReviewIssue } from "@/types";

interface IssueCardProps {
  issue: ReviewIssue;
}

export default function IssueCard({ issue }: IssueCardProps) {
  return (
    <div className="bg-slate-800 overflow-hidden shadow rounded-lg border border-slate-700">
      <div className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <SeverityBadge severity={issue.severity} />
              <span className="text-sm font-medium text-slate-300">
                {issue.kind}
              </span>
            </div>
            <div className="mt-2">
              <p className="text-sm font-mono text-slate-400">
                {issue.file_path}
                {issue.line !== null && `:${issue.line}`}
              </p>
            </div>
            <div className="mt-3">
              <p className="text-sm text-slate-100">{issue.message}</p>
              {issue.suggestion && (
                <div className="mt-2 p-3 bg-slate-900/50 rounded-md border border-slate-700">
                  <p className="text-xs font-medium text-slate-400 mb-1">
                    Suggestion:
                  </p>
                  <p className="text-sm text-slate-300">{issue.suggestion}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
