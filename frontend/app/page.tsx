import Link from "next/link";
import { checkBackendStatus } from "@/lib/api";

export default async function Home() {
  let backendStatus = "Offline";
  let backendStatusColor = "text-red-600";

  try {
    await checkBackendStatus();
    backendStatus = "Online";
    backendStatusColor = "text-green-600";
  } catch (error) {
    backendStatus = "Offline";
    backendStatusColor = "text-red-600";
  }

  const statusColorClass =
    backendStatus === "Online" ? "text-green-400" : "text-red-400";

  return (
    <div className="px-4 py-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-100 mb-4">
          Welcome to PRAuditor
        </h1>
        <p className="text-lg text-slate-400 mb-8">
          Automated Pull Request Review Agent Dashboard
        </p>

        <div className="bg-slate-800 shadow rounded-lg border border-slate-700 p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-medium text-slate-100">
                Backend Status
              </h2>
              <p className="text-sm text-slate-400 mt-1">
                Connection to API server
              </p>
            </div>
            <div className={`text-lg font-semibold ${statusColorClass}`}>
              {backendStatus}
            </div>
          </div>
        </div>

        <div className="flex space-x-4">
          <Link
            href="/repos"
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 focus:ring-offset-slate-900"
          >
            View Repositories
          </Link>
        </div>
      </div>
    </div>
  );
}
