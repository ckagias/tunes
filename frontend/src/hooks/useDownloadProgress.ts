import { useEffect, useRef, useState } from "react";
import { openProgressStream } from "../api/progress";
import type { ProgressEvent, TrackProgress } from "../types";

interface DownloadProgressState {
  tracks: Map<string, TrackProgress>;
  zipFilename: string | null;
  isComplete: boolean;
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
    case "all_done":
      return { ...state, tracks, isComplete: true };
    default:
      break;
  }

  return { ...state, tracks };
}

/**
 * Subscribes to the SSE progress stream for a download session and exposes
 * a reduced, render-friendly view: per-track status/percent, the playlist
 * zip filename (once ready), and whether the whole job has finished.
 */
export function useDownloadProgress(sessionId: string | null) {
  const [state, setState] = useState<DownloadProgressState>({
    tracks: new Map(),
    zipFilename: null,
    isComplete: false,
  });
  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    // Always reset first, even when sessionId is cleared (e.g. "Start
    // over") — otherwise a stale zipFilename/tracks from a previous session
    // lingers in state and, if a new session starts before its own
    // zip_ready arrives, the Save button renders pointing at the new
    // session's not-yet-ready zip using the old filename.
    setState({ tracks: new Map(), zipFilename: null, isComplete: false });

    if (!sessionId) return;

    const close = openProgressStream(sessionId, (event) => {
      setState((prev) => reduce(prev, event));
    });

    return close;
  }, [sessionId]);

  return state;
}
