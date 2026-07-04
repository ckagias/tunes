import type { DownloadRequestPayload, DownloadResponse, InfoResponse } from "../types";

// Relative so it works through the Vite dev proxy and same-origin in production.
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

// Ends a session and frees its temp files. sendBeacon survives page unload; fetch is the fallback.
export function endSession(sessionId: string): void {
  const url = `${API_BASE}/session/${encodeURIComponent(sessionId)}`;
  if (navigator.sendBeacon) {
    navigator.sendBeacon(url);
    return;
  }
  fetch(url, { method: "DELETE", keepalive: true }).catch(() => {
    // Best-effort cleanup — nothing to do client-side if this fails.
  });
}
