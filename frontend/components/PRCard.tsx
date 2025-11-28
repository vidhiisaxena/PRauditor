import Link from "next/link";
import { PullRequest } from "@/types";

interface PRCardProps {
  pr: PullRequest;
}

export default function PRCard({ pr }: PRCardProps) {
  const stateColor =
    pr.state === "open"
      ? "bg-green-900/30 text-green-400 border-green-700"
      : pr.state === "closed"
      ? "bg-slate-700 text-slate-300 border-slate-600"
      : "bg-yellow-900/30 text-yellow-400 border-yellow-700";

  return (
    <div className="bg-slate-800 overflow-hidden shadow rounded-lg border border-slate-700">
      <div className="p-5">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-medium text-slate-100">
                #{pr.pr_number}
              </h3>
              {pr.state && (
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${stateColor}`}
                >
                  {pr.state}
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-slate-400">
              {pr.title || "No title"}
            </p>
            {pr.head_sha && (
              <p className="mt-1 text-xs text-slate-500 font-mono">
                {pr.head_sha.substring(0, 7)}
              </p>
            )}
          </div>
          <div className="ml-4">
            <Link
              href={`/prs/${pr.id}`}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 focus:ring-offset-slate-800"
            >
              View Review
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
