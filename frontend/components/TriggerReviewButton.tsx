"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface TriggerReviewButtonProps {
  prId: number;
}

export default function TriggerReviewButton({
  prId,
}: TriggerReviewButtonProps) {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleTrigger = async () => {
    if (loading) return;

    setLoading(true);
    const BASE_URL =
      process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

    try {
      const response = await fetch(
        `${BASE_URL}/api/prs/${prId}/trigger-review`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        const error = await response
          .json()
          .catch(() => ({ detail: "Unknown error" }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      alert(`Review triggered successfully! Found ${data.issues} issues.`);

      // Refresh the page to show new issues
      router.refresh();
    } catch (error) {
      alert(
        `Failed to trigger review: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleTrigger}
      disabled={loading}
      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {loading ? "Triggering..." : "Trigger Review Again"}
    </button>
  );
}
