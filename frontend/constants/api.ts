export const API_BASE_URL = "http://localhost:8000";

// I LITERALLY DON'T KNOW WHAT TO DO REVIEW THIS LATER RAHHHH

const NGROK_HEADERS: HeadersInit = {
  "ngrok-skip-browser-warning": "1",
};

/**
 * Use this for every backend API call. Adds ngrok header automatically so you
 * don't have to remember it. Pass a path (e.g. "/trips/airlines") or full URL.
 */
export function apiFetch(
  pathOrUrl: string,
  options: RequestInit = {},
): Promise<Response> {
  const url = pathOrUrl.startsWith("http")
    ? pathOrUrl
    : `${API_BASE_URL}${pathOrUrl.startsWith("/") ? "" : "/"}${pathOrUrl}`;
  const headers = new Headers(options.headers ?? {});
  Object.entries(NGROK_HEADERS).forEach(([k, v]) =>
    headers.set(k, Array.isArray(v) ? v.join(", ") : v),
  );
  return fetch(url, { ...options, headers });
}
