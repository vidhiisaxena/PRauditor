/**
 * Central frontend configuration. Anything environment-specific lives here so
 * pages/services never read `process.env` directly.
 */

// Base URL of the FastAPI backend. Override per-environment with
// NEXT_PUBLIC_BACKEND_URL (e.g. the Render URL in production).
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

// Default TanStack Query cache timings (ms).
export const QUERY_STALE_TIME = 30_000;
export const QUERY_GC_TIME = 5 * 60_000;
