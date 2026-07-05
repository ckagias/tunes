import { useEffect, useRef, useState } from "react";
import { openProgressStream } from "../api/progress";
import type { ProgressEvent, TrackProgress } from "../types";

export interface ImportStatus {
  state: "importing" | "done" | "error";
  added?: number;
  total?: number;
  message?: string;
}

interface DownloadProgressState {
  tracks: Map<string, TrackProgress>;
  zipFilename: string | null;
  isComplete: boolean;
  importStatus: ImportStatus | null;
}

function reduce(
  state: DownloadProgressState,
  event: ProgressEvent,
): DownloadProgressState {
  const tracks = new Map(state.tracks);

  const patchTrack = (url: string, patch: Partial<TrackProgress>) => {
    const existing = tracks.get(url) ?? {
      url,
      title: patch.title ?? url,
      status: "pending" as const,
      percent: 0,
    };
    tracks.set(url, { ...existing, ...patch });
  };

  switch (event.type) {
    case "started":
      patchTrack(event.url, { title: event.title, status: "downloading", percent: 0 });
      break;
    case "progress":
      patchTrack(event.url, {
        title: event.title,
        status: "downloading",
        percent: event.percent,
        speed: event.speed,
        eta: event.eta,
      });
      break;
    case "converting":
      patchTrack(event.url, { title: event.title, status: "converting" });
      break;
    case "track_done":
      patchTrack(event.url, {
        title: event.title,
        status: "done",
        percent: 100,
        filename: event.filename,
      });
      break;
    case "track_error":
      patchTrack(event.url, {
        title: event.title,
        status: "error",
        errorMessage: event.message,
      });
      break;
    case "zip_ready":
      return { ...state, tracks, zipFilename: event.filename };
    case "importing":
      return { ...state, tracks, importStatus: { state: "importing" } };
    case "imported":
      return {
        ...state,
        tracks,
        importStatus: {
          state: "done",
          added: event.added,
          total: event.total,
          message: event.message,
        },
      };
    case "import_error":
      return {
        ...state,
        tracks,
        importStatus: { state: "error", message: event.message },
      };
    case "all_done":
      return { ...state, tracks, isComplete: true };
    default:
      break;
  }

  return { ...state, tracks };
}

// Subscribes to the SSE progress stream, exposing per-track status, zip filename, and completion.
export function useDownloadProgress(sessionId: string | null) {
  const [state, setState] = useState<DownloadProgressState>({
    tracks: new Map(),
    zipFilename: null,
    isComplete: false,
    importStatus: null,
  });
  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    // Reset even when sessionId is cleared, or a stale zipFilename could leak into the next session.
    setState({ tracks: new Map(), zipFilename: null, isComplete: false, importStatus: null });

    if (!sessionId) return;

    const close = openProgressStream(sessionId, (event) => {
      setState((prev) => reduce(prev, event));
    });

    return close;
  }, [sessionId]);

  return state;
}
