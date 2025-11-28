const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function apiGet<T>(path: string): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export async function checkBackendStatus(): Promise<{ status: string }> {
  try {
    const response = await fetch(`${BASE_URL}/`, {
      cache: "no-store",
    });
    if (response.ok) {
      return await response.json();
    }
    throw new Error("Backend not responding");
  } catch (error) {
    throw new Error("Backend offline");
  }
}
