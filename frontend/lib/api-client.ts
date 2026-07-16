import { API_BASE_URL } from "@/lib/config";

/**
 * Thin, typed fetch wrapper shared by every service in `services/`.
 * Services never call `fetch` directly and pages never call services'
 * transport — they go through hooks. This keeps transport concerns
 * (base URL, headers, error shape) in exactly one place.
 */

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

/**
 * Thrown by service methods that map to backend endpoints which do not exist
 * yet. Lets the UI render a graceful "coming soon" state instead of crashing.
 */
export class NotImplementedError extends Error {
  constructor(endpoint: string) {
    super(`Backend endpoint not implemented yet: ${endpoint}`);
    this.name = "NotImplementedError";
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers, ...rest } = options;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    // Always hit the backend for fresh data; caching is handled by TanStack Query.
    cache: "no-store",
  });

  if (!response.ok) {
    const errorBody = await safeParse(response);
    throw new ApiError(
      response.status,
      `Request failed: ${response.status} ${response.statusText}`,
      errorBody,
    );
  }

  // 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

async function safeParse(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
