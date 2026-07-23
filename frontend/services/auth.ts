import { apiClient } from "@/lib/api-client";
import { API_BASE_URL } from "@/lib/config";
import type { AuthUser } from "@/types";

/**
 * Auth service. `getMe` and `logout` go through the credentialed api-client so
 * the session cookie rides along. Login is a full-page redirect to the backend
 * (OAuth must be a top-level navigation, not a fetch) — the frontend never
 * builds the GitHub OAuth URL itself.
 */
export const authService = {
  getMe(): Promise<AuthUser> {
    return apiClient.get<AuthUser>("/api/auth/me");
  },

  logout(): Promise<void> {
    return apiClient.post<void>("/api/auth/logout");
  },

  loginUrl(): string {
    return `${API_BASE_URL}/api/auth/github/login`;
  },
};
