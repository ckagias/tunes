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
