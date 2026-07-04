import type { DownloadRequestPayload, DownloadResponse, InfoResponse } from "../types";

// Base URL is relative so it works through the Vite dev proxy (see
// vite.config.ts) in development, and same-origin in any future deploy.
const API_BASE = "/api";

async function parseErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail || body.error || response.statusText;
  } catch {
    return response.statusText || `Request failed (${response.status})`;
  }
}

export async function getInfo(url: string): Promise<InfoResponse> {
  const response = await fetch(`${API_BASE}/info`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}

export async function startDownload(
  payload: DownloadRequestPayload,
): Promise<DownloadResponse> {
  const response = await fetch(`${API_BASE}/download`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}

export function singleFileUrl(sessionId: string, filename: string): string {
  return `${API_BASE}/serve/${encodeURIComponent(sessionId)}/${encodeURIComponent(filename)}`;
}

export function zipFileUrl(sessionId: string): string {
  return `${API_BASE}/serve-zip/${encodeURIComponent(sessionId)}`;
}

/**
 * Ends a session and frees its temp files server-side. The backend no
 * longer deletes a playlist zip after a single serve (so re-clicking Save
 * works), so the frontend is responsible for cleaning up once the user is
 * actually done — see callers in App.tsx (Start over, starting a new
 * lookup) and the beforeunload handler (page close/navigate away).
 *
 * Uses sendBeacon when available since it's the only reliable way to fire
 * a request during beforeunload — a normal fetch can be cancelled by the
 * browser before it completes. sendBeacon can't set a DELETE method or
 * custom headers, so the backend route accepts this as a no-body POST-like
 * beacon too (see routes/serve.py).
 */
export function endSession(sessionId: string): void {
  const url = `${API_BASE}/session/${encodeURIComponent(sessionId)}`;
  if (navigator.sendBeacon) {
    navigator.sendBeacon(url);
    return;
  }
  fetch(url, { method: "DELETE", keepalive: true }).catch(() => {
    // Best-effort cleanup — nothing the user can do if this fails, and the
    // session will still be reachable/retryable until the process restarts.
  });
}
