"use client";

import { useRouter } from "next/navigation";

export default function RefreshButton() {
  const router = useRouter();

  return (
    <button
      onClick={() => router.refresh()}
      className="inline-flex items-center px-4 py-2 border border-slate-600 text-sm font-medium rounded-md text-slate-200 bg-slate-700 hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 focus:ring-offset-slate-800"
    >
      Refresh
    </button>
  );
}
