import Link from "next/link";
import { Repository } from "@/types";

interface RepoCardProps {
  repo: Repository;
}

export default function RepoCard({ repo }: RepoCardProps) {
  return (
    <div className="bg-slate-800 overflow-hidden shadow rounded-lg border border-slate-700">
      <div className="p-5">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-medium text-slate-100">
              {repo.full_name}
            </h3>
          </div>
          <div className="ml-4">
            <Link
              href={`/repos/${repo.id}`}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 focus:ring-offset-slate-800"
            >
              View PRs
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
